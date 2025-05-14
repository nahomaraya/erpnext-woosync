import frappe
from frappe import _
from woocommerce_sync.sales_order_to_woocommerce import WooCommerceSync

@frappe.whitelist()
def sync_invoice(invoice_name):
    """Sync a Sales Invoice to WooCommerce"""
    try:
        sync = WooCommerceSync()
        return sync.sync_invoice_to_woocommerce(invoice_name)
    except Exception as e:
        frappe.log_error(f"Error in sync_invoice: {str(e)}", "WooCommerce Sync Error")
        return {"status": "Failed", "message": str(e)}

@frappe.whitelist()
def get_invoice_sync_status(invoice_name):
    """Get sync status of a Sales Invoice"""
    try:
        sync = WooCommerceSync()
        return sync.get_invoice_sync_status(invoice_name)
    except Exception as e:
        return {"status": "error", "message": str(e)} 