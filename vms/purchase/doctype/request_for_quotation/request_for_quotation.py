# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RequestForQuotation(Document):
	def on_update(self, method=None):
		send_quotation_email(self)
		print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  send_quotation_email")


def send_quotation_email(doc):
	# For onboarded vendors
	for row in doc.vendor_details:
		if row.office_email_primary and not row.mail_sent:
			subject = "Request for Quotation - Action Required"
			message = f"""
				<p>Dear {row.vendor_name},</p>
				<p>You have been selected to submit a quotation for the requested items in our RFQ document.</p>
				<p>Please log in to the portal and create your quotation at the earliest.</p>
				<p>Thank you,<br>VMS Team</p>
			"""
			frappe.sendmail(
				recipients=row.office_email_primary,
				subject=subject,
				message=message,
				now=True
			)
			row.mail_sent = 1

	# For non-onboarded vendors
	for row in doc.non_onboarded_vendor_details:
		if row.office_email_primary and not row.mail_sent:
			subject = "Request for Quotation - Action Required"
			message = f"""
				<p>Dear {row.vendor_name},</p>
				<p>You have been selected to submit a quotation for the requested items in our RFQ document.</p>
				<p>Please get in touch with our procurement team to complete the onboarding process before submitting your quotation.</p>
				<p>Thank you,<br>VMS Team</p>
			"""
			frappe.sendmail(
				recipients=row.office_email_primary,
				subject=subject,
				message=message,
				now=True
			)
			row.mail_sent = 1

