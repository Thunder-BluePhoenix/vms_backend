import json

import frappe
from frappe.model.document import Document

# vms.APIs.gr_waiver.create_gr_waiver.create_gr_waiver
@frappe.whitelist(methods=["POST", "PUT"])
def create_gr_waiver(data=None):
    
    try:
        # Handle different data input formats
        if data:
            # If data is provided as a parameter (JSON string or dict)
            gr_waiver_data = json.loads(data) if isinstance(data, str) else data
        else:
            # If data is sent as form data, get from frappe.form_dict
            gr_waiver_data = frappe.form_dict.copy()
            
            # Remove standard Frappe parameters
            gr_waiver_data.pop('cmd', None)
            gr_waiver_data.pop('data', None)
        
        # Convert string representations of lists/dicts if needed
        for key, value in gr_waiver_data.items():
            if isinstance(value, str) and value.startswith(('[', '{')):
                try:
                    gr_waiver_data[key] = json.loads(value)
                except json.JSONDecodeError:
                    pass  # Keep as string if not valid JSON

        files_to_attach = {}
        if frappe.request and frappe.request.files:
            for fieldname, file_obj in frappe.request.files.items():
                if file_obj and file_obj.filename:
                    files_to_attach[fieldname] = file_obj
        
        # Start transaction
        frappe.db.begin()
        
        # Check if 'name' is provided to determine update vs create
        if gr_waiver_data.get('name'):
            # Update existing document
            doc_name = gr_waiver_data.pop('name')
            
            # Get existing document
            gr_waiver = frappe.get_doc("GR Waiver", doc_name)
            
            # Update fields
            for key, value in gr_waiver_data.items():
                setattr(gr_waiver, key, value)
            
            # Save the updated document
            gr_waiver.save(ignore_permissions=True)
            action = "Updated"
        else:
            # Create new document
            gr_waiver = frappe.get_doc({
                "doctype": "GR Waiver",
                **gr_waiver_data
            })
            gr_waiver.insert(ignore_permissions=True)
            action = "Created"


        attached_files = []
        for fieldname, file_obj in files_to_attach.items():
            try:
                # Save the file
                file_doc = frappe.get_doc({
                    "doctype": "File",
                    "file_name": file_obj.filename,
                    "attached_to_doctype": "GR Waiver",
                    "attached_to_name": gr_waiver.name,
                    "attached_to_field": fieldname,
                    "content": file_obj.read(),
                    "is_private": 1  
                })
                file_doc.save(ignore_permissions=True)
                
                # Update the attach field in the document
                setattr(gr_waiver, fieldname, file_doc.file_url)
                
                attached_files.append({
                    "fieldname": fieldname,
                    "file_url": file_doc.file_url,
                    "file_name": file_doc.file_name
                })
            except Exception as file_error:
                frappe.log_error(
                    f"Error attaching file {file_obj.filename}: {str(file_error)}",
                    "GR Waiver File Attachment Error"
                )
        
        # Save again if files were attached
        if attached_files:
            gr_waiver.save(ignore_permissions=True)
        
        # Commit changes
        frappe.db.commit()
        
        return {
            "message": "Success",
            "action": action,
            "gr_waiver": gr_waiver.name,
        }
    
    except frappe.DoesNotExistError:
        frappe.db.rollback()
        frappe.response.http_status_code = 404
        return {
            "message": "Failed",
            "error": "Document not found"
        }
    
    except frappe.ValidationError as e:
        frappe.db.rollback()
        frappe.response.http_status_code = 400
        return {
            "message": "Failed",
            "error": str(e)
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "GR Waiver Creation Error")
        return {
            "message": "Failed",
            "error": str(e)
        }