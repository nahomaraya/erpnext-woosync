import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def after_install():
    # define your custom field(s)
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

    # create them
    create_custom_fields(custom_fields, update=True)
