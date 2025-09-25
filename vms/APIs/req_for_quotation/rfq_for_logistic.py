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

# @frappe.whitelist(allow_guest=False)
# def vendor_list(rfq_type=None, vendor_name=None, service_provider=None, page_no=1, page_length=10, company=None):
#     if not rfq_type:
#         frappe.throw(_("Missing required parameter: rfq_type"))

#     if not company:
#         frappe.throw(_("Missing required parameter: company"))

#     try:
#         # Return empty result if the service provider is All Service Provider, Premium Service Provider
#         if service_provider in ["All Service Provider", "Premium Service Provider"]:
#             return {
#                 "status": "success",
#                 "message": "No vendors returned for this service provider.",
#                 "data": [],
#                 "total_count": 0,
#                 "page_no": page_no,
#                 "page_length": page_length
#             }
		
#         # Get all vendor linked to this company
#         company_vendor_links = frappe.get_all(
#             "Company Vendor Code",
#             filters={"company_name": company},
#             pluck="vendor_ref_no"
#         )

#         if not company_vendor_links:
#             return {
#                 "status": "success",
#                 "message": "No vendors found for the given company.",
#                 "data": [],
#                 "total_count": 0,
#                 "page_no": page_no,
#                 "page_length": page_length
#             }
		
#         vendor_links = frappe.get_all(
#             "Vendor Type Group",
#             filters={
#                 "vendor_type": rfq_type,
#                 "parenttype": "Vendor Master",
#                 "parent": ["in", company_vendor_links]
#             },
#             pluck="parent"
#         )

#         conditions = {"name": ["in", list(set(vendor_links))]}

#         if service_provider=="Courier Service Provider":
#             conditions["service_provider_type"] = "Courier Partner"
#         if service_provider == "Adhoc Service Provider":
#             conditions["service_provider_type"] = ["in", ["Courier Partner", "Premium Service Provider", "Service Provider"]]
#         if vendor_name:
#             conditions["vendor_name"] = ["like", f"%{vendor_name}%"]

#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 10
#         offset = (page_no - 1) * page_length

#         vendor_masters = frappe.get_all(
#             "Vendor Master",
#             filters=conditions,
#             fields=["name", "vendor_name", "office_email_primary", "mobile_number", "country", "service_provider_type"],
#             start=offset,
#             page_length=page_length
#         )
#         total_count = frappe.db.count("Vendor Master", filters=conditions)
#         output = []

#         for vm in vendor_masters:
#             vendor_code = []
#             company_vendor_code_list = frappe.get_all(
#                 "Company Vendor Code",
#                 filters={"vendor_ref_no": vm.name},
#                 fields=["name"]
#             )
#             for row in company_vendor_code_list:
#                 doc = frappe.get_doc("Company Vendor Code", row.name)
#                 for code_row in doc.vendor_code:
#                     vendor_code.append(code_row.vendor_code)

#             output.append({
#                 "refno": vm.name,
#                 "vendor_name": vm.vendor_name,
#                 "office_email_primary": vm.office_email_primary,
#                 "mobile_number": vm.mobile_number,
#                 "country": vm.country,
#                 "vendor_code": vendor_code,
#                 "service_provider_type": vm.service_provider_type
#             })

#         return {
#             "status": "success",
#             "message": f"{len(output)} vendor(s) found",
#             "data": output,
#             "total_count": total_count,
#             "page_no": page_no,
#             "page_length": page_length
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Vendor List Error")
#         frappe.throw(_("Error fetching vendor list: ") + str(e))

@frappe.whitelist(allow_guest=False)
def vendor_list(rfq_type=None, vendor_name=None, service_provider=None, page_no=1, page_length=10, company=None):
    if not rfq_type:
        frappe.throw(_("Missing required parameter: rfq_type"))

    if not company:
        frappe.throw(_("Missing required parameter: company"))

    if not service_provider:
        frappe.throw(_("Missing required parameter: service_provider"))

    try:
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

        if service_provider == "All Service Provider":
            conditions["service_provider_type"] = ["in", ["Premium Service Provider", "Service Provider"]]
        if service_provider == "Premium Service Provider":
            conditions["service_provider_type"] = ["in", ["Premium Service Provider"]]
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
			
		# data = frappe.form_dict

		# child_tables = ['rfq_items', 'vendor_details', 'non_onboarded_vendors','vendors']  
		# for table_name in child_tables:
		# 	if table_name in data and isinstance(data[table_name], str):
		# 		try:
		# 			data[table_name] = json.loads(data[table_name])
		# 		except (json.JSONDecodeError, ValueError):
		# 			data[table_name] = []

		files = []

		# Handle request files
		if hasattr(frappe, 'request') and hasattr(frappe.request, 'files'):
			request_files = frappe.request.files
			if 'file' in request_files:
				file_list = request_files.getlist('file')
				files.extend(file_list)

		# Handle frappe.local uploaded files
		if hasattr(frappe.local, 'uploaded_files') and frappe.local.uploaded_files:
			uploaded_files = frappe.local.uploaded_files
			if isinstance(uploaded_files, list):
				files.extend(uploaded_files)
			else:
				files.append(uploaded_files)

		# Handle file data from form_dict
		if 'file' in data:
			file_data = data.get('file')
			if hasattr(file_data, 'filename'):
				files.append(file_data)
			elif isinstance(file_data, list):
				files.extend([f for f in file_data if hasattr(f, 'filename')])

		# Create RFQ doc
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
		rfq.unique_srno = data.get("sr_no")

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

		if files:
			handle_rfq_files(rfq, files)
			rfq.save(ignore_permissions=True)
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
		# data = frappe.form_dict

		# child_tables = ['rfq_items', 'vendor_details', 'non_onboarded_vendors','vendors']  
		# for table_name in child_tables:
		# 	if table_name in data and isinstance(data[table_name], str):
		# 		try:
		# 			data[table_name] = json.loads(data[table_name])
		# 		except (json.JSONDecodeError, ValueError):
		# 			data[table_name] = []

		files = []

		# Handle request files
		if hasattr(frappe, 'request') and hasattr(frappe.request, 'files'):
			request_files = frappe.request.files
			if 'file' in request_files:
				file_list = request_files.getlist('file')
				files.extend(file_list)

		# Handle frappe.local uploaded files
		if hasattr(frappe.local, 'uploaded_files') and frappe.local.uploaded_files:
			uploaded_files = frappe.local.uploaded_files
			if isinstance(uploaded_files, list):
				files.extend(uploaded_files)
			else:
				files.append(uploaded_files)

		# Handle file data from form_dict
		if 'file' in data:
			file_data = data.get('file')
			if hasattr(file_data, 'filename'):
				files.append(file_data)
			elif isinstance(file_data, list):
				files.extend([f for f in file_data if hasattr(f, 'filename')])

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

		rfq.destination_port        = data.get("port_code")

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
		rfq.unique_srno = data.get("sr_no")

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

		if files:
			handle_rfq_files(rfq, files)
			rfq.save(ignore_permissions=True)
			frappe.db.commit()

		return {
			"status": "success",
			"message": "RFQ created successfully",
			"rfq_name": rfq.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create RFQ API Error")
		frappe.throw(_("Error creating RFQ: ") + str(e))

                   

def handle_rfq_files(rfq, files):
    
    if not files:
        frappe.log_error("No files to process", "file_debug")
        return
    
    frappe.log_error(f"Processing {len(files)} files", "file_debug")
    
    
    if rfq.get('multiple_attachments'):
        rfq.set('multiple_attachments', [])
    
    for i, file_obj in enumerate(files):
        try:
            frappe.log_error(f"Processing file {i}: {type(file_obj)}", "file_debug")
            
            file_name = None
            file_content = None
            
          
            if hasattr(file_obj, 'filename') and hasattr(file_obj, 'stream'):
                file_name = file_obj.filename
                file_obj.stream.seek(0)  
                file_content = file_obj.stream.read()
                frappe.log_error(f"FileStorage: {file_name}, size: {len(file_content) if file_content else 0}", "file_debug")
                
           
            elif hasattr(file_obj, 'filename') and hasattr(file_obj, 'read'):
                file_name = file_obj.filename
                file_content = file_obj.read()
                frappe.log_error(f"File with read: {file_name}, size: {len(file_content) if file_content else 0}", "file_debug")
                
           
            elif hasattr(file_obj, 'filename') and hasattr(file_obj, 'file'):
                file_name = file_obj.filename
                file_content = file_obj.file.read()
                frappe.log_error(f"File with file attr: {file_name}, size: {len(file_content) if file_content else 0}", "file_debug")
                
            
            elif isinstance(file_obj, dict):
                file_name = file_obj.get('filename')
                file_content = file_obj.get('content')
                
                
                if isinstance(file_content, str):
                    try:
                        file_content = base64.b64decode(file_content)
                    except:
                        pass
                        
            else:
                frappe.log_error(f"Unknown file object type: {type(file_obj)}, attributes: {dir(file_obj)}", "file_debug")
                continue
            
            if not file_name or not file_content:
                frappe.log_error(f"Missing file name or content: name={file_name}, content_size={len(file_content) if file_content else 0}", "file_debug")
                continue
            
            
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "content": file_content,
                "decode": False,
                "is_private": 0,
                "attached_to_doctype": "Request For Quotation",
                "attached_to_name": rfq.name
            })
            file_doc.insert(ignore_permissions=True)

            
            
            attachment_row = rfq.append('multiple_attachments', {})
            attachment_row.attachment_name = file_doc.file_url
            attachment_row.name1 = file_name  
            
            frappe.log_error(f"Successfully attached file: {file_name} -> {file_doc.file_url}", "file_debug")
            
        except Exception as e:
            frappe.log_error(f"Error handling file attachment {i}: {str(e)}", "file_attachment_error")
            import traceback
            frappe.log_error(traceback.format_exc(), "file_attachment_traceback")
            continue

                   



		
