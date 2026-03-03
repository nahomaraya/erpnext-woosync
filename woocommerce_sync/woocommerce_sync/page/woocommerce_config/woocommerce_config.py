import frappe
from woocommerce import API

# This must be a Single DocType you create (e.g., "WooCommerce Sync Settings")
CONFIG_KEY = "WooCommerce Settings"


def _get_config_doc():
    """Use Frappe's single-value store (tabSingles)."""
    return frappe.db.get_singles_dict(CONFIG_KEY)


@frappe.whitelist()
def get_config():
    """Fetch current WooCommerce configuration"""
    return _get_config_doc()


@frappe.whitelist()
def save_config(config):
    """Save WooCommerce config into Singles"""
    if isinstance(config, str):
        config = frappe.parse_json(config)

    for key, value in config.items():
        frappe.db.set_single_value(CONFIG_KEY, key, value)

    return "✅ Configuration saved successfully!"


@frappe.whitelist()
def test_connection():
    """Test connection to WooCommerce"""
    cfg = _get_config_doc()
    try:
        wcapi = API(
            url=cfg.get("woocommerce_url"),
            consumer_key=cfg.get("consumer_key"),
            consumer_secret=cfg.get("consumer_secret"),
            version="wc/v3"
        )
        response = wcapi.get("products")
        if response.status_code == 200:
            return "✅ Connection successful!"
        return f"❌ Failed: {response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@frappe.whitelist()
def sync_now():
    """Start a manual sync"""
    frappe.db.set_single_value(CONFIG_KEY, "sync_status", "Running")
    return "🔄 Sync started..."
