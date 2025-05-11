# import frappe
# from frappe import _
# from frappe.utils import now_datetime
# from woocommerce import API
# import json
# from .config.woocommerce_config import WOOCOMMERCE_CONFIG, SYNC_CONFIG
# from .utils.logger import WooCommerceLogger

# class WooCommerceSync:
#     def __init__(self):
#         self.config = WOOCOMMERCE_CONFIG
#         self.sync_config = SYNC_CONFIG
#         self.validate_config()
#         self.wcapi = self.get_wcapi()

#     def validate_config(self):
#         """Validate WooCommerce configuration"""
#         if not self.config["url"] or not self.config["consumer_key"] or not self.config["consumer_secret"]:
#             WooCommerceLogger.log_error(
#                 "WooCommerce configuration is incomplete",
#                 details={"config": self.config}
#             )
#             frappe.throw(_("WooCommerce configuration is incomplete. Please check woocommerce_config.py"))

#     def get_wcapi(self):
#         """Initialize WooCommerce API client"""
#         return API(
#             url=self.config["url"],
#             consumer_key=self.config["consumer_key"],
#             consumer_secret=self.config["consumer_secret"],
#             version=self.config["version"],
#             verify_ssl=self.config["verify_ssl"],
#             timeout=self.config["timeout"]
#         )

#     def sync_from_woocommerce(self):
#         """Sync orders from WooCommerce to ERPNext"""
#         if not self.sync_config["enable_sync"]:
#             WooCommerceLogger.log_error("WooCommerce sync is disabled")
#             return

#         WooCommerceLogger.log_sync_start()
#         try:
#             # Get orders from WooCommerce
#             response = self.wcapi.get("orders", params={"status": "processing"})
            
#             if response.status_code != 200:
#                 error_msg = f"Failed to fetch WooCommerce orders: {response.text}"
#                 WooCommerceLogger.log_error(error_msg, details={"response": response.text})
#                 frappe.throw(error_msg)

#             orders = response.json()
#             WooCommerceLogger.log(
#                 "Sync",
#                 "Info",
#                 f"Found {len(orders)} orders to sync",
#                 details={"order_count": len(orders)}
#             )
            
#             for order in orders:
#                 self.create_erpnext_order(order)

#             # Update sync status
#             self.sync_config["last_sync"] = now_datetime()
#             self.sync_config["sync_status"] = "Success"
#             self.save_sync_status()

#             WooCommerceLogger.log_sync_end(True, f"Successfully synced {len(orders)} orders")

#         except Exception as e:
#             self.sync_config["sync_status"] = f"Failed: {str(e)}"
#             self.save_sync_status()
#             WooCommerceLogger.log_sync_end(False, str(e))
#             WooCommerceLogger.log_error("WooCommerce Sync Error", e)

#     def create_erpnext_order(self, wc_order):
#         """Create Sales Order in ERPNext from WooCommerce order"""
#         try:
#             # Check if order already exists
#             existing_order = frappe.get_all(
#                 "Sales Order",
#                 filters={"woocommerce_order_id": str(wc_order["id"])},
#                 fields=["name"]
#             )

#             if existing_order:
#                 WooCommerceLogger.log(
#                     "Order",
#                     "Warning",
#                     f"Order {wc_order['id']} already exists in ERPNext",
#                     details={"order_id": wc_order["id"], "existing_order": existing_order[0]["name"]}
#                 )
#                 return

#             # Get or create customer
#             customer = self.get_or_create_customer(wc_order)

#             # Create Sales Order
#             sales_order = frappe.get_doc({
#                 "doctype": "Sales Order",
#                 "customer": customer,
#                 "delivery_date": frappe.utils.today(),
#                 "woocommerce_order_id": str(wc_order["id"]),
#                 "items": self.get_order_items(wc_order),
#                 "taxes_and_charges": self.get_tax_template(),
#                 "taxes": self.get_tax_details(wc_order),
#                 "status": "Draft"
#             })

#             sales_order.insert()
#             sales_order.submit()
#             frappe.db.commit()

#             WooCommerceLogger.log_order_creation(
#                 wc_order["id"],
#                 True,
#                 reference_name=sales_order.name
#             )

#         except Exception as e:
#             WooCommerceLogger.log_order_creation(wc_order["id"], False, e)
#             raise

#     def get_or_create_customer(self, wc_order):
#         """Get or create customer in ERPNext"""
#         try:
#             # Check if customer exists by email
#             customer_email = wc_order["billing"]["email"]
#             existing_customer = frappe.get_all(
#                 "Customer",
#                 filters={"email_id": customer_email},
#                 fields=["name"]
#             )

#             if existing_customer:
#                 WooCommerceLogger.log(
#                     "Customer",
#                     "Info",
#                     f"Found existing customer: {existing_customer[0]['name']}",
#                     details={"email": customer_email}
#                 )
#                 return existing_customer[0]["name"]

#             # Create new customer
#             customer = frappe.get_doc({
#                 "doctype": "Customer",
#                 "customer_name": f"{wc_order['billing']['first_name']} {wc_order['billing']['last_name']}",
#                 "customer_type": "Individual",
#                 "customer_group": "Commercial",
#                 "territory": "United States",
#                 "email_id": customer_email,
#                 "phone": wc_order["billing"]["phone"],
#                 "address_line1": wc_order["billing"]["address_1"],
#                 "city": wc_order["billing"]["city"],
#                 "state": wc_order["billing"]["state"],
#                 "pincode": wc_order["billing"]["postcode"],
#                 "country": wc_order["billing"]["country"]
#             })

#             customer.insert()
#             frappe.db.commit()

#             WooCommerceLogger.log_customer_creation(customer.customer_name, True)
#             return customer.name

#         except Exception as e:
#             WooCommerceLogger.log_customer_creation(
#                 f"{wc_order['billing']['first_name']} {wc_order['billing']['last_name']}",
#                 False,
#                 e
#             )
#             raise

#     def get_order_items(self, wc_order):
#         """Get items for ERPNext Sales Order"""
#         items = []
#         for item in wc_order["line_items"]:
#             # Get or create item
#             item_code = self.get_or_create_item(item)
            
#             items.append({
#                 "item_code": item_code,
#                 "qty": item["quantity"],
#                 "rate": float(item["price"]),
#                 "amount": float(item["total"])
#             })
#         return items

#     def get_or_create_item(self, wc_item):
#         """Get or create item in ERPNext"""
#         try:
#             # Check if item exists by SKU
#             existing_item = frappe.get_all(
#                 "Item",
#                 filters={"item_code": wc_item["sku"]},
#                 fields=["name"]
#             )

#             if existing_item:
#                 WooCommerceLogger.log(
#                     "Item",
#                     "Info",
#                     f"Found existing item: {existing_item[0]['name']}",
#                     details={"sku": wc_item["sku"]}
#                 )
#                 return existing_item[0]["name"]

#             # Create new item
#             item = frappe.get_doc({
#                 "doctype": "Item",
#                 "item_code": wc_item["sku"],
#                 "item_name": wc_item["name"],
#                 "item_group": "Products",
#                 "description": wc_item.get("description", ""),
#                 "stock_uom": "Nos",
#                 "is_stock_item": 1
#             })

#             item.insert()
#             frappe.db.commit()

#             WooCommerceLogger.log_item_creation(item.item_code, True)
#             return item.name

#         except Exception as e:
#             WooCommerceLogger.log_item_creation(wc_item["sku"], False, e)
#             raise

#     def get_tax_template(self):
#         """Get default tax template"""
#         tax_templates = frappe.get_all("Tax Template", fields=["name"])
#         return tax_templates[0]["name"] if tax_templates else None

#     def get_tax_details(self, wc_order):
#         """Get tax details for Sales Order"""
#         taxes = []
#         for tax in wc_order.get("tax_lines", []):
#             taxes.append({
#                 "charge_type": "On Net Total",
#                 "account_head": self.get_tax_account(),
#                 "rate": float(tax["rate"]),
#                 "description": tax["label"]
#             })
#         return taxes

#     def get_tax_account(self):
#         """Get default tax account"""
#         tax_accounts = frappe.get_all("Account", filters={"account_type": "Tax"}, fields=["name"])
#         return tax_accounts[0]["name"] if tax_accounts else None

#     def save_sync_status(self):
#         """Save sync status to a file"""
#         try:
#             with open("woocommerce_sync_status.json", "w") as f:
#                 json.dump({
#                     "last_sync": str(self.sync_config["last_sync"]),
#                     "sync_status": self.sync_config["sync_status"]
#                 }, f)
#         except Exception as e:
#             WooCommerceLogger.log_error("Error saving sync status", e)

#     def get_sync_status(self):
#         """Get current sync status"""
#         try:
#             with open("woocommerce_sync_status.json", "r") as f:
#                 return json.load(f)
#         except FileNotFoundError:
#             return {
#                 "last_sync": None,
#                 "sync_status": "No sync performed yet"
#             } 