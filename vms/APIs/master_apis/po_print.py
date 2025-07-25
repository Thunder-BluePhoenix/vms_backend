import frappe
from frappe import _


# @frappe.whitelist(allow_guest = True)
# def get_po_printformat():
#     po_pf = frappe.get_all("PO PrintFormat Master", fields = {"name", "print_format_name"})
#     return po_pf



@frappe.whitelist(allow_guest=True)
def get_po_printformat():
    try:
        # Check if DocType exists
        if not frappe.db.exists("DocType", "PO PrintFormat Master"):
            frappe.response["http_status_code"] = 404
            frappe.log_error(frappe.get_traceback(), "PO PrintFormat - DocType Not Found")
            return {
                "success": False,
                "error": "DocType does not exist",
                "message": "PO PrintFormat Master DocType not found in the system"
            }
        
        # Validate user permissions (optional, since allow_guest=True)
        if not frappe.has_permission("PO PrintFormat Master", "read"):
            frappe.response["http_status_code"] = 403
            frappe.log_error(frappe.get_traceback(), "PO PrintFormat - Permission Denied")
            return {
                "success": False,
                "error": "Permission denied",
                "message": "You don't have permission to access this data"
            }
        
        # Get data with error handling
        po_pf = frappe.get_all(
            "PO PrintFormat Master", 
            fields=["name", "print_format_name"],
            limit_page_length=None
        )
        
        # Success response
        frappe.response["http_status_code"] = 200
        return {
            "success": True,
            "message": "Data retrieved successfully" if po_pf else "No records found",
            "data": po_pf,
            "count": len(po_pf)
        }
        
    except frappe.PermissionError:
        frappe.response["http_status_code"] = 403
        frappe.log_error(frappe.get_traceback(), "PO PrintFormat - Permission Denied")
        return {
            "success": False,
            "error": "Permission denied",
            "message": "You don't have permission to access this data"
        }
        
    except frappe.DataError as e:
        frappe.response["http_status_code"] = 400
        frappe.log_error(frappe.get_traceback(), "PO PrintFormat - Data Error")
        return {
            "success": False,
            "error": "Data error",
            "message": f"Invalid field or data structure: {str(e)}"
        }
        
    except Exception as e:
        frappe.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "PO PrintFormat - Unexpected Error")
        return {
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please contact administrator."
        }
    


