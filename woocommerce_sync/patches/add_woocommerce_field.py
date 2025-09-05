import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Sales Order": [
            dict(
                fieldname="woocommerce_order_id",
                fieldtype="Data",
                label="Woocommerce Order Id",
                insert_after="owner",
                read_only=0
            )
        ]
    }
    create_custom_fields(custom_fields, update=True)
