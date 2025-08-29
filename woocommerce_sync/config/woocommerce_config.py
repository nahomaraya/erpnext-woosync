"""
WooCommerce Configuration
This file contains functions to get WooCommerce API configuration from ERPNext doctype.
"""
import frappe

def get_woocommerce_config():
    """Get WooCommerce configuration from ERPNext WooCommerce Settings doctype"""
    try:
        # Get all WooCommerce Settings documents
        settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        if not settings_list:
            # Create default WooCommerce Settings document
            create_default_woocommerce_settings()
            settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        # Get the first WooCommerce Settings document
        settings = frappe.get_doc("WooCommerce Settings", settings_list[0]["name"])
        
        return {
            "url": settings.woocommerce_url,
            "consumer_key": settings.consumer_key,
            "consumer_secret": settings.consumer_secret,
            "version": "wc/v3",  # WooCommerce API version
            "verify_ssl": True,  # SSL verification
            "timeout": 30,  # API request timeout in seconds
        }
    except Exception as e:
        frappe.log_error(f"Error getting WooCommerce configuration: {str(e)}", "WooCommerce Config Error")
        # Return default/fallback config
        return {
            "url": "",
            "consumer_key": "",
            "consumer_secret": "",
            "version": "wc/v3",
            "verify_ssl": True,
            "timeout": 30,
        }

def get_sync_config():
    """Get sync configuration from ERPNext WooCommerce Settings doctype"""
    try:
        # Get all WooCommerce Settings documents
        settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        if not settings_list:
            # Create default WooCommerce Settings document
            create_default_woocommerce_settings()
            settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        # Get the first WooCommerce Settings document
        settings = frappe.get_doc("WooCommerce Settings", settings_list[0]["name"])
        
        return {
            "enable_sync": settings.enable_sync,
            "sync_interval": settings.sync_interval.lower() if settings.sync_interval else "daily",
            "sync_status": settings.sync_status or "",
            "last_sync": settings.last_sync
        }
    except Exception as e:
        frappe.log_error(f"Error getting sync configuration: {str(e)}", "WooCommerce Config Error")
        # Return default/fallback config
        return {
            "enable_sync": False,
            "sync_interval": "daily",
            "sync_status": "",
            "last_sync": None
        }

def create_default_woocommerce_settings():
    """Create default WooCommerce Settings document if it doesn't exist"""
    try:
        # Check if any WooCommerce Settings document exists
        settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        if not settings_list:
            settings = frappe.get_doc({
                "doctype": "WooCommerce Settings",
                "woocommerce_url": "",
                "consumer_key": "",
                "consumer_secret": "",
                "enable_sync": False,
                "sync_interval": "Daily",
                "sync_status": "",
                "last_sync": None
            })
            settings.insert(ignore_permissions=True)
            frappe.db.commit()
            frappe.msgprint("Default WooCommerce Settings document created. Please configure your WooCommerce credentials.")
    except Exception as e:
        frappe.log_error(f"Error creating default WooCommerce Settings: {str(e)}", "WooCommerce Config Error")

def update_sync_status(last_sync=None, sync_status=None):
    """Update sync status in ERPNext WooCommerce Settings doctype"""
    try:
        # Get all WooCommerce Settings documents
        settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        if not settings_list:
            create_default_woocommerce_settings()
            settings_list = frappe.get_all("WooCommerce Settings", fields=["name"])
        
        # Get the first WooCommerce Settings document
        settings = frappe.get_doc("WooCommerce Settings", settings_list[0]["name"])
        if last_sync is not None:
            settings.last_sync = last_sync
        if sync_status is not None:
            settings.sync_status = sync_status
        settings.save()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error updating sync status: {str(e)}", "WooCommerce Config Error")

# For backward compatibility, provide the old variable names as functions
def WOOCOMMERCE_CONFIG():
    return get_woocommerce_config()

def SYNC_CONFIG():
    return get_sync_config() 