import frappe
import json

#vms.APIs.employee.get_employee.get_employee_details
@frappe.whitelist()
def get_employee_details(user=None):
    try:
        
        if not user:
            user = frappe.session.user
            
            
            if not user or user == "Guest":
                frappe.response.http_status_code = 401
                return {
                    "message": "Failed",
                    "error": "Authentication required. Please login to continue."
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

        
        if employee_data.get("company"):
            enhanced_company_list = []
            
            for row in employee_data.get("company", []):
                if row.get("company_name"):
                    # Fetch company details
                    company_details = frappe.db.get_value(
                        "Company Master",
                        row.get("company_name"),
                        ["company_name", "company_code", "company_short_form"],
                        as_dict=True
                    )
                    
                    if company_details:
                        
                        enhanced_company_list.append(company_details)
            
            
            employee_data["company"] = enhanced_company_list

        
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