# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EarthInvoice(Document):
    def validate(self):
        self.update_upload_status()
    
    def update_upload_status(self):
        child_tables = {
            'confirmation_voucher': 'confirmation_voucher',  
            'invoice_attachment': 'invoice_attachment',   
            'debit_note_attachment': 'debit_note_attachment' 
        }
        
        uploaded_count = 0
        
        for table_field, attachment_field in child_tables.items():
            child_table = self.get(table_field) or []
            
            has_attachment = any(
                row.get(attachment_field) for row in child_table
            )
            
            if has_attachment:
                uploaded_count += 1
        
        if uploaded_count == 3:
            self.doc_upload_status = "Fully Uploaded"
        elif uploaded_count > 0:
            self.doc_upload_status = "Partially Uploaded"
        else:
            self.doc_upload_status = "Not Uploaded"