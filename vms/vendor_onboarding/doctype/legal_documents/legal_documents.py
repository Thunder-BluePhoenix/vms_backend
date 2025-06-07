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
			return  # Or frappe.throw(...) if it's required

		vonb_comp = frappe.get_doc("Vendor Onboarding Company Details", vonb_comp_name)

		# ✅ Check if gst_table exists and has at least one row
		if self.gst_table and len(self.gst_table) > 0:
			vonb_comp.gst = self.gst_table[0].gst_number
			vonb_comp.save()
			frappe.db.commit()
		else:
			frappe.log_error("GST table is empty or missing in Legal Documents", "on_update")
			pass
