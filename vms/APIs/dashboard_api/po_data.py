import frappe
import json


@frappe.whitelist(allow_guest = True)
def get_po():
    all_po = frappe.get_all("Purchase Order", fields ="*", order_by = "modified desc")
    return all_po



@frappe.whitelist(allow_guest = True)
def get_po_details(po_name):
    try:
        po = frappe.get_doc("Purchase Order", po_name)
        po_dict = po.as_dict()
        
      
        po_dict["requisitioner_email"] = None
        po_dict["requisitioner_name"] = None
        
        pr_no = po.get("ref_pr_no")
        
        if pr_no:
            
            pr_form_name = frappe.db.get_value("Purchase Requisition Form", {"sap_pr_code": pr_no}, "name")
            
            if pr_form_name:
                pr_doc = frappe.get_doc("Purchase Requisition Form", pr_form_name)
                purchase_requisitioner = pr_doc.get("requisitioner")
                
                if purchase_requisitioner:
                    
                    po_dict["requisitioner_email"] = purchase_requisitioner
                    
                    
                    requisitioner_name = frappe.get_value("User", purchase_requisitioner, "first_name") or frappe.get_value("User", purchase_requisitioner, "full_name")
                    po_dict["requisitioner_name"] = requisitioner_name
        
        return po_dict
        
    except frappe.DoesNotExistError:
        frappe.throw(f"Purchase Order '{po_name}' not found")
    except Exception as e:
        frappe.log_error(f"Error in get_po_details: {str(e)}")
        frappe.throw(f"An error occurred while fetching PO details: {str(e)}")


@frappe.whitelist(allow_guest = True)
def filtering_data(data):
    pass