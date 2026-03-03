from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class WooCommerceSyncLogController(Document):
    def validate(self):
        if not self.sync_date:
            self.sync_date = frappe.utils.now_datetime() 