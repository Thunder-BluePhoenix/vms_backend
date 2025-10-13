import frappe
import json

#vms.APIs.employee.get_employee.get_employee_details
@frappe.whitelist()
def get_employee_details(user=None):
    try:
        # Check if user parameter is provided
        if not user:
            frappe.response.http_status_code = 400
            return {
                "message": "Failed",
                "error": "User ID is required"
            }

        # Check permission
        if not frappe.has_permission("Employee", "read"):
            frappe.response.http_status_code = 403
            return {
                "message": "Failed",
                "error": "You don't have permission to view Employee details"
            }

        # Find employee by user_id
        employees = frappe.get_all(
            "Employee",
            filters={"user_id": user},
            fields=["name"],
            limit=1
        )

        if not employees:
            frappe.response.http_status_code = 404
            return {
                "message": "Failed",
                "error": f"No employee found for user: {user}"
            }

        employee_id = employees[0].name

        
        employee_doc = frappe.get_doc("Employee", employee_id)

        
        employee_data = employee_doc.as_dict()

        
        fields_to_remove = [
            "docstatus",
            "idx",
            "owner",
            "modified_by",
            "creation",
            "modified",
            "__islocal",
            "__onload",
            "__unsaved"
        ]
        
        for field in fields_to_remove:
            employee_data.pop(field, None)

        return {
            "message": "Success",
            "data": employee_data
        }

    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {
            "message": "Failed",
            "error": "Permission denied"
        }
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Get Employee By User Error")
        return {
            "message": "Failed",
            "error": str(e)
        }