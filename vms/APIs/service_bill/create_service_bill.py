import json

import frappe
from frappe.model.document import Document


# vms.APIs.service_bill.create_service_bill.create_service_bill
@frappe.whitelist()
def create_service_bill(data):
    try:
        service_bill_data = (
            json.loads(data)
            if isinstance(data, str)
            else data
        )

        # Start transaction
        frappe.db.begin()

        # Check if 'name' is provided to determine update vs create
        if service_bill_data.get('name'):
            # Update existing document
            doc_name = service_bill_data.pop('name')  # Remove name from data to avoid conflicts
            
            # Get existing document
            service_bill = frappe.get_doc("Service Bill", doc_name)
            
            # Update fields
            for key, value in service_bill_data.items():
                setattr(service_bill, key, value)
            
            # Save the updated document
            service_bill.save(ignore_permissions=True)
            
            action = "Updated"
        else:
            # Create new document
            service_bill = frappe.get_doc({"doctype": "Service Bill", **service_bill_data})
            service_bill.insert(ignore_permissions=True)
            
            action = "Created"

        # Commit changes
        frappe.db.commit()

        return {
            "message": "Success",
            "action": action,
            "service_bill": service_bill.name,
        }

    except frappe.DoesNotExistError:
        frappe.db.rollback()
        frappe.response.http_status_code = 404
        return {"message": "Failed", "error": "Document not found"}
    
    except Exception as e:
        frappe.db.rollback()  
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}