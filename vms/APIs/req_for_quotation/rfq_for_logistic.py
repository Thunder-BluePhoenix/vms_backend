import frappe
import json
from frappe import _
from datetime import datetime


# filter storage location
@frappe.whitelist(allow_guest=True)
def filter_storage_locatioon(company):
    try:
        if not company:
            return {
                "status": "error",
                "message": "Company is required"
            }

        storage = frappe.get_all(
            "Storage Location Master",
            filters={"company": company},
            fields=["storage_name", "storage_location_name", "description"]
        )

        return {
            "status": "success",
            "storage": storage
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering storage location")
        return {
            "status": "error",
            "message": "Failed to filter storage location.",
            "error": str(e)
        }

# @frappe.whitelist(allow_guest=False)
# def vendor_list(rfq_type=None, vendor_name=None, service_provider=None, page_no=1, page_length=10):
# 	if not rfq_type:
# 		frappe.throw(_("Missing required parameter: rfq_type"))

# 	try:
# 		# Return empty result if the service provider is All Service Provider, Premium Service Provider
# 		if service_provider in ["All Service Provider", "Premium Service Provider"]:
# 			return {
# 				"status": "success",
# 				"message": "No vendors returned for this service provider.",
# 				"data": [],
# 				"total_count": 0,
# 				"page_no": page_no,
# 				"page_length": page_length
# 			}

# 		vendor_links = frappe.get_all(
# 			"Vendor Type Group",
# 			filters={
# 				"vendor_type": rfq_type,
# 				"parenttype": "Vendor Master"
# 			},
# 			pluck="parent"
# 		)

# 		conditions = {"name": ["in", list(set(vendor_links))]}

# 		if service_provider=="Courier Service Provider":
# 			conditions["service_provider_type"] = "Courier Partner"

# 		if service_provider == "Adhoc Service Provider":
# 			conditions["service_provider_type"] = ["in", ["Courier Partner", "Premium Service Provider", "Service Provider"]]

# 		if vendor_name:
# 			conditions["vendor_name"] = ["like", f"%{vendor_name}%"]

# 		page_no = int(page_no) if page_no else 1
# 		page_length = int(page_length) if page_length else 10
# 		offset = (page_no - 1) * page_length

# 		vendor_masters = frappe.get_all(
# 			"Vendor Master",
# 			filters=conditions,
# 			fields=["name", "vendor_name", "office_email_primary", "mobile_number", "country", "service_provider_type"],
# 			start=offset,
# 			page_length=page_length
# 		)

# 		total_count = frappe.db.count("Vendor Master", filters=conditions)

# 		output = []
# 		for vm in vendor_masters:
# 			vendor_code = []
# 			company_vendor_code = frappe.get_all(
# 				"Company Vendor Code",
# 				filters={"vendor_ref_no": vm.name},
# 				fields=["name"]
# 			)
# 			for row in company_vendor_code:
# 				doc = frappe.get_doc("Company Vendor Code", row.name)
# 				for code_row in doc.vendor_code:
# 					vendor_code.append(code_row.vendor_code)

# 			output.append({
# 				"refno": vm.name,
# 				"vendor_name": vm.vendor_name,
# 				"office_email_primary": vm.office_email_primary,
# 				"mobile_number": vm.mobile_number,
# 				"country": vm.country,
# 				"vendor_code": vendor_code,
# 				"service_provider_type": vm.service_provider_type
# 			})

# 		return {
# 			"status": "success",
# 			"message": f"{len(output)} vendor(s) found",
# 			"data": output,
# 			"total_count": total_count,
# 			"page_no": page_no,
# 			"page_length": page_length
# 		}

# 	except Exception as e:
# 		frappe.log_error(frappe.get_traceback(), "Vendor List Error")
# 		frappe.throw(_("Error fetching vendor list: ") + str(e))


# vendor list acc to company wise
@frappe.whitelist(allow_guest=False)
def vendor_list(rfq_type=None, vendor_name=None, service_provider=None, page_no=1, page_length=10, company=None):
    if not rfq_type:
        frappe.throw(_("Missing required parameter: rfq_type"))
    if not company:
        frappe.throw(_("Missing required parameter: company"))
    try:
        # Return empty result if the service provider is All Service Provider, Premium Service Provider
        if service_provider in ["All Service Provider", "Premium Service Provider"]:
            return {
                "status": "success",
                "message": "No vendors returned for this service provider.",
                "data": [],
                "total_count": 0,
                "page_no": page_no,
                "page_length": page_length
            }
        # Get all vendor linked to this company
        company_vendor_links = frappe.get_all(
            "Company Vendor Code",
            filters={"company_name": company},
            pluck="vendor_ref_no"
        )
        if not company_vendor_links:
            return {
                "status": "success",
                "message": "No vendors found for the given company.",
                "data": [],
                "total_count": 0,
                "page_no": page_no,
                "page_length": page_length
            }
        vendor_links = frappe.get_all(
            "Vendor Type Group",
            filters={
                "vendor_type": rfq_type,
                "parenttype": "Vendor Master",
                "parent": ["in", company_vendor_links]
            },
            pluck="parent"
        )
        conditions = {"name": ["in", list(set(vendor_links))]}
        if service_provider=="Courier Service Provider":
            conditions["service_provider_type"] = "Courier Partner"
        if service_provider == "Adhoc Service Provider":
            conditions["service_provider_type"] = ["in", ["Courier Partner", "Premium Service Provider", "Service Provider"]]
        if vendor_name:
            conditions["vendor_name"] = ["like", f"%{vendor_name}%"]
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 10
        offset = (page_no - 1) * page_length
        vendor_masters = frappe.get_all(
            "Vendor Master",
            filters=conditions,
            fields=["name", "vendor_name", "office_email_primary", "mobile_number", "country", "service_provider_type"],
            start=offset,
            page_length=page_length
        )
        total_count = frappe.db.count("Vendor Master", filters=conditions)
        output = []
        for vm in vendor_masters:
            vendor_code = []
            company_vendor_code_list = frappe.get_all(
                "Company Vendor Code",
                filters={"vendor_ref_no": vm.name},
                fields=["name"]
            )
            for row in company_vendor_code_list:
                doc = frappe.get_doc("Company Vendor Code", row.name)
                for code_row in doc.vendor_code:
                    vendor_code.append(code_row.vendor_code)
            output.append({
                "refno": vm.name,
                "vendor_name": vm.vendor_name,
                "office_email_primary": vm.office_email_primary,
                "mobile_number": vm.mobile_number,
                "country": vm.country,
                "vendor_code": vendor_code,
                "service_provider_type": vm.service_provider_type
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

		rfq = frappe.new_doc("Request For Quotation")

		# Generate unique_id
		now = datetime.now()
		year_month_prefix = f"RFQ{now.strftime('%y')}{now.strftime('%m')}"
		existing_max = frappe.db.sql(
			"""
			SELECT MAX(CAST(SUBSTRING(unique_id, 8) AS UNSIGNED))
			FROM `tabRequest For Quotation`
			WHERE unique_id LIKE %s
			""",
			(year_month_prefix + "%",),
			as_list=True
		)
		max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
		new_count = max_count + 1
		unique_id = f"{year_month_prefix}{str(new_count).zfill(5)}"

		# Set fields
		rfq.head_target = 1
		rfq.unique_id = unique_id
		rfq.form_fully_submitted = 1
		rfq.status = "Pending"
		rfq.rfq_type = data.get("rfq_type")
		rfq.raised_by = frappe.local.session.user
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

		rfq.insert(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Import Logistic RFQ created successfully",
			"rfq_name": rfq.name,
			"unique_id": rfq.unique_id
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "create_import_logistic_rfq Error")
		frappe.throw("Failed to create Import Logistic RFQ")

            
 # create logistic export rfq data  -----------------------------------------------------------------------------------------------

@frappe.whitelist(allow_guest=False)
def create_export_logistic_rfq(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		rfq = frappe.new_doc(
		    "Request For Quotation"	
		)

		# Generate unique_id
		now = datetime.now()
		year_month_prefix = f"RFQ{now.strftime('%y')}{now.strftime('%m')}"
		existing_max = frappe.db.sql(
			"""
			SELECT MAX(CAST(SUBSTRING(unique_id, 8) AS UNSIGNED))
			FROM `tabRequest For Quotation`
			WHERE unique_id LIKE %s
			""",
			(year_month_prefix + "%",),
			as_list=True
		)
		max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
		new_count = max_count + 1
		unique_id = f"{year_month_prefix}{str(new_count).zfill(5)}"

		# Set fields
		rfq.head_target             = 1
		rfq.unique_id               = unique_id
		rfq.form_fully_submitted    = 1
		rfq.status                  = "Pending"
		rfq.rfq_type                = data.get("rfq_type")
		rfq.raised_by               = frappe.local.session.user
		rfq.logistic_type           = data.get("logistic_type")
		rfq.company_name_logistic   = data.get("company_name_logistic")
		rfq.service_provider        = data.get("service_provider")
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

		# Add all vendors if "All Service Provider" is selected
		if data.get("service_provider") == "All Service Provider":
			vendors = frappe.get_all(
				"Vendor Master",
				filters={"service_provider_type": ["in", ["Service Provider", "Premium Service Provider"]]},
				fields=["name", "vendor_name", "office_email_primary", "mobile_number", "country"]
			)
			for vm in vendors:
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

				rfq.append("vendor_details", {
					"ref_no": vm.name,
					"vendor_name": vm.vendor_name,
					"office_email_primary": vm.office_email_primary,
					"vendor_code": ", ".join(vendor_code),
					"mobile_number": vm.mobile_number,
					"service_provider_type": vm.service_provider_type,
					"country": vm.country
				})

		# Add all vendors if "Premium Service Provider" is selected	
		if data.get("service_provider") == "Premium Service Provider":
			vendors = frappe.get_all(
				"Vendor Master",
				filters={"service_provider_type": ["in", ["Premium Service Provider"]]},
				fields=["name", "vendor_name", "office_email_primary", "mobile_number", "country"]
			)
			for vm in vendors:
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

				rfq.append("vendor_details", {
					"ref_no": vm.name,
					"vendor_name": vm.vendor_name,
					"office_email_primary": vm.office_email_primary,
					"vendor_code": ", ".join(vendor_code),
					"mobile_number": vm.mobile_number,
					"service_provider_type": vm.service_provider_type,
					"country": vm.country
				})

        # Vendor Details Table
		vendors = data.get("vendors", [])
		for vendor in vendors:
			rfq.append("vendor_details", {
				"ref_no": vendor.get("refno"),
				"vendor_name": vendor.get("vendor_name"),
				"vendor_code": ", ".join(vendor.get("vendor_code", [])),
				"office_email_primary": vendor.get("office_email_primary"),
				"mobile_number": vendor.get("mobile_number"),
				"service_provider_type": vendor.get("service_provider_type"),
				"country": vendor.get("country")
			})
			
        # Non Onboarded Vendor Details Table
		vendors = data.get("non_onboarded_vendors", [])
		for vendor in vendors:
			rfq.append("non_onboarded_vendor_details", {
				"office_email_primary": vendor.get("office_email_primary"),
				"vendor_name": vendor.get("vendor_name"),
				"mobile_number": vendor.get("mobile_number"),
				"country": vendor.get("country"),
				"company_pan": vendor.get("company_pan"),
				"gst_number": vendor.get("gst_number")
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

                   



		
