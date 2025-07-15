import frappe
from frappe.utils.file_manager import save_file
import base64
import os




def get_context(context):
	# do your magic here
	pass




# @frappe.whitelist(allow_guest=True)
# def simple_file_upload():
#     """
#     Simple file upload for webforms
#     """
#     try:
#         files = frappe.request.files
#         if not files or 'file' not in files:
#             return {"success": False, "message": "No file uploaded"}
        
#         file_obj = files['file']
        
#         # Set permissions flags
#         frappe.flags.ignore_permissions = True
        
#         # Save file using Frappe's built-in method
#         # from frappe.utils.file_manager import save_file
        
#         file_doc = save_file(
#             file_obj.filename,
#             file_obj.read(),
#             dt="Supplier QMS Assessment Form",  # Your doctype
#             dn=None,
#             folder="Home/Attachments",
#             decode=False,
#             is_private=0
#         )
        
#         return {
#             "success": True,
#             "file_url": file_doc.file_url,
#             "file_name": file_doc.file_name,
#             "name": file_doc.name
#         }
        
#     except Exception as e:
#         frappe.log_error(str(e))
#         return {"success": False, "message": str(e)}
    





# import frappe
# from frappe.utils.file_manager import save_file
# import os

# @frappe.whitelist(allow_guest=True)
# def bypass_upload_file():
#     """
#     Completely bypass Frappe's permission system for file uploads
#     """
#     try:
#         # Force administrator privileges temporarily
#         original_user = frappe.session.user
#         frappe.set_user("Administrator")
#         frappe.flags.ignore_permissions = True
        
#         # Get uploaded file
#         files = frappe.request.files
#         if not files or 'file' not in files:
#             frappe.throw("No file uploaded")
        
#         file_obj = files['file']
#         content = file_obj.read()
#         filename = file_obj.filename
        
#         # Save file with full permissions
#         file_doc = save_file(
#             filename,
#             content,
#             dt=frappe.form_dict.get('doctype'),
#             dn=frappe.form_dict.get('docname'), 
#             folder=frappe.form_dict.get('folder', 'Home/Attachments'),
#             decode=False,
#             is_private=int(frappe.form_dict.get('is_private', 0)),
#             df=frappe.form_dict.get('docfield')
#         )
        
#         frappe.db.commit()
        
#         # Restore original user
#         frappe.set_user(original_user)
        
#         return {
#             "file_name": file_doc.file_name,
#             "file_url": file_doc.file_url,
#             "name": file_doc.name
#         }
        
#     except Exception as e:
#         # Restore original user in case of error
#         if 'original_user' in locals():
#             frappe.set_user(original_user)
        
#         frappe.log_error(f"File upload bypass error: {str(e)}")
#         frappe.throw(f"File upload failed: {str(e)}")






import frappe
from frappe import _
import json




@frappe.whitelist(allow_guest=True)
def check_supplier_qms_filled(vendor_onboarding):
    if not vendor_onboarding:
        frappe.throw(_("vendor_onboarding is required."))

    existing = frappe.get_all(
        'Supplier QMS Assessment Form',
        filters={'vendor_onboarding': vendor_onboarding},
        limit=1
    )

    return {
        'exists': len(existing) > 0
    }




# Add this to your Supplier QMS Assessment Form doctype .py file
# Or create a separate Python file for web form handling




@frappe.whitelist(allow_guest=True)
def process_qms_web_form(doc_data):
    """
    Process the web form data and populate table multiselect fields
    """
    try:
        # Parse the document data if it's a string
        if isinstance(doc_data, str):
            doc_data = json.loads(doc_data)
        
        # Create the main document
        doc = frappe.new_doc("Supplier QMS Assessment Form")
        
        # Set basic fields first
        for field, value in doc_data.items():
            if field not in ['quality_control_system_checkboxes', 'have_documentsprocedure_checkboxes', 
                           'if_yes_for_prior_notification_checkboxes', 'details_of_batch_records_checkboxes']:
                doc.set(field, value)
        
        # Process checkbox fields and populate table multiselect
        process_checkbox_field(doc, doc_data, 'quality_control_system', 'quality_control_system_checkboxes', 'QMS Quality Control', 'value')
        process_checkbox_field(doc, doc_data, 'have_documentsprocedure', 'have_documentsprocedure_checkboxes', 'QMS Procedure Doc', 'value')
        process_checkbox_field(doc, doc_data, 'if_yes_for_prior_notification', 'if_yes_for_prior_notification_checkboxes', 'QMS Prior Notification Table', 'value')
        process_checkbox_field(doc, doc_data, 'details_of_batch_records', 'details_of_batch_records_checkboxes', 'QMS Batch Record Table', 'value')
        process_checkbox_field(doc, doc_data, 'inspection_reports', 'inspection_reports_checkboxes', 'QMS Inspection Report Table', 'value')
        
        # Save the document
        doc.insert()
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "QMS Assessment Form submitted successfully",
            "name": doc.name
        }
        
    except Exception as e:
        frappe.log_error(f"Error processing QMS web form: {str(e)}")
        return {
            "status": "error", 
            "message": f"Error submitting form: {str(e)}"
        }

def process_checkbox_field(doc, doc_data, table_field, checkbox_field, child_doctype, child_field):
    """
    Process checkbox data and populate table multiselect field
    """
    if checkbox_field in doc_data and doc_data[checkbox_field]:
        selected_values = doc_data[checkbox_field]
        
        # Handle different input formats
        if isinstance(selected_values, str):
            # If it's a string, try to parse as JSON or split by newlines/commas
            try:
                selected_values = json.loads(selected_values)
            except:
                selected_values = [v.strip() for v in selected_values.replace('\n', ',').split(',') if v.strip()]
        
        # Clear existing rows
        doc.set(table_field, [])
        
        # Add new rows for each selected value
        for value in selected_values:
            if value:  # Skip empty values
                child_doc = {
                    "doctype": child_doctype,
                    child_field: value
                }
                doc.append(table_field, child_doc)

# Alternative method: Override the web form's accept method
@frappe.whitelist(allow_guest=True)
def custom_web_form_accept(**kwargs):
    """
    Custom web form submission handler
    """
    try:
        # Get form data
        form_data = frappe.local.form_dict
        
        # Extract checkbox data
        checkbox_data = {}
        for key in list(form_data.keys()):
            if key.endswith('_checkboxes'):
                checkbox_data[key] = form_data.pop(key)
        
        # Create document with regular fields
        doc = frappe.new_doc("Supplier QMS Assessment Form")
        for field, value in form_data.items():
            if field not in ['cmd', 'csrf_token']:
                doc.set(field, value)
        
        # Process checkbox data
        if 'quality_control_system_checkboxes' in checkbox_data:
            populate_table_field(doc, 'quality_control_system', checkbox_data['quality_control_system_checkboxes'], 'QMS Quality Control')
            
        if 'have_documentsprocedure_checkboxes' in checkbox_data:
            populate_table_field(doc, 'have_documentsprocedure', checkbox_data['have_documentsprocedure_checkboxes'], 'QMS Procedure Doc')
            
        if 'if_yes_for_prior_notification_checkboxes' in checkbox_data:
            populate_table_field(doc, 'if_yes_for_prior_notification', checkbox_data['if_yes_for_prior_notification_checkboxes'], 'QMS Prior Notification Table')
            
        if 'details_of_batch_records_checkboxes' in checkbox_data:
            populate_table_field(doc, 'details_of_batch_records', checkbox_data['details_of_batch_records_checkboxes'], 'QMS Batch Record Table')
        
        # Save document
        doc.insert()
        frappe.db.commit()
        
        return {"status": "success", "name": doc.name}
        
    except Exception as e:
        frappe.log_error(f"Custom web form error: {str(e)}")
        frappe.throw(f"Error submitting form: {str(e)}")

def populate_table_field(doc, field_name, selected_values, child_doctype):
    """
    Populate a table multiselect field with selected checkbox values
    """
    if not selected_values:
        return
        
    # Handle string input
    if isinstance(selected_values, str):
        selected_values = [v.strip() for v in selected_values.split(',') if v.strip()]
    
    # Clear existing entries
    doc.set(field_name, [])
    
    # Add selected values
    for value in selected_values:
        if value:
            doc.append(field_name, {
                "doctype": child_doctype,
                "value": value
            })

# Doctype hooks - add to your doctype's .py file
# class SupplierQMSAssessmentForm(Document):
#     def before_save(self):
#         """
#         Process any checkbox data before saving
#         """
#         # This will run on normal saves too, so be careful
#         pass
    
#     def on_update(self):
#         """
#         Called after document is saved
#         """
#         pass

# Web form validation method
@frappe.whitelist(allow_guest=True)
def validate_qms_form(doc_data):
    """
    Validate form data before submission
    """
    try:
        # Add any validation logic here
        required_fields = ['vendor_onboarding', 'organization_name']
        
        for field in required_fields:
            if not doc_data.get(field):
                return {"valid": False, "message": f"{field} is required"}
        
        return {"valid": True, "message": "Validation passed"}
        
    except Exception as e:
        return {"valid": False, "message": f"Validation error: {str(e)}"}











import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_vendor_company_data(vendor_onboarding):
    """
    Custom API to get vendor onboarding data and associated company codes.
    Handles both single company and multiple companies scenarios.
    """
    try:
        # Validate vendor onboarding parameter
        if not vendor_onboarding:
            return {
                "success": False,
                "message": "Vendor onboarding ID is required"
            }
        
        # Check if vendor onboarding document exists
        if not frappe.db.exists("Vendor Onboarding", vendor_onboarding):
            return {
                "success": False,
                "message": "Vendor onboarding document not found"
            }
        
        # Get vendor onboarding document
        vendor_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        
        company_codes = []
        company_details = []
        
        # Check if registered for multiple companies
        if vendor_doc.registered_for_multi_companies:
            # Handle multiple companies
            if hasattr(vendor_doc, 'multiple_company') and vendor_doc.multiple_company:
                for company_row in vendor_doc.multiple_company:
                    if company_row.company:
                        company_data = get_company_code(company_row.company)
                        if company_data["success"]:
                            company_codes.append(company_data["company_code"])
                            company_details.append({
                                "name": company_row.company,
                                "code": company_data["company_code"]
                            })
                        else:
                            frappe.log_error(
                                f"Could not fetch company code for {company_row.company}",
                                "Company Code Fetch Error"
                            )
            else:
                return {
                    "success": False,
                    "message": "No companies found in multiple company table"
                }
        else:
            # Handle single company
            if vendor_doc.company_name:
                company_data = get_company_code(vendor_doc.company_name)
                if company_data["success"]:
                    company_codes.append(company_data["company_code"])
                    company_details.append({
                        "name": vendor_doc.company_name,
                        "code": company_data["company_code"]
                    })
                else:
                    return {
                        "success": False,
                        "message": f"Could not fetch company code for {vendor_doc.company_name}"
                    }
            else:
                return {
                    "success": False,
                    "message": "No company name found in vendor onboarding"
                }
        
        # Return successful response
        return {
            "success": True,
            "data": {
                "vendor_onboarding": vendor_onboarding,
                "registered_for_multi_companies": vendor_doc.registered_for_multi_companies,
                "company_codes": company_codes,
                "company_details": company_details,
                "total_companies": len(company_details)
            }
        }
        
    except Exception as e:
        frappe.log_error(
            f"Error in get_vendor_company_data: {str(e)}",
            "Vendor Company Data API Error"
        )
        return {
            "success": False,
            "message": f"An error occurred while fetching vendor company data: {str(e)}"
        }

def get_company_code(company_name):
    """
    Helper function to get company code for a given company name.
    """
    try:
        if not company_name:
            return {
                "success": False,
                "message": "Company name is required"
            }
        
        # Check if company exists
        if not frappe.db.exists("Company", company_name):
            return {
                "success": False,
                "message": f"Company '{company_name}' not found"
            }
        
        # Get company code
        company_code = frappe.db.get_value("Company", company_name, "company_code")
        
        if not company_code:
            return {
                "success": False,
                "message": f"No company code found for '{company_name}'"
            }
        
        return {
            "success": True,
            "company_code": company_code
        }
        
    except Exception as e:
        frappe.log_error(
            f"Error in get_company_code for {company_name}: {str(e)}",
            "Company Code Fetch Error"
        )
        return {
            "success": False,
            "message": f"Error fetching company code: {str(e)}"
        }