import frappe
import json

# PR Numbers list
@frappe.whitelist(allow_guest=False)
def pr_number_list():
    try:
        pr_numbers = frappe.get_all("Purchase Requisition Form", fields=["sap_pr_code"])

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
import frappe

@frappe.whitelist(allow_guest=False)
def add_pr_number(pr_number):
    try:
        if not pr_number:
            return {
                "status": "error",
                "message": "Please select PR number"
            }

        pur_req = frappe.get_doc("Purchase Requisition Form", {"sap_pr_code": pr_number})

        if pur_req:
            pur_req_table = []
            for row in pur_req.purchase_requisition_form_table:
                pur_req_table.append({
                    "material_code": row.material_code_head,
                    "material_name": row.product_name_head,
                    "quantity": row.quantity_head,
                    "uom": row.uom_head,
                    "price": row.product_price_head
                })

            return {
                "status": "success",
                "pr_items": pur_req_table
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
