import frappe
import json




@frappe.whitelist(allow_guest=True)
def get_currency_list():
    try:
        

        # Fetch all currency records
        all_cur = frappe.get_all("Currency Master", fields="name")

        if not all_cur:
            return {
                "status": "success",
                "message": "No currency records found.",
                "data": []
            }

        return {
            "status": "success",
            "message": f"{len(all_cur)} currencies found.",
            "data": all_cur
        }

    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "Currency Master Doctype Not Found")
        return {
            "status": "error",
            "message": "Currency Master doctype does not exist."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_currency_list")
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }
