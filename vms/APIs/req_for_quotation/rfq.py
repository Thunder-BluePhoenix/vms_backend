import frappe
import json
from frappe.utils import now_datetime
from datetime import datetime
from frappe.utils.file_manager import save_file


@frappe.whitelist(allow_guest=False)
def get_full_rfq_data(unique_id):
	try:
		latest_name = frappe.db.sql("""
			SELECT MAX(name) AS name
			FROM `tabRequest For Quotation`
			WHERE unique_id = %s
		""", unique_id, as_dict=True)

		if not latest_name or not latest_name[0].name:
			frappe.throw("Could not find latest RFQ version.")

		rfq_name = latest_name[0].name
		doc = frappe.get_doc("Request For Quotation", rfq_name)

		# Child Tables
		grouped_data = {}

		for row in sorted(doc.rfq_items, key=lambda x: x.idx):
			head_id = row.head_unique_field
			if not head_id:
				continue

			if head_id not in grouped_data:
					grouped_data[head_id] = {
					"row_id": row.name,
					"head_unique_field": row.head_unique_field,
					"purchase_requisition_number": row.purchase_requisition_number,
					"material_code_head": row.material_code_head,
					"delivery_date_head": row.delivery_date_head,
					"material_name_head": row.material_name_head,
					"quantity_head": row.quantity_head,
					"uom_head": row.uom_head,
					"price_head": row.price_head,
					"rate_with_tax": row.rate_with_tax,
					"rate_without_tax": row.rate_without_tax,
					"moq_head": row.moq_head,
					"lead_time_head": row.lead_time_head,
					"tax": row.tax,
					"remarks": row.remarks,
					"subhead_fields": []
				}
			subhead_data = {
					"subhead_unique_field": row.subhead_unique_field,
					"material_code_subhead": row.material_code_subhead,
					"material_name_subhead": row.material_name_subhead,
					"quantity_subhead": row.quantity_subhead,
					"uom_subhead": row.uom_subhead,
					"price_subhead": row.price_subhead,
					"delivery_date_subhead": row.delivery_date_subhead
			}
			grouped_data[head_id]["subhead_fields"].append(subhead_data)

		# Onboarded Vendor Details Table
		vendor_details_data = []
		vendor_with_quotation = 0
		for row in doc.vendor_details:
			if row.quotation:
				vendor_with_quotation += 1    

			# Parse json_field if present
			try:
				parsed_json = frappe.parse_json(row.json_field) if row.json_field else []
			except Exception:
				parsed_json = []

			if parsed_json:
				vendor_details_data.append({
					"refno": row.ref_no,
					"vendor_name": row.vendor_name,
					"vendor_code": [v.strip() for v in row.vendor_code.split(",")] if row.vendor_code else [],
					"office_email_primary": row.office_email_primary,
					"mobile_number": row.mobile_number,
					"service_provider_type": row.service_provider_type,
					"country": row.country,
					"bid_won": row.bid_won,
					"bid_loss": row.bid_loss,
					"quotations": parsed_json   
				})

		# Non-Onboarded Vendor Details Table
		non_onboarded_with_quotation = 0
		for row in doc.non_onboarded_vendor_details:
			if row.quotation:
				non_onboarded_with_quotation += 1

			try:
				parsed_json = frappe.parse_json(row.json_field) if row.json_field else []
			except Exception:
				parsed_json = []

			if parsed_json:
				vendor_details_data.append({
					"office_email_primary": row.office_email_primary,
					"vendor_name": row.vendor_name,
					"mobile_number": row.mobile_number,
					"country": row.country,
					"company_pan": row.company_pan,
					"gst_number": row.gst_number,
					"bid_won": row.bid_won,
					"bid_loss": row.bid_loss,
					"quotations": parsed_json 
				})

		all_vendors = []

		for row in doc.vendor_details:
				all_vendors.append({
					"refno": row.ref_no,
					"vendor_name": row.vendor_name,
					"vendor_code": [v.strip() for v in row.vendor_code.split(",")] if row.vendor_code else [],
					"office_email_primary": row.office_email_primary,
					"mobile_number": row.mobile_number,
					"service_provider_type": row.service_provider_type,
					"country": row.country
				})

		for row in doc.non_onboarded_vendor_details:
				all_vendors.append({
					"office_email_primary": row.office_email_primary,
					"vendor_name": row.vendor_name,
					"mobile_number": row.mobile_number,
					"country": row.country,
					"company_pan": row.company_pan,
					"gst_number": row.gst_number
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

		# Total RFQs Sent and Quotations Received
		total_rfq_sent = len(doc.vendor_details) + len(doc.non_onboarded_vendor_details)
		total_quotation_received = vendor_with_quotation + non_onboarded_with_quotation

		final_approve_quotation = None

		for row in doc.vendor_details:
			if row.quotation:
				final_approve_quotation = frappe.get_doc("Quotation", row.quotation)
						
		for row in doc.non_onboarded_vendor_details:
			if row.quotation:
				final_approve_quotation = frappe.get_doc("Quotation", row.quotation)

		data = {
			# logistic import rfq data / logistic export rfq data
			"name": doc.name,
			"status": doc.status,
			"form_fully_submitted": doc.form_fully_submitted,
			"is_approved": doc.is_approved,
			"revised_rfq": doc.revised_rfq,
			"unique_id": doc.unique_id,
			"rfq_type": doc.rfq_type,
			"raised_by": doc.raised_by,
			"logistic_type": doc.logistic_type,
			"company_name_logistic": doc.company_name_logistic,
			"rfq_cutoff_date_logistic": doc.rfq_cutoff_date_logistic,
			"mode_of_shipment": doc.mode_of_shipment,
			"port_of_loading": doc.port_of_loading,
			"destination_port": doc.destination_port,
			"ship_to_address": doc.ship_to_address,
			"no_of_pkg_units": doc.no_of_pkg_units,
			"vol_weight": doc.vol_weight,
			"invoice_date": doc.invoice_date,
			"shipment_date": doc.shipment_date,
			"remarks": doc.remarks,
			"expected_date_of_arrival": doc.expected_date_of_arrival,
			"service_provider": doc.service_provider,
			"consignee_name": doc.consignee_name,
			"sr_no": doc.sr_no,
			"rfq_date_logistic": doc.rfq_date_logistic,
			"country": doc.country,
			"port_code": doc.port_code,
			"inco_terms": doc.inco_terms,
			"package_type": doc.package_type,
			"product_category": doc.product_category,
			"actual_weight": doc.actual_weight,
			"invoice_no": doc.invoice_no,
			"shipment_type": doc.shipment_type,
			"shipper_name": doc.shipper_name,
			"invoice_value": doc.invoice_value,

			# Material/service rfq common data
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
			"pr_items": list(grouped_data.values()),
			"vendor_details": vendor_details_data,
			"all_vendors": all_vendors,
			"attachments": attachments,

			# approved quotation details
			"final_quotation_id": final_approve_quotation.name if final_approve_quotation else "",
			"is_negotiated": final_approve_quotation.is_negotiated if final_approve_quotation else 0,
			"final_mode_of_shipment": final_approve_quotation.mode_of_shipment if final_approve_quotation else "",
			"final_ffn": final_approve_quotation.final_ffn if final_approve_quotation else "",
			"final_freight_fcr": final_approve_quotation.final_freight_fcr if final_approve_quotation else "",
			"final_xcr": final_approve_quotation.final_xcr if final_approve_quotation else "",
			"final_sum_freight_inr": final_approve_quotation.final_sum_freight_inr if final_approve_quotation else "",
			"final_others": final_approve_quotation.final_others if final_approve_quotation else "",
			"final_dc": final_approve_quotation.final_dc if final_approve_quotation else "",
			"final_remarks": final_approve_quotation.final_remarks if final_approve_quotation else "",
			"final_rate_kg": final_approve_quotation.final_rate_kg if final_approve_quotation else "",
			"final_fsc": final_approve_quotation.final_fsc if final_approve_quotation else "",
			"final_pickup": final_approve_quotation.final_pickup if final_approve_quotation else "",
			"final_gst_amount": final_approve_quotation.final_gst_amount if final_approve_quotation else "",
			"final_airline": final_approve_quotation.final_airline if final_approve_quotation else "",
			"final_transit_days": final_approve_quotation.final_transit_days if final_approve_quotation else "",
			"final_tat": final_approve_quotation.final_tat if final_approve_quotation else "",
			"final_chargeable_weight": final_approve_quotation.final_chargeable_weight if final_approve_quotation else "",
			"final_sc": final_approve_quotation.final_sc if final_approve_quotation else "",
			"final_xray": final_approve_quotation.final_xray if final_approve_quotation else "",
			"final_total": final_approve_quotation.final_total if final_approve_quotation else "",
			"final_landing_price": final_approve_quotation.final_landing_price if final_approve_quotation else "",
			"final_freight_total": final_approve_quotation.final_freight_total if final_approve_quotation else "",
			"final_cfs_charge": final_approve_quotation.final_cfs_charge if final_approve_quotation else "",

			# Counts
			"total_rfq_sent": total_rfq_sent,
			"total_quotation_received": total_quotation_received
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


# send revised rfq

# @frappe.whitelist(allow_guest=False)
# def send_revised_rfq(data):
# 	if isinstance(data, str):
# 		data = json.loads(data)

# 	if not data.get("name"):
# 		frappe.throw("Missing RFQ name")

# 	old_rfq = frappe.get_doc("Request For Quotation", data.get("name"))

# 	frappe.db.set_value("Request For Quotation", old_rfq.name, "revised_quotation", 1)

# 	new_rfq = frappe.new_doc("Request For Quotation")
# 	old_rfq_data = old_rfq.as_dict()
# 	for unwanted in ["name", "creation", "modified", "owner", "head_target", "revised_rfq"]:
# 		old_rfq_data.pop(unwanted, None)

# 	new_rfq.update(old_rfq_data)

# 	new_rfq.name = None
# 	new_rfq.prev_rfq = old_rfq.name
# 	new_rfq.status = "Pending"

# 	excluded_fields = ["head_target", "revised_rfq"]

# 	main_fields = [
# 		"status", "company_name_logistic", "rfq_cutoff_date_logistic", "mode_of_shipment",
# 		"destination_port", "port_of_loading", "ship_to_address", "no_of_pkg_units", "vol_weight",
# 		"invoice_date", "shipment_date", "remarks", "expected_date_of_arrival", "service_provider",
# 		"consignee_name", "sr_no", "rfq_date_logistic", "country", "port_code", "inco_terms",
# 		"package_type", "product_category", "actual_weight", "invoice_no", "invoice_value",
# 		"shipment_type", "material", "quantity", "shipper_name", "rfq_date", "rfq_cutoff_date",
# 		"company_name", "purchase_organization", "purchase_group", "currency", "collection_number",
# 		"quotation_deadline", "validity_start_date", "validity_end_date", "requestor_name",
# 		"bidding_person", "material_code", "material_category", "plant_code", "storage_location",
# 		"short_text", "catalogue_number", "service_code", "service_location", "service_category",
# 		"quantity_and_date_section", "rfq_quantity", "quantity_unit", "delivery_date",
# 		"add_expected_budgetary_target_price_section", "estimated_price", "first_reminder",
# 		"second_reminder", "third_reminder"
# 	]

# 	for field in main_fields:
# 		if field in excluded_fields:
# 			continue
# 		if field in data and data.get(field) != old_rfq.get(field):
# 			new_rfq.set(field, data.get(field))
# 		else:
# 			new_rfq.set(field, old_rfq.get(field)) 


# 	old_child_rows = {row.name: row for row in old_rfq.get("rfq_items", [])}

# 	updated_data = data.get("rfq_items", [])
# 	updated_row_ids = set(row.get("row_id") for row in updated_data if row.get("row_id"))

# 	new_items = []

# 	for row in updated_data:
# 		row_id = row.get("row_id")
# 		old_child = old_child_rows.get(row_id)

# 		if old_child:
# 			for key, value in row.items():
# 				if key != "row_id" and value != old_child.get(key):
# 					old_child.set(key, value)
# 			new_items.append(old_child)

# 	for name, old_row in old_child_rows.items():
# 		if name not in updated_row_ids:
# 			new_items.append(old_row)

# 	new_rfq.set("rfq_items", new_items)


# 	# Save new RFQ
# 	new_rfq.insert(ignore_permissions=True)
# 	frappe.db.commit()

# 	return {
# 		"status": "success",
# 		"message": "Revised RFQ created successfully",
# 		"new_rfq": new_rfq.name
# 	}


@frappe.whitelist(allow_guest=False)
def send_revised_rfq(data): 
    if isinstance(data, str):
        data = json.loads(data)

    if not data.get("name"):
        frappe.throw("Missing RFQ name")

    # Get old RFQ and mark it as revised
    old_rfq = frappe.get_doc("Request For Quotation", data.get("name"))
    frappe.db.set_value("Request For Quotation", old_rfq.name, "revised_rfq", 1)

    # Create new RFQ document
    rfq = frappe.new_doc("Request For Quotation")
    rfq.unique_id = old_rfq.unique_id
    rfq.prev_rfq = old_rfq.name
    rfq.raised_by = frappe.local.session.user
    rfq.form_fully_submitted = 1
    rfq.status = "Pending"
    rfq.rfq_type = data.get("rfq_type")

    # Logistic Vendor RFQ
    if data.get("rfq_type") == "Logistics Vendor":
        rfq.logistic_type = data.get("logistic_type")
        rfq.company_name_logistic = data.get("company_name_logistic")
        rfq.service_provider = data.get("service_provider")
        rfq.sr_no = data.get("sr_no")
        rfq.rfq_cutoff_date_logistic = data.get("rfq_cutoff_date_logistic")
        rfq.rfq_date_logistic = data.get("rfq_date_logistic")
        rfq.mode_of_shipment = data.get("mode_of_shipment")
        rfq.shipment_type = data.get("shipment_type")
        rfq.destination_port = data.get("destination_port")
        rfq.country = data.get("country")
        rfq.port_code = data.get("port_code")
        rfq.port_of_loading = data.get("port_of_loading")
        rfq.inco_terms = data.get("inco_terms")
        rfq.shipper_name = data.get("shipper_name")
        rfq.ship_to_address = data.get("ship_to_address")
        rfq.package_type = data.get("package_type")
        rfq.no_of_pkg_units = data.get("no_of_pkg_units")
        rfq.product_category = data.get("product_category")
        rfq.vol_weight = data.get("vol_weight")
        rfq.actual_weight = data.get("actual_weight")
        rfq.invoice_date = data.get("invoice_date")
        rfq.invoice_no = data.get("invoice_no")
        rfq.invoice_value = data.get("invoice_value")
        rfq.expected_date_of_arrival = data.get("expected_date_of_arrival")
        rfq.consignee_name = data.get("consignee_name")
        rfq.shipment_date = data.get("shipment_date")
        rfq.remarks = data.get("remarks")

        # Add vendors from Vendor Master (All Service Provider)
        if data.get("service_provider") == "All Service Provider":
            vendors = frappe.get_all(
                "Vendor Master",
                filters={"service_provider_type": ["in", ["Service Provider", "Premium Service Provider"]]},
                fields=["name", "vendor_name", "office_email_primary", "mobile_number", "country", "service_provider_type"]
            )
            for vm in vendors:
                vendor_code = []
                company_codes = frappe.get_all("Company Vendor Code", filters={"vendor_ref_no": vm.name}, fields=["name"])
                for row in company_codes:
                    doc = frappe.get_doc("Company Vendor Code", row.name)
                    for code_row in doc.vendor_code:
                        vendor_code.append(code_row.vendor_code)

                rfq.append("vendor_details", {
                    "ref_no": vm.name,
                    "vendor_name": vm.vendor_name,
                    "office_email_primary": vm.office_email_primary,
                    "vendor_code": ", ".join(vendor_code),
                    "mobile_number": vm.mobile_number,
                    "service_provider_type": vm.service_provider_type,
                    "country": vm.country
                })

        # Premium Only
        elif data.get("service_provider") == "Premium Service Provider":
            vendors = frappe.get_all(
                "Vendor Master",
                filters={"service_provider_type": "Premium Service Provider"},
                fields=["name", "vendor_name", "office_email_primary", "mobile_number", "country", "service_provider_type"]
            )
            for vm in vendors:
                vendor_code = []
                company_codes = frappe.get_all("Company Vendor Code", filters={"vendor_ref_no": vm.name}, fields=["name"])
                for row in company_codes:
                    doc = frappe.get_doc("Company Vendor Code", row.name)
                    for code_row in doc.vendor_code:
                        vendor_code.append(code_row.vendor_code)

                rfq.append("vendor_details", {
                    "ref_no": vm.name,
                    "vendor_name": vm.vendor_name,
                    "office_email_primary": vm.office_email_primary,
                    "vendor_code": ", ".join(vendor_code),
                    "mobile_number": vm.mobile_number,
                    "service_provider_type": vm.service_provider_type,
                    "country": vm.country
                })

        # Manually passed onboarded vendors
        for vendor in data.get("vendors", []):
            rfq.append("vendor_details", {
                "ref_no": vendor.get("refno"),
                "vendor_name": vendor.get("vendor_name"),
                "vendor_code": ", ".join(vendor.get("vendor_code", [])),
                "office_email_primary": vendor.get("office_email_primary"),
                "mobile_number": vendor.get("mobile_number"),
                "service_provider_type": vendor.get("service_provider_type"),
                "country": vendor.get("country")
            })

        # Non-onboarded vendor table
        for vendor in data.get("non_onboarded_vendors", []):
            rfq.append("non_onboarded_vendor_details", {
                "office_email_primary": vendor.get("office_email_primary"),
                "vendor_name": vendor.get("vendor_name"),
                "mobile_number": vendor.get("mobile_number"),
                "country": vendor.get("country"),
                "company_pan": vendor.get("company_pan"),
                "gst_number": vendor.get("gst_number")
            })

    # Material Vendor RFQ
    elif data.get("rfq_type") == "Material Vendor":
        rfq.rfq_date = data.get("rfq_date")
        rfq.company_name = data.get("company_name")
        rfq.purchase_organization = data.get("purchase_organization")
        rfq.purchase_group = data.get("purchase_group")
        rfq.currency = data.get("currency") or "INR"

        # Administrative Fields
        rfq.collection_number = data.get("collection_number")
        rfq.rfq_cutoff_date_logistic = data.get("rfq_cutoff_date_logistic")
        rfq.validity_start_date = data.get("validity_start_date")
        rfq.validity_end_date = data.get("validity_end_date")
        rfq.bidding_person = data.get("bidding_person")

        # Material/Service Details
        rfq.service_code = data.get("service_code")
        rfq.service_category = data.get("service_category")
        rfq.material_code = data.get("material_code")
        rfq.material_category = data.get("material_category")
        rfq.plant_code = data.get("plant_code")
        rfq.storage_location = data.get("storage_location")
        rfq.short_text = data.get("short_text")

        # Quantity & Dates
        rfq.rfq_quantity = data.get("rfq_quantity")
        rfq.quantity_unit = data.get("quantity_unit")
        rfq.delivery_date = data.get("delivery_date")

        # Target Price
        rfq.estimated_price = data.get("estimated_price")

        # RFQ Items Table
        for item in data.get("pr_items", []):
            rfq.append("rfq_items", {
                "head_unique_field": item.get("head_unique_field"),
                "purchase_requisition_number": item.get("requisition_no"),
                "material_code_head": item.get("material_code_head"),
                "delivery_date_head": item.get("delivery_date_head"),
                "material_name_head": item.get("material_name_head"),
                "quantity_head": item.get("quantity_head"),
                "uom_head": item.get("uom_head"),
                "price_head": item.get("price_head"),
                "rate_with_tax": item.get("rate_with_tax"),
                "rate_without_tax": item.get("rate_without_tax"),
                "moq_head": item.get("moq_head"),
                "lead_time_head": item.get("lead_time_head"),
                "tax": item.get("tax")
            })

        # Vendor Details Table
        for vendor in data.get("vendors", []):
            rfq.append("vendor_details", {
                "ref_no": vendor.get("refno"),
                "vendor_name": vendor.get("vendor_name"),
                "vendor_code": ", ".join(vendor.get("vendor_code", [])),
                "office_email_primary": vendor.get("office_email_primary"),
                "mobile_number": vendor.get("mobile_number"),
                "service_provider_type": vendor.get("service_provider_type"),
                "country": vendor.get("country")
            })

        # Non-Onboarded Vendor Table
        for vendor in data.get("non_onboarded_vendors", []):
            rfq.append("non_onboarded_vendor_details", {
                "office_email_primary": vendor.get("office_email_primary"),
                "vendor_name": vendor.get("vendor_name"),
                "mobile_number": vendor.get("mobile_number"),
                "country": vendor.get("country"),
                "company_pan": vendor.get("company_pan"),
                "gst_number": vendor.get("gst_number")
            })

    # Service Vendor RFQ
    elif data.get("rfq_type") == "Service Vendor":
        rfq.rfq_date = data.get("rfq_date")
        rfq.company_name = data.get("company_name")
        rfq.purchase_organization = data.get("purchase_organization")
        rfq.purchase_group = data.get("purchase_group")
        rfq.currency = data.get("currency")

        # Administrative Fields
        rfq.collection_number = data.get("collection_number")
        rfq.rfq_cutoff_date_logistic = data.get("rfq_cutoff_date_logistic")
        rfq.validity_start_date = data.get("validity_start_date")
        rfq.validity_end_date = data.get("validity_end_date")
        rfq.bidding_person = data.get("bidding_person")

        # Material/Service Details
        rfq.service_code = data.get("service_code")
        rfq.service_category = data.get("service_category")
        rfq.service_location = data.get("service_location")
        rfq.material_code = data.get("material_code")
        rfq.material_category = data.get("material_category")
        rfq.plant_code = data.get("plant_code")
        rfq.storage_location = data.get("storage_location")
        rfq.short_text = data.get("short_text")

        # Quantity & Dates
        rfq.rfq_quantity = data.get("rfq_quantity")
        rfq.quantity_unit = data.get("quantity_unit")
        rfq.delivery_date = data.get("delivery_date")

        # Target Price
        rfq.estimated_price = data.get("estimated_price")

        # Group RFQ items head-wise and subhead-wise
        for item in data.get("pr_items", []):
            head_fields = {
                "head_unique_field": item.get("head_unique_field"),
                "purchase_requisition_number": item.get("requisition_no"),
                "material_code_head": item.get("material_code_head"),
                "delivery_date_head": item.get("delivery_date_head"),
                "material_name_head": item.get("material_name_head"),
                "quantity_head": item.get("quantity_head"),
                "uom_head": item.get("uom_head"),
                "price_head": item.get("price_head"),
                "rate_with_tax": item.get("rate_with_tax"),
                "rate_without_tax": item.get("rate_without_tax"),
                "moq_head": item.get("moq_head"),
                "lead_time_head": item.get("lead_time_head"),
                "tax": item.get("tax")
            }

            subheads = item.get("subhead_fields", [])
            if subheads:
                for sub in subheads:
                    rfq.append("rfq_items", {**head_fields, **{
                        "is_subhead": 1,
                        "subhead_unique_field": sub.get("subhead_unique_field"),
                        "material_code_subhead": sub.get("material_code_subhead"),
                        "material_name_subhead": sub.get("material_name_subhead"),
                        "quantity_subhead": sub.get("quantity_subhead"),
                        "uom_subhead": sub.get("uom_subhead"),
                        "price_subhead": sub.get("price_subhead"),
                        "delivery_date_subhead": sub.get("delivery_date_subhead")
                    }})
            else:
                rfq.append("rfq_items", {
                    **head_fields,
                    "is_subhead": 0,
                    "subhead_unique_field": "",
                    "material_code_subhead": "",
                    "material_name_subhead": "",
                    "quantity_subhead": "",
                    "uom_subhead": "",
                    "price_subhead": "",
                    "delivery_date_subhead": ""
                })

        # Vendor Details Table
        for vendor in data.get("vendors", []):
            rfq.append("vendor_details", {
                "ref_no": vendor.get("refno"),
                "vendor_name": vendor.get("vendor_name"),
                "vendor_code": ", ".join(vendor.get("vendor_code", [])),
                "office_email_primary": vendor.get("office_email_primary"),
                "mobile_number": vendor.get("mobile_number"),
                "service_provider_type": vendor.get("service_provider_type"),
                "country": vendor.get("country")
            })

        # Non-Onboarded Vendor Table
        for vendor in data.get("non_onboarded_vendors", []):
            rfq.append("non_onboarded_vendor_details", {
                "office_email_primary": vendor.get("office_email_primary"),
                "vendor_name": vendor.get("vendor_name"),
                "mobile_number": vendor.get("mobile_number"),
                "country": vendor.get("country"),
                "company_pan": vendor.get("company_pan"),
                "gst_number": vendor.get("gst_number")
            })

    rfq.insert(ignore_permissions=True)

    files = frappe.request.files.getlist("file")
    for file in files:
        saved = save_file(file.filename, file.stream.read(), rfq.doctype, rfq.name, is_private=0)
        rfq.append("multiple_attachments", {
            "attachment_name": saved.file_url
        })
		
    frappe.db.commit()

    return {
        "status": "success",
        "message": "Revised RFQ created successfully",
        "new_rfq": rfq.name
    }


# dashboard for rfq logistic

# @frappe.whitelist(allow_guest=False)
# def rfq_dashboard(company_name=None, name=None, page_no=1, page_length=5, rfq_type=None, status=None):
# 	try:
# 		page_no = int(page_no) if page_no else 1
# 		page_length = int(page_length) if page_length else 5
# 		offset = (page_no - 1) * page_length

# 		# Build dynamic filters
# 		conditions = []
# 		values = {}

# 		if company_name:
# 			conditions.append("(company_name = %(company_name)s OR company_name_logistic = %(company_name)s)")
# 			values["company_name"] = company_name

# 		if name:
# 			conditions.append("name LIKE %(name)s")
# 			values["name"] = f"%{name}%"

# 		if rfq_type:
# 			conditions.append("rfq_type = %(rfq_type)s")
# 			values["rfq_type"] = rfq_type

# 		if status:
# 			conditions.append("status = %(status)s")
# 			values["status"] = status

# 		condition_clause = " AND ".join(conditions)
# 		condition_clause = f"WHERE {condition_clause}" if condition_clause else ""

# 		# Total count
# 		total_count = frappe.db.sql(f"""
#             SELECT COUNT(*) FROM (
#                 SELECT 1
#                 FROM `tabRequest For Quotation`
#                 {condition_clause}
#                 GROUP BY unique_id
#             ) AS grouped
#         """, values)[0][0]

# 		# Paginated result
# 		data = frappe.db.sql(f"""
#             SELECT
#                 rfq.name,
#                 IFNULL(rfq.company_name_logistic, rfq.company_name) AS company_name,
#                 rfq.rfq_type,
#                 IFNULL(rfq.rfq_date_logistic, rfq.rfq_date) AS rfq_date,
#                 IFNULL(rfq.delivery_date, rfq.shipment_date) AS delivery_date,
#                 rfq.status
#             FROM `tabRequest For Quotation` rfq
#             INNER JOIN (
#                 SELECT MAX(name) AS name
#                 FROM `tabRequest For Quotation`
#                 {condition_clause}
#                 GROUP BY unique_id
#             ) latest_rfq ON rfq.name = latest_rfq.name
#             ORDER BY rfq.creation DESC
#             LIMIT %(limit)s OFFSET %(offset)s
#         """, {**values, "limit": page_length, "offset": offset}, as_dict=True)

# 		return {
# 			"status": "success",
# 			"message": f"{len(data)} RFQ(s) found",
# 			"data": data,
# 			"total_count": total_count,
# 			"page_no": page_no,
# 			"page_length": page_length
# 		}

# 	except Exception as e:
# 		frappe.log_error(frappe.get_traceback(), "RFQ Dashboard Error")
# 		return {
# 			"status": "error",
# 			"message": "Failed to fetch RFQ dashboard data.",
# 			"error": str(e)
# 		}


@frappe.whitelist(allow_guest=False)
def rfq_dashboard(company_name=None, name=None, page_no=1, page_length=5, rfq_type=None, status=None):
	try:
		usr = frappe.session.user
		user_roles = frappe.get_roles(usr)

		if "Vendor" in user_roles:
			return vendor_rfq_dashboard(company_name, name, page_no, page_length, rfq_type, status, usr)

		if "Purchase Team" in user_roles:
			# team = frappe.get_value("Employee", filters={"user_id": usr}, fields=["team"])
			# employees = frappe.get_all("Employee", filters={"team": team}, pluck=["user_id"])
			# if session user belongs to this employees list 
			return purchase_team_rfq_dashboard(company_name, name, page_no, page_length, rfq_type, status)

		return {
			"status": "error",
			"message": "You do not have permission to access this dashboard."
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "RFQ Dashboard Error")
		return {
			"status": "error",
			"message": "Failed to fetch RFQ dashboard data.",
			"error": str(e)
		}


# Dashboard for Vendors
def vendor_rfq_dashboard(company_name, name, page_no, page_length, rfq_type, status, usr):
	try:
		page_no = int(page_no) if page_no else 1
		page_length = int(page_length) if page_length else 5
		offset = (page_no - 1) * page_length

		conditions = []
		values = {}

		if company_name:
			conditions.append("(company_name LIKE %(company_name)s OR company_name_logistic LIKE %(company_name)s)")
			values["company_name"] = f"%{company_name}%"

		if name:
			conditions.append("name LIKE %(name)s")
			values["name"] = f"%{name}%"

		if rfq_type:
			conditions.append("rfq_type = %(rfq_type)s")
			values["rfq_type"] = rfq_type

		if status:
			conditions.append("status = %(status)s")
			values["status"] = status

		condition_clause = " AND ".join(conditions)
		condition_clause = f"WHERE {condition_clause}" if condition_clause else ""

		# Filter RFQs by vendor email
		rfq_names = [r[0] for r in frappe.db.sql("""
			SELECT parent FROM `tabVendor Details`
			WHERE office_email_primary = %s
		""", usr)]

		if not rfq_names:
			return {
				"status": "success",
				"message": "No RFQs found for vendor",
				"data": [],
				"total_count": 0
			}

		values["rfq_names"] = tuple(rfq_names)

		# Total count
		total_count = frappe.db.sql(f"""
			SELECT COUNT(*) FROM (
				SELECT 1 FROM `tabRequest For Quotation`
				WHERE name IN %(rfq_names)s
				{f"AND {condition_clause}" if condition_clause else ""}
				GROUP BY unique_id
			) AS grouped
		""", values)[0][0]

		# Overall total RFQ count for vendor (merged from total_rfq_count logic)
		overall_total_rfq = frappe.db.sql("""
			SELECT COUNT(*) FROM (
				SELECT DISTINCT parent
				FROM (
					SELECT parent FROM `tabVendor Details`
					WHERE office_email_primary = %(email)s
					UNION
					SELECT parent FROM `tabNon Onboarded Vendor Details`
					WHERE office_email_primary = %(email)s
				) AS combined
				JOIN `tabRequest For Quotation` rfq ON rfq.name = combined.parent
				GROUP BY rfq.unique_id
			) AS grouped
		""", {"email": usr})[0][0]

		data = frappe.db.sql(f"""
			SELECT
				rfq.name,
				IFNULL(rfq.company_name_logistic, rfq.company_name) AS company_name,
				rfq.creation,
				rfq.rfq_type,
				rfq.logistic_type,
				rfq.unique_id,
				IFNULL(rfq.rfq_date_logistic, rfq.quotation_deadline) AS rfq_date,
				IFNULL(rfq.delivery_date, rfq.shipment_date) AS delivery_date,
				rfq.status
			FROM `tabRequest For Quotation` rfq
			INNER JOIN (
				SELECT MAX(name) AS name FROM `tabRequest For Quotation`
				WHERE name IN %(rfq_names)s
				{f"AND {condition_clause}" if condition_clause else ""}
				GROUP BY unique_id
			) latest_rfq ON rfq.name = latest_rfq.name
			ORDER BY rfq.creation DESC
			LIMIT %(limit)s OFFSET %(offset)s
		""", {**values, "limit": page_length, "offset": offset}, as_dict=True)

		return {
			"status": "success",
			"message": f"{len(data)} RFQ(s) found",
			"data": data,
			"total_count": total_count or 0,
			"overall_total_rfq": overall_total_rfq,
			"page_no": page_no,
			"page_length": page_length
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Vendor RFQ Dashboard Error")
		return {
			"status": "error",
			"message": "Failed to fetch vendor RFQ dashboard.",
			"error": str(e)
		}


# Dashboard for Purchase Team
def purchase_team_rfq_dashboard(company_name, name, page_no, page_length, rfq_type, status):
	try:
		page_no = int(page_no) if page_no else 1
		page_length = int(page_length) if page_length else 5
		offset = (page_no - 1) * page_length

		conditions = []
		values = {}

		if company_name:
			conditions.append("(company_name LIKE %(company_name)s OR company_name_logistic LIKE %(company_name)s)")
			values["company_name"] = f"%{company_name}%"

		if name:
			conditions.append("name LIKE %(name)s")
			values["name"] = f"%{name}%"

		if rfq_type:
			conditions.append("rfq_type = %(rfq_type)s")
			values["rfq_type"] = rfq_type

		if status:
			conditions.append("status = %(status)s")
			values["status"] = status

		condition_clause = " AND ".join(conditions)
		condition_clause = f"WHERE {condition_clause}" if condition_clause else ""

		# Total count
		total_count = frappe.db.sql(f"""
			SELECT COUNT(*) FROM (
				SELECT 1 FROM `tabRequest For Quotation`
				{condition_clause}
				GROUP BY unique_id
			) AS grouped
		""", values)[0][0]

		# Overall total RFQ count for purchase team (merged from total_rfq_count logic)
		overall_total_rfq = frappe.db.sql("""
			SELECT COUNT(*) FROM (
				SELECT 1
				FROM `tabRequest For Quotation`
				GROUP BY unique_id
			) AS grouped
		""")[0][0]

		data = frappe.db.sql(f"""
			SELECT
				rfq.name,
				IFNULL(rfq.company_name_logistic, rfq.company_name) AS company_name,
				rfq.creation,
				rfq.rfq_type,
				rfq.logistic_type,
				rfq.unique_id,
				IFNULL(rfq.rfq_date_logistic, rfq.quotation_deadline) AS rfq_date,
				IFNULL(rfq.delivery_date, rfq.shipment_date) AS delivery_date,
				rfq.status
			FROM `tabRequest For Quotation` rfq
			INNER JOIN (
				SELECT MAX(name) AS name FROM `tabRequest For Quotation`
				{condition_clause}
				GROUP BY unique_id
			) latest_rfq ON rfq.name = latest_rfq.name
			ORDER BY rfq.creation DESC
			LIMIT %(limit)s OFFSET %(offset)s
		""", {**values, "limit": page_length, "offset": offset}, as_dict=True)

		return {
			"status": "success",
			"message": f"{len(data)} RFQ(s) found",
			"data": data,
			"total_count": total_count or 0,
			"overall_total_rfq": overall_total_rfq,
			"page_no": page_no,
			"page_length": page_length
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Purchase Team RFQ Dashboard Error")
		return {
			"status": "error",
			"message": "Failed to fetch purchase team RFQ dashboard.",
			"error": str(e)
		}


# total count of rfq
# @frappe.whitelist(allow_guest=False)
# def total_rfq_count():
# 	try:
# 		total_rfq = frappe.db.sql("""
# 			SELECT COUNT(*) FROM (
# 				SELECT 1
# 				FROM `tabRequest For Quotation`
# 				GROUP BY unique_id
# 			) AS grouped
# 		""")[0][0]

# 		return {
# 			"status": "success",
# 			"total_rfq": total_rfq
# 		}
# 	except Exception as e:
# 		frappe.log_error(frappe.get_traceback(), "Total RFQ Count Error")
# 		return {
# 			"status": "error",
# 			"message": "Failed to get RFQ count.",
# 			"error": str(e)
# 		}
   
@frappe.whitelist(allow_guest=False)
def total_rfq_count():
	try:
		user = frappe.session.user
		user_email = frappe.db.get_value("User", user, "email")

		roles = frappe.get_roles(user)

		is_vendor = "Vendor" in roles

		if is_vendor:
			total_rfq = frappe.db.sql("""
				SELECT COUNT(*) FROM (
					SELECT DISTINCT parent
					FROM (
						SELECT parent FROM `tabVendor Details`
						WHERE office_email_primary = %(email)s
						UNION
						SELECT parent FROM `tabNon Onboarded Vendor Details`
						WHERE office_email_primary = %(email)s
					) AS combined
					JOIN `tabRequest For Quotation` rfq ON rfq.name = combined.parent
					GROUP BY rfq.unique_id
				) AS grouped
			""", {"email": user_email})[0][0]

		else:
			# For Purchase team or any other internal user
			total_rfq = frappe.db.sql("""
				SELECT COUNT(*) FROM (
					SELECT 1
					FROM `tabRequest For Quotation`
					GROUP BY unique_id
				) AS grouped
			""")[0][0]

		return {
			"status": "success",
			"total_rfq": total_rfq
		}
	
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Total RFQ Count Error")
		return {
			"status": "error",
			"message": "Failed to get RFQ count.",
			"error": str(e)
		}

   


@frappe.whitelist(allow_guest=True)
def check_duplicate_vendor():
    try:
        data = frappe.local.form_dict
        
        if isinstance(data.get('data'), str):
            try:
                data = json.loads(data.get('data'))
            except json.JSONDecodeError:
                data = frappe.local.form_dict
        
        mobile_number = data.get('mobile_number', '').strip()
        email = data.get('email', '').strip().lower()
        
        if not mobile_number and not email:
            return {
                "status": "error",
                "message": "Please provide either mobile number or email to check for duplicates",
                "error_type": "validation"
            }
        
        duplicate_records = []
        duplicate_fields = []
        
        if mobile_number:
            mobile_duplicates = frappe.db.sql("""
                SELECT name, mobile_number,vendor_name, office_email_primary
                FROM `tabVendor Master`
                WHERE mobile_number = %s
            """, (mobile_number,), as_dict=True)
            
            if mobile_duplicates:
                duplicate_records.extend(mobile_duplicates)
                duplicate_fields.append("mobile number")
        
        if email:
            email_duplicates = frappe.db.sql("""
                SELECT name,vendor_name, mobile_number, office_email_primary
                FROM `tabVendor Master`
                WHERE LOWER(office_email_primary) = %s
            """, (email,), as_dict=True)
            
            if email_duplicates:
                for email_dup in email_duplicates:
                    if not any(rec['name'] == email_dup['name'] for rec in duplicate_records):
                        duplicate_records.append(email_dup)
                duplicate_fields.append("email")
        
        duplicate_fields = list(set(duplicate_fields))
        
        if duplicate_records:
            formatted_records = []
            for record in duplicate_records:
                formatted_records.append({
                    "vendor_id": record.get('name'),
                    "vendor_name": record.get('vendor_name'),
                    "mobile_number": record.get('mobile_number'),
                    "email": record.get('office_email_primary')
                })
            
            return {
                "status": "duplicate_found",
                "message": f"Duplicate entry found! There is already a vendor with this {' and '.join(duplicate_fields)}",
                # "duplicate_count": len(duplicate_records),
                "existing_vendors": formatted_records
            }
        else:
            return {
                "status": "no_duplicate",
                "message": "No duplicate entry found. No vendor exists with this mobile number or email",
                "duplicate_count": 0
            }
    
    except Exception as e:
        frappe.log_error(f"Vendor Duplicate Check API Error: {str(e)}", "vendor_duplicate_check_error")
        return {
            "status": "error",
            "message": f"An error occurred while checking for duplicates: {str(e)}",
            "error_type": "general"
        }


@frappe.whitelist(allow_guest=True)
def get_countries_with_ports():
    query = """
        SELECT 
            c.name as country,
            pm.port_code,
            pm.port_name
        FROM 
            `tabCountry Master` c
        INNER JOIN 
            `tabPort Master` pm ON c.name = pm.country
        ORDER BY 
            c.name, pm.port_name
    """
    
    result = frappe.db.sql(query, as_dict=True)
    return result



@frappe.whitelist(allow_guest=True)
def get_ports_by_mode_of_shipment_simple(mode_of_shipment):
    
    if not mode_of_shipment:
        return []
    
    try:
        query = """
            SELECT 
                pm.port_name
            FROM 
                `tabPort Master` pm
            WHERE 
                pm.mode_of_shipment = %(mode_of_shipment)s
            ORDER BY 
                pm.port_name
        """
        
        result = frappe.db.sql(query, {"mode_of_shipment": mode_of_shipment}, as_dict=True)
        
        return [port['port_name'] for port in result]
        
    except Exception as e:
        frappe.log_error(f"Error in get_ports_by_mode_of_shipment_simple: {str(e)}")
        return []

