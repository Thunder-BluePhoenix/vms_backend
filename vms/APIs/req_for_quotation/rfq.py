# http://127.0.0.1:8003/api/method/vms.APIs.req_for_quotation.rfq.get_full_rfq_data
# apps/vms/vms/APIs/req_for_quotation/rfq.py
import frappe

@frappe.whitelist(allow_guest=False)
def get_full_rfq_data(name):
	try:
		doc = frappe.get_doc("Request For Quotation", name)

		# Child Tables
		pr_items = []
		for row in doc.rfq_items:
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

		# Onboarded Vendor Details Table
		vendor_details_data = []
		for row in doc.vendor_details:
			vendor_details_data.append({
				"refno": row.ref_no,
				"vendor_name": row.vendor_name,
				"vendor_code": [v.strip() for v in row.vendor_code.split(",")] if row.vendor_code else [],
				"office_email_primary": row.office_email_primary,
				"mobile_number": row.mobile_number,
				"service_provider_type": row.service_provider_type,
				"country": row.country
			})

		# Non-Onboarded Vendor Details Table
		non_onboarded_vendor_details_data = []
		for row in doc.non_onboarded_vendor_details:
			non_onboarded_vendor_details_data.append({
				"office_email_primary": row.office_email_primary,
				"vendor_name": row.vendor_name,
				"mobile_number": row.mobile_number,
				"country": row.country
			})

		# File Attachments Section
		attachments = []
		for row in doc.multiple_attachments:
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

		data = {
			# logistic import rfq data
			"rfq_type": doc.rfq_type,
			"company_name_logistic": doc.company_name_logistic,
			"service_provider": doc.service_provider,
			"sr_no": doc.sr_no,
			"rfq_cutoff_date_logistic": doc.rfq_cutoff_date_logistic,
			"rfq_date_logistic": doc.rfq_date_logistic,
			"mode_of_shipment": doc.mode_of_shipment,
			"destination_port": doc.destination_port,
			"country": doc.country,
			"port_code": doc.port_code,
			"port_of_loading": doc.port_of_loading,
			"inco_terms": doc.inco_terms,
			"shipper_name": doc.shipper_name,
			"ship_to_address": doc.ship_to_address,
			"package_type": doc.package_type,
			"no_of_pkg_units": doc.no_of_pkg_units,
			"product_category": doc.product_category,
			"vol_weight": doc.vol_weight,
			"actual_weight": doc.actual_weight,
			"invoice_date": doc.invoice_date,
			"invoice_no": doc.invoice_no,
			"invoice_value": doc.invoice_value,
			"expected_date_of_arrival": doc.expected_date_of_arrival,
			"remarks": doc.remarks,

			# logistic export rfq data
			"consignee_name": doc.consignee_name,
			"shipment_date": doc.shipment_date,

			# logistic/service rfq common data
			"rfq_date": doc.rfq_date,
			"company_name": doc.company_name,
			"purchase_organization": doc.purchase_organization,
			"purchase_group": doc.purchase_group,
			"currency": doc.currency,
			"collection_number": doc.collection_number,
			"quotation_deadline": doc.quotation_deadline,
			"validity_start_date": doc.validity_start_date,
			"validity_end_date": doc.validity_end_date,
			"bidding_person": doc.bidding_person,
			"service_code": doc.service_code,
			"service_category": doc.service_category,
			"material_code": doc.material_code,
			"material_category": doc.material_category,
			"plant_code": doc.plant_code,
			"storage_location": doc.storage_location,
			"short_text": doc.short_text,
			"rfq_quantity": doc.rfq_quantity,
			"quantity_unit": doc.quantity_unit,
			"delivery_date": doc.delivery_date,
			"estimated_price": doc.estimated_price,
			"first_reminder": doc.first_reminder,
			"second_reminder": doc.second_reminder,
			"third_reminder": doc.third_reminder,

			# Tables
			"pr_items": pr_items,
			"vendor_details": vendor_details_data,
			"non_onboarded_vendors": non_onboarded_vendor_details_data,
			"attachments": attachments
		}

		return data

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "get_full_rfq_data failed")
		frappe.throw("Could not fetch RFQ details.")
