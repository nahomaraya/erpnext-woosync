from __future__ import unicode_literals
import frappe

def get_list_context(context):
    context.update({
        "title": "WooCommerce Sync Logs",
        "get_list": get_woocommerce_sync_logs,
        "row_template": "woocommerce_sync/doctype/woocommerce_sync_log/templates/woocommerce_sync_log_row.html",
        "filters": {
            "status": ["in", ["Success", "Failed", "Info"]]
        }
    })

def get_woocommerce_sync_logs(doctype, txt, filters, limit_start, limit_page_length=20, order_by=None):
    return frappe.get_list(doctype,
        fields=["name", "log_type", "status", "message", "sync_date"],
        filters=filters,
        limit_start=limit_start,
        limit_page_length=limit_page_length,
        order_by=order_by or "sync_date desc"
    ) 