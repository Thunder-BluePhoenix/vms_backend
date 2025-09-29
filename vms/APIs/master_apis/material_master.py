import json
import frappe
from frappe import _


#vms.APIs.master_apis.material_master.get_material_master_details
@frappe.whitelist()
def get_material_master_details(name):
    try:
        if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Document name is required"}

        material_master = frappe.get_doc("Material Master", name)
        doc_dict = material_master.as_dict()
        
        return {
            "message": "Success",
            "data": doc_dict
        }

    except frappe.DoesNotExistError:
        frappe.response.http_status_code = 404
        return {"message": "Failed", "error": "Document not found"}
    
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}


#vms.APIs.master_apis.material_master.get_material_master_list
@frappe.whitelist()
def get_material_master_list(filters=None, fields=None, limit=20, offset=0, order_by=None, search_term=None):

    try:
        # Parse filters if they're passed as JSON string
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Parse fields if they're passed as JSON string
        if isinstance(fields, str):
            fields = json.loads(fields) if fields else [
                "name", "description", "material_type", 
                "material_group", "plant", "company_code"
            ]
        elif fields is None:
            fields = [
                "name", "description", "material_name","material_code"
            ]

        # Convert limit and offset to integers
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        # Set default order_by if not provided
        if not order_by:
            order_by = "creation desc"

        # Add search term to filters if provided
        if search_term:
            # Search across multiple fields using OR condition
            or_filters = [
                ["description", "like", f"%{search_term}%"],
                ["name", "like", f"%{search_term}%"],
                ["material_name", "like", f"%{search_term}%"],
                ["material_code", "like", f"%{search_term}%"]
            ]
            
            # Get documents with OR filters
            documents = frappe.get_list(
                "Material Master",
                filters=filters,
                or_filters=or_filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )
            
            # Count with OR filters
            total_count = len(frappe.get_all(
                "Material Master",
                filters=filters,
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            # Get list of documents with filters
            documents = frappe.get_list(
                "Material Master",
                filters=filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )
            
            # Get total count for pagination
            total_count = frappe.db.count("Material Master", filters)

        return {
            "message": "Success",
            "data": documents,
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

