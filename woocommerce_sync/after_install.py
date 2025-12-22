"""
WooCommerce Sync - Post-Installation Setup
===========================================

This module runs after the app is installed to set up required custom fields
and other configuration needed for the WooCommerce sync functionality.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    """
    Execute post-installation setup tasks.
    
    This function is called automatically by Frappe after the app is installed.
    It creates custom fields required for WooCommerce integration:
    - woocommerce_order_id field on Sales Order doctype
    
    This field is used to link ERPNext Sales Orders to their corresponding
    WooCommerce orders, enabling duplicate detection and status updates.
    """
    # Define custom fields to be added to existing doctypes
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

    # Create the custom fields
    create_custom_fields(custom_fields, update=True)
