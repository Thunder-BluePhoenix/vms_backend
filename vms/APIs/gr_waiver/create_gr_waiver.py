import json

import frappe
from frappe.model.document import Document


# vms.APIs.gr_waiver.create_gr_waiver.create_gr_waiver
@frappe.whitelist()
def create_gr_waiver(data):
    try:
        gr_waiver_data = (
            json.loads(data)
            if isinstance(data, str)
            else data
        )

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
            gr_waiver = frappe.get_doc({"doctype": "GR Waiver", **gr_waiver_data})
            gr_waiver.insert(ignore_permissions=True)
            
            action = "Created"

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
        return {"message": "Failed", "error": "Document not found"}
    
    except Exception as e:
        frappe.db.rollback()  
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}