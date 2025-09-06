"""
WooCommerce Configuration
Centralized config access for WooCommerce integration.
Uses the Single DocType: WooCommerce Settings
"""

import frappe


# ----------------------------
# Core Config Access
# ----------------------------

def get_woocommerce_config():
    """Return WooCommerce API config from WooCommerce Settings (Single Doctype)."""
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
    """Return sync-specific config values from WooCommerce Settings (Single Doctype)."""
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
    """Update last_sync and/or sync_status in WooCommerce Settings."""
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
