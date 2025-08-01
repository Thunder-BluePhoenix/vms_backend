# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import jwt
from frappe.utils import get_datetime, now_datetime
from datetime import datetime
from frappe import _
from datetime import datetime, timedelta


class RequestForQuotation(Document):
	def on_update(self, method=None):
		send_quotation_email(self)
		update_quotation(self)
		send_mail_on_revised_quotation(self)
		print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  send_quotation_email")


# def send_quotation_email(doc):
# 	site_url = frappe.get_site_config().get('frontend_http', 'https://saksham-v.merillife.com/')

# 	# For onboarded vendors
# 	for row in doc.vendor_details:
# 		if row.office_email_primary and not row.mail_sent and doc.form_fully_submitted:
# 			ref_no = row.ref_no
# 			link = f"{site_url}/quotation-form?name={doc.name}&ref_no={ref_no}"

# 			subject = "Request for Quotation - Action Required"
# 			message = f"""
# 				<p>Dear {row.vendor_name},</p>
# 				<p>You have been selected to submit a quotation for the requested items in our RFQ document.</p>
# 				<p>Please log in to the portal and create your quotation at the earliest.</p>
# 				<p>Thank you,<br>VMS Team</p><br>
# 				<a href="{link}" target="_blank">Click here to fill quotation</a>
# 			"""
# 			frappe.sendmail(
# 				recipients=row.office_email_primary,
# 				subject=subject,
# 				message=message,
# 				now=True
# 			)
# 			frappe.db.set_value("Vendor Details", row.name, "mail_sent", 1)

# 	# For non-onboarded vendors
# 	for row in doc.non_onboarded_vendor_details:
# 		if row.office_email_primary and not row.mail_sent and doc.form_fully_submitted:
# 			link = f"{site_url}/quotation-form?name={doc.name}&office_email_primary={row.office_email_primary}"

# 			subject = "Request for Quotation - Action Required"
# 			message = f"""
# 				<p>Dear {row.vendor_name},</p>
# 				<p>You have been selected to submit a quotation for the requested items in our RFQ document.</p>
# 				<p>Please get in touch with our procurement team to complete the onboarding process before submitting your quotation.</p>
# 				<p>Thank you,<br>VMS Team</p><br>
# 				<a href="{link}" target="_blank">Click here to fill quotation</a>
# 			"""
# 			frappe.sendmail(
# 				recipients=row.office_email_primary,
# 				subject=subject,
# 				message=message,
# 				now=True
# 			)
# 			frappe.db.set_value("Non Onboarded Vendor Details", row.name, "mail_sent", 1)



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



# ----------------------------------------------------------------------------------------------------------------------

def send_quotation_email(doc):
    site_url = frappe.get_site_config().get('frontend_http', 'https://saksham-v.merillife.com/')

    # For onboarded vendors
    for row in doc.vendor_details:
        if row.office_email_primary and not row.mail_sent and doc.form_fully_submitted:
            token = generate_secure_token(
                ref_no=row.ref_no,
                email=row.office_email_primary,
                rfq_name=doc.name
                # cutoff_date=doc.rfq_cutoff_date_logistic
            )
            link = f"{site_url}/quatation-form?token={token}"

            subject = "Request for Quotation - Action Required"
            message = f"""
                <p>Dear {row.vendor_name}</p>
                <p>You have been selected to submit a quotation for the requested items in our RFQ document.</p>
                <p>Please log in to the portal and create your quotation using the secure link below. This link will expire on <strong>{doc.rfq_cutoff_date_logistic}</strong>.</p>
                <a href="{link}" target="_blank">Click here to fill quotation</a>
                <p>Thank you,<br>VMS Team</p>
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
        if row.office_email_primary and not row.mail_sent and doc.form_fully_submitted:
            token = generate_secure_token(
                email=row.office_email_primary,
                rfq_name=doc.name
                # cutoff_date=doc.rfq_cutoff_date_logistic
            )
            link = f"{site_url}/quatation-form?token={token}"

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


SECRET_KEY = str(frappe.conf.get("secret_key", ""))

def generate_secure_token(ref_no=None, email=None, rfq_name=None):
    payload = {
        "ref_no": ref_no,
        "email": email,
        "rfq": rfq_name
    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@frappe.whitelist(allow_guest=True)
def process_token(token):
    try:
        # Decode JWT without expiration validation
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})

        ref_no = decoded.get("ref_no")
        email = decoded.get("email")
        rfq = decoded.get("rfq")

        vendor_details = {}
        if ref_no:
            vendor_master = frappe.get_doc("Vendor Master", ref_no)
            vendor_details = {
                "vendor_name": vendor_master.vendor_name,
                "office_email_primary": vendor_master.office_email_primary,
                "mobile_number": vendor_master.mobile_number,
                "country": vendor_master.country
            }

        if rfq:
            rfq_doc = frappe.get_doc("Request For Quotation", rfq)

            # Check real-time cutoff first
            cutoff = get_datetime(rfq_doc.rfq_cutoff_date_logistic)
            now = now_datetime()
            if now > cutoff:
                frappe.local.response["http_status_code"] = 410  # Gone
                frappe.local.response["message"] = "This secure link has expired due to cutoff date."
                return

            # Shared attachment extraction
            def get_attachments():
                attachments = []
                for row in rfq_doc.multiple_attachments:
                    file_url = row.get("attachment_name")
                    if file_url:
                        file_doc = frappe.get_doc("File", {"file_url": file_url})
                        attachments.append({
                            "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                            "name": file_doc.name,
                            "file_name": file_doc.file_name
                        })
                    else:
                        attachments.append({
                            "url": "",
                            "name": "",
                            "file_name": ""
                        })
                return attachments

            # Based on RFQ Type
            if rfq_doc.rfq_type == "Logistic Vendor":
                return {
                    "status": "success",
                    "unique_id": rfq_doc.unique_id,
                    "rfq_type": rfq_doc.rfq_type,
                    "logistic_type": rfq_doc.logistic_type,
                    "company_name_logistic": rfq_doc.company_name_logistic,
                    "rfq_cutoff_date_logistic": rfq_doc.rfq_cutoff_date_logistic,
                    "service_provider": rfq_doc.service_provider,
                    "raised_by": rfq_doc.raised_by,
                    "mode_of_shipment": rfq_doc.mode_of_shipment,
                    "port_of_loading": rfq_doc.port_of_loading,
                    "destination_port": rfq_doc.destination_port,
                    "ship_to_address": rfq_doc.ship_to_address,
                    "no_of_pkg_units": rfq_doc.no_of_pkg_units,
                    "vol_weight": rfq_doc.vol_weight,
                    "invoice_date": rfq_doc.invoice_date,
                    "shipment_date": rfq_doc.shipment_date,
                    "remarks": rfq_doc.remarks,
                    "expected_date_of_arrival": rfq_doc.expected_date_of_arrival,
                    "consignee_name": rfq_doc.consignee_name,
                    "sr_no": rfq_doc.sr_no,
                    "rfq_date_logistic": rfq_doc.rfq_date_logistic,
                    "country": rfq_doc.country,
                    "port_code": rfq_doc.port_code,
                    "inco_terms": rfq_doc.inco_terms,
                    "package_type": rfq_doc.package_type,
                    "product_category": rfq_doc.product_category,
                    "actual_weight": rfq_doc.actual_weight,
                    "invoice_no": rfq_doc.invoice_no,
                    "invoice_value": rfq_doc.invoice_value,
                    "shipment_type": rfq_doc.shipment_type,
                    "shipper_name": rfq_doc.shipper_name,
                    "attachments": get_attachments(),
                    "ref_no": ref_no,
                    "email": email,
                    "rfq": rfq,
                    "vendor_details": vendor_details
                }

            elif rfq_doc.rfq_type == "Material Vendor":
                pr_items = []
                for row in rfq_doc.rfq_items:
                    pr_items.append({
                        "row_id": row.name,
                        "head_unique_field": row.head_unique_field,
                        "purchase_requisition_number": row.purchase_requisition_number,
                        "material_code_head": row.material_code_head,
                        "delivery_date_head": row.delivery_date_head,
                        "plant_head": row.plant_head,
                        "material_name_head": row.material_name_head,
                        "quantity_head": row.quantity_head,
                        "uom_head": row.uom_head,
                        "price_head": row.price_head
                    })

                return {
                    "status": "success",
					"unique_id": rfq_doc.unique_id,
					"rfq_type": rfq_doc.rfq_type,
                    "rfq_date": rfq_doc.rfq_date,
                    "company_name": rfq_doc.company_name,
                    "purchase_organization": rfq_doc.purchase_organization,
                    "purchase_group": rfq_doc.purchase_group,
                    "currency": rfq_doc.currency,
                    "collection_number": rfq_doc.collection_number,
                    "quotation_deadline": rfq_doc.quotation_deadline,
                    "validity_start_date": rfq_doc.validity_start_date,
                    "validity_end_date": rfq_doc.validity_end_date,
                    "bidding_person": rfq_doc.bidding_person,
                    "storage_location": rfq_doc.storage_location,
                    "service_code": rfq_doc.service_code,
                    "service_category": rfq_doc.service_category,
                    "service_location": rfq_doc.service_location,
                    "rfq_quantity": rfq_doc.rfq_quantity,
                    "quantity_unit": rfq_doc.quantity_unit,
                    "delivery_date": rfq_doc.delivery_date,
                    "estimated_price": rfq_doc.estimated_price,
                    "pr_items": pr_items,
                    "attachments": get_attachments(),
                    "ref_no": ref_no,
                    "email": email,
                    "rfq": rfq,
                    "vendor_details": vendor_details
                }

            elif rfq_doc.rfq_type == "Service Vendor":
                pr_items = []
                for row in rfq_doc.rfq_items:
                    pr_items.append({
                        "row_id": row.name,
                        "head_unique_field": row.head_unique_field,
                        "purchase_requisition_number": row.purchase_requisition_number,
                        "material_code_head": row.material_code_head,
                        "delivery_date_head": row.delivery_date_head,
                        "plant_head": row.plant_head,
                        "material_name_head": row.material_name_head,
                        "quantity_head": row.quantity_head,
                        "uom_head": row.uom_head,
                        "price_head": row.price_head,
                        "subhead_unique_field": row.subhead_unique_field,
                        "material_code_subhead": row.material_code_subhead,
                        "material_name_subhead": row.material_name_subhead,
                        "quantity_subhead": row.quantity_subhead,
                        "uom_subhead": row.uom_subhead,
                        "price_subhead": row.price_subhead,
                        "delivery_date_subhead": row.delivery_date_subhead
                    })

                return {
                    "status": "success",
					"unique_id": rfq_doc.unique_id,
					"rfq_type": rfq_doc.rfq_type,
                    "rfq_date": rfq_doc.rfq_date,
                    "company_name": rfq_doc.company_name,
                    "purchase_organization": rfq_doc.purchase_organization,
                    "purchase_group": rfq_doc.purchase_group,
                    "currency": rfq_doc.currency,
                    "collection_number": rfq_doc.collection_number,
                    "quotation_deadline": rfq_doc.quotation_deadline,
                    "validity_start_date": rfq_doc.validity_start_date,
                    "validity_end_date": rfq_doc.validity_end_date,
                    "bidding_person": rfq_doc.bidding_person,
                    "storage_location": rfq_doc.storage_location,
                    "service_code": rfq_doc.service_code,
                    "service_category": rfq_doc.service_category,
                    "service_location": rfq_doc.service_location,
                    "rfq_quantity": rfq_doc.rfq_quantity,
                    "quantity_unit": rfq_doc.quantity_unit,
                    "delivery_date": rfq_doc.delivery_date,
                    "estimated_price": rfq_doc.estimated_price,
                    "pr_items": pr_items,
                    "attachments": get_attachments(),
                    "ref_no": ref_no,
                    "email": email,
                    "rfq": rfq,
                    "vendor_details": vendor_details
                }

        # fallback in case no rfq_type matched (shouldn't happen)
        # frappe.throw(_("Invalid RFQ Type."))

    except jwt.InvalidTokenError:
        frappe.local.response["http_status_code"] = 417
        frappe.throw(_("Invalid or tampered link."))

    except frappe.ValidationError:
        frappe.local.response["http_status_code"] = 404
        frappe.throw(_("The request was invalid or failed validation."))
		
    except Exception:
        frappe.log_error(frappe.get_traceback(), "RFQ Token Processing Error")
        frappe.local.response["http_status_code"] = 500
        frappe.throw(_("Something went wrong while processing the link."))
