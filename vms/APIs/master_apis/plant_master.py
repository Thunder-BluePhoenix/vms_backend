import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_plant_master_list(limit=None, offset=0, order_by=None, search_term=None):
    try:
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        order_by = order_by if order_by else "creation desc"

        if search_term:
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["plant_code", "like", f"%{search_term}%"],
                ["plant_name", "like", f"%{search_term}%"],
                ["description", "like", f"%{search_term}%"]
            ]

            plant_masters = frappe.get_list(
                "Plant Master",
                or_filters=or_filters,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "plant_code", "plant_name", "description", "company", "city", "plant_address"]
            )
            
            total_count = len(frappe.get_all(
                "Plant Master",
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            plant_masters = frappe.get_list(
                "Plant Master",
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "plant_code", "plant_name", "description", "company", "city", "plant_address"]
            )
            
            total_count = frappe.db.count("Plant Master")

        frappe.response.http_status_code = 200
        return {
            "message": "Success",
            "data": plant_masters,
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
