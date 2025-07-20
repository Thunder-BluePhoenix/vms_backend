import frappe
import json


def get_state_data_safely(state_name):
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
            "country_name": state.country_name if hasattr(state, 'country_name') else None
        }
    except frappe.DoesNotExistError:
        frappe.log_error(f"State Master not found: {state_name}")
        return None
    except Exception as e:
        frappe.log_error(f"Error getting state data for {state_name}: {str(e)}")
        return None


def add_state_to_list(state_data, all_states):
    """Helper function to add state data to list if it's valid and not duplicate"""
    if state_data and state_data not in all_states:
        all_states.append(state_data)


@frappe.whitelist(allow_guest=True)
def get_states_for_gst(ref_no=None, vendor_onboarding=None):
    try:
        # Validate input
        if not vendor_onboarding:
            return {
                "status": "error",
                "message": "vendor_onboarding parameter is required",
                "data": []
            }
        
        # Get the vendor onboarding document
        vend_onboarding = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        all_states = []
        
        # Iterate through vendor company details
        for vend_comp in vend_onboarding.vendor_company_details:
            try:
                company = frappe.get_doc("Vendor Onboarding Company Details", vend_comp.vendor_company_details)
                
                # Handle office state (safely)
                if hasattr(company, 'state') and company.state:
                    office_state_data = get_state_data_safely(company.state)
                    add_state_to_list(office_state_data, all_states)
                
                # Handle manufacturing state (safely)
                if hasattr(company, 'manufacturing_state') and company.manufacturing_state:
                    manu_state_data = get_state_data_safely(company.manufacturing_state)
                    add_state_to_list(manu_state_data, all_states)
                
                # Iterate through multiple location table (safely)
                if hasattr(company, 'multiple_location_table') and company.multiple_location_table:
                    for comp_add in company.multiple_location_table:
                        if hasattr(comp_add, 'ma_state') and comp_add.ma_state:
                            state_data = get_state_data_safely(comp_add.ma_state)
                            add_state_to_list(state_data, all_states)
                            
            except frappe.DoesNotExistError:
                frappe.log_error(f"Vendor Onboarding Company Details not found: {vend_comp.vendor_company_details}")
                continue
            except Exception as e:
                frappe.log_error(f"Error processing company details {vend_comp.vendor_company_details}: {str(e)}")
                continue
        
        # Return the response
        return {
            "status": "success",
            "data": all_states,
            "count": len(all_states)
        }
        
    except frappe.DoesNotExistError:
        return {
            "status": "error",
            "message": f"Vendor Onboarding document not found: {vendor_onboarding}",
            "data": []
        }
    except Exception as e:
        frappe.log_error(f"Error in get_states_for_gst: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }