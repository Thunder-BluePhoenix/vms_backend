# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RequestForQuotation(Document):
	def on_update(self, method=None):
		send_quotation_email(self)
		update_quotation(self)
		send_mail_on_revised_quotation(self)
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
			link = f"{site_url}/quotation-form?name={doc.name}&office_email_primary={row.office_email_primary}"

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


# get version data from version doc
@frappe.whitelist()
def get_version_data(docname):
	try:
		doc = frappe.get_doc("Request For Quotation", docname)

		latest_version_name = frappe.db.sql("""
			SELECT name FROM `tabVersion`
			WHERE ref_doctype=%s AND docname=%s
			ORDER BY creation DESC
			LIMIT 1
		""", ("Request For Quotation", doc.name))[0][0]

		version = frappe.get_doc("Version", latest_version_name)
		version_data = frappe.parse_json(version.data)

		field_changes = version_data.get("changed", [])
		child_table_changes = version_data.get("row_changed", [])

		if not field_changes and not child_table_changes:
			return

		added = version_data.get("added", [])
		if any(row[0] == "version_history" for row in added):
			return

		filtered_data = {
			"changed": field_changes,
			"row_changed": child_table_changes
		}

		doc.append("version_history", {
			"field_json": frappe.as_json(filtered_data),
			"date_and_time": version.creation
		})
		doc.save(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "get_version_data Error")


# update quotation doc on updation of rfq
def update_quotation(doc):
	try:
		quotations = frappe.get_all("Quotation", filters={"rfq_number": doc.name})
		if not quotations:
			return

		rfq_meta = frappe.get_meta("Request For Quotation")
		quotation_meta = frappe.get_meta("Quotation")

		rfq_fields = [f.fieldname for f in rfq_meta.fields]
		quotation_fields = [f.fieldname for f in quotation_meta.fields]
		common_fields = list(set(rfq_fields) & set(quotation_fields))

		for q in quotations:
			quotation = frappe.get_doc("Quotation", q.name)
			updated = False

			for field in common_fields:
				if doc.get(field) is not None:
					quotation.set(field, doc.get(field))
					updated = True

			rfq_items = doc.get("rfq_items", [])
			quotation_items = quotation.get("rfq_item_list", [])

			for i, rfq_row in enumerate(rfq_items):
				if i < len(quotation_items):
					quote_row = quotation_items[i]
					for field in rfq_row.as_dict():
						if field in quote_row.as_dict() and rfq_row.get(field) is not None:
							quote_row.set(field, rfq_row.get(field))
							updated = True

			if updated:
				quotation.save(ignore_permissions=True)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "update_quotation failed")
			

# mail send to vendor on updation of rfq
def send_mail_on_revised_quotation(doc):
	try:
		site_url = frappe.get_site_config().get('frontend_http', 'https://saksham-v.merillife.com/')

		# Onboarded vendors
		for row in doc.vendor_details:
			quotation_id = row.get("quotation")
			ref_no = row.get("ref_no")
			email = row.get("office_email_primary")
			vendor_name = row.get("vendor_name")

			if not email:
				continue
			
			if row.mail_sent:
				if quotation_id:
					link = f"{site_url}/quotation-form?name={doc.name}&quotation={quotation_id}"
					body = f"""
						<p> Dear {vendor_name}</p><br
						<p>The RFQ <strong>{doc.name}</strong> has been revised. Please review your previously submitted quotation <strong>{quotation_id}</strong>.</p>
						<p><a href="{link}">Click here to view/update the quotation</a></p>
					"""
				else:
					link = f"{site_url}/quotation-form?name={doc.name}&ref_no={ref_no}"
					body = f"""
						<p> Dear {vendor_name}</p><br
						<p>The RFQ <strong>{doc.name}</strong> has been revised. Please review and submit your quotation.</p>
						<p><a href="{link}">Click here to fill the quotation</a></p>
					"""

			frappe.sendmail(
				recipients=[email],
				subject=f"Revised RFQ Notification - {doc.name}",
				message=body,
				now=True
			)

		# Non-onboarded vendors
		for row in doc.non_onboarded_vendor_details:
			quotation_id = row.get("quotation")
			email = row.get("office_email_primary")
			vendor_name = row.get("vendor_name")

			if not email:
				continue
			
			if row.mail_sent:
				if quotation_id:
					link = f"{site_url}/quotation-form?name={doc.name}&quotation={quotation_id}"
					body = f"""
						<p> Dear {vendor_name}</p><br
						<p>The RFQ <strong>{doc.name}</strong> has been revised. Please review your previously submitted quotation <strong>{quotation_id}</strong>.</p>
						<p><a href="{link}">Click here to view/update the quotation</a></p>
					"""
				else:
					link = f"{site_url}/quotation-form?name={doc.name}"
					body = f"""
						<p> Dear {vendor_name}</p><br
						<p>The RFQ <strong>{doc.name}</strong> has been revised. Please review and submit your quotation.</p>
						<p><a href="{link}">Click here to fill the quotation</a></p>
					"""

			frappe.sendmail(
				recipients=[email],
				subject=f"Revised RFQ Notification - {doc.name}",
				message=body,
				now=True
			)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "send_mail_on_revised_quotation Error")

