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

        pr_items = []

        for pr_number in pr_numbers:
            pur_req = frappe.get_doc("Purchase Requisition Form", {"sap_pr_code": pr_number})
            if not pur_req or not pur_req.purchase_requisition_form_table:
                continue

            if pur_req.purchase_requisition_type == "NB":
                for row in pur_req.purchase_requisition_form_table:
                    pr_items.append({
                        # head
                        "head_unique_field": row.head_unique_id or "",
                        "requisition_no": pr_number,
                        "material_code_head": row.material_code_head or "",
                        "material_name_head": row.short_text_head or "",
                        "quantity_head": row.quantity_head or 0,
                        "uom_head": row.uom_head or "",
                        "price_head": row.product_price_head or 0,
                    })

            elif pur_req.purchase_requisition_type == "SB":
                for row in pur_req.purchase_requisition_form_table:
                    pr_items.append({
                        # head
                        "head_unique_field": row.head_unique_id or "",
                        "requisition_no": pr_number,
                        "material_code_head": row.material_code_head or "",
                        "material_name_head": row.short_text_head or "",
                        "quantity_head": row.quantity_head or 0,
                        "uom_head": row.uom_head or "",
                        "price_head": row.product_price_head or 0,
                        # subhead
                        "subhead_unique_field": row.sub_head_unique_id or "",
                        "material_code_subhead": row.material_code_subhead or "",
                        "material_name_subhead": row.short_text_subhead or "",
                        "quantity_subhead": row.quantity_subhead or 0,
                        "uom_subhead": row.uom_subhead or "",
                        "price_subhead": row.gross_price_subhead or 0
                    })

            else:
                return {
                    "status": "error",
                    "message": f"No Purchase Requisition Type found for PR: {pr_number}"
                }

        if pr_items:
            return {
                "status": "success",
                "pr_items": pr_items
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
    

# create Material rfq
@frappe.whitelist(allow_guest=False)
def create_rfq_material(data):
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

        # RFQ Items Table
        pr_items = data.get("pr_items", [])
        for item in pr_items:
            rfq.append("rfq_items", {
                # head
                "head_unique_field": item.get("head_unique_field"),
                "purchase_requisition_number": item.get("purchase_requisition_number"),
                "material_code_head": item.get("material_code_head"),
                "material_name_head": item.get("material_name_head"),
                "quantity_head": item.get("quantity_head"),
                "uom_head": item.get("uom_head"),
                "price_head": item.get("price_head"),
                # subhead
                "subhead_unique_field": item.get("subhead_unique_field"),
                "material_code_subhead": item.get("material_code_subhead"),
                "material_name_subhead": item.get("material_name_subhead"),
                "quantity_subhead": item.get("quantity_subhead"),
                "uom_subhead": item.get("uom_subhead"),
                "price_subhead": item.get("price_subhead")
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

