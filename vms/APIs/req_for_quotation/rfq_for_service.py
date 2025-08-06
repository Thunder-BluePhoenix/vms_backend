import frappe
import json
from frappe.utils.file_manager import save_file
from frappe import _
from datetime import datetime

# create Service rfq
@frappe.whitelist(allow_guest=False)
def create_rfq_service(data):
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

        # RFQ Basic Fields
        rfq.form_fully_submitted = 1
        rfq.status = "Pending"
        rfq.rfq_type = data.get("rfq_type")
        rfq.raised_by = frappe.local.session.user
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
                "country": vendor.get("country"),
                "company_pan": vendor.get("company_pan") or "",
				"gst_number": vendor.get("gst_number") or ""
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



