import frappe
import json




@frappe.whitelist(allow_guest=True)
def get_bank_list(company_name=None):
    try:
        

        # Fetch all currency records
        all_banks = frappe.get_all("Bank Master",filters={"company": company_name}, fields=["name", "bank_code", "bank_name", "description", "ifsc_code"])

        if not all_banks:
            return {
                "status": "success",
                "message": "No Bank records found.",
                "data": []
            }

        return {
            "status": "success",
            "message": f"{len(all_banks)} Bank found.",
            "data": all_banks
        }

    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "Bank Master Doctype Not Found")
        return {
            "status": "error",
            "message": "Bank Master doctype does not exist."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_bank_list")
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }
