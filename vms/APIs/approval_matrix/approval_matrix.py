
import frappe
from frappe import _
import json

def set_approval_matrix(doc, method):
    """Auto-assign appropriate approval matrix based on invoice type"""
    if doc.is_new():
        matrix = get_approval_matrix_for_invoice(doc.type)
        if matrix:
            doc.approval_matrix = matrix.name
            
            
            first_level = matrix.approval_levels[0]
            doc.current_approval_level = first_level.sequence
            doc.workflow_state = "Pending"
            doc.next_approver = first_level.approver_value
            doc.approval_status = "Pending"

def get_approval_matrix_for_invoice(invoice_type):
  
    matrix = frappe.get_list("Approval Matrix", 
        filters={
            "document_type": "Earth Invoice",
            "invoice_type": invoice_type,
            "is_active": 1
        }, limit=1)
    
    if matrix:
        return frappe.get_doc("Approval Matrix", matrix[0].name)
    
    
    default_matrix = frappe.get_list("Approval Matrix",
        filters={
            "document_type": "Earth Invoice", 
            "is_default": 1,
            "is_active": 1
        }, limit=1)
    
    if default_matrix:
        return frappe.get_doc("Approval Matrix", default_matrix[0].name)
    
    return None







@frappe.whitelist()
def process_single_approval(docname, action, comments=None):
   
    try:
        doc = frappe.get_doc("Earth Invoice", docname)
        result = process_approval_logic(doc, action, comments)
        
        return {
            "success": True,
            "message": f"Document {action.lower()} successfully",
            "workflow_state": doc.workflow_state,
            "next_approver": doc.next_approver
        }
    except Exception as e:
        frappe.log_error(f"Single approval error: {str(e)}")
        frappe.throw(str(e))



@frappe.whitelist()
def process_bulk_approval(docnames, action, comments=None):
   
    if isinstance(docnames, str):
        docnames = json.loads(docnames)
    
    results = {
        "success_count": 0,
        "error_count": 0,
        "results": [],
        "errors": []
    }
    
    for docname in docnames:
        try:
            doc = frappe.get_doc("Earth Invoice", docname)
            
            if not can_user_approve(doc, frappe.session.user):
                results["errors"].append({
                    "docname": docname,
                    "error": f"No permission to approve {docname}"
                })
                results["error_count"] += 1
                continue
            
           
            process_approval_logic(doc, action, comments)
            
            results["results"].append({
                "docname": docname,
                "status": "success",
                "workflow_state": doc.workflow_state,
                "message": f"{docname} {action.lower()} successfully"
            })
            results["success_count"] += 1
            
        except Exception as e:
            results["errors"].append({
                "docname": docname,
                "error": str(e)
            })
            results["error_count"] += 1
            frappe.log_error(f"Bulk approval error for {docname}: {str(e)}")
    
   
    frappe.db.commit()
    
    return results



def process_approval_logic(doc, action, comments=None):
    
    
    
    if not can_user_approve(doc, frappe.session.user):
        frappe.throw(f"You are not authorized to {action.lower()} this document")
    
    
    if not doc.approval_matrix:
        frappe.throw("No approval matrix assigned to this document")
    
    matrix = frappe.get_doc("Approval Matrix", doc.approval_matrix)
    current_level = get_current_approval_level(matrix, doc.current_approval_level)
    
    if not current_level:
        frappe.throw("Invalid approval level")
    
  
    doc.append("approval_history", {
        "sequence": current_level.sequence,
        "level_name": current_level.level_name,
        "approver": frappe.session.user,
        "action": action,
        "comments": comments or "",
        "approval_date": frappe.utils.now()
    })
    
    if action == "Approved":
        
        doc.workflow_state = current_level.status_when_approved or f"Approved by {current_level.level_name}"
        
        # Get next level
        next_level = get_next_approval_level(matrix, current_level.sequence)
        
        if next_level:
            
            doc.current_approval_level = next_level.sequence
            doc.next_approver = next_level.approver_value
            doc.approval_status = "Pending"
        else:
            # Final approval
            doc.approval_status = "Approved"
            doc.workflow_state = "Approved"
            doc.next_approver = ""
            doc.docstatus = 1  
            
    elif action == "Rejected":
        doc.workflow_state = current_level.status_on_reject or f"Rejected by {current_level.level_name}"
        doc.approval_status = "Rejected"
        doc.next_approver = ""
    
    doc.save()
    return doc


def get_current_approval_level(matrix, sequence):
   
    for level in matrix.approval_levels:
        if level.sequence == sequence:
            return level
    return None

def get_next_approval_level(matrix, current_sequence):
   
    for level in matrix.approval_levels:
        if level.sequence > current_sequence:
            return level
    return None

def can_user_approve(doc, user):
    if not doc.approval_matrix or doc.approval_status != "Pending":
        return False
        
    matrix = frappe.get_doc("Approval Matrix", doc.approval_matrix)
    current_level = get_current_approval_level(matrix, doc.current_approval_level)
    
    
    if not current_level:
        return False
    
    if current_level.approver_type == "Role":
        user_roles = frappe.get_roles(user)
        p
        return current_level.approver_value in user_roles
    elif current_level.approver_type == "User":
        return user == current_level.approver_value
    
    return False



@frappe.whitelist()
def get_pending_approvals_for_user():
  
    user = frappe.session.user
    
    
    from vms.APIs.approval_matrix.dynamic_permissions import get_pending_for_current_user
    
    pending_doc_names = get_pending_for_current_user()
    
    if not pending_doc_names:
        return []
    
    
    pending_docs = frappe.get_all("Earth Invoice",
        filters={"name": ["in", pending_doc_names]},
        fields=["name", "workflow_state", "type", "creation", "next_approver"]
    )
    
    return [{
        "name": doc.name,
        "workflow_state": doc.workflow_state,
        "invoice_type": doc.type,
        "creation": doc.creation,
        "next_approver": doc.next_approver
    } for doc in pending_docs]


@frappe.whitelist()
def check_user_can_approve(docname):
  
    try:
        doc = frappe.get_doc("Earth Invoice", docname)
        return can_user_approve(doc, frappe.session.user)
    except:
        return False

