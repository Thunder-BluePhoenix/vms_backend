import frappe
import json

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
# @frappe.whitelist(allow_guest=False)
# def create_rfq_material(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)

        
