import frappe
from frappe import _
import json


# @frappe.whitelist(allow_guest = True)
# def get_po_printformat():
#     po_pf = frappe.get_all("PO PrintFormat Master", fields = {"name", "print_format_name"})
#     return po_pf



@frappe.whitelist(allow_guest=True)
def get_po_printformat():
    try:
        # Check if DocType exists
        if not frappe.db.exists("DocType", "PO PrintFormat Master"):
            frappe.response["http_status_code"] = 404
            frappe.log_error(frappe.get_traceback(), "PO PrintFormat - DocType Not Found")
            return {
                "success": False,
                "error": "DocType does not exist",
                "message": "PO PrintFormat Master DocType not found in the system"
            }
        
        # Validate user permissions (optional, since allow_guest=True)
        if not frappe.has_permission("PO PrintFormat Master", "read"):
            frappe.response["http_status_code"] = 403
            frappe.log_error(frappe.get_traceback(), "PO PrintFormat - Permission Denied")
            return {
                "success": False,
                "error": "Permission denied",
                "message": "You don't have permission to access this data"
            }
        
        # Get data with error handling
        po_pf = frappe.get_all(
            "PO PrintFormat Master", 
            fields=["name", "print_format_name"],
            limit_page_length=None
        )
        
        # Success response
        frappe.response["http_status_code"] = 200
        return {
            "success": True,
            "message": "Data retrieved successfully" if po_pf else "No records found",
            "data": po_pf,
            "count": len(po_pf)
        }
        
    except frappe.PermissionError:
        frappe.response["http_status_code"] = 403
        frappe.log_error(frappe.get_traceback(), "PO PrintFormat - Permission Denied")
        return {
            "success": False,
            "error": "Permission denied",
            "message": "You don't have permission to access this data"
        }
        
    except frappe.DataError as e:
        frappe.response["http_status_code"] = 400
        frappe.log_error(frappe.get_traceback(), "PO PrintFormat - Data Error")
        return {
            "success": False,
            "error": "Data error",
            "message": f"Invalid field or data structure: {str(e)}"
        }
        
    except Exception as e:
        frappe.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "PO PrintFormat - Unexpected Error")
        return {
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please contact administrator."
        }
    





def handle_api_exception(e, operation_name="API Operation"):
    """Dynamic exception handler for Frappe APIs"""
    
    # Get exception type and name
    exc_type = type(e)
    exc_name = exc_type.__name__
    
    # Dynamic mapping based on exception name patterns
    status_code = 500
    error_type = "Internal server error"
    default_message = "An unexpected error occurred"
    
    # Check frappe exception types dynamically
    if hasattr(frappe, exc_name):
        if "NotFound" in exc_name or "DoesNotExist" in exc_name:
            status_code = 404
            error_type = "Resource not found"
            default_message = "The requested resource does not exist"
        elif "Permission" in exc_name:
            status_code = 403
            error_type = "Permission denied"
            default_message = "You don't have permission to access this resource"
        elif "Validation" in exc_name:
            status_code = 400
            error_type = "Validation error"
            default_message = "Invalid data provided"
        elif "Data" in exc_name:
            status_code = 400
            error_type = "Data error"
            default_message = "Invalid field or data structure"
        elif "Duplicate" in exc_name:
            status_code = 409
            error_type = "Duplicate entry"
            default_message = "Resource already exists"
        elif "Link" in exc_name:
            status_code = 400
            error_type = "Link validation error"
            default_message = "Invalid link reference"
    
    # Set HTTP status code
    frappe.response["http_status_code"] = status_code
    
    # Log error with operation context
    log_title = f"{operation_name} - {error_type}"
    frappe.log_error(frappe.get_traceback(), log_title)
    
    # Return structured error response
    return {
        "success": False,
        "error": error_type,
        "message": f"{default_message}: {str(e)}" if str(e) else default_message,
        "exception_type": exc_name
    }

@frappe.whitelist(allow_guest=True)
def get_po_printformat():
    try:
        # Check if DocType exists
        if not frappe.db.exists("DocType", "PO PrintFormat Master"):
            raise frappe.DoesNotExistError("PO PrintFormat Master DocType not found")
        
        # Validate user permissions
        if not frappe.has_permission("PO PrintFormat Master", "read"):
            raise frappe.PermissionError("Insufficient permissions for PO PrintFormat Master")
        
        # Get data
        po_pf = frappe.get_all(
            "PO PrintFormat Master", 
            fields=["name", "print_format_name"],
            limit_page_length=None
        )
        
        # Success response
        frappe.response["http_status_code"] = 200
        return {
            "success": True,
            "message": "Data retrieved successfully" if po_pf else "No records found",
            "data": po_pf,
            "count": len(po_pf)
        }
        
    except Exception as e:
        return handle_api_exception(e, "PO PrintFormat API")

@frappe.whitelist(allow_guest=True)
def po_download_track(data):
    try:
        # Parse JSON data if string
        if isinstance(data, str):
            import json
            data = json.loads(data)
        
        # Validate required fields
        if not data.get("po_name"):
            raise frappe.ValidationError("PO Name is required")
        
        # Check if PO exists
        if not frappe.db.exists("Purchase Order", data["po_name"]):
            raise frappe.DoesNotExistError(f"Purchase Order {data['po_name']} not found")
        
        # Check if track document already exists for this PO
        existing_doc = frappe.db.get_value("PO Track On Download", {"po_name": data["po_name"]}, "name")
        
        if existing_doc:
            # Update existing document
            doc = frappe.get_doc("PO Track On Download", existing_doc)
            if not frappe.has_permission("PO Track On Download", "write", doc):
                raise frappe.PermissionError("Insufficient permissions to update PO Track record")
        else:
            # Create new document
            if not frappe.has_permission("PO Track On Download", "create"):
                raise frappe.PermissionError("Insufficient permissions to create PO Track record")
            doc = frappe.new_doc("PO Track On Download")
            doc.po_name = data["po_name"]
        
        # Add child table records if provided
        if data.get("track_download"):
            for track_item in data["track_download"]:
                child_row = doc.append("track_download", {})
                child_row.datetime = frappe.utils.now()  # Auto-populate current time
                child_row.user_id = frappe.session.user  # Auto-populate current user
                child_row.print_format_type = track_item.get("print_format_type")
                
                # Validate print format exists
                if child_row.print_format_type and not frappe.db.exists("PO PrintFormat Master", child_row.print_format_type):
                    raise frappe.DoesNotExistError(f"Print Format {child_row.print_format_type} not found")
        
        # Save document
        if existing_doc:
            doc.save()
        else:
            doc.insert()
        frappe.db.commit()
        
        # Success response
        frappe.response["http_status_code"] = 200 if existing_doc else 201
        return {
            "success": True,
            "message": f"PO Track record {'updated' if existing_doc else 'created'} successfully",
            "data": {
                "name": doc.name,
                "po_name": doc.po_name,
                "track_count": len(doc.track_download),
                "action": "updated" if existing_doc else "created"
            }
        }
        
    except Exception as e:
        frappe.db.rollback()
        return handle_api_exception(e, "PO Download Track API")