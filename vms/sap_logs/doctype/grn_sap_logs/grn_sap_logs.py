# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GRNSAPLogs(Document):
    """
    GRN SAP Logs DocType Controller
    Logs all SAP to ERP GRN transactions
    """
    
    def validate(self):
        """Validate the log entry"""
        # Auto-set processed date if status changes to Success or Failed
        if self.status in ["Success", "Failed"] and not self.processed_date:
            self.processed_date = frappe.utils.now()
    
    def before_save(self):
        """Before save validations"""
        # Ensure transaction_date is set
        if not self.transaction_date:
            self.transaction_date = frappe.utils.now()