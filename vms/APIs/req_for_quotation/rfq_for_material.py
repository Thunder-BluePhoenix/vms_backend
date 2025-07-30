import frappe
import json
from frappe.utils.file_manager import save_file

# PR Numbers list
@frappe.whitelist(allow_guest=False)
def pr_number_list(pr_number=None, rfq_type=None):
    try:
        user = frappe.session.user

        # Get user's team from Employee
        employee_team = frappe.db.get_value("Employee", {"user_id": user}, "team")
        if not employee_team:
            return {
                "status": "error",
                "message": "No team assigned to the user"
            }

        # Get all Purchase Group names where this team is linked
        purchase_groups = frappe.get_all(
            "Purchase Group Master",
            filters={"team": employee_team},
            pluck="name"
        )

        if not purchase_groups:
            return {
                "status": "success",
                "pr_numbers": []
            }

        # Set filters
        filters = {
            "purchase_group": ["in", purchase_groups]
        }

        if pr_number:
            filters["sap_pr_code"] = ["like", f"{pr_number}%"]

        if rfq_type == "Material Vendor":
            filters["purchase_requisition_type"] = "NB"
        elif rfq_type == "Service Vendor":
            filters["purchase_requisition_type"] = "SB"

        # Fetch PR Numbers
        pr_numbers = frappe.get_all(
            "Purchase Requisition Form",
            filters=filters,
            fields=["name", "sap_pr_code"],
            limit_page_length=20
        )

        return {
            "status": "success",
            "pr_numbers": pr_numbers
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PR Number List Error")
        return {
            "status": "error",
            "message": str(e)
        }


# add pr numbers

@frappe.whitelist(allow_guest=False)
def add_pr_number(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		pr_numbers = data.get("pr_numbers", [])

		if not pr_numbers:
			return {
				"status": "error",
				"message": "Please select at least one PR number"
			}

		grouped_data = {}

		for pr_number in pr_numbers:
			pur_req = frappe.get_doc("Purchase Requisition Form", {"sap_pr_code": pr_number})
			if not pur_req or not pur_req.purchase_requisition_form_table:
				continue

			for row in sorted(pur_req.purchase_requisition_form_table, key=lambda x: x.idx):
				head_id = row.head_unique_id
				if not head_id:
					continue

				if head_id not in grouped_data:
					grouped_data[head_id] = {
						"row_id": row.name,
						"head_unique_field": head_id,
						"requisition_no": pr_number,
						"material_code_head": row.material_code_head or "",
						"material_name_head": row.short_text_head or "",
						"quantity_head": row.quantity_head or 0,
						"uom_head": row.uom_head or "",
						"price_head": row.product_price_head or 0,
						"delivery_date_head": row.delivery_date_head or "",
						"plant_head": row.plant_head or "",
						"subhead_fields": []
					}

				if (
					pur_req.purchase_requisition_type == "SB"
					and row.sub_head_unique_id
					and row.is_created
					and not row.is_deleted
				):
					parent_id = row.head_unique_id
					if parent_id in grouped_data:
						subhead_entry = {
							"row_id": row.name,
							"subhead_unique_field": row.sub_head_unique_id or "",
							"material_code_subhead": row.material_code_subhead or "",
							"material_name_subhead": row.short_text_subhead or "",
							"quantity_subhead": row.quantity_subhead or 0,
							"uom_subhead": row.uom_subhead or "",
							"price_subhead": row.gross_price_subhead or 0,
							"delivery_date_subhead": row.delivery_date_subhead or ""
						}
						if subhead_entry not in grouped_data[parent_id]["subhead_fields"]:
							grouped_data[parent_id]["subhead_fields"].append(subhead_entry)

		if grouped_data:
			return {
				"status": "success",
				"pr_items": list(grouped_data.values())
			}

		return {
			"status": "error",
			"message": "No matching Purchase Requisition items found"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Add PR Number Error")
		return {
			"status": "error",
			"message": str(e)
		}


# company wise filter purchase Group
@frappe.whitelist(allow_guest=True)
def filter_purchase_group(company):
    try:
        if not company:
            return {
                "status": "error",
                "message": "Company is required"
            }

        pur_grp = frappe.get_all(
            "Purchase Group Master",
            filters={"company": company},
            fields=["name", "purchase_group_code", "purchase_group_name", "description"]
        )

        return {
            "status": "success",
            "pur_grp": pur_grp
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering purchase group")
        return {
            "status": "error",
            "message": "Failed to filter purchase group.",
            "error": str(e)
        }
	
# company wise Purchase Organisation
@frappe.whitelist(allow_guest=True)
def filter_purchase_organisation(company):
    try:
        if not company:
            return {
                "status": "error",
                "message": "Company is required"
            }
        purchase_org = frappe.get_all(
            "Purchase Organization Master",
            filters={"company": company},
            fields=["name", "purchase_organization_code", "purchase_organization_name", "description"]
        )
        return {
            "status": "success",
            "purchase_org": purchase_org
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering purchase organisation")
        return {
            "status": "error",
            "message": "Failed to filter purchase organisation",
            "error": str(e)
        }
	
# company wise filter plant
@frappe.whitelist(allow_guest=True)
def filter_plant(company):
    try:
        if not company:
            return {
                "status": "error",
                "message": "Company is required"
            }

        plant = frappe.get_all(
            "Plant Master",
            filters={"company": company},
            fields=["name", "plant_name", "city", "zone", "plant_address", "description"]
        )

        return {
            "status": "success",
            "plant": plant
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering Plant")
        return {
            "status": "error",
            "message": "Failed to filter Plant.",
            "error": str(e)
        }
	
	
# company wise material master
@frappe.whitelist(allow_guest=True)
def filter_material_master(company):
    try:
        if not company:
            return {
                "status": "error",
                "message": "Company is required"
            }

        material_master = frappe.get_all(
            "Material Master",
            filters={"company": company},
            fields=["name", "material_code", "material_name", "material_type", "material_category", "description"]
        )

        return {
            "status": "success",
            "material_master": material_master
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering material master")
        return {
            "status": "error",
            "message": "Failed to filter material master",
            "error": str(e)
        }


# company wise material group
@frappe.whitelist(allow_guest=True)
def filter_material_group_master(company):
    try:
        if not company:
            return {
                "status": "error",
                "message": "Company is required"
            }
        material_group = frappe.get_all(
            "Material Group Master",
            filters={"material_group_company": company},
            fields=["name", "material_group_name", "material_group_description", "material_group_long_description"]
        )
        return {
            "status": "success",
            "material_group": material_group
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering material group")
        return {
            "status": "error",
            "message": "Failed to filter material group",
            "error": str(e)
        }
	
# filter the company wise master fields for material and services 
@frappe.whitelist(allow_guest=True)
def filter_master_fields(company):
	try:
		if not company:
			return {
				"status": "error",
				"message": "Company is required"
			}

		pur_grp = frappe.get_all(
			"Purchase Group Master",
			filters={"company": company},
			fields=["name", "purchase_group_code", "purchase_group_name", "description"]
		)

		purchase_org = frappe.get_all(
			"Purchase Organization Master",
			filters={"company": company},
			fields=["name", "purchase_organization_code", "purchase_organization_name", "description"]
		)

		plant = frappe.get_all(
			"Plant Master",
			filters={"company": company},
			fields=["name", "plant_name", "city", "zone", "plant_address", "description"]
		)

		material_master = frappe.get_all(
			"Material Master",
			filters={"company": company},
			fields=["name", "material_code", "material_name", "material_type", "material_category", "description"]
		)

		material_group = frappe.get_all(
			"Material Group Master",
			filters={"material_group_company": company},
			fields=["name", "material_group_name", "material_group_description", "material_group_long_description"]
		)

		return {
			"status": "success",
			"purchase_group": pur_grp,
			"purchase_organisation": purchase_org,
			"plant": plant,
			"material_master": material_master,
			"material_group_master": material_group
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in consolidated company master fetch")
		return {
			"status": "error",
			"message": "Failed to fetch master data",
			"error": str(e)
		}



# create Material rfq
@frappe.whitelist(allow_guest=False)
def create_rfq_material(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		rfq = frappe.new_doc("Request For Quotation")

		# RFQ Basic Fields
		rfq.form_fully_submitted = 1
		rfq.rfq_type = data.get("rfq_type") or ""
		rfq.raised_by = frappe.local.session.user
		rfq.rfq_date = data.get("rfq_date") or None
		rfq.company_name = data.get("company_name") or ""
		rfq.purchase_organization = data.get("purchase_organization") or ""
		rfq.purchase_group = data.get("purchase_group") or ""
		rfq.currency = data.get("currency") or "INR"

		# Administrative Fields
		rfq.collection_number = data.get("collection_number") or ""
		rfq.quotation_deadline = data.get("quotation_deadline") or None
		rfq.validity_start_date = data.get("validity_start_date") or None
		rfq.validity_end_date = data.get("validity_end_date") or None
		rfq.bidding_person = data.get("bidding_person") or ""

		# Material/Service Details
		rfq.service_code = data.get("service_code") or ""
		rfq.service_category = data.get("service_category") or ""
		rfq.material_code = data.get("material_code") or ""
		rfq.material_category = data.get("material_category") or ""
		rfq.plant_code = data.get("plant_code") or ""
		rfq.storage_location = data.get("storage_location") or ""
		rfq.short_text = data.get("short_text") or ""

		# Quantity & Dates
		rfq.rfq_quantity = data.get("rfq_quantity") or 0
		rfq.quantity_unit = data.get("quantity_unit") or ""
		rfq.delivery_date = data.get("delivery_date") or None

		# Target Price
		rfq.estimated_price = data.get("estimated_price") or 0

		# Reminders
		rfq.first_reminder = data.get("first_reminder") or None
		rfq.second_reminder = data.get("second_reminder") or None
		rfq.third_reminder = data.get("third_reminder") or None

		# RFQ Items Table
		pr_items = data.get("pr_items") or []
		for item in pr_items:
			rfq.append("rfq_items", {
				"head_unique_field": item.get("head_unique_field") or "",
				"purchase_requisition_number": item.get("requisition_no") or "",
				"material_code_head": item.get("material_code_head") or "",
				"delivery_date_head": item.get("delivery_date_head") or None,
				"plant_head": item.get("plant_head") or "",
				"material_name_head": item.get("material_name_head") or "",
				"quantity_head": item.get("quantity_head") or 0,
				"uom_head": item.get("uom_head") or "",
				"price_head": item.get("price_head") or 0
			})

		# Vendor Details Table
		vendors = data.get("vendors") or []
		for vendor in vendors:
			rfq.append("vendor_details", {
				"ref_no": vendor.get("refno") or "",
				"vendor_name": vendor.get("vendor_name") or "",
				"vendor_code": ", ".join(vendor.get("vendor_code") or []),
				"office_email_primary": vendor.get("office_email_primary") or "",
				"mobile_number": vendor.get("mobile_number") or "",
				"service_provider_type": vendor.get("service_provider_type") or "",
				"country": vendor.get("country") or ""
			})

		# Non-Onboarded Vendor Table
		non_vendors = data.get("non_onboarded_vendors") or []
		for vendor in non_vendors:
			rfq.append("non_onboarded_vendor_details", {
				"office_email_primary": vendor.get("office_email_primary") or "",
				"vendor_name": vendor.get("vendor_name") or "",
				"mobile_number": vendor.get("mobile_number") or "",
				"country": vendor.get("country") or "",
				"company_pan": vendor.get("company_pan") or  "",
				"gst_number": vendor.get("gst_number") or ""
			})

		rfq.insert(ignore_permissions=True)

		# Attachments Handling
		files = frappe.request.files.getlist("file")
		for file in files:
			saved = save_file(file.filename, file.stream.read(), rfq.doctype, rfq.name, is_private=0)
			rfq.append("multiple_attachments", {
				"attachment_name": saved.file_url
			})

		rfq.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "RFQ created successfully",
			"rfq_name": rfq.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create RFQ API Error")
		return {
			"status": "error",
			"message": "Error creating RFQ: " + str(e)
		}


@frappe.whitelist(allow_guest=False)
def get_full_data_material_rfq(name):
	try:
		doc = frappe.get_doc("Request For Quotation", name)

		# RFQ Items Table
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
				"price_head": row.price_head
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

		# RFQ Basic Fields
		data = {
			"rfq_type": doc.rfq_type,
			"rfq_date": doc.rfq_date,
			"company_name": doc.company_name,
			"purchase_organization": doc.purchase_organization,
			"purchase_group": doc.purchase_group,
			"currency": doc.currency,

			# Administrative Fields
			"collection_number": doc.collection_number,
			"quotation_deadline": doc.quotation_deadline,
			"validity_start_date": doc.validity_start_date,
			"validity_end_date": doc.validity_end_date,
			"bidding_person": doc.bidding_person,

			# Material/Service Details
			"service_code": doc.service_code,
			"service_category": doc.service_category,
			"material_code": doc.material_code,
			"material_category": doc.material_category,
			"plant_code": doc.plant_code,
			"storage_location": doc.storage_location,
			"short_text": doc.short_text,

			# Quantity & Dates
			"rfq_quantity": doc.rfq_quantity,
			"quantity_unit": doc.quantity_unit,
			"delivery_date": doc.delivery_date,

			# Target Price
			"estimated_price": doc.estimated_price,

			# Reminders
			"first_reminder": doc.first_reminder,
			"second_reminder": doc.second_reminder,
			"third_reminder": doc.third_reminder,

			# Child Tables
			"pr_items": pr_items,
			"vendor_details": vendor_details_data,
			"non_onboarded_vendors": non_onboarded_vendor_details_data,
			"attachments": attachments
		}

		return {
			"status": "success",
			"rfq_name": name,
			"data": data
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Fetch Material RFQ Error")
		frappe.throw(_("Error fetching RFQ: ") + str(e))




