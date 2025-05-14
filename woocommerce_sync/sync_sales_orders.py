import frappe
from frappe import _
from woocommerce_sync.sales_order_to_woocommerce import WooCommerceSync
from woocommerce_sync.config.woocommerce_config import WOOCOMMERCE_CONFIG, SYNC_CONFIG

@frappe.whitelist()
def sync_orders():
    try:
        sync = WooCommerceSync()
        sync.sync_from_woocommerce()
        return {"status": "success", "message": "Orders synced from WooCommerce successfully"}
    except Exception as e:
        frappe.log_error(f"Error in sync_orders: {str(e)}", "WooCommerce Sync Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_sync_status():
    try:
        sync = WooCommerceSync()
        return sync.get_sync_status()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def update_config(config_data):
    try:
        # Update WooCommerce configuration
        WOOCOMMERCE_CONFIG.update(config_data.get("woocommerce", {}))
        SYNC_CONFIG.update(config_data.get("sync", {}))
        
        # Save configuration to file
        with open("woocommerce_config.py", "w") as f:
            f.write(f"""
# WooCommerce API Configuration
WOOCOMMERCE_CONFIG = {WOOCOMMERCE_CONFIG}

# Sync Configuration
SYNC_CONFIG = {SYNC_CONFIG}
            """)
        
        return {"status": "success", "message": "Configuration updated successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)} 