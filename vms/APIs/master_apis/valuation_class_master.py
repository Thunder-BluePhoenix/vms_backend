import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_valuation_class_list(limit=None, offset=0, order_by=None, search_term=None):
    try:
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        order_by = order_by if order_by else "creation desc"

        if search_term:
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["valuation_class_code", "like", f"%{search_term}%"],
                ["valuation_class_name", "like", f"%{search_term}%"]
            ]

            valuation_class = frappe.get_list(
                "Valuation Class",
                or_filters=or_filters,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "valuation_class_code", "valuation_class_name", "company"]
            )
            
            total_count = len(frappe.get_all(
                "Valuation Class",
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            valuation_class = frappe.get_list(
                "Valuation Class",
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "valuation_class_code", "valuation_class_name", "company"]
            )
            
            total_count = frappe.db.count("Valuation Class")

        frappe.response.http_status_code = 200
        return {
            "message": "Success",
            "data": valuation_class,
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
