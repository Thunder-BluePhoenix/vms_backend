# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SupplierQMSAssessmentForm(Document):
	def on_update(self):
		set_qms_form_link(self, method=None)




@frappe.whitelist(allow_guest=True)
def set_qms_form_link(doc, method=None):
	if doc.vendor_onboarding:
		ven_onb = frappe.get_doc("Vendor Onboarding", doc.vendor_onboarding)
		ven_onb.qms_form_link = doc.name
		ven_onb.save()
		frappe.db.commit()