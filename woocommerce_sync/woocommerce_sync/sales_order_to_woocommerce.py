import frappe
from frappe import _
from frappe.utils import now_datetime
from woocommerce import API
import json
from .config.woocommerce_config import WOOCOMMERCE_CONFIG, SYNC_CONFIG

class WooCommerceSync:
    def __init__(self):
        self.config = WOOCOMMERCE_CONFIG
        self.sync_config = SYNC_CONFIG
        self.validate_config()
        self.wcapi = self.get_wcapi()

    def validate_config(self):
        """Validate WooCommerce configuration"""
        if not self.config["url"] or not self.config["consumer_key"] or not self.config["consumer_secret"]:
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

    def sync_sales_orders(self):
        """Sync sales orders from ERPNext to WooCommerce"""
        if not self.sync_config["enable_sync"]:
            frappe.log_error("WooCommerce sync is disabled", "WooCommerce Sync")
            return

        try:
            # Get sales orders that need to be synced
            sales_orders = frappe.get_all(
                "Sales Order",
                filters={
                    "docstatus": 1,
                    "per_delivered": 100,
                    "woocommerce_order_id": ["is", "null"]
                },
                fields=["name", "customer", "delivery_date", "total", "items"]
            )

            for so in sales_orders:
                self.create_woocommerce_order(so)

            # Update sync status
            self.sync_config["last_sync"] = now_datetime()
            self.sync_config["sync_status"] = "Success"
            self.save_sync_status()

        except Exception as e:
            self.sync_config["sync_status"] = f"Failed: {str(e)}"
            self.save_sync_status()
            frappe.log_error(f"WooCommerce Sync Error: {str(e)}", "WooCommerce Sync Error")

    def save_sync_status(self):
        """Save sync status to a file"""
        try:
            with open("woocommerce_sync_status.json", "w") as f:
                json.dump({
                    "last_sync": str(self.sync_config["last_sync"]),
                    "sync_status": self.sync_config["sync_status"]
                }, f)
        except Exception as e:
            frappe.log_error(f"Error saving sync status: {str(e)}", "WooCommerce Sync Status Error")

    def get_sync_status(self):
        """Get current sync status"""
        try:
            with open("woocommerce_sync_status.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "last_sync": None,
                "sync_status": "No sync performed yet"
            }

    def create_woocommerce_order(self, sales_order):
        """Create order in WooCommerce"""
        try:
            # Get customer details
            customer = frappe.get_doc("Customer", sales_order.customer)
            
            # Prepare order data
            order_data = {
                "customer_id": self.get_or_create_customer(customer),
                "status": "processing",
                "billing": {
                    "first_name": customer.customer_name,
                    "email": customer.email_id or "",
                    "phone": customer.phone or "",
                    "address_1": customer.address_line1 or "",
                    "city": customer.city or "",
                    "state": customer.state or "",
                    "postcode": customer.pincode or "",
                    "country": customer.country or ""
                },
                "shipping": {
                    "first_name": customer.customer_name,
                    "address_1": customer.address_line1 or "",
                    "city": customer.city or "",
                    "state": customer.state or "",
                    "postcode": customer.pincode or "",
                    "country": customer.country or ""
                },
                "line_items": self.get_line_items(sales_order),
                "payment_method": "bacs",
                "payment_method_title": "Direct Bank Transfer",
                "set_paid": True
            }

            # Create order in WooCommerce
            response = self.wcapi.post("orders", order_data)
            
            if response.status_code == 201:
                # Update sales order with WooCommerce order ID
                frappe.db.set_value(
                    "Sales Order",
                    sales_order.name,
                    "woocommerce_order_id",
                    response.json()["id"]
                )
                frappe.db.commit()
            else:
                frappe.throw(f"Failed to create WooCommerce order: {response.text}")

        except Exception as e:
            frappe.log_error(f"Error creating WooCommerce order: {str(e)}", "WooCommerce Order Creation Error")
            raise

    def get_or_create_customer(self, customer):
        """Get or create customer in WooCommerce"""
        try:
            # Search for existing customer
            response = self.wcapi.get("customers", params={"search": customer.email_id})
            
            if response.status_code == 200 and response.json():
                return response.json()[0]["id"]
            
            # Create new customer
            customer_data = {
                "email": customer.email_id or f"{customer.name}@example.com",
                "first_name": customer.customer_name,
                "billing": {
                    "first_name": customer.customer_name,
                    "email": customer.email_id or "",
                    "phone": customer.phone or "",
                    "address_1": customer.address_line1 or "",
                    "city": customer.city or "",
                    "state": customer.state or "",
                    "postcode": customer.pincode or "",
                    "country": customer.country or ""
                }
            }
            
            response = self.wcapi.post("customers", customer_data)
            if response.status_code == 201:
                return response.json()["id"]
            else:
                frappe.throw(f"Failed to create WooCommerce customer: {response.text}")

        except Exception as e:
            frappe.log_error(f"Error in get_or_create_customer: {str(e)}", "WooCommerce Customer Creation Error")
            raise

    def get_line_items(self, sales_order):
        """Get line items for WooCommerce order"""
        items = []
        for item in frappe.get_doc("Sales Order", sales_order.name).items:
            items.append({
                "product_id": self.get_or_create_product(item),
                "quantity": item.qty,
                "total": str(item.amount)
            })
        return items

    def get_or_create_product(self, item):
        """Get or create product in WooCommerce"""
        try:
            # Search for existing product
            response = self.wcapi.get("products", params={"search": item.item_code})
            
            if response.status_code == 200 and response.json():
                return response.json()[0]["id"]
            
            # Create new product
            product_data = {
                "name": item.item_name,
                "type": "simple",
                "regular_price": str(item.rate),
                "description": item.description or "",
                "sku": item.item_code
            }
            
            response = self.wcapi.post("products", product_data)
            if response.status_code == 201:
                return response.json()["id"]
            else:
                frappe.throw(f"Failed to create WooCommerce product: {response.text}")

        except Exception as e:
            frappe.log_error(f"Error in get_or_create_product: {str(e)}", "WooCommerce Product Creation Error")
            raise 