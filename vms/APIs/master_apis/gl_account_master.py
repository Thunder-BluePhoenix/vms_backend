import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_gl_account_list(limit=None, offset=0, order_by=None, search_term=None):
    try:
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        order_by = order_by if order_by else "creation desc"

        if search_term:
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["gl_account_code", "like", f"%{search_term}%"],
                ["gl_account_name", "like", f"%{search_term}%"],
                ["description", "like", f"%{search_term}%"]
            ]

            gl_accounts = frappe.get_list(
                "GL Account",
                or_filters=or_filters,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "gl_account_code", "gl_account_name", "company", "description", "account_group"]
            )
            
            total_count = len(frappe.get_all(
                "GL Account",
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            gl_accounts = frappe.get_list(
                "GL Account",
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False,
                fields=["name", "gl_account_code", "gl_account_name", "company", "description", "account_group"]
            )
            
            total_count = frappe.db.count("GL Account")

        frappe.response.http_status_code = 200
        return {
            "message": "Success",
            "data": gl_accounts,
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
