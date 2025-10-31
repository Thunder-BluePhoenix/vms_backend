import frappe
from functools import wraps

def api_response_handler(func):
    """
    Decorator to automatically handle API responses and set HTTP status codes
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Auto-set HTTP status code if not already set
            if not frappe.local.response.get("http_status_code"):
                if isinstance(result, dict):
                    # Check for success/error status
                    if result.get("status") == "success" or result.get("success") == True:
                        frappe.local.response.http_status_code = 200
                    elif result.get("status") == "error" or result.get("success") == False:
                        frappe.local.response.http_status_code = 400
                else:
                    # Default to 200 if result exists
                    frappe.local.response.http_status_code = 200
            
            return result
            
        except Exception as e:
            return handle_api_exception(e, func.__name__)
    
    return wrapper


def handle_api_exception(e, operation_name="API Operation"):
    """Dynamic exception handler for Frappe APIs"""
    
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
    frappe.local.response.http_status_code = status_code
    
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



import frappe

def auto_set_status_codes(response):
    """
    Ensures every API response includes the HTTP status code both
    in frappe.response and in the actual JSON payload sent to the client.
    """

    try:
        # Determine the status code (default 200 if not set)
        status_code = getattr(frappe.response, "http_status_code", 200)

        # Make sure frappe.response is a dictionary (JSON response)
        if isinstance(frappe.response, dict):
            # Add or update the HTTP status code
            frappe.response["http_status_code"] = status_code

            # Auto-define success/error based on the code
            if status_code >= 400:
                frappe.response["status"] = "error"
            else:
                frappe.response.setdefault("status", "success")

            # Ensure the client-side response (actual output) includes code
            if isinstance(response, dict):
                response["http_status_code"] = status_code
                response["status"] = frappe.response["status"]

        # Return the modified response object
        return response

    except Exception as e:
        frappe.log_error(f"auto_set_status_codes error: {str(e)}")
        return response
