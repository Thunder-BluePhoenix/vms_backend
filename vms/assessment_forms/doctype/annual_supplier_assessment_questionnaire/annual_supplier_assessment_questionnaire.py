# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime



class AnnualSupplierAssessmentQuestionnaire(Document):
	def after_insert(self):
		try:
			if self.vendor_ref_no:
				vendor_master = frappe.get_doc("Vendor Master", self.vendor_ref_no)

				vendor_master.append("form_records", {
					"assessment_form": self.name,
					"date_time": now_datetime()
				})

				vendor_master.save(ignore_permissions=True)  # save the changes
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Error in ASAQ after_insert")