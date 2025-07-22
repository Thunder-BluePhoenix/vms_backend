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

		for q in quotations:
			quotation = frappe.get_doc("Quotation", q.name)

			# logistic
			quotation.company_name_logistic = doc.company_name_logistic
			quotation.mode_of_shipment = doc.mode_of_shipment
			quotation.sr_no = doc.sr_no
			quotation.rfq_date_logistic = doc.rfq_date_logistic
			quotation.rfq_cutoff_date = doc.rfq_cutoff_date_logistic
			quotation.destination_port = doc.destination_port
			quotation.port_code = doc.port_code
			quotation.port_of_loading = doc.port_of_loading
			quotation.inco_terms = doc.inco_terms
			quotation.shipper_name = doc.shipper_name
			quotation.package_type = doc.package_type
			quotation.no_of_pkg_units = doc.no_of_pkg_units
			quotation.product_category_logistic = doc.product_category
			quotation.vol_weight = doc.vol_weight
			quotation.actual_weight = doc.actual_weight
			quotation.invoice_date = doc.invoice_date
			quotation.invoice_no = doc.invoice_no
			quotation.invoice_value = doc.invoice_value
			quotation.expected_date_of_arrival = doc.expected_date_of_arrival
			quotation.consignee_name = doc.consignee_name
			quotation.shipment_date = doc.shipment_date
			quotation.shipment_type = doc.shipment_type
			quotation.quantity = doc.quantity
			quotation.ship_to_address = doc.ship_to_address

			# material & services
			quotation.rfq_date = doc.rfq_date
			quotation.quotation_deadline = doc.quotation_deadline
			quotation.company_name = doc.company_name
			quotation.purchase_organization = doc.purchase_organization
			quotation.purchase_group = doc.purchase_group
			quotation.currency = doc.currency
			quotation.collection_number = doc.collection_number
			quotation.validity_start_date = doc.validity_start_date
			quotation.validity_end_date = doc.validity_end_date
			quotation.bidding_person = doc.bidding_person
			quotation.storage_location = doc.storage_location
			quotation.service_location = doc.service_location
			quotation.service_code = doc.service_code
			quotation.service_category = doc.service_category
			quotation.rfq_quantity = doc.rfq_quantity
			quotation.quantity_unit = doc.quantity_unit
			quotation.delivery_date = doc.delivery_date

			# Update child table rows based on idx
			for rfq_row in doc.rfq_items:
				for q_row in quotation.rfq_item_list:
					if rfq_row.idx == q_row.idx:
						q_row.head_unique_field = rfq_row.head_unique_field
						q_row.purchase_requisition_number = rfq_row.purchase_requisition_number
						q_row.material_code_head = rfq_row.material_code_head
						q_row.delivery_date_head = rfq_row.delivery_date_head
						q_row.plant_head = rfq_row.plant_head
						q_row.material_name_head = rfq_row.material_name_head
						q_row.quantity_head = rfq_row.quantity_head
						q_row.uom_head = rfq_row.uom_head
						q_row.price_head = rfq_row.price_head

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

			if not email or not row.mail_sent:
				continue

			if quotation_id:
				link = f"{site_url}/quotation-form?name={doc.name}&quotation={quotation_id}"
				body = f"""
					<p>Dear {vendor_name},</p><br/>
					<p>The RFQ <strong>{doc.name}</strong> has been revised. Please review your previously submitted quotation <strong>{quotation_id}</strong>.</p>
					<p><a href="{link}">Click here to view/update the quotation</a></p>
				"""
			else:
				link = f"{site_url}/quotation-form?name={doc.name}&ref_no={ref_no}"
				body = f"""
					<p>Dear {vendor_name},</p><br/>
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

			if not email or not row.mail_sent:
				continue

			if quotation_id:
				link = f"{site_url}/quotation-form?name={doc.name}&quotation={quotation_id}"
				body = f"""
					<p>Dear {vendor_name},</p><br/>
					<p>The RFQ <strong>{doc.name}</strong> has been revised. Please review your previously submitted quotation <strong>{quotation_id}</strong>.</p>
					<p><a href="{link}">Click here to view/update the quotation</a></p>
				"""
			else:
				link = f"{site_url}/quotation-form?name={doc.name}"
				body = f"""
					<p>Dear {vendor_name},</p><br/>
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

