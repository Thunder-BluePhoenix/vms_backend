# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime


class SupplierQMSAssessmentForm(Document):
	def on_update(self):

		# set_unique_data(self, method=None)
		# set_qms_form_link(self, method=None)
		set_qms_form_link_unique_data(self, method=None)

		set_unique_data(self, method=None)
		set_qms_form_link(self, method=None)
		send_mail_qa_team(self, method=None)





@frappe.whitelist(allow_guest=True)
def set_qms_form_link(doc, method=None):

	if doc.vendor_onboarding != None:
		ven_onb = frappe.get_doc("Vendor Onboarding", doc.vendor_onboarding)
		ven_onb.qms_form_link = doc.unique_name
		ven_onb.qms_form_filled = 1
		ven_onb.save()
		frappe.db.commit()



def set_unique_data(doc, method=None):
	if doc.unique_name == None or doc.unique_name == "":
		now = datetime.now()
		year_month_prefix = f"QMS{now.strftime('%y')}{now.strftime('%m')}"
		
		existing_max = frappe.db.sql(
			"""
			SELECT MAX(CAST(SUBSTRING(unique_name, 8) AS UNSIGNED))
			FROM `tabSupplier QMS Assessment Form`
			WHERE unique_name LIKE %s
			""",
			(year_month_prefix + "%",),
			as_list=True
		)
		
		max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
		new_count = max_count + 1

		unique_name = f"{year_month_prefix}{str(new_count).zfill(5)}"

		frappe.db.set_value("Supplier QMS Assessment Form", doc.name, "unique_name", unique_name)





@frappe.whitelist(allow_guest=True)
def set_qms_form_link_unique_data(doc, method=None):
	# unique_name = None
	if doc.unique_name == None or doc.unique_name == "":
		now = datetime.now()
		year_month_prefix = f"QMS{now.strftime('%y')}{now.strftime('%m')}"
		
		existing_max = frappe.db.sql(
			"""
			SELECT MAX(CAST(SUBSTRING(unique_name, 8) AS UNSIGNED))
			FROM `tabSupplier QMS Assessment Form`
			WHERE unique_name LIKE %s
			""",
			(year_month_prefix + "%",),
			as_list=True
		)
		
		max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
		new_count = max_count + 1
		unique_name = f"{year_month_prefix}{str(new_count).zfill(5)}"

		frappe.db.set_value("Supplier QMS Assessment Form", doc.name, "unique_name", unique_name)
		if doc.vendor_onboarding != None:
			ven_onb = frappe.get_doc("Vendor Onboarding", doc.vendor_onboarding)
			frappe.db.set_value("Vendor Onboarding", ven_onb.name, "qms_form_link", unique_name)
			frappe.db.set_value("Vendor Onboarding", ven_onb.name, "qms_form_filled", 1)
			# ven_onb.qms_form_link = unique_name
			# ven_onb.qms_form_filled = 1
			# ven_onb.save()
			frappe.db.commit()

	

		doc.unique_name = f"{year_month_prefix}{str(new_count).zfill(5)}"


def send_mail_qa_team(doc, method=None):
	try:
		qa_users = frappe.get_all("Has Role", 
			filters={"role": "QA Team"},
			fields=["parent as user"])

		emails = []
		for u in qa_users:
			user_email = frappe.db.get_value("User", u.user, "email")
			if user_email:
				emails.append(user_email)
		
		if not emails:
			frappe.log_error("No QA users with email found", "send_mail_qa_team")
			return

		http_server = frappe.conf.get("frontend_http")
		
		form_link = f"{http_server}/qms-webform/{doc.name}"

		subject = "Vendor QMS Form Submitted"
		message = f"""
		Dear QA Team,<br><br>
		The vendor has submitted the Supplier QMS Assessment Form.<br>
		Please review it using the link below:<br><br>
		<a href="{form_link}">{form_link}</a><br><br>
		Regards,<br>
		VMS Team
		"""

		# Send the email
		if not doc.mail_sent_to_qa_team:
			frappe.sendmail(
				recipients=emails,
				subject=subject,
				message=message,
				now=True
			)
			frappe.db.set_value("Supplier QMS Assessment Form", doc.name, "mail_sent_to_qa_team", 1)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in send_mail_qa_team")

