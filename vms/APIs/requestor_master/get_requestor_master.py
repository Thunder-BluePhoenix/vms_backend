import json
import frappe
from frappe import _


#vms.APIs.requestor_master.get_requestor_master.get_requestor_master_details
@frappe.whitelist()
def get_requestor_master_details(name):
    try:
        if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Document name is required"}

        # Get the document
        doc = frappe.get_doc("Requestor Master", name)
        doc_dict = doc.as_dict()

        # Remove the default material_request child table
        if "material_request" in doc_dict:
            del doc_dict["material_request"]

        # Format material request items with company name
        material_request_items = []
        for child in doc.material_request:
            company_name = frappe.db.get_value(
                "Company Master", 
                child.company_name, 
                "company_name"
            ) if child.company_name else ""

            material_request_items.append({
                "child_name": child.name,
                "company_code": child.company_name,
                "company_name": company_name,
                "material_description": child.material_name_description,
                "material_type": child.material_type,
                "material_category": child.material_category,
                "comment_by_user": child.comment_by_user,
                "material_specifications": child.material_specifications,
                "material_group": child.material_group,
                "material_image": child.material_image,
                "quantity": child.quantity,
                "unit_of_measure": child.unit_of_measure,
                "rate": child.rate,
                "amount": child.amount,
                "manufacturer": child.manufacturer,
                "plant": child.plant,
                "material_code_revised": child.material_code_revised,
                "is_revised_code_new": child.is_revised_code_new
            })

        doc_dict["material_request_items"] = material_request_items

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
        frappe.log_error(frappe.get_traceback(), "Requestor Master Detail Error")
        return {"message": "Failed", "error": str(e)}


#vms.APIs.requestor_master.get_requestor_master.get_requestor_master_list
@frappe.whitelist()
def get_requestor_master_list(filters=None, fields=None, limit=20, offset=0, order_by=None, search_term=None, include_items=True):
    """
    Get list of Requestor Master documents with pagination and search
    
    Parameters:
    - filters: JSON string or dict of filters
    - fields: JSON string or list of fields to return
    - limit: Number of records per page (default: 20)
    - offset: Starting position (default: 0)
    - order_by: Sort order (default: "request_date DESC, creation DESC")
    - search_term: Search in name or other fields
    - include_items: Whether to include material_request_items (default: True)
    """
    try:
        # Parse filters if they're passed as JSON string
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Parse fields if they're passed as JSON string
        if isinstance(fields, str):
            fields = json.loads(fields) if fields else ["name","material_master_ref_no","material_onboarding_ref_no","approval_status"]
        elif fields is None:
            fields = ["name","material_master_ref_no","material_onboarding_ref_no","approval_status"]

        # Convert limit and offset to integers
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        # Convert include_items to boolean
        if isinstance(include_items, str):
            include_items = include_items.lower() in ['true', '1', 'yes']
        
        # Set default order_by if not provided
        if not order_by:
            order_by = "request_date DESC, creation DESC"

        # Build search filters
        search_filters = filters.copy()
        or_filters = None
        
        if search_term:
            # Search across multiple fields using OR condition
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["requestor_name", "like", f"%{search_term}%"],
                ["approval_status", "like", f"%{search_term}%"]
            ]

        # Get list of documents with filters
        if or_filters:
            documents = frappe.get_list(
                "Requestor Master",
                filters=search_filters,
                or_filters=or_filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )
            
            # Get total count with OR filters
            total_count = len(frappe.get_all(
                "Requestor Master",
                filters=search_filters,
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            documents = frappe.get_list(
                "Requestor Master",
                filters=search_filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )
            
            # Get total count for pagination
            total_count = frappe.db.count("Requestor Master", search_filters)

        # Format the response with material request items if requested
        requestor_master_list = []
        
        for item in documents:
            if include_items:
                # Get full document to access child table
                doc = frappe.get_doc("Requestor Master", item.name)
                doc_dict = doc.as_dict()

                # Remove the default material_request child table
                if "material_request" in doc_dict:
                    del doc_dict["material_request"]

                # Format material request items with company name
                material_request_items = []
                for child in doc.material_request:
                    company_name = frappe.db.get_value(
                        "Company Master", 
                        child.company_name, 
                        "company_name"
                    ) if child.company_name else ""

                    material_request_items.append({
                        "child_name": child.name,
                        "company_code": child.company_name,
                        "company_name": company_name,
                        "plant": child.plant,
                        "material_description": child.material_name_description,
                        "material_type": child.material_type,
                        "comment_by_user": child.comment_by_user,
                    })

                doc_dict["material_request_items"] = material_request_items
                requestor_master_list.append(doc_dict)
            else:
                # Just return the basic fields without child table
                requestor_master_list.append(item)

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
        frappe.log_error(frappe.get_traceback(), "Requestor Master List Error")
        return {"message": "Failed", "error": str(e)}
