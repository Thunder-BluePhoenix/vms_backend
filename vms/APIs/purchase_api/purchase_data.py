import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_purchase_order_data(po_id):

    try:
        if not po_id:
            return {
                "status": "error",
                "message": "Missing required field: 'po_id'."
            }

       
        if not frappe.db.exists("Purchase Order", po_id):
            return {
                "status": "error",
                "message": f"Purchase Order '{po_id}' not found."
            }

        
        po_doc = frappe.get_doc("Purchase Order", po_id)
        
        
        po_data = po_doc.as_dict()
        
        #  Remove sensitive fields if needed
        # sensitive_fields = ['owner', 'modified_by', 'creation', 'modified']
        # for field in sensitive_fields:
        #     po_data.pop(field, None)
        
        return {
            "status": "success",
            "message": "Purchase Order data retrieved successfully.",
            "data": po_data
        }

    except frappe.PermissionError:
        return {
            "status": "error",
            "message": "Permission denied. You don't have access to this Purchase Order."
        }
    
    except frappe.DoesNotExistError:
        return {
            "status": "error",
            "message": f"Purchase Order '{po_id}' does not exist."
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_purchase_order_data: {str(e)}")
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }


