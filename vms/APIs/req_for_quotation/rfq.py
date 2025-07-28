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


# get quotation data if vendor has fill the data

@frappe.whitelist(allow_guest=False)
def get_quotation_data(name):
	try:
		doc = frappe.get_doc("Request For Quotation", name)
		quotations = []

		def get_rfq_item_list(quotation):
			items = []
			for item in quotation.rfq_item_list:
				items.append({
					"head_unique_field": item.head_unique_field,
					"purchase_requisition_number": item.purchase_requisition_number,
					"material_code_head": item.material_code_head,
					"delivery_date_head": item.delivery_date_head,
					"plant_head": item.plant_head,
					"material_name_head": item.material_name_head,
					"quantity_head": item.quantity_head,
					"uom_head": item.uom_head,
					"price_head": item.price_head,
					"subhead_unique_field": item.subhead_unique_field,
					"material_code_subhead": item.material_code_subhead,
					"material_name_subhead": item.material_name_subhead,
					"quantity_subhead": item.quantity_subhead,
					"uom_subhead": item.uom_subhead,
					"price_subhead": item.price_subhead,
					"delivery_date_subhead": item.delivery_date_subhead
				})
			return items

		def build_quotation_data(quotation):
			return {
				"quotation_name": quotation.name,
				"ref_no": quotation.ref_no,
				"vendor_name": quotation.vendor_name,
				"office_email_primary": quotation.office_email_primary,

				# Logistic
				"mode_of_shipment": quotation.mode_of_shipment,
				"airlinevessel_name": quotation.airlinevessel_name,
				"chargeable_weight": quotation.chargeable_weight,
				"ratekg": quotation.ratekg,
				"fuel_surcharge": quotation.fuel_surcharge,
				"surcharge": quotation.surcharge,
				"sc": quotation.sc,
				"xray": quotation.xray,
				"pickuporigin": quotation.pickuporigin,
				"ex_works": quotation.ex_works,
				"transit_days": quotation.transit_days,
				"total_freight": quotation.total_freight,
				"from_currency": quotation.from_currency,
				"to_currency": quotation.to_currency,
				"exchange_rate": quotation.exchange_rate,
				"total_freightinr": quotation.total_freightinr,
				"destination_charge": quotation.destination_charge,
				"shipping_line_charge": quotation.shipping_line_charge,
				"cfs_charge": quotation.cfs_charge,
				"total_landing_price": quotation.total_landing_price,
				"remarks": quotation.remarks,
				"material": quotation.material,
				"company_name_logistic": quotation.company_name_logistic,
				"sr_no": quotation.sr_no,
				"rfq_date_logistic": quotation.rfq_date_logistic,
				"rfq_cutoff_date": quotation.rfq_cutoff_date,
				"destination_port": quotation.destination_port,
				"port_code": quotation.port_code,
				"port_of_loading": quotation.port_of_loading,
				"inco_terms": quotation.inco_terms,
				"shipper_name": quotation.shipper_name,
				"package_type": quotation.package_type,
				"no_of_pkg_units": quotation.no_of_pkg_units,
				"product_category_logistic": quotation.product_category_logistic,
				"vol_weight": quotation.vol_weight,
				"actual_weight": quotation.actual_weight,
				"invoice_date": quotation.invoice_date,
				"invoice_no": quotation.invoice_no,
				"invoice_value": quotation.invoice_value,
				"expected_date_of_arrival": quotation.expected_date_of_arrival,
				"consignee_name": quotation.consignee_name,
				"shipment_date": quotation.shipment_date,
				"shipment_type": quotation.shipment_type,
				"quantity": quotation.quantity,
				"ship_to_address": quotation.ship_to_address,

				# Material / Service
				"rfq_date": quotation.rfq_date,
				"quotation_deadline": quotation.quotation_deadline,
				"company_name": quotation.company_name,
				"purchase_organization": quotation.purchase_organization,
				"purchase_group": quotation.purchase_group,
				"currency": quotation.currency,
				"collection_number": quotation.collection_number,
				"validity_start_date": quotation.validity_start_date,
				"validity_end_date": quotation.validity_end_date,
				"contact_person": quotation.contact_person,
				"bidding_person": quotation.bidding_person,
				"storage_location": quotation.storage_location,
				"product_code": quotation.product_code,
				"product_category": quotation.product_category,
				"material_code": quotation.material_code,
				"material_category": quotation.material_category,
				"material_name": quotation.material_name,

				# Service
				"service_location": quotation.service_location,
				"service_code": quotation.service_code,
				"service_category": quotation.service_category,

				# Financials
				"rfq_quantity": quotation.rfq_quantity,
				"quantity_unit": quotation.quantity_unit,
				"delivery_date": quotation.delivery_date,
				"quote_amount": quotation.quote_amount,
				"negotiable": quotation.negotiable,
				"non_negotiable": quotation.non_negotiable,
				"payment_terms": quotation.payment_terms,

				# Child table
				"rfq_item_list": get_rfq_item_list(quotation)
			}

		# Process onboarded vendors
		for row in doc.vendor_details:
			if row.quotation:
				quotation = frappe.get_doc("Quotation", row.quotation)
				quotations.append(build_quotation_data(quotation))

		# Process non-onboarded vendors
		for row in doc.non_onboarded_vendor_details:
			if row.quotation:
				quotation = frappe.get_doc("Quotation", row.quotation)
				quotations.append(build_quotation_data(quotation))

		return {"quotations": quotations}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "get_quotation_data failed")
		frappe.throw("Could not fetch quotation details.")
