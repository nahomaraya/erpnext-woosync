import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields_to_add = [
        {
            "dt": "Sales Order",
            "fieldname": "woocommerce_order_id",
            "fieldtype": "Data",
            "label": "Woocommerce Order Id",
            "insert_after": "title",
        },
        {
            "dt": "Customer",
            "fieldname": "woocommerce_customer_id",
            "fieldtype": "Data",
            "label": "Woocommerce Customer Id",
            "insert_after": "title",
        },
        {
            "dt": "Item",
            "fieldname": "woocommerce_product_id",
            "fieldtype": "Data",
            "label": "Woocommerce Product Id",
            "insert_after": "title",
        }
    ]

    for field in fields_to_add:
        if not frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
            frappe.get_doc({
                "doctype": "Custom Field",
                **field
            }).insert()
