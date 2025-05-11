import frappe
from frappe import _
from frappe.utils import now_datetime
from woocommerce import API
import json
from woocommerce_sync.config.woocommerce_config import WOOCOMMERCE_CONFIG, SYNC_CONFIG
from woocommerce_sync.utils.logger import WooCommerceLogger

class WooCommerceSync:
    def __init__(self):
        self.config = WOOCOMMERCE_CONFIG
        self.sync_config = SYNC_CONFIG
        self.validate_config()
        self.wcapi = self.get_wcapi()

    def validate_config(self):
        """Validate WooCommerce configuration"""
        if not self.config["url"] or not self.config["consumer_key"] or not self.config["consumer_secret"]:
            WooCommerceLogger.log_error(
                "WooCommerce configuration is incomplete",
                details={"config": self.config}
            )
            frappe.throw(_("WooCommerce configuration is incomplete. Please check woocommerce_config.py"))

    def get_wcapi(self):
        """Initialize WooCommerce API client"""
        return API(
            url=self.config["url"],
            consumer_key=self.config["consumer_key"],
            consumer_secret=self.config["consumer_secret"],
            version=self.config["version"],
            verify_ssl=self.config["verify_ssl"],
            timeout=self.config["timeout"]
        )

    def sync_from_woocommerce(self):
        """Sync orders from WooCommerce to ERPNext"""
        if not self.sync_config["enable_sync"]:
            WooCommerceLogger.log_error("WooCommerce sync is disabled")
            return

        WooCommerceLogger.log_sync_start()
        try:
            # Get orders from WooCommerce with all statuses
            response = self.wcapi.get("orders", params={
                "status": "pending,processing,on-hold,completed,cancelled,refunded,failed"
            })
            
            if response.status_code != 200:
                error_msg = f"Failed to fetch WooCommerce orders: {response.text}"
                WooCommerceLogger.log_error(error_msg, details={"response": response.text})
                frappe.throw(error_msg)

            orders = response.json()
            WooCommerceLogger.log(
                "Sync",
                "Info",
                f"Found {len(orders)} orders to sync",
                details={"order_count": len(orders)}
            )
            
            for order in orders:
                self.create_erpnext_order(order)

            # Update sync status
            self.sync_config["last_sync"] = now_datetime()
            self.sync_config["sync_status"] = "Success"
            self.save_sync_status()

            WooCommerceLogger.log_sync_end(True, f"Successfully synced {len(orders)} orders")

        except Exception as e:
            self.sync_config["sync_status"] = f"Failed: {str(e)}"
            self.save_sync_status()
            WooCommerceLogger.log_sync_end(False, str(e))
            WooCommerceLogger.log_error("WooCommerce Sync Error", e)

    def get_erpnext_status(self, wc_status):
        """Map WooCommerce status to ERPNext status"""
        status_mapping = {
            "pending": "Draft",
            "processing": "To Deliver and Bill",
            "on-hold": "On Hold",
            "completed": "Completed",
            "cancelled": "Cancelled",
            "refunded": "Closed",
            "failed": "Cancelled"
        }
        return status_mapping.get(wc_status, "Draft")

    def create_erpnext_order(self, wc_order):
        """Create Sales Order in ERPNext from WooCommerce order"""
        try:
            # Check if order already exists
            existing_order = frappe.get_all(
                "Sales Order",
                filters={"woocommerce_order_id": str(wc_order["id"])},
                fields=["name"]
            )

            if existing_order:
                # Update existing order status if needed
                existing_order_doc = frappe.get_doc("Sales Order", existing_order[0]["name"])
                new_status = self.get_erpnext_status(wc_order["status"])
                
                if existing_order_doc.status != new_status:
                    existing_order_doc.status = new_status
                    existing_order_doc.save()
                    frappe.db.commit()
                    WooCommerceLogger.log(
                        "Order",
                        "Info",
                        f"Updated order {wc_order['id']} status to {new_status}",
                        details={"order_id": wc_order["id"], "old_status": existing_order_doc.status, "new_status": new_status}
                    )
                return

            # Get or create customer
            customer = self.get_or_create_customer(wc_order)

            # Create Sales Order
            sales_order = frappe.get_doc({
                "doctype": "Sales Order",
                "customer": customer,
                "delivery_date": frappe.utils.today(),
                "woocommerce_order_id": str(wc_order["id"]),
                "items": self.get_order_items(wc_order),
                "taxes_and_charges": self.get_tax_template(),
                "taxes": self.get_tax_details(wc_order),
                "status": self.get_erpnext_status(wc_order["status"])
            })

            sales_order.insert()
            
            # Only submit if the status is not Draft or Cancelled
            if sales_order.status not in ["Draft", "Cancelled"]:
                sales_order.submit()
            
            frappe.db.commit()

            WooCommerceLogger.log_order_creation(
                wc_order["id"],
                True,
                reference_name=sales_order.name
            )

        except Exception as e:
            WooCommerceLogger.log_order_creation(wc_order["id"], False, e)
            raise

    def get_or_create_customer(self, wc_order):
        """Get or create customer in ERPNext"""
        try:
            # Check if customer exists by email
            customer_email = wc_order["billing"]["email"]
            existing_customer = frappe.get_all(
                "Customer",
                filters={"email_id": customer_email},
                fields=["name"]
            )

            if existing_customer:
                WooCommerceLogger.log(
                    "Customer",
                    "Info",
                    f"Found existing customer: {existing_customer[0]['name']}",
                    details={"email": customer_email}
                )
                return existing_customer[0]["name"]

            # Create new customer
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": f"{wc_order['billing']['first_name']} {wc_order['billing']['last_name']}",
                "customer_type": "Individual",
                "customer_group": "Commercial",
                "territory": "United States",
                "email_id": customer_email,
                "phone": wc_order["billing"]["phone"],
                "address_line1": wc_order["billing"]["address_1"],
                "city": wc_order["billing"]["city"],
                "state": wc_order["billing"]["state"],
                "pincode": wc_order["billing"]["postcode"],
                "country": wc_order["billing"]["country"]
            })

            customer.insert()
            frappe.db.commit()

            WooCommerceLogger.log_customer_creation(customer.customer_name, True)
            return customer.name

        except Exception as e:
            WooCommerceLogger.log_customer_creation(
                f"{wc_order['billing']['first_name']} {wc_order['billing']['last_name']}",
                False,
                e
            )
            raise

    def get_order_items(self, wc_order):
        """Get items for ERPNext Sales Order"""
        items = []
        for item in wc_order["line_items"]:
            # Get or create item
            item_code = self.get_or_create_item(item)
            
            items.append({
                "item_code": item_code,
                "qty": item["quantity"],
                "rate": float(item["price"]),
                "amount": float(item["total"])
            })
        return items

    def get_or_create_item(self, wc_item):
        """Get or create item in ERPNext"""
        try:
            # Generate item code from SKU or product name
            item_code = wc_item.get("sku")
            if not item_code:
                # If SKU is not available, create a code from product name
                item_code = frappe.scrub(wc_item["name"])[:20]  # Take first 20 chars of scrubbed name
                # Add a random suffix to ensure uniqueness
                item_code = f"{item_code}-{frappe.generate_hash(length=4)}"

            # Check if item exists by item_code
            existing_item = frappe.get_all(
                "Item",
                filters={"item_code": item_code},
                fields=["name"]
            )

            if existing_item:
                WooCommerceLogger.log(
                    "Item",
                    "Info",
                    f"Found existing item: {existing_item[0]['name']}",
                    details={"item_code": item_code}
                )
                return existing_item[0]["name"]

            # Create new item
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": wc_item["name"],
                "description": wc_item.get("description", ""),
                "item_group": "WooCommerce Products",
                "stock_uom": "Oz",
                "is_stock_item": 1,
                "include_item_in_manufacturing": 0,
                "is_sales_item": 1,
                "is_purchase_item": 1
            })

            item.insert()
            frappe.db.commit()

            WooCommerceLogger.log_item_creation(item.item_code, True)
            return item.name

        except Exception as e:
            WooCommerceLogger.log_item_creation(item_code if 'item_code' in locals() else 'unknown', False, e)
            raise

    def get_tax_template(self):
        """Get default tax template"""
        return frappe.get_value("Tax Template", {"is_default": 1}, "name")

    def get_tax_details(self, wc_order):
        """Get tax details for Sales Order"""
        tax_details = []
        if wc_order.get("tax_lines"):
            for tax in wc_order["tax_lines"]:
                tax_details.append({
                    "charge_type": "On Net Total",
                    "account_head": self.get_tax_account(),
                    "rate": float(tax["rate"]),
                    "description": tax["label"]
                })
        return tax_details

    def get_tax_account(self):
        """Get default tax account"""
        return frappe.get_value("Account", {"is_default": 1, "account_type": "Tax"}, "name")

    def save_sync_status(self):
        """Save sync status to configuration"""
        try:
            with open("woocommerce_config.py", "w") as f:
                f.write(f"""
# WooCommerce API Configuration
WOOCOMMERCE_CONFIG = {WOOCOMMERCE_CONFIG}

# Sync Configuration
SYNC_CONFIG = {SYNC_CONFIG}
                """)
        except Exception as e:
            WooCommerceLogger.log_error("Failed to save sync status", e)

    def get_sync_status(self):
        """Get current sync status"""
        return {
            "last_sync": self.sync_config.get("last_sync"),
            "sync_status": self.sync_config.get("sync_status"),
            "enable_sync": self.sync_config.get("enable_sync", False)
        } 