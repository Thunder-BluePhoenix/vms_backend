# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SignatureRecord(Document):
    def on_update(self):
        usr = self.user_email
        
        if usr:
            try:
                # Check if Employee exists using frappe.db (more efficient)
                employee_name = frappe.db.get_value("Employee", {"user_id": usr}, "name")
                
                if employee_name:
                    updates = {}
                    
                    if self.signature_image:
                        updates["sign_attach"] = self.signature_image
                    if self.esignature:
                        updates["esignature"] = self.esignature
                    
                    if updates:
                        for field, value in updates.items():
                            frappe.db.set_value("Employee", employee_name, field, value)
                        frappe.db.commit()
                    
                    # frappe.msgprint(f"Employee signature updated for user: {usr}")
                else:
                    frappe.log_error(f"No Employee document found for user: {usr}", "SignatureRecord Update")
                    
            except Exception as e:
                frappe.log_error(f"Error updating Employee signature for user {usr}: {str(e)}", "SignatureRecord Update Error")
                # frappe.throw(f"Failed to update employee signature: {str(e)}")