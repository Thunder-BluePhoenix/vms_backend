import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_employee_list(limit=None, offset=0, order_by=None, search_term=None):
    try:
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0
        
        order_by = order_by if order_by else "creation desc"

        if search_term:
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["user_id", "like", f"%{search_term}%"],
                ["first_name", "like", f"%{search_term}%"],
                ["last_name", "like", f"%{search_term}%"],
                ["employee_code", "like", f"%{search_term}%"],
                ["full_name", "like", f"%{search_term}%"]
            ]

            employees = frappe.get_list(
                "Employee",
                or_filters=or_filters,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "user_id", "first_name", "last_name", "full_name", "employee_code", "designation", "team"]
            )
            
            total_count = len(frappe.get_all(
                "Employee",
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            employees = frappe.get_list(
                "Employee",
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "user_id", "first_name", "last_name", "full_name", "employee_code", "designation", "team"]
            )
            
            total_count = frappe.db.count("Employee")

        frappe.response.http_status_code = 200
        return {
            "message": "Success",
            "data": employees,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count,
                "has_previous": offset > 0
            }
        }
    
    except json.JSONDecodeError:
        frappe.response.http_status_code = 400
        return {"message": "Failed", "error": "Invalid JSON in filters or fields"}
    except Exception as e:
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}
