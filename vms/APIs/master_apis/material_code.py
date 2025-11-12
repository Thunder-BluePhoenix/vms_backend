import json
import frappe
from frappe import _


#vms.APIs.master_apis.material_code.get_material_code_details
@frappe.whitelist()
def get_material_code_details(name):
    try:
        if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Document name is required"}

        material_code = frappe.get_doc("Material Code", name)
        doc_dict = material_code.as_dict()
        
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


#vms.APIs.master_apis.material_code.get_material_code_list
@frappe.whitelist()
def get_material_code_list(filters=None, fields=None, limit=None, offset=0, order_by=None, search_term=None):

    try:
        # Parse filters if they're passed as JSON string
        # if isinstance(filters, str):
        #     filters = json.loads(filters) if filters else {}
        # elif filters is None:
        #     filters = {}
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}

        # Handle None
        if not filters:
            filters = {}

        # Convert list of dicts -> single dict (Frappe-friendly)
        if isinstance(filters, list):
            # Merge list of single-key dicts into one dict
            merged_filters = {}
            for f in filters:
                if isinstance(f, dict):
                    merged_filters.update(f)
            filters = merged_filters

        # Parse fields if they're passed as JSON string
        if isinstance(fields, str):
            fields = json.loads(fields) if fields else [
                "name", "material_description", "material_type", 
                "material_group", "plant", "company", "material_code", "valuation_class", "profit_center"
            ]
        elif fields is None:
            fields = [
                "name", "material_description", "material_code_name","material_code", "material_type", "material_group", "plant", "company", "valuation_class", "profit_center"
            ]

        # # --- Convert offset ---
        # offset = int(offset) if offset else 0

        # # --- Smart limit logic ---
        if search_term:
            # If user is searching, show more results but cap at 1000
            limit = min(int(limit) if limit else 500, 1000)
        elif filters and len(filters.keys()) > 0:
            # If filters applied (company/material type etc.), fetch more (up to 5000)
            limit = min(int(limit) if limit else 2000, 5000)
        else:
            # Default for general browsing
            limit = int(limit) if limit else 20
        # limit = int(limit) if limit else 20
        # offset = int(offset) if offset else 0
        
        # Set default order_by if not provided
        if not order_by:
            order_by = "creation desc"

        # Add search term to filters if provided
        or_filters = []
        if search_term:
            # Search across multiple fields using OR condition
            or_filters = [
                ["material_description", "like", f"%{search_term}%"],
                ["name", "like", f"%{search_term}%"],
                ["material_code_name", "like", f"%{search_term}%"],
                ["material_code", "like", f"%{search_term}%"]
            ]
            
            # Get documents with OR filters
            documents = frappe.get_list(
                "Material Code",
                filters=filters,
                or_filters=or_filters if search_term else None,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )
            
            # Count with OR filters
            total_count = len(
                frappe.get_all(
                    "Material Code",
                    filters=filters,
                    or_filters=or_filters,
                    fields=["name"]
                )
            )
        else:
            # Get list of documents with filters
            documents = frappe.get_list(
                "Material Code",
                filters=filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )
            
            # Get total count for pagination
            total_count = frappe.db.count("Material Code", filters)

        return {
            "message": "Success",
            "data": documents,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count if limit else False,
                "has_previous": offset > 0
            }
        }

    except json.JSONDecodeError:
        frappe.response.http_status_code = 400
        return {"message": "Failed", "error": "Invalid JSON in filters or fields"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}

