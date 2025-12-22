"""
WooCommerce Sync - Invoice Synchronization API
==============================================

This module provides API endpoints for syncing Sales Invoices from ERPNext
back to WooCommerce. This enables bidirectional synchronization where invoice
creation in ERPNext updates the corresponding WooCommerce order.
"""

import frappe
from frappe import _
from woocommerce_sync.sales_order_to_woocommerce import WooCommerceSync


@frappe.whitelist()
def sync_invoice(invoice_name):
    """
    Whitelisted API endpoint to sync a Sales Invoice to WooCommerce.
    
    This function:
    1. Initializes the WooCommerceSync class
    2. Calls sync_invoice_to_woocommerce() to update the WooCommerce order
    3. Returns success/failure status
    
    Args:
        invoice_name (str): Name of the ERPNext Sales Invoice to sync
    
    Returns:
        dict: Status dictionary with 'status' and 'message' keys
    """
    try:
        sync = WooCommerceSync()
        return sync.sync_invoice_to_woocommerce(invoice_name)
    except Exception as e:
        frappe.log_error(f"Error in sync_invoice: {str(e)}", "WooCommerce Sync Error")
        return {"status": "Failed", "message": str(e)}


@frappe.whitelist()
def get_invoice_sync_status(invoice_name):
    """
    Whitelisted API endpoint to check if a Sales Invoice has been synced to WooCommerce.
    
    Args:
        invoice_name (str): Name of the ERPNext Sales Invoice to check
    
    Returns:
        dict: Status dictionary with sync information including:
            - status: "success" or "error"
            - is_synced: Boolean indicating sync status
            - woocommerce_order_id: Linked WooCommerce order ID
            - woocommerce_order_status: Current order status in WooCommerce
    """
    try:
        sync = WooCommerceSync()
        return sync.get_invoice_sync_status(invoice_name)
    except Exception as e:
        return {"status": "error", "message": str(e)} 