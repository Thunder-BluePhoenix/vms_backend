import frappe
import json

# PR Numbers list
@frappe.whitelist(allow_guest=False)
def pr_number_list(pr_number=None):
    try:
        filters = {}
        if pr_number:
            filters["sap_pr_code"] = ["like", f"{pr_number}%"]

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
            if pur_req:
                for row in pur_req.purchase_requisition_form_table:
                    pr_items.append({
                        "requisition_no": pr_number,
                        "material_code": row.material_code_head,
                        "material_name": row.product_name_head,
                        "quantity": row.quantity_head,
                        "uom": row.uom_head,
                        "price": row.product_price_head
                    })

        if pr_items:
            return {
                "status": "success",
                "pr_items": pr_items
            }
        else:
            return {
                "status": "error",
                "message": "No matching Purchase Requisition found"
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Add PR Number Error")
        return {
            "status": "error",
            "message": str(e)
        }
    

# create Material rfq
# @frappe.whitelist(allow_guest=False)
# def 
