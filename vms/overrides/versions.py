
import frappe
from frappe import _


# @frappe.whitelist()
# def get_version_data(self, method=None):
#     try:
#         # self is Version doctype
#         if self.ref_doctype == "Request For Quotation" and self.docname:
            
#             # Parse the version data from current version
#             version_data = frappe.parse_json(self.data)
            
#             field_changes = version_data.get("changed", [])
#             child_table_changes = version_data.get("row_changed", [])
            
#             # Check if there are any meaningful changes (excluding version_history)
#             meaningful_changes = []
#             meaningful_row_changes = []
            
#             # Filter field changes - exclude version_history related changes
#             for change in field_changes:
#                 if len(change) >= 2 and change[0] != "version_history":
#                     meaningful_changes.append(change)
            
#             # Filter row changes - exclude version_history table changes  
#             for row_change in child_table_changes:
#                 if len(row_change) >= 2 and row_change[0] != "version_history":
#                     meaningful_row_changes.append(row_change)
            
#             # If no meaningful changes, don't create version history entry
#             if not meaningful_changes and not meaningful_row_changes:
#                 return
            
#             # Prepare filtered data
#             filtered_data = {
#                 "changed": meaningful_changes,
#                 "row_changed": meaningful_row_changes
#             }
            
#             # Get next index for child table
#             next_idx = frappe.db.sql("""
#                 SELECT COALESCE(MAX(idx), 0) + 1 
#                 FROM `tabRFQ Item History` 
#                 WHERE parent = %s
#             """, (self.docname,))[0][0]
            
#             # Direct DB insert for maximum efficiency
#             frappe.db.sql("""
#                 INSERT INTO `tabRFQ Item History` 
#                 (name, parent, parenttype, parentfield, field_json, date_and_time, 
#                  creation, modified, modified_by, owner, docstatus, idx)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s)
#             """, (
#                 frappe.generate_hash(length=10),
#                 self.docname,
#                 "Request For Quotation",
#                 "version_history", 
#                 frappe.as_json(filtered_data),
#                 self.creation,
#                 frappe.utils.now(),
#                 frappe.utils.now(),
#                 frappe.session.user,
#                 frappe.session.user,
#                 next_idx
#             ))
            
#             # Update parent's modified timestamp
#             frappe.db.sql("""
#                 UPDATE `tabRequest For Quotation` 
#                 SET modified = %s, modified_by = %s 
#                 WHERE name = %s
#             """, (frappe.utils.now(), frappe.session.user, self.docname))

#             # frappe.clear_document_cache("Request For Quotation", self.docname)
#             # fresh_rfq_doc = frappe.get_doc("Request For Quotation", self.docname)
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_version_data Error")





@frappe.whitelist()
def get_version_data_universal(self, method=None):
    """Universal version tracking for both RFQ and Quotation"""
    try:
        
        doctype_mapping = {
            "Request For Quotation": "RFQ Item History",
            "Quotation": "RFQ Item History",
            "Purchase Order": "Purchase Order History",
            "Vendor Onboarding": "Vendor Onboarding History"
        }
        
        if self.ref_doctype in doctype_mapping and self.docname:
            
            version_data = frappe.parse_json(self.data)
            
            field_changes = version_data.get("changed", [])
            child_table_changes = version_data.get("row_changed", [])
            
            if self.ref_doctype == "Vendor Onboarding":
                allowed_fields = [
                    "company_name", "company", "purchase_organization", 
                    "order_currency", "purchase_group", "terms_of_payment", 
                    "account_group", "enterprise", "reconciliation_account", 
                    "qa_team_remarks", "incoterms"
                ]
                
                meaningful_changes = [
                    c for c in field_changes 
                    if len(c) >= 2 and c[0] in allowed_fields
                ]
                meaningful_row_changes = []
            else:
                meaningful_changes = [c for c in field_changes if len(c) >= 2 and c[0] != "version_history"]
                meaningful_row_changes = [c for c in child_table_changes if len(c) >= 2 and c[0] != "version_history"]
            
            
            if not meaningful_changes and not meaningful_row_changes:
                return
            
            # Prepare filtered data
            filtered_data = {
                "changed": meaningful_changes,
                "row_changed": meaningful_row_changes
            }
            
            # Get the correct child table doctype
            child_doctype = doctype_mapping[self.ref_doctype]
            
            # Create child table entry
            version_history_doc = frappe.get_doc({
                "doctype": child_doctype,
                "parent": self.docname,
                "parenttype": self.ref_doctype,
                "parentfield": "version_history",
                "field_json": frappe.as_json(filtered_data),
                "date_and_time": self.creation
            })
            
            # Insert without triggering document events
            version_history_doc.insert(ignore_permissions=True, ignore_mandatory=True)
            
            # Update parent's modified timestamp
            frappe.db.set_value(self.ref_doctype, self.docname, {
                "modified": frappe.utils.now(),
                "modified_by": frappe.session.user
            }, update_modified=False)
            
            # Clear cache and send reload signal
            frappe.clear_document_cache(self.ref_doctype, self.docname)
            
            frappe.publish_realtime(
                event="refresh_form",
                message={
                    "doctype": self.ref_doctype,
                    "docname": self.docname
                },
                user=frappe.session.user
            )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_version_data_universal Error")