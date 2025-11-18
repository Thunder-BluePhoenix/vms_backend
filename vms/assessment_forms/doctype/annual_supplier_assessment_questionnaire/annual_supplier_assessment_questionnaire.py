# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from vms.utils.custom_send_mail import custom_sendmail



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

	def on_update(self):
		send_asa_completion_email(self)



def send_asa_completion_email(doc, method=None):
	try:
		if doc.form_is_submitted == 1 and doc.vendor_ref_no:
			vendor_master = frappe.get_doc("Vendor Master", doc.vendor_ref_no)

			for row in vendor_master.form_records:
				if row.assessment_form == doc.name and not row.form_is_submitted:
					frappe.db.set_value(
						"Assessment Form Records",
						row.name,
						"form_is_submitted",
						1
					)
					
					# Get all users who have ASA role
					user_list = frappe.get_all(
						"Has Role",
						filters={"role": "ASA"},
						fields=["parent"]
					)

					recipients = []
					for u in user_list:
						email = frappe.db.get_value("User", u.parent, "email")
						if email:
							recipients.append(email)

					if not recipients:
						frappe.local.response["http_status_code"] = 404
						frappe.log_error("No users with ASA role found", "ASA Completion Email")
						return

					subject = f"The Vendor {vendor_master.vendor_name} has completed the ASA Form"

					message = f"""
						Dear Sir/Madam,

						The vendor has successfully completed the ASA Form.

						Please log in to the VMS Portal to review and verify the submitted form.

						Regards,
						VMS System
						"""

					frappe.custom_sendmail(
						recipients=recipients,
						subject=subject,
						message=message
					)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in ASAQ on_update")
