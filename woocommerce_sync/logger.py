import frappe
from frappe import _
from frappe.utils import now_datetime
import traceback
import json

class WooCommerceLogger:
    @staticmethod
    def truncate_message(message, max_length=140):
        """Truncate message to max_length characters"""
        if len(message) > max_length:
            return message[:max_length-3] + "..."
        return message

    @staticmethod
    def log(log_type, status, message, details=None, reference_doctype=None, reference_name=None, error_traceback=None, woocommerce_order_id=None):
        """Create a log entry in WooCommerce Sync Log"""
        try:
            # Truncate message to prevent length exceeded errors
            truncated_message = WooCommerceLogger.truncate_message(message)
            
            # If details is a string, truncate it too
            if isinstance(details, str):
                details = WooCommerceLogger.truncate_message(details)
            
            log = frappe.get_doc({
                "doctype": "WooCommerce Sync Log",
                "log_type": log_type,
                "status": status,
                "message": truncated_message,
                "details": json.dumps(details) if details else None,
                "reference_doctype": reference_doctype,
                "reference_name": reference_name,
                "sync_date": now_datetime(),
                "error_traceback": error_traceback,
                "woocommerce_order_id": woocommerce_order_id
            })
            log.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            # Prevent recursive error logging
            if "Error creating WooCommerce Sync Log" not in str(e):
                frappe.log_error(
                    WooCommerceLogger.truncate_message(f"Error creating WooCommerce Sync Log: {str(e)}"),
                    "WooCommerce Logger Error"
                )

    @staticmethod
    def log_sync_start():
        """Log the start of a sync process"""
        WooCommerceLogger.log(
            log_type="Sync",
            status="Info",
            message="Starting WooCommerce sync process",
            details={"timestamp": str(now_datetime())}
        )

    @staticmethod
    def log_sync_end(success=True, message=None):
        """Log the end of a sync process"""
        WooCommerceLogger.log(
            log_type="Sync",
            status="Success" if success else "Failed",
            message=message or ("Sync completed successfully" if success else "Sync failed"),
            details={"timestamp": str(now_datetime())}
        )

    @staticmethod
    def log_customer_creation(customer_name, success=True, error=None):
        """Log customer creation attempt"""
        message = f"{'Created' if success else 'Failed to create'} customer: {customer_name}"
        if error:
            message += f" - {str(error)}"
        WooCommerceLogger.log(
            log_type="Customer",
            status="Success" if success else "Failed",
            message=message,
            details={"customer_name": customer_name},
            error_traceback=traceback.format_exc() if error else None
        )

    @staticmethod
    def log_item_creation(item_code, success=True, error=None):
        """Log item creation attempt"""
        message = f"{'Created' if success else 'Failed to create'} item: {item_code}"
        if error:
            message += f" - {str(error)}"
        WooCommerceLogger.log(
            log_type="Item",
            status="Success" if success else "Failed",
            message=message,
            details={"item_code": item_code},
            error_traceback=traceback.format_exc() if error else None
        )

    @staticmethod
    def log_order_creation(order_id, success=True, error=None, reference_name=None):
        """Log order creation attempt"""
        message = f"{'Created' if success else 'Failed to create'} order: {order_id}"
        if error:
            message += f" - {str(error)}"
        WooCommerceLogger.log(
            log_type="Order",
            status="Success" if success else "Failed",
            message=message,
            details={"order_id": order_id},
            reference_doctype="Sales Order" if reference_name else None,
            reference_name=reference_name,
            error_traceback=traceback.format_exc() if error else None,
            woocommerce_order_id=order_id
        )

    @staticmethod
    def log_error(message, error=None, details=None):
        """Log an error"""
        if error:
            message = f"{message} - {str(error)}"
        WooCommerceLogger.log(
            log_type="Sync",
            status="Info",
            message=message,
            details=details,
            error_traceback=traceback.format_exc() if error else None
        ) 