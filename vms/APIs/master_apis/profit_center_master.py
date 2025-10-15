import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_profit_center_list(limit=None, offset=0, order_by=None, search_term=None):
    try:
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0
        
        order_by = order_by if order_by else "creation desc"

        if search_term:
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["profit_center_code", "like", f"%{search_term}%"],
                ["profit_center_name", "like", f"%{search_term}%"],
                ["description", "like", f"%{search_term}%"]
            ]

            profit_centers = frappe.get_list(
                "Profit Center",
                or_filters=or_filters,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "profit_center_code", "profit_center_name", "description", "company_code"]
            )
            
            total_count = len(frappe.get_all(
                "Profit Center",
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            profit_centers = frappe.get_list(
                "Profit Center",
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "profit_center_code", "profit_center_name", "description", "company_code"]
            )
            
            total_count = frappe.db.count("Profit Center")

        frappe.response.http_status_code = 200
        return {
            "message": "Success",
            "data": profit_centers,
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
