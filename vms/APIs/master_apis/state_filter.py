import frappe
import json


@frappe.whitelist(allow_guest=True)
def get_states_for_gst(ref_no=None, vendor_onboarding=None):
    try:
        # Get the vendor onboarding document
        vend_onboarding = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        all_states = []
        
        # Iterate through vendor company details
        for vend_comp in vend_onboarding.vendor_company_details:
            company = frappe.get_doc("Vendor Onboarding Company Details", vend_comp.vendor_company_details)
            
            # Iterate through multiple location table
            for comp_add in company.multiple_location_table:
                state = frappe.get_doc("State Master", comp_add.ma_state)
                
                # Create state dictionary with all required fields
                state_data = {
                    "state_code": state.state_code,
                    "state_name": state.state_name,
                    "sap_state_code": state.sap_state_code,
                    "custom_gst_state_code": state.custom_gst_state_code,
                    "country_name": state.country_name
                }
                
                # Add to list if not already present (to avoid duplicates)
                if state_data not in all_states:
                    all_states.append(state_data)
        
        # Return the response
        return {
            "status": "success",
            "data": all_states,
            "count": len(all_states)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_states_for_gst: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }




