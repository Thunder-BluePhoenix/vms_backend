# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LegalDocuments(Document):
# 	def on_update(self):
		
# 		vonb_comp_name = frappe.db.get_value(
# 			"Vendor Onboarding Company Details",
# 			{"ref_no": self.ref_no, "vendor_onboarding": self.vendor_onboarding},
# 			"name"
# 		)

# 		vonb_comp = frappe.get_doc("Vendor Onboarding Company Details", vonb_comp_name)

# 		vonb_comp.gst = self.gst_table[0].gst_number
# 		vonb_comp.save()
# 		frappe.db.commit()


	def on_update(self):
		vonb_comp_name = frappe.db.get_value(
			"Vendor Onboarding Company Details",
			{"ref_no": self.ref_no, "vendor_onboarding": self.vendor_onboarding},
			"name"
		)

		if not vonb_comp_name:
			frappe.log_error("Vendor Onboarding Company Details not found.", "on_update")
			return  

		vonb_comp = frappe.get_doc("Vendor Onboarding Company Details", vonb_comp_name)

		vonb_comp.company_pan_number = self.company_pan_number
		
		vonb_comp.comp_gst_table = []
		
		if self.gst_table and len(self.gst_table) > 0:
			matching_gst_records = [gst_d for gst_d in self.gst_table if gst_d.company == vonb_comp.company_name]
			
			if matching_gst_records:
				vonb_comp.gst = matching_gst_records[0].gst_number
				
				for gst_d in matching_gst_records:
					gst_row = vonb_comp.append("comp_gst_table", {})
				
					gst_row.gst_state = gst_d.gst_state
					gst_row.gst_number = gst_d.gst_number
					gst_row.gst_registration_date = gst_d.gst_registration_date
					gst_row.gst_ven_type = gst_d.gst_ven_type
					gst_row.gst_document = gst_d.gst_document
					gst_row.pincode = gst_d.pincode
			else:
				frappe.log_error(f"No GST records found matching company: {vonb_comp.company_name}", "on_update")
		else:
			frappe.log_error("GST table is empty or missing in Legal Documents", "on_update")
		
		vonb_comp.save()
		frappe.db.commit()
