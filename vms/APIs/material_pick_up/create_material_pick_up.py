import json

import frappe
from frappe.model.document import Document
from frappe import _


# vms.APIs.material_pick_up.create_material_pick_up.create_material_pick_up
@frappe.whitelist()
def create_material_pick_up():
    try:
        form_data = frappe.form_dict
        files = frappe.request.files
        
        # Support both JSON and direct form fields
        if form_data.get('data'):
            # If data is sent as JSON string
            material_pick_up_data = json.loads(form_data.get('data'))
        else:
            # If data is sent as direct form fields
            material_pick_up_data = {}
            for key, value in form_data.items():
                if key not in ['cmd', 'attachment_names']:
                    material_pick_up_data[key] = value
        
        frappe.db.begin()

        # Check if 'name' is provided to determine update vs create
        doc_name = material_pick_up_data.get('name')
        
        if doc_name and frappe.db.exists("Material Pickup Request", doc_name):
            # Update existing document
            material_pick_up_data.pop('name')
            material_pick_up = frappe.get_doc("Material Pickup Request", doc_name)
            
            # Update fields (excluding child table)
            for key, value in material_pick_up_data.items():
                if key != 'attachment':
                    setattr(material_pick_up, key, value)
            
            action = "Updated"
        else:
            # Create new document (remove 'name' if it exists to let Frappe generate it)
            if 'name' in material_pick_up_data:
                material_pick_up_data.pop('name')
                
            material_pick_up = frappe.get_doc({
                "doctype": "Material Pickup Request",
                **{k: v for k, v in material_pick_up_data.items() if k != 'attachment'}
            })
            material_pick_up.insert(ignore_permissions=True)
            action = "Created"

        # Handle file attachments
        if files:
            # Process each uploaded file
            for file_key in files:
                uploaded_file = files[file_key]
                
                if uploaded_file and uploaded_file.filename:
                    # Save file
                    file_doc = save_file(
                        fname=uploaded_file.filename,
                        content=uploaded_file.stream.read(),
                        dt="Material Pickup Request",
                        dn=material_pick_up.name,
                        is_private=1
                    )
                    
                    # Add to child table
                    material_pick_up.append('attachment', {
                        'name1': file_doc.file_name,
                        'attachment_name': file_doc.file_url
                    })
        
        # Save the document
        material_pick_up.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "message": "Success",
            "action": action,
            "material_pick_up": material_pick_up.name,
            "attachments": [
                {
                    'attach': att.name1,
                    'attachment_name': att.attachment_name
                } for att in material_pick_up.get('attachment', [])
            ]
        }

    except frappe.DoesNotExistError:
        frappe.db.rollback()
        frappe.response.http_status_code = 404
        return {"message": "Failed", "error": "Document not found"}
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), _("Material Pickup Error"))
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}



def save_file(fname, content, dt, dn, is_private=1):
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": fname,
        "attached_to_doctype": dt,
        "attached_to_name": dn,
        "is_private": is_private,
        "content": content
    })
    file_doc.save(ignore_permissions=True)
    return file_doc