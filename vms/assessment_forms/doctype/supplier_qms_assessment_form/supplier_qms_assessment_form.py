# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SupplierQMSAssessmentForm(Document):
	def on_update(self):
		if self.vendor_onboarding:
			ven_onb = frappe.get_doc("Vendor Onboarding", self.vendor_onboarding)
			ven_onb.qms_form_link = self.name
			ven_onb.save()
			frappe.db.commit()