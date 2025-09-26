import json

import frappe
from frappe.model.document import Document


# vms.APIs.shipment_status.create_shipment_status.create_shipment_status
@frappe.whitelist()
def create_shipment_status(data):
    try:
        shipment_status_data = (
            json.loads(data)
            if isinstance(data, str)
            else data
        )

        # Start transaction
        frappe.db.begin()

        # Check if 'name' is provided to determine update vs create
        if shipment_status_data.get('name'):
            # Update existing document
            doc_name = shipment_status_data.pop('name')  # Remove name from data to avoid conflicts
            
            # Get existing document
            shipment_status = frappe.get_doc("Shipment Status", doc_name)
            
            # Update fields
            for key, value in shipment_status_data.items():
                setattr(shipment_status, key, value)
            
            # Save the updated document
            shipment_status.save(ignore_permissions=True)
            
            action = "Updated"
        else:
            # Create new document
            shipment_status = frappe.get_doc({"doctype": "Shipment Status", **shipment_status_data})
            shipment_status.insert(ignore_permissions=True)
            
            action = "Created"

        # Commit changes
        frappe.db.commit()

        return {
            "message": "Success",
            "action": action,
            "shipment_status": shipment_status.name,
        }

    except frappe.DoesNotExistError:
        frappe.db.rollback()
        frappe.response.http_status_code = 404
        return {"message": "Failed", "error": "Document not found"}
    
    except Exception as e:
        frappe.db.rollback()  # Rollback changes in case of error
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}