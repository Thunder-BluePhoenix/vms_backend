import frappe
import json

def get_state_data_safely(state_name, pincode=None):
    """Helper function to safely get state data and handle null/empty states"""
    if not state_name:
        return None
    
    try:
        state = frappe.get_doc("State Master", state_name)
        return {
            "state_code": state.state_code if hasattr(state, 'state_code') else None,
            "state_name": state.state_name if hasattr(state, 'state_name') else None,
            "sap_state_code": state.sap_state_code if hasattr(state, 'sap_state_code') else None,
            "custom_gst_state_code": state.custom_gst_state_code if hasattr(state, 'custom_gst_state_code') else None,
            "country_name": state.country_name if hasattr(state, 'country_name') else None,
            "name": state.name,
            "pincode": pincode
        }
    except frappe.DoesNotExistError:
        frappe.log_error(f"State Master not found: {state_name}")
        return None
    except Exception as e:
        frappe.log_error(f"Error getting state data for {state_name}: {str(e)}")
        return None


def add_state_to_list(state_data, all_states):
    """Helper function to add state data to list if it's valid and not duplicate"""
    if state_data:
        # Check for duplicate based on state name and pincode combination
        existing = next((s for s in all_states if s.get("name") == state_data.get("name") and s.get("pincode") == state_data.get("pincode")), None)
        if not existing:
            all_states.append(state_data)


@frappe.whitelist(allow_guest=True)
def get_states_for_gst(ref_no=None, vendor_onboarding=None):
    try:
        # Validate input
        if not vendor_onboarding:
            raise frappe.ValidationError("vendor_onboarding parameter is required")
        
        # Check if vendor onboarding exists
        if not frappe.db.exists("Vendor Onboarding", vendor_onboarding):
            raise frappe.DoesNotExistError(f"Vendor Onboarding {vendor_onboarding} not found")
        
        # Get the vendor onboarding document
        vend_onboarding = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        all_states = []
        
        # Iterate through vendor company details
        for vend_comp in vend_onboarding.vendor_company_details:
            try:
                company = frappe.get_doc("Vendor Onboarding Company Details", vend_comp.vendor_company_details)
                
                # Handle office state with pincode
                if hasattr(company, 'state') and company.state:
                    office_state_data = get_state_data_safely(company.state, company.pincode if hasattr(company, 'pincode') else None)
                    add_state_to_list(office_state_data, all_states)
                
                # Handle manufacturing state with pincode
                if hasattr(company, 'manufacturing_state') and company.manufacturing_state:
                    manu_state_data = get_state_data_safely(company.manufacturing_state, company.manufacturing_pincode if hasattr(company, 'manufacturing_pincode') else None)
                    add_state_to_list(manu_state_data, all_states)
                
                # Iterate through multiple location table
                if hasattr(company, 'multiple_location_table') and company.multiple_location_table:
                    for comp_add in company.multiple_location_table:
                        if hasattr(comp_add, 'ma_state') and comp_add.ma_state:
                            state_data = get_state_data_safely(comp_add.ma_state, comp_add.ma_pincode if hasattr(comp_add, 'ma_pincode') else None)
                            add_state_to_list(state_data, all_states)
                            
            except frappe.DoesNotExistError:
                frappe.log_error(f"Vendor Onboarding Company Details not found: {vend_comp.vendor_company_details}")
                continue
            except Exception as e:
                frappe.log_error(f"Error processing company details {vend_comp.vendor_company_details}: {str(e)}")
                continue
        
        # Success response
        frappe.response["http_status_code"] = 200
        return {
            "success": True,
            "message": "States data retrieved successfully",
            "data": all_states,
            "count": len(all_states)
        }
        
    except Exception as e:
        return handle_api_exception(e, "Get States for GST API")
    





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

