import frappe
from frappe import _
from frappe.utils import now_datetime
import traceback
import json

class WooCommerceLogger:
    @staticmethod
    def log(log_type, status, message, details=None, reference_doctype=None, reference_name=None, error_traceback=None, woocommerce_order_id=None):
        """Create a log entry in WooCommerce Sync Log"""
        try:
            # Ensure status is one of the valid values
            valid_statuses = ["Success", "Failed", "Warning", "Info"]
            if status not in valid_statuses:
                status = "Failed" if status.lower() in ["error", "failed"] else "Info"

            log = frappe.get_doc({
                "doctype": "WooCommerce Sync Log",
                "log_type": log_type,
                "status": status,
                "message": message,
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
            frappe.log_error(f"Error creating WooCommerce Sync Log: {str(e)}", "WooCommerce Logger Error")

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
        WooCommerceLogger.log(
            log_type="Customer",
            status="Success" if success else "Failed",
            message=f"{'Created' if success else 'Failed to create'} customer: {customer_name}",
            details={"customer_name": customer_name},
            error_traceback=traceback.format_exc() if error else None
        )

    @staticmethod
    def log_item_creation(item_code, success=True, error=None):
        """Log item creation attempt"""
        WooCommerceLogger.log(
            log_type="Item",
            status="Success" if success else "Failed",
            message=f"{'Created' if success else 'Failed to create'} item: {item_code}",
            details={"item_code": item_code},
            error_traceback=traceback.format_exc() if error else None
        )

    @staticmethod
    def log_order_creation(order_id, success=True, error=None, reference_name=None):
        """Log order creation attempt"""
        WooCommerceLogger.log(
            log_type="Order",
            status="Success" if success else "Failed",
            message=f"{'Created' if success else 'Failed to create'} order: {order_id}",
            details={"order_id": order_id},
            reference_doctype="Sales Order" if reference_name else None,
            reference_name=reference_name,
            error_traceback=traceback.format_exc() if error else None,
            woocommerce_order_id=order_id
        )

    @staticmethod
    def log_error(message, error=None, details=None):
        """Log an error"""
        WooCommerceLogger.log(
            log_type="Error",
            status="Failed",
            message=message,
            details=details,
            error_traceback=traceback.format_exc() if error else None
        ) 