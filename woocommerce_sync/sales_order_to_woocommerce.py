import frappe
from frappe import _
from frappe.utils import now_datetime
from woocommerce import API
import json
from woocommerce_sync.config.woocommerce_config import get_woocommerce_config, get_sync_config, update_sync_status
from woocommerce_sync.utils.logger import WooCommerceLogger

class WooCommerceSync:
    def __init__(self):
        self.config = get_woocommerce_config()
        self.sync_config = get_sync_config()
        self.validate_config()
        self.wcapi = self.get_wcapi()

    def validate_config(self):
        """Validate WooCommerce configuration"""
        if not self.config["url"] or not self.config["consumer_key"] or not self.config["consumer_secret"]:
            WooCommerceLogger.log_error(
                "WooCommerce configuration is incomplete",
                details={"config": self.config}
            )
            frappe.throw(_("WooCommerce configuration is incomplete. Please check WooCommerce Settings doctype."))

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
            
            orders = self.validate_api_response(response, "fetch orders")
            WooCommerceLogger.log(
                "Sync",
                "Info",
                f"Found {len(orders)} orders to sync",
                details={"order_count": len(orders)}
            )
            
            successful_syncs = 0
            failed_syncs = 0
            skipped_orders = []

            for order in orders:
                try:
                    # Validate order data first
                    self.validate_woocommerce_order(order)
                    self.create_erpnext_order(order)
                    successful_syncs += 1
                except Exception as e:
                    failed_syncs += 1
                    error_details = {
                        "order_id": order.get("id", "unknown"),
                        "error": str(e),
                        "order_data": {
                            "status": order.get("status"),
                            "customer_email": order.get("billing", {}).get("email"),
                            "total": order.get("total")
                        }
                    }
                    WooCommerceLogger.log(
                        "Order",
                        "Info",
                        f"Failed to sync order {order.get('id', 'unknown')}: {str(e)}",
                        details=error_details
                    )
                    skipped_orders.append(error_details)

            # Update sync status
            self.sync_config["last_sync"] = now_datetime()
            self.sync_config["sync_status"] = "Partial Success" if failed_syncs > 0 else "Success"
            self.save_sync_status()

            # Log final sync summary
            WooCommerceLogger.log(
                "Sync",
                "Info",
                f"Sync completed. Successful: {successful_syncs}, Failed: {failed_syncs}",
                details={
                    "successful_syncs": successful_syncs,
                    "failed_syncs": failed_syncs,
                    "skipped_orders": skipped_orders
                }
            )

            WooCommerceLogger.log_sync_end(True, f"Successfully synced {successful_syncs} orders, {failed_syncs} failed")

        except Exception as e:
            self.sync_config["sync_status"] = f"Failed: {str(e)}"
            self.save_sync_status()
            WooCommerceLogger.log_sync_end(False, str(e))
            WooCommerceLogger.log_error("WooCommerce Sync Error", e)

    def validate_api_response(self, response, operation="fetch orders"):
        """Validate WooCommerce API response"""
        if response.status_code != 200:
            error_msg = f"WooCommerce API error during {operation}: {response.status_code} - {response.text}"
            WooCommerceLogger.log_error(error_msg, details={
                "status_code": response.status_code,
                "response_text": response.text,
                "operation": operation
            })
            raise ValueError(error_msg)
        
        # Check if response is valid JSON
        try:
            data = response.json()
            if not isinstance(data, list):
                error_msg = f"Unexpected response format during {operation}: expected list, got {type(data)}"
                WooCommerceLogger.log_error(error_msg, details={"response_type": str(type(data))})
                raise ValueError(error_msg)
            return data
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response during {operation}: {str(e)}"
            WooCommerceLogger.log_error(error_msg, details={"response_text": response.text})
            raise ValueError(error_msg)

    def validate_woocommerce_order(self, wc_order):
        """Validate WooCommerce order data before processing"""
        errors = []
        
        # Check required fields
        if not wc_order.get("id"):
            errors.append("Order ID is missing")
        
        if not wc_order.get("billing"):
            errors.append("Billing information is missing")
        elif not wc_order["billing"].get("email"):
            errors.append("Customer email is missing")
        
        if not wc_order.get("line_items"):
            errors.append("Order has no line items")
        else:
            # Validate each line item
            for i, item in enumerate(wc_order["line_items"]):
                if not item.get("name"):
                    errors.append(f"Line item {i+1} has no name")
                if not item.get("quantity") or float(item.get("quantity", 0)) <= 0:
                    errors.append(f"Line item {i+1} has invalid quantity")
                price = item.get("price")
                if price is None or price == "" or (isinstance(price, (int, float)) and str(price).lower() == "nan"):
                    errors.append(f"Line item {i+1} has no price")
        
        # Check for valid status
        valid_statuses = ["pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"]
        if wc_order.get("status") not in valid_statuses:
            errors.append(f"Invalid order status: {wc_order.get('status')}")
        
        if errors:
            raise ValueError(f"Order validation failed: {'; '.join(errors)}")
        
        return True

    def update_order_with_retry(self, order_doc, new_status, max_retries=3):
        """Update order status with retry logic for handling database conflicts"""
        for attempt in range(max_retries):
            try:
                # Reload the document to get the latest state
                if attempt > 0:
                    order_doc = frappe.get_doc("Sales Order", order_doc.name)
                
                order_doc.status = new_status
                order_doc.save()
                frappe.db.commit()
                return True, f"Successfully updated on attempt {attempt + 1}"
                
            except Exception as e:
                if attempt < max_retries - 1:
                    WooCommerceLogger.log("Order", "Info", f"Update attempt {attempt + 1} failed, retrying: {str(e)}", details={
                        "order_name": order_doc.name,
                        "attempt": attempt + 1,
                        "error": str(e)
                    })
                    frappe.db.rollback()
                    import time
                    time.sleep(1)  # Brief pause before retry
                else:
                    return False, f"Failed after {max_retries} attempts: {str(e)}"
        
        return False, "Max retries exceeded"

    def can_update_order_status(self, order_doc, new_status):
        """Check if an order can be updated to the new status"""
        # If order is already in the target status, no update needed
        if order_doc.status == new_status:
            return False, "Order already in target status"
        
        # Check if order is in a state that allows status updates
        if order_doc.docstatus == 1:  # Submitted
            # For submitted orders, only allow certain status transitions
            allowed_transitions = {
                "To Deliver and Bill": ["Completed", "Cancelled"],
                "Completed": ["Cancelled"],
                "Cancelled": []  # No further transitions from cancelled
            }
            current_status = order_doc.status
            if current_status in allowed_transitions and new_status in allowed_transitions[current_status]:
                return True, "Valid status transition"
            else:
                return False, f"Invalid status transition from {current_status} to {new_status}"
        
        elif order_doc.docstatus == 0:  # Draft
            # Draft orders can be updated to any status
            return True, "Draft order can be updated"
        
        else:  # Cancelled
            return False, "Cancelled order cannot be updated"
    
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
            WooCommerceLogger.log("Order", "Info", f"Starting order sync for WooCommerce order {wc_order.get('id')}")
            
            # Order validation is now done in validate_woocommerce_order method
            WooCommerceLogger.log("Order", "Info", "Order validation passed", details={"order_id": wc_order.get("id")})

            # Check if order already exists
            existing_order = frappe.get_all(
                "Sales Order",
                filters={"woocommerce_order_id": str(wc_order["id"])},
                fields=["name"]
            )

            if existing_order:
                WooCommerceLogger.log("Order", "Info", f"Order {wc_order['id']} already exists. Checking for status update.")
                try:
                    # Update existing order status if needed
                    existing_order_doc = frappe.get_doc("Sales Order", existing_order[0]["name"])
                    new_status = self.get_erpnext_status(wc_order["status"])

                    # Check if order can be updated
                    can_update, reason = self.can_update_order_status(existing_order_doc, new_status)
                    
                    if can_update:
                        WooCommerceLogger.log("Order", "Info", f"Updating order {existing_order_doc.name} status from {existing_order_doc.status} to {new_status}")
                        success, message = self.update_order_with_retry(existing_order_doc, new_status)
                        
                        if success:
                            WooCommerceLogger.log("Order", "Success", f"Updated existing order status: {message}", details={"order_id": wc_order["id"], "old_status": existing_order_doc.status, "new_status": new_status})
                        else:
                            raise ValueError(f"Failed to update order status: {message}")
                    else:
                        WooCommerceLogger.log("Order", "Info", f"Order {wc_order['id']} cannot be updated: {reason}", details={
                            "order_id": wc_order["id"], 
                            "current_status": existing_order_doc.status,
                            "target_status": new_status,
                            "docstatus": existing_order_doc.docstatus,
                            "reason": reason
                        })
                    
                    # Log successful handling of existing order (whether updated or not)
                    WooCommerceLogger.log_order_creation(wc_order["id"], True, reference_name=existing_order_doc.name)
                    return
                    
                except Exception as e:
                    error_msg = f"Failed to update existing order {wc_order['id']}: {str(e)}"
                    WooCommerceLogger.log("Order", "Info", error_msg, details={
                        "order_id": wc_order["id"],
                        "existing_order_name": existing_order[0]["name"],
                        "error": str(e)
                    })
                    # Don't return here - let the error propagate to be handled by the main sync loop
                    raise ValueError(error_msg)

            # Get or create customer
            WooCommerceLogger.log("Order", "Info", f"Getting or creating customer for order {wc_order['id']}")
            try:
                customer = self.get_or_create_customer(wc_order)
            except Exception as e:
                raise ValueError(f"Failed to create/get customer: {str(e)}")

            WooCommerceLogger.log("Order", "Info", f"Customer obtained: {customer}")

            # Get order items
            WooCommerceLogger.log("Order", "Info", f"Getting order items for WooCommerce order {wc_order['id']}")
            try:
                items = self.get_order_items(wc_order)
                if not items:
                    raise ValueError("No valid items found in order")
            except Exception as e:
                raise ValueError(f"Failed to process order items: {str(e)}")

            WooCommerceLogger.log("Order", "Info", f"Order items retrieved", details={"item_count": len(items)})

            # Get taxes
            tax_template = self.get_tax_template()
            tax_details = self.get_tax_details(wc_order)

            WooCommerceLogger.log("Order", "Info", "Tax info retrieved", details={"tax_template": tax_template, "tax_details": tax_details})

            # Create Sales Order
            WooCommerceLogger.log("Order", "Info", f"Creating Sales Order document for WooCommerce order {wc_order['id']}")
            sales_order = frappe.get_doc({
                "doctype": "Sales Order",
                "customer": customer,
                "delivery_date": frappe.utils.today(),
                "woocommerce_order_id": str(wc_order["id"]),
                "items": items,
                "taxes_and_charges": tax_template,
                "taxes": tax_details,
                "status": self.get_erpnext_status(wc_order["status"])
            })

            WooCommerceLogger.log("Order", "Info", f"Inserting Sales Order document for {wc_order['id']}")
            sales_order.insert()

            # Submit Sales Order if not in Draft or Cancelled
            if sales_order.status not in ["Draft", "Cancelled"]:
                WooCommerceLogger.log("Order", "Info", f"Submitting Sales Order {sales_order.name}")
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
        """Get or create customer in ERPNext, checking by woocommerce_customer_id from customer_id, then create if not found"""
        try:
            customer_email = wc_order["billing"]["email"]
            woocommerce_customer_id = wc_order.get("customer_id")

            if woocommerce_customer_id:
                WooCommerceLogger.log(
                    "Customer",
                    "Info",
                    f"Using woocommerce_customer_id from customer_id: {woocommerce_customer_id}",
                    details={"customer_id": woocommerce_customer_id, "wc_order": wc_order}
                )
                existing_customer = frappe.get_all(
                    "Customer",
                    filters={"woocommerce_customer_id": str(woocommerce_customer_id)},
                    fields=["name"]
                )
                if existing_customer:
                    WooCommerceLogger.log(
                        "Customer",
                        "Info",
                        f"Found existing customer by WooCommerce ID: {existing_customer[0]['name']}",
                        details={"woocommerce_customer_id": woocommerce_customer_id, "wc_order": wc_order}
                    )
                    return existing_customer[0]["name"]
                else:
                    WooCommerceLogger.log(
                        "Customer",
                        "Info",
                        f"No customer found with woocommerce_customer_id: {woocommerce_customer_id}. Proceeding to create new customer.",
                        details={"woocommerce_customer_id": woocommerce_customer_id, "wc_order": wc_order}
                    )
            else:
                WooCommerceLogger.log(
                    "Customer",
                    "Info",
                    "No woocommerce_customer_id (customer_id) present in order. Proceeding to create new customer.",
                    details={"wc_order": wc_order}
                )

            # Ensure Customer Group exists
            customer_group = "All Customer Groups"
            if not frappe.db.exists("Customer Group", customer_group):
                customer_group_doc = frappe.get_doc({
                    "doctype": "Customer Group",
                    "customer_group_name": customer_group,
                    "parent_customer_group": "All Customer Groups",
                    "is_group": 0
                })
                customer_group_doc.insert(ignore_permissions=True)
                frappe.db.commit()

            # Ensure Territory exists
            territory = "All Territories"
            if not frappe.db.exists("Territory", territory):
                territory_doc = frappe.get_doc({
                    "doctype": "Territory",
                    "territory_name": territory,
                    "parent_territory": "All Territories",
                    "is_group": 0
                })
                territory_doc.insert(ignore_permissions=True)
                frappe.db.commit()

            # Create customer name from billing information
            first_name = wc_order["billing"].get("first_name", "").strip()
            last_name = wc_order["billing"].get("last_name", "").strip()
            if not first_name and not last_name:
                customer_name = customer_email.split("@")[0]
            else:
                customer_name = f"{first_name} {last_name}".strip()
            if not customer_name:
                customer_name = f"WooCommerce Customer {frappe.generate_hash(length=4)}"

            # Create new customer, set woocommerce_customer_id if available
            customer_data = {
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_type": "Individual",
                "customer_group": customer_group,
                "territory": territory,
                "email_id": customer_email,
                "phone": wc_order["billing"].get("phone", ""),
                "address_line1": wc_order["billing"].get("address_1", ""),
                "city": wc_order["billing"].get("city", ""),
                "state": wc_order["billing"].get("state", ""),
                "pincode": wc_order["billing"].get("postcode", ""),
                "country": wc_order["billing"].get("country", "")
            }
            if woocommerce_customer_id:
                customer_data["woocommerce_customer_id"] = str(woocommerce_customer_id)

            customer = frappe.get_doc(customer_data)
            customer.insert(ignore_permissions=True)
            frappe.db.commit()

            WooCommerceLogger.log_customer_creation(customer_name, True)
            return customer.name

        except Exception as e:
            WooCommerceLogger.log_customer_creation(
                customer_name if 'customer_name' in locals() else 'Unknown Customer',
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
        # Try to get SKU from main field first
            WooCommerceLogger.log(
                "Item",
                "Info",
                f"Checking for existing item by name'",
                details={"item_code": wc_item}
            )
            item_code = wc_item.get("sku")

            # If not available, try fetching it from meta_data
            if not item_code:
                for meta in wc_item.get("meta_data", []):
                    key = meta.get("key", "").strip().lower()
                    display_key = meta.get("display_key", "").strip().lower()
                    if key == "sku" or display_key == "sku":
                        item_code = meta.get("value")
                        break

            # Still not found? Try to extract from _ywapo_meta_data
            if not item_code:
                for meta in wc_item.get("meta_data", []):
                    if meta.get("key") == "_ywapo_meta_data":
                        for entry in meta.get("value", []):
                            for subkey, subval in entry.items():
                                if isinstance(subval, dict):
                                    label = subval.get("display_label", "").strip().lower()
                                    if label == "sku":
                                        item_code = subval.get("addon_value")
                                        break
                            if item_code:
                                break
                    if item_code:
                        break

            # If still no SKU, generate fallback item_code
            if not item_code:
                item_code = frappe.scrub(wc_item["name"])[:20]
                item_code = f"{item_code}-{frappe.generate_hash(length=4)}"

            WooCommerceLogger.log(
                "Item",
                "Info",
                f"Checking for existing item by name: '{item_code.strip()}'",
                details={"item_code": item_code.strip()}
            )
            existing_item = frappe.get_all(
                "Item",
                filters={"name": item_code.strip()},
                fields=["name"]
            )
            WooCommerceLogger.log(
                "Item",
                "Info",
                f"Existing item lookup result for '{item_code.strip()}': {existing_item}",
                details={"item_code": item_code.strip(), "existing_item": existing_item}
            )

            if existing_item:
                WooCommerceLogger.log(
                    "Item",
                    "Info",
                    f"Found existing item: {existing_item[0]['name']}",
                    details={"item_code": item_code}
                )
                return existing_item[0]["name"]

            # default_item_group = frappe.db.get_single_value("Stock Settings", "default_item_group") or "All Item Groups"
            # default_uom = frappe.db.get_single_value("Stock Settings", "stock_uom") or "Nos"
            # Create new item
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": wc_item["name"][:140],
                "description": wc_item.get("description", "")[:1000],
                "item_group": "All Item Groups", 
                "stock_uom": "Nos",
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
        """Save sync status to ERPNext WooCommerce Settings doctype"""
        try:
            update_sync_status(
                last_sync=self.sync_config.get("last_sync"),
                sync_status=self.sync_config.get("sync_status")
            )
        except Exception as e:
            WooCommerceLogger.log_error("Failed to save sync status", e)

    def get_sync_status(self):
        """Get current sync status from ERPNext WooCommerce Settings doctype"""
        try:
            sync_config = get_sync_config()
            return {
                "last_sync": sync_config.get("last_sync"),
                "sync_status": sync_config.get("sync_status"),
                "enable_sync": sync_config.get("enable_sync", False)
            }
        except Exception as e:
            WooCommerceLogger.log_error("Failed to get sync status", e)
            return {
                "last_sync": None,
                "sync_status": "Error",
                "enable_sync": False
            }

    def sync_invoice_to_woocommerce(self, invoice_name):
        """Sync ERPNext Sales Invoice to WooCommerce"""
        try:
            # Get the invoice
            invoice = frappe.get_doc("Sales Invoice", invoice_name)
            
            # Get the linked WooCommerce order ID
            woocommerce_order_id = None
            if invoice.sales_order:
                sales_order = frappe.get_doc("Sales Order", invoice.sales_order)
                woocommerce_order_id = sales_order.woocommerce_order_id

            if not woocommerce_order_id:
                raise ValueError("No WooCommerce order ID found for this invoice")

            # Prepare invoice data for WooCommerce
            invoice_data = {
                "status": "completed",
                "meta_data": [
                    {
                        "key": "erpnext_invoice",
                        "value": invoice_name
                    }
                ]
            }

            # Update the order in WooCommerce
            response = self.wcapi.put(f"orders/{woocommerce_order_id}", invoice_data)
            
            if response.status_code not in [200, 201]:
                raise ValueError(f"Failed to update WooCommerce order: {response.text}")

            # Log success
            WooCommerceLogger.log(
                "Invoice",
                "Success",
                f"Successfully synced invoice {invoice_name} to WooCommerce order {woocommerce_order_id}",
                details={
                    "invoice": invoice_name,
                    "woocommerce_order": woocommerce_order_id,
                    "response": response.json()
                }
            )

            return {
                "status": "success",
                "message": f"Invoice {invoice_name} synced to WooCommerce successfully",
                "woocommerce_order_id": woocommerce_order_id
            }

        except Exception as e:
            WooCommerceLogger.log(
                "Invoice",
                "Info",
                f"Failed to sync invoice {invoice_name} to WooCommerce: {str(e)}",
                details={
                    "invoice": invoice_name,
                    "error": str(e)
                }
            )
            raise

    def get_invoice_sync_status(self, invoice_name):
        """Get sync status of an invoice"""
        try:
            invoice = frappe.get_doc("Sales Invoice", invoice_name)
            if not invoice.sales_order:
                return {
                    "status": "Failed",
                    "message": "No Sales Order linked to this invoice"
                }

            sales_order = frappe.get_doc("Sales Order", invoice.sales_order)
            if not sales_order.woocommerce_order_id:
                return {
                    "status": "Failed",
                    "message": "No WooCommerce order linked to this invoice"
                }

            # Check if invoice is already synced
            response = self.wcapi.get(f"orders/{sales_order.woocommerce_order_id}")
            if response.status_code != 200:
                return {
                    "status": "Failed",
                    "message": f"Failed to fetch WooCommerce order: {response.text}"
                }

            order_data = response.json()
            is_synced = any(
                meta["key"] == "erpnext_invoice" and meta["value"] == invoice_name
                for meta in order_data.get("meta_data", [])
            )

            return {
                "status": "success",
                "is_synced": is_synced,
                "woocommerce_order_id": sales_order.woocommerce_order_id,
                "woocommerce_order_status": order_data.get("status")
            }

        except Exception as e:
            return {
                "status": "Failed",
                "message": str(e)
            } 