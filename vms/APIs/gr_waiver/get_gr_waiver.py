import json

import frappe
from frappe.model.document import Document

# vms.APIs.gr_waiver.get_gr_waiver.get_gr_waiver_details
@frappe.whitelist()
def get_gr_waiver_details(name):
    try:
        # Check if name parameter is provided
        if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Document name is required"}

        # Get the document
        gr_waiver = frappe.get_doc("GR Waiver", name)
        
        # Convert to dictionary and include all fields
        doc_dict = gr_waiver.as_dict()
        
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



# vms.APIs.gr_waiver.get_gr_waiver.get_gr_waiver_list
@frappe.whitelist()
def get_gr_waiver_list(filters=None, fields=None, limit=20, offset=0, order_by=None):
    try:
        # Parse filters if they're passed as JSON string
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Parse fields if they're passed as JSON string
        if isinstance(fields, str):
            fields = json.loads(fields) if fields else ["*"]
        elif fields is None:
            fields = ["*"]

        # Convert limit and offset to integers
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        # Set default order_by if not provided
        if not order_by:
            order_by = "creation desc"

        # Get list of documents with filters
        documents = frappe.get_list(
            "GR Waiver",
            filters=filters,
            fields=fields,
            limit=limit,
            start=offset,
            order_by=order_by,
            ignore_permissions=False 
        )

        # Get total count for pagination
        total_count = frappe.db.count("GR Waiver", filters)

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

