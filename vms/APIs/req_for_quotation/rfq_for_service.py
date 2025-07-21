import frappe
import json
from frappe.utils.file_manager import save_file

# create Service rfq
@frappe.whitelist(allow_guest=False)
def create_rfq_service(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        rfq = frappe.new_doc("Request For Quotation")

        # RFQ Basic Fields
        rfq.rfq_type = data.get("rfq_type")
        rfq.rfq_date = data.get("rfq_date")
        rfq.company_name = data.get("company_name")
        rfq.purchase_organization = data.get("purchase_organization")
        rfq.purchase_group = data.get("purchase_group")
        rfq.currency = data.get("currency")

        # Administrative Fields
        rfq.collection_number = data.get("collection_number")
        rfq.quotation_deadline = data.get("quotation_deadline")
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

        # Reminders
        rfq.first_reminder = data.get("first_reminder")
        rfq.second_reminder = data.get("second_reminder")
        rfq.third_reminder = data.get("third_reminder")

        # Group RFQ items head-wise and subhead-wise as one row per subhead (with head repeated)
        for item in data.get("pr_items", []):
            head_fields = {
                "head_unique_field": item.get("head_unique_field"),
                "purchase_requisition_number": item.get("requisition_no"),
                "material_code_head": item.get("material_code_head"),
                "delivery_date_head": item.get("delivery_date_head"),
                "plant_head": item.get("plant_head") or 0,
                "material_name_head": item.get("material_name_head"),
                "quantity_head": item.get("quantity_head"),
                "uom_head": item.get("uom_head"),
                "price_head": item.get("price_head")
            }

            subheads = item.get("subhead_fields", [])

            if subheads:
                for sub in subheads:
                    rfq.append("rfq_items", {
                        **head_fields,
                        "is_subhead": 1,
                        "subhead_unique_field": sub.get("subhead_unique_field"),
                        "material_code_subhead": sub.get("material_code_subhead"),
                        "material_name_subhead": sub.get("material_name_subhead"),
                        "quantity_subhead": sub.get("quantity_subhead"),
                        "uom_subhead": sub.get("uom_subhead"),
                        "price_subhead": sub.get("price_subhead"),
                        "delivery_date_subhead": sub.get("delivery_date_subhead")
                    })
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
        vendors = data.get("vendors", [])
        for vendor in vendors:
            rfq.append("vendor_details", {
                "ref_no": vendor.get("refno"),
                "vendor_name": vendor.get("vendor_name"),
                "vendor_code": ", ".join(vendor.get("vendor_code") or []),
                "office_email_primary": vendor.get("office_email_primary"),
                "mobile_number": vendor.get("mobile_number"),
                "service_provider_type": vendor.get("service_provider_type"),
                "country": vendor.get("country")
            })


        # Non-Onboarded Vendor Table
        non_vendors = data.get("non_onboarded_vendors", [])
        for vendor in non_vendors:
            rfq.append("non_onboarded_vendor_details", {
                "office_email_primary": vendor.get("office_email_primary"),
                "vendor_name": vendor.get("vendor_name"),
                "mobile_number": vendor.get("mobile_number"),
                "country": vendor.get("country")
            })

        rfq.insert(ignore_permissions=True)

        # Attachments Handling (multiple file uploads)
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


# get full data of service rfq
@frappe.whitelist(allow_guest=False)
def get_full_data_service_rfq(name):
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