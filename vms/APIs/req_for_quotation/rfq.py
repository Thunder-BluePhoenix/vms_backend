import frappe
import json
from frappe.utils import now_datetime
from datetime import datetime

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
			"name": doc.name,
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
			"unique_id": doc.unique_id,

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


# send revised rfq

@frappe.whitelist(allow_guest=False)
def send_revised_rfq(data):
	if isinstance(data, str):
		data = json.loads(data)

	if not data.get("name"):
		frappe.throw("Missing RFQ name")

	old_rfq = frappe.get_doc("Request For Quotation", data.get("name"))

	# Mark old RFQ as revised
	frappe.db.set_value("Request For Quotation", old_rfq.name, "revised_quotation", 1)

	# Create new RFQ based on old
	new_rfq = frappe.new_doc("Request For Quotation")
	old_rfq_data = old_rfq.as_dict()
	for unwanted in ["name", "creation", "modified", "owner", "head_target", "revised_rfq"]:
		old_rfq_data.pop(unwanted, None)

	new_rfq.update(old_rfq_data)

	new_rfq.name = None
	new_rfq.prev_rfq = old_rfq.name
	new_rfq.status = "Pending"

	# Excluded fields from comparison
	excluded_fields = ["head_target", "revised_rfq"]

	# Fields to consider for comparison and update
	main_fields = [
		"status", "company_name_logistic", "rfq_cutoff_date_logistic", "mode_of_shipment",
		"destination_port", "port_of_loading", "ship_to_address", "no_of_pkg_units", "vol_weight",
		"invoice_date", "shipment_date", "remarks", "expected_date_of_arrival", "service_provider",
		"consignee_name", "sr_no", "rfq_date_logistic", "country", "port_code", "inco_terms",
		"package_type", "product_category", "actual_weight", "invoice_no", "invoice_value",
		"shipment_type", "material", "quantity", "shipper_name", "rfq_date", "rfq_cutoff_date",
		"company_name", "purchase_organization", "purchase_group", "currency", "collection_number",
		"quotation_deadline", "validity_start_date", "validity_end_date", "requestor_name",
		"bidding_person", "material_code", "material_category", "plant_code", "storage_location",
		"short_text", "catalogue_number", "service_code", "service_location", "service_category",
		"quantity_and_date_section", "rfq_quantity", "quantity_unit", "delivery_date",
		"add_expected_budgetary_target_price_section", "estimated_price", "first_reminder",
		"second_reminder", "third_reminder"
	]

	for field in main_fields:
		if field in excluded_fields:
			continue
		if field in data and data.get(field) != old_rfq.get(field):
			new_rfq.set(field, data.get(field))
		else:
			new_rfq.set(field, old_rfq.get(field)) 


	# Step 1: Create map of old rows by name
	old_child_rows = {row.name: row for row in old_rfq.get("rfq_items", [])}

	# Step 2: Collect updated row IDs
	updated_data = data.get("rfq_items", [])
	updated_row_ids = set(row.get("row_id") for row in updated_data if row.get("row_id"))

	# Step 3: Start new item list
	new_items = []

	# Step 4: Process updated rows
	for row in updated_data:
		row_id = row.get("row_id")
		old_child = old_child_rows.get(row_id)

		if old_child:
			for key, value in row.items():
				if key != "row_id" and value != old_child.get(key):
					old_child.set(key, value)
			new_items.append(old_child)

	# Step 5: Add untouched rows
	for name, old_row in old_child_rows.items():
		if name not in updated_row_ids:
			new_items.append(old_row)

	# Step 6: Set child table in new RFQ
	new_rfq.set("rfq_items", new_items)

	# --- END CHILD TABLE LOGIC ---

	# Save new RFQ
	new_rfq.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": "success",
		"message": "Revised RFQ created successfully",
		"new_rfq": new_rfq.name
	}


# dashboard for rfq logistic

@frappe.whitelist(allow_guest=False)
def rfq_dashboard(company_name=None, name=None, page_no=1, page_length=5, rfq_type=None, status=None):
	try:
		page_no = int(page_no) if page_no else 1
		page_length = int(page_length) if page_length else 5
		offset = (page_no - 1) * page_length

		# Build dynamic filters
		conditions = []
		values = {}

		if company_name:
			conditions.append("(company_name = %(company_name)s OR company_name_logistic = %(company_name)s)")
			values["company_name"] = company_name

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
                SELECT 1
                FROM `tabRequest For Quotation`
                {condition_clause}
                GROUP BY unique_id
            ) AS grouped
        """, values)[0][0]

		# Paginated result
		data = frappe.db.sql(f"""
            SELECT
                rfq.name,
                IFNULL(rfq.company_name_logistic, rfq.company_name) AS company_name,
                rfq.rfq_type,
                IFNULL(rfq.rfq_date_logistic, rfq.rfq_date) AS rfq_date,
                IFNULL(rfq.delivery_date, rfq.shipment_date) AS delivery_date,
                rfq.status
            FROM `tabRequest For Quotation` rfq
            INNER JOIN (
                SELECT MAX(name) AS name
                FROM `tabRequest For Quotation`
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
			"total_count": total_count,
			"page_no": page_no,
			"page_length": page_length
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "RFQ Dashboard Error")
		return {
			"status": "error",
			"message": "Failed to fetch RFQ dashboard data.",
			"error": str(e)
		}


# total count of rfq
@frappe.whitelist(allow_guest=False)
def total_rfq_count():
	try:
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
