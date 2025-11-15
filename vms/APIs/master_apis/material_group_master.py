import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_material_group_list(limit=None, offset=0, order_by=None, search_term=None, company_name=None):
    print("Material Group Company Name ---->", company_name)

    try:
        limit = int(limit) if limit else 500
        offset = int(offset) if offset else 0
        order_by = order_by or "creation desc"

        filters = {}
        if company_name:
            filters["material_group_company"] = company_name

        or_filters = None

        if search_term:
            or_filters = [
                ["Material Group Master", "name", "like", f"%{search_term}%"],
                ["Material Group Master", "material_group_name", "like", f"%{search_term}%"],
                ["Material Group Master", "material_group_long_description", "like", f"%{search_term}%"],
                ["Material Group Master", "material_group_description", "like", f"%{search_term}%"],
            ]

        material_groups = frappe.get_list(
            "Material Group Master",
            filters=filters,
            or_filters=or_filters,
            limit=limit,
            start=offset,
            order_by=order_by,
            ignore_permissions=False,
            fields=[
                "name",
                "material_group_name",
                "material_group_long_description",
                "material_group_description",
                "material_group_company"
            ]
        )

        total_count = frappe.db.count(
            "Material Group Master",
            filters=filters,
        )

        frappe.response.http_status_code = 200

        return {
            "message": "Success",
            "data": material_groups,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count,
                "has_previous": offset > 0
            }
        }

    except Exception as e:
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}


import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_material_group_list_custom(filters=None, fields=None, limit=None, offset=0, order_by=None, search_term=None):
    try:
        # Parse filters if they're passed as JSON string
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Parse fields if they're passed as JSON string
        if isinstance(fields, str):
            fields = json.loads(fields) if fields else [
                "name", "material_group_name", "material_group_long_description", 
                "material_group_description", "material_group_company"
            ]
        elif fields is None:
            fields = [
                "name", "material_group_name", "material_group_long_description", 
                "material_group_description", "material_group_company"
            ]

        # Convert limit and offset to integers
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        # Set default order_by if not provided
        order_by = order_by if order_by else "creation desc"

        # Add search term to filters if provided
        if search_term:
            # Search across multiple fields using OR condition
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["material_group_name", "like", f"%{search_term}%"],
                ["material_group_long_description", "like", f"%{search_term}%"],
                ["material_group_description", "like", f"%{search_term}%"]
            ]
            
            # Get documents with OR filters
            material_groups = frappe.get_list(
                "Material Group Master",
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
                "Material Group Master",
                filters=filters,
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            # Get list of documents with filters
            material_groups = frappe.get_list(
                "Material Group Master",
                filters=filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )
            
            # Get total count for pagination
            total_count = frappe.db.count("Material Group Master", filters)

        frappe.response.http_status_code = 200
        return {
            "message": "Success",
            "data": material_groups,
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