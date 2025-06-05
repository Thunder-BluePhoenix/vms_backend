# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LegalDocuments(Document):
	def on_update(self):
		
		vonb_comp_name = frappe.db.get_value(
			"Vendor Onboarding Company Details",
			{"ref_no": self.ref_no, "vendor_onboarding": self.vendor_onboarding},
			"name"
		)

		vonb_comp = frappe.get_doc("Vendor Onboarding Company Details", vonb_comp_name)

		vonb_comp.gst = self.gst_table[0].gst_number
		vonb_comp.save()
		frappe.db.commit()
