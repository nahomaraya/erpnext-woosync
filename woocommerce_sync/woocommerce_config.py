"""
WooCommerce Configuration Module
=================================

This module provides centralized access to WooCommerce configuration settings.
All configuration is stored in the WooCommerce Settings doctype (Single DocType).

Functions:
- get_woocommerce_config(): Retrieves WooCommerce API credentials and settings
- get_sync_config(): Retrieves synchronization-specific settings
- update_sync_status(): Updates sync status and timestamp
"""

import frappe


# ----------------------------
# Core Config Access
# ----------------------------

def get_woocommerce_config():
    """
    Retrieve WooCommerce API configuration from WooCommerce Settings doctype.
    
    Returns a dictionary containing:
    - url: WooCommerce store URL
    - consumer_key: WooCommerce REST API consumer key
    - consumer_secret: WooCommerce REST API consumer secret
    - version: API version (always "wc/v3")
    - verify_ssl: SSL verification flag (default: True)
    - timeout: API request timeout in seconds (default: 30)
    
    Returns:
        dict: WooCommerce API configuration dictionary
    
    Note:
        Returns default values if configuration cannot be retrieved or is incomplete.
    """
    try:
        config = frappe.db.get_singles_dict("WooCommerce Settings")
        return {
            "url": config.get("woocommerce_url") or "",
            "consumer_key": config.get("consumer_key") or "",
            "consumer_secret": config.get("consumer_secret") or "",
            "version": "wc/v3",
            "verify_ssl": True,
            "timeout": 30,
        }
    except Exception as e:
        frappe.log_error(f"Error getting WooCommerce configuration: {str(e)}", "WooCommerce Config Error")
        return {
            "url": "",
            "consumer_key": "",
            "consumer_secret": "",
            "version": "wc/v3",
            "verify_ssl": True,
            "timeout": 30,
        }


def get_sync_config():
    """
    Retrieve synchronization-specific configuration from WooCommerce Settings.
    
    Returns a dictionary containing:
    - enable_sync: Boolean flag indicating if sync is enabled
    - sync_interval: Sync interval setting (daily/weekly/monthly)
    - sync_status: Current sync status (Success/Failed/Partial Success)
    - last_sync: Timestamp of last synchronization
    
    Returns:
        dict: Synchronization configuration dictionary
    
    Note:
        Returns default values if configuration cannot be retrieved.
    """
    try:
        config = frappe.db.get_singles_dict("WooCommerce Settings")
        return {
            "enable_sync": bool(config.get("enable_sync")),
            "sync_interval": (config.get("sync_interval") or "Daily").lower(),
            "sync_status": config.get("sync_status") or "",
            "last_sync": config.get("last_sync"),
        }
    except Exception as e:
        frappe.log_error(f"Error getting sync configuration: {str(e)}", "WooCommerce Config Error")
        return {
            "enable_sync": False,
            "sync_interval": "daily",
            "sync_status": "",
            "last_sync": None,
        }


def update_sync_status(last_sync=None, sync_status=None):
    """
    Update synchronization status and/or timestamp in WooCommerce Settings.
    
    This function is called after each sync operation to record:
    - When the last sync occurred (last_sync)
    - The result of the sync operation (sync_status)
    
    Args:
        last_sync (datetime, optional): Timestamp of the last sync operation
        sync_status (str, optional): Status of the sync (e.g., "Success", "Failed", "Partial Success")
    
    Note:
        Both parameters are optional. Only provided parameters will be updated.
    """
    try:
        if last_sync is not None:
            frappe.db.set_single_value("WooCommerce Settings", "last_sync", last_sync)
        if sync_status is not None:
            frappe.db.set_single_value("WooCommerce Settings", "sync_status", sync_status)
    except Exception as e:
        frappe.log_error(f"Error updating sync status: {str(e)}", "WooCommerce Config Error")


# ----------------------------
# Backward Compatibility Aliases
# ----------------------------

def WOOCOMMERCE_CONFIG():
    """Legacy alias for get_woocommerce_config"""
    return get_woocommerce_config()


def SYNC_CONFIG():
    """Legacy alias for get_sync_config"""
    return get_sync_config()
