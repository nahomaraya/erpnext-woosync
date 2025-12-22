"""
WooCommerce Sync - API Endpoints
=================================

This module provides whitelisted API endpoints for the WooCommerce Sync application.
These endpoints are called from the frontend JavaScript to trigger synchronization
and manage configuration.
"""

import frappe
from frappe import _
from woocommerce_sync.sales_order_to_woocommerce import WooCommerceSync
from woocommerce_sync.woocommerce_config import get_woocommerce_config, get_sync_config, update_sync_status


@frappe.whitelist()
def sync_orders():
    """
    Whitelisted API endpoint to manually trigger order synchronization from WooCommerce to ERPNext.
    
    This function:
    1. Initializes the WooCommerceSync class
    2. Triggers the sync_from_woocommerce() method
    3. Returns success/failure status with appropriate messages
    
    Returns:
        dict: Status dictionary with 'status' and 'message' keys
    """
    try:
        sync = WooCommerceSync()
        sync.sync_from_woocommerce()
        return {"status": "success", "message": "Orders synced from WooCommerce successfully. Check the logs for details."}
    except Exception as e:
        frappe.log_error(f"Error in sync_orders: {str(e)}", "WooCommerce Sync Error")
        return {"status": "Failed", "message": str(e)}


@frappe.whitelist()
def get_sync_status():
    """
    Whitelisted API endpoint to retrieve the current synchronization status.
    
    Returns information about:
    - Last sync timestamp
    - Current sync status (Success/Failed/Partial Success)
    - Whether sync is enabled
    
    Returns:
        dict: Status dictionary with sync information
    """
    try:
        sync = WooCommerceSync()
        return sync.get_sync_status()
    except Exception as e:
        frappe.log_error(f"Error in get_sync_status: {str(e)}", "WooCommerce Sync Error")
        return {"status": "Failed", "message": str(e)}


@frappe.whitelist()
def update_config(config_data):
    """
    Whitelisted API endpoint to update WooCommerce configuration settings.
    
    This function updates the WooCommerce Settings doctype with:
    - WooCommerce URL
    - Consumer Key and Secret (API credentials)
    - Sync enable/disable flag
    - Sync interval (Daily/Weekly/Monthly)
    
    Args:
        config_data (dict): Configuration data containing:
            - woocommerce: dict with url, consumer_key, consumer_secret
            - sync: dict with enable_sync (bool) and sync_interval (str)
    
    Returns:
        dict: Status dictionary with 'status' and 'message' keys
    """
    try:
        # Get all WooCommerce Settings documents
        settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        if not settings_list:
            # Create default WooCommerce Settings document if none exists
            from woocommerce_sync.woocommerce_config import create_default_woocommerce_settings
            create_default_woocommerce_settings()
            settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        # Get the first WooCommerce Settings document
        settings = frappe.get_doc("WooCommerce Settings", settings_list[0]["name"])
        
        # Update WooCommerce API configuration
        woocommerce_config = config_data.get("woocommerce", {})
        if woocommerce_config.get("url"):
            settings.woocommerce_url = woocommerce_config["url"]
        if woocommerce_config.get("consumer_key"):
            settings.consumer_key = woocommerce_config["consumer_key"]
        if woocommerce_config.get("consumer_secret"):
            settings.consumer_secret = woocommerce_config["consumer_secret"]
        
        # Update sync configuration settings
        sync_config = config_data.get("sync", {})
        if "enable_sync" in sync_config:
            settings.enable_sync = sync_config["enable_sync"]
        if sync_config.get("sync_interval"):
            settings.sync_interval = sync_config["sync_interval"].title()
        
        # Save the document and commit changes
        settings.save()
        frappe.db.commit()
        
        return {"status": "success", "message": "Configuration updated successfully"}
    except Exception as e:
        frappe.log_error(f"Error updating WooCommerce configuration: {str(e)}", "WooCommerce Config Error")
        return {"status": "Failed", "message": str(e)}


# @frappe.whitelist()
# def test_connection():
#     """Test WooCommerce API connection"""
#     try:
#         result = test_woocommerce_connection()
#         return result
#     except Exception as e:
#         frappe.log_error(f"Error in test_connection: {str(e)}", "WooCommerce Sync Error")
#         return {"status": "Failed", "message": str(e)}

# @frappe.whitelist()
# def test_connection():
#     """Test WooCommerce API connection"""
#     try:
#         result = test_woocommerce_connection()
#         return result
#     except Exception as e:
#         frappe.log_error(f"Error in test_connection: {str(e)}", "WooCommerce Sync Error")
#         return {"status": "Failed", "message": str(e)} 