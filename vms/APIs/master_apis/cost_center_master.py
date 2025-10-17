import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_cost_center_list(limit=None, offset=0, order_by=None, search_term=None):
    try:
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        order_by = order_by if order_by else "creation desc"

        if search_term:
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["cost_center_code", "like", f"%{search_term}%"],
                ["cost_center_name", "like", f"%{search_term}%"],
                ["description", "like", f"%{search_term}%"],
                ["short_text", "like", f"%{search_term}%"]
            ]

            cost_centers = frappe.get_list(
                "Cost Center",
                or_filters=or_filters,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "cost_center_code", "cost_center_name", "description", "company_code", "short_text"]
            )
            
            total_count = len(frappe.get_all(
                "Cost Center",
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            cost_centers = frappe.get_list(
                "Cost Center",
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "cost_center_code", "cost_center_name", "description", "company_code", "description", "short_text"]
            )
            
            total_count = frappe.db.count("Cost Center")

        frappe.response.http_status_code = 200
        return {
            "message": "Success",
            "data": cost_centers,
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
