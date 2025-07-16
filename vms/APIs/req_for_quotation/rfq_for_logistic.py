import frappe
import json
from frappe import _

@frappe.whitelist(allow_guest=False)
def vendor_list(rfq_type=None, vendor_name=None, page_no=1, page_length=10):
	if not rfq_type:
		frappe.throw(_("Missing required parameter: rfq_type"))

	try:
		vendor_links = frappe.get_all(
			"Vendor Type Group",
			filters={
				"vendor_type": rfq_type,
				"parenttype": "Vendor Master"
			},
			pluck="parent"
		)

		conditions = {"name": ["in", list(set(vendor_links))]}
		if vendor_name:
			conditions["vendor_name"] = ["like", f"%{vendor_name}%"]

		page_no = int(page_no) if page_no else 1
		page_length = int(page_length) if page_length else 10
		offset = (page_no - 1) * page_length

		vendor_masters = frappe.get_all(
			"Vendor Master",
			filters=conditions,
			fields=["name", "vendor_name", "office_email_primary", "mobile_number", "country"],
			start=offset,
			page_length=page_length
		)

		total_count = frappe.db.count("Vendor Master", filters=conditions)

		output = []
		for vm in vendor_masters:
			vendor_code = []
			company_vendor_code = frappe.get_all(
				"Company Vendor Code",
				filters={"vendor_ref_no": vm.name},
				fields=["name"]
			)
			for row in company_vendor_code:
				doc = frappe.get_doc("Company Vendor Code", row.name)
				for code_row in doc.vendor_code:
					vendor_code.append(code_row.vendor_code)

			output.append({
				"refno": vm.name,
				"vendor_name": vm.vendor_name,
				"office_email_primary": vm.office_email_primary,
				"mobile_number": vm.mobile_number,
				"country": vm.country,
				"vendor_code": vendor_code
			})

		return {
			"status": "success",
			"message": f"{len(output)} vendor(s) found",
			"data": output,
			"total_count": total_count,
			"page_no": page_no,
			"page_length": page_length
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Vendor List Error")
		frappe.throw(_("Error fetching vendor list: ") + str(e))



# create logistic import rfq data -----------------------------------------------------------------------------------------------

@frappe.whitelist(allow_guest=False)
def create_import_logistic_rfq(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		rfq = frappe.new_doc(
		    "Request For Quotation"	
		)

		rfq.rfq_type                = data.get("rfq_type")
		rfq.company_name_logistic   = data.get("company_name_logistic")
		rfq.sr_no                   = data.get("sr_no")
		rfq.rfq_cutoff_date_logistic = data.get("rfq_cutoff_date_logistic")
		rfq.rfq_date_logistic       = data.get("rfq_date_logistic")
		rfq.mode_of_shipment        = data.get("mode_of_shipment")
		rfq.destination_port        = data.get("destination_port")
		rfq.country                 = data.get("country")
		rfq.port_code               = data.get("port_code")
		rfq.port_of_loading         = data.get("port_of_loading")
		rfq.inco_terms              = data.get("inco_terms")
		rfq.shipper_name            = data.get("shipper_name")
		rfq.ship_to_address         = data.get("ship_to_address")
		rfq.package_type            = data.get("package_type")
		rfq.no_of_pkg_units         = data.get("no_of_pkg_units")
		rfq.product_category        = data.get("product_category")
		rfq.vol_weight              = data.get("vol_weight")
		rfq.actual_weight           = data.get("actual_weight")
		rfq.invoice_date            = data.get("invoice_date")
		rfq.invoice_no              = data.get("invoice_no")
		rfq.invoice_value           = data.get("invoice_value")
		rfq.expected_date_of_arrival  = data.get("expected_date_of_arrival")
		rfq.remarks                 = data.get("remarks")

        # Vendor Details Table
		vendors = data.get("vendors", [])
		for vendor in vendors:
			rfq.append("vendor_details", {
				"ref_no": vendor.get("refno"),
				"vendor_name": vendor.get("vendor_name"),
				"vendor_code": ", ".join(vendor.get("vendor_code", [])),
				"office_email_primary": vendor.get("office_email_primary"),
				"mobile_number": vendor.get("mobile_number"),
				"country": vendor.get("country")
			})
			
        # Non Onboarded Vendor Details Table
		vendors = data.get("non_onboarded_vendors", [])
		for vendor in vendors:
			rfq.append("non_onboarded_vendor_details", {
				"office_email_primary": vendor.get("office_email_primary"),
				"vendor_name": vendor.get("vendor_name"),
				"mobile_number": vendor.get("mobile_number"),
				"country": vendor.get("country")
			})

		rfq.insert(ignore_permissions=True)
		frappe.db.commit()  

		return {
			"status": "success",
			"message": "RFQ created successfully",
			"rfq_name": rfq.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create RFQ API Error")
		frappe.throw(_("Error creating RFQ: ") + str(e))
            

# get full data of logistic import rfq
@frappe.whitelist(allow_guest=False)
def get_full_data_import_logistic_rfq(name):
	try:
		doc = frappe.get_doc("Request For Quotation", name)

		vendor_details_data = []
		for row in doc.vendor_details:
			vendor_details_data.append({
				"refno": row.ref_no,
				"vendor_name": row.vendor_name,
        		"vendor_code": [v.strip() for v in row.vendor_code.split(",")] if row.vendor_code else [],
				"office_email_primary": row.office_email_primary,
				"mobile_number": row.mobile_number,
				"country": row.country
			})

		non_onboarded_vendor_details_data = []
		for row in doc.non_onboarded_vendor_details:
			non_onboarded_vendor_details_data.append({
				"office_email_primary": row.office_email_primary,
				"vendor_name": row.vendor_name,
				"mobile_number": row.mobile_number,
				"country": row.country
			})

		data = {
			"rfq_type": doc.rfq_type,
			"company_name_logistic": doc.company_name_logistic,
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
			"vendor_details": vendor_details_data,
			"non_onboarded_vendor_details": non_onboarded_vendor_details_data
		}

		return {
			"status": "success",
			"rfq_name": name,
			"data": data
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Fetch Import Logistic RFQ Error")
		frappe.throw(_("Error fetching RFQ: ") + str(e))



 # create logistic export rfq data  -----------------------------------------------------------------------------------------------

@frappe.whitelist(allow_guest=False)
def create_export_logistic_rfq(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		rfq = frappe.new_doc(
		    "Request For Quotation"	
		)

		rfq.rfq_type                = data.get("rfq_type")
		rfq.company_name_logistic   = data.get("company_name_logistic")
		rfq.sr_no                   = data.get("sr_no")
		rfq.rfq_cutoff_date_logistic = data.get("rfq_cutoff_date_logistic")
		rfq.rfq_date_logistic       = data.get("rfq_date_logistic")
		rfq.mode_of_shipment        = data.get("mode_of_shipment")
		rfq.destination_port        = data.get("destination_port")
		rfq.country                 = data.get("country")
		rfq.port_code               = data.get("port_code")
		rfq.port_of_loading         = data.get("port_of_loading")
		rfq.inco_terms            = data.get("inco_terms")
		rfq.ship_to_address      = data.get("ship_to_address")
		rfq.package_type       = data.get("package_type")
		rfq.no_of_pkg_units        = data.get("no_of_pkg_units")
		rfq.product_category        = data.get("product_category")
		rfq.vol_weight        = data.get("vol_weight")
		rfq.actual_weight        = data.get("actual_weight")
		rfq.invoice_date        = data.get("invoice_date")
		rfq.invoice_no        = data.get("invoice_no")
		rfq.consignee_name        = data.get("consignee_name")
		rfq.shipment_date        = data.get("shipment_date")
		rfq.remarks        = data.get("remarks")

        # Vendor Details Table
		vendors = data.get("vendors", [])
		for vendor in vendors:
			rfq.append("vendor_details", {
				"ref_no": vendor.get("refno"),
				"vendor_name": vendor.get("vendor_name"),
				"vendor_code": ", ".join(vendor.get("vendor_code", [])),
				"office_email_primary": vendor.get("office_email_primary"),
				"mobile_number": vendor.get("mobile_number"),
				"country": vendor.get("country")
			})
			
        # Non Onboarded Vendor Details Table
		vendors = data.get("non_onboarded_vendors", [])
		for vendor in vendors:
			rfq.append("non_onboarded_vendor_details", {
				"office_email_primary": vendor.get("office_email_primary"),
				"vendor_name": vendor.get("vendor_name"),
				"mobile_number": vendor.get("mobile_number"),
				"country": vendor.get("country")
			})

		rfq.insert(ignore_permissions=True)
		frappe.db.commit()  

		return {
			"status": "success",
			"message": "RFQ created successfully",
			"rfq_name": rfq.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create RFQ API Error")
		frappe.throw(_("Error creating RFQ: ") + str(e))

                   
# get full data of logistic export rfq

@frappe.whitelist(allow_guest=False)
def get_full_data_export_logistic_rfq(name):
	try:
		doc = frappe.get_doc("Request For Quotation", name)

		vendor_details_data = []
		for row in doc.vendor_details:
			vendor_details_data.append({
				"refno": row.ref_no,
				"vendor_name": row.vendor_name,
        		"vendor_code": [v.strip() for v in row.vendor_code.split(",")] if row.vendor_code else [],
				"office_email_primary": row.office_email_primary,
				"mobile_number": row.mobile_number,
				"country": row.country
			})

		non_onboarded_vendor_details_data = []
		for row in doc.non_onboarded_vendor_details:
			non_onboarded_vendor_details_data.append({
				"office_email_primary": row.office_email_primary,
				"vendor_name": row.vendor_name,
				"mobile_number": row.mobile_number,
				"country": row.country
			})

		data = {
			"rfq_type": doc.rfq_type,
			"company_name_logistic": doc.company_name_logistic,
			"sr_no": doc.sr_no,
			"rfq_cutoff_date_logistic": doc.rfq_cutoff_date_logistic,
			"rfq_date_logistic": doc.rfq_date_logistic,
			"mode_of_shipment": doc.mode_of_shipment,
			"destination_port": doc.destination_port,
			"country": doc.country,
			"port_code": doc.port_code,
			"port_of_loading": doc.port_of_loading,
			"inco_terms": doc.inco_terms,
			"ship_to_address": doc.ship_to_address,
			"package_type": doc.package_type,
			"no_of_pkg_units": doc.no_of_pkg_units,
			"product_category": doc.product_category,
			"vol_weight": doc.vol_weight,
			"actual_weight": doc.actual_weight,
			"invoice_date": doc.invoice_date,
			"invoice_no": doc.invoice_no,
			"consignee_name": doc.consignee_name,
			"shipment_date": doc.shipment_date,
			"remarks": doc.remarks,
			"vendor_details": vendor_details_data,
			"non_onboarded_vendor_details": non_onboarded_vendor_details_data
		}

		return {
			"status": "success",
			"rfq_name": name,
			"data": data
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Fetch Export Logistic RFQ Error")
		frappe.throw(_("Error fetching RFQ: ") + str(e))


# dashboard for rfq logistic
# take care for vendor login also now it is not hanled in the function
@frappe.whitelist(allow_guest=False)
def rfq_logistic_dashboard(company_name_logistic=None, name=None, page_no=1, page_length=5):
	try:
		conditions = {}
		if company_name_logistic:
			conditions["company_name_logistic"] = ["like", f"%{company_name_logistic}%"]
		if name:
			conditions["name"] = ["like", f"%{name}%"]

		page_no = int(page_no) if page_no else 1
		page_length = int(page_length) if page_length else 5
		offset = (page_no - 1) * page_length

		rfq_list = frappe.get_all(
			"Request For Quotation",
			filters=conditions,
			fields=["name", "company_name_logistic", "rfq_type", "rfq_date_logistic", "status"],
			start=offset,
			page_length=page_length,
			order_by="modified desc"
		)

		total_count = frappe.db.count("Request For Quotation", filters=conditions)

		return {
			"status": "success",
			"message": f"{len(rfq_list)} RFQ(s) found",
			"data": rfq_list,
			"total_count": total_count,
			"page_no": page_no,
			"page_length": page_length
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "RFQ Dashboard Error")
		frappe.throw(_("Error fetching RFQ list: ") + str(e))

