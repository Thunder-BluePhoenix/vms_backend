import frappe
import json




@frappe.whitelist(allow_guest=True)
def get_reconcilation_list(data):
    try:
        
        company = data.get("company")
        # Fetch all currency records
        rc_account = frappe.get_all("Reconciliation Account", filters={"company": company, "inactive": 0}, fields=["name", "reconcil_account", "reconcil_account_code", "reconcil_description"])

        if not rc_account:
            return {
                "status": "success",
                "message": "No Reconciliation account records found.",
                "data": []
            }

        return {
            "status": "success",
            "message": f"{len(rc_account)} Reconciliation Account found.",
            "data": rc_account
        }

    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "Reconciliation Account Doctype Not Found")
        return {
            "status": "error",
            "message": "Reconciliation Account doctype does not exist."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_reconcilation_list")
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }
