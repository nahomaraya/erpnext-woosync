import frappe
from frappe.model.document import Document
from woocommerce import API
import json

class WooCommerceSettings(Document):
    def validate(self):
        if self.enable_sync:
            self.test_connection()

    def test_connection(self):
        try:
            wcapi = self.get_wcapi()
            response = wcapi.get("products")
            if response.status_code != 200:
                frappe.throw("Could not connect to WooCommerce. Please check your credentials.")
        except Exception as e:
            frappe.throw(f"Error connecting to WooCommerce: {str(e)}")

    def get_wcapi(self):
        return API(
            url=self.woocommerce_url,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            version="wc/v3"
        )

    def get_sync_status(self):
        return {
            "last_sync": self.last_sync,
            "sync_status": self.sync_status
        } 