# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RequestForQuotation(Document):
	def on_update(self, method=None):
		send_quotation_email(self)
		print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  send_quotation_email")


def send_quotation_email(doc):
	site_url = frappe.get_site_config().get('frontend_http', 'https://saksham-v.merillife.com/')

	# For onboarded vendors
	for row in doc.vendor_details:
		if row.office_email_primary and not row.mail_sent:
			ref_no = row.ref_no
			link = f"{site_url}/quotation-form?name={doc.name}&ref_no={ref_no}"

			subject = "Request for Quotation - Action Required"
			message = f"""
				<p>Dear {row.vendor_name},</p>
				<p>You have been selected to submit a quotation for the requested items in our RFQ document.</p>
				<p>Please log in to the portal and create your quotation at the earliest.</p>
				<p>Thank you,<br>VMS Team</p><br>
				<a href="{link}" target="_blank">Click here to fill quotation</a>
			"""
			frappe.sendmail(
				recipients=row.office_email_primary,
				subject=subject,
				message=message,
				now=True
			)
			frappe.db.set_value("Vendor Details", row.name, "mail_sent", 1)

	# For non-onboarded vendors
	for row in doc.non_onboarded_vendor_details:
		if row.office_email_primary and not row.mail_sent:
			link = f"{site_url}/quotation-form?rfq={doc.name}"

			subject = "Request for Quotation - Action Required"
			message = f"""
				<p>Dear {row.vendor_name},</p>
				<p>You have been selected to submit a quotation for the requested items in our RFQ document.</p>
				<p>Please get in touch with our procurement team to complete the onboarding process before submitting your quotation.</p>
				<p>Thank you,<br>VMS Team</p><br>
				<a href="{link}" target="_blank">Click here to fill quotation</a>
			"""
			frappe.sendmail(
				recipients=row.office_email_primary,
				subject=subject,
				message=message,
				now=True
			)
			frappe.db.set_value("Non Onboarded Vendor Details", row.name, "mail_sent", 1)
