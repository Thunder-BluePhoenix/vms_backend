import frappe
import json
from frappe import _

@frappe.whitelist(allow_guest=True)
def hod_approval_check(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        pur_req = data.get("pur_req")
        user = data.get("user")
        is_approved = int(data.get("approve"))
        is_rejected = int(data.get("reject"))
        rejection_reason = data.get("   ")
        comments = data.get("comments")

        if is_approved and is_rejected:
            frappe.throw(_("Cannot approve and reject at the same time."))

        # Fetch cart details document
        pur_req_doc = frappe.get_doc("Purchase Requisition Webform", pur_req)
        
        if is_approved:
            pur_req_doc.hod_approved = 1
            pur_req_doc.hod_approval_status = "Approved"
            pur_req_doc.hod_approval_remarks = comments
        elif is_rejected:
            pur_req_doc.rejected = 1
            pur_req_doc.rejected_by = user
            pur_req_doc.hod_approval_status = "Rejected"
            pur_req_doc.reason_for_rejection = rejection_reason
        else:
            frappe.throw(_("Invalid request: either approve or reject must be set."))

        pur_req_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Purchase Requisition updated successfully.",
            "Purchase Requisition": pur_req_doc.name,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error updating Purchase Requisition")
        return {
            "status": "error",
            "message": "Failed to update Purchase Requisition.",
            "error": str(e),
        }
    

@frappe.whitelist(allow_guest=True)
def purchase_head_approval_check(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        pur_req = data.get("pur_req")
        user = data.get("user")
        is_approved = int(data.get("approve"))
        is_rejected = int(data.get("reject"))
        rejection_reason = data.get("rejected_reason")
        comments = data.get("comments")

        if is_approved and is_rejected:
            frappe.throw(_("Cannot approve and reject at the same time."))

        # Fetch cart details document
        pur_req_doc = frappe.get_doc("Purchase Requisition Webform", pur_req)
        
        if is_approved:
            pur_req_doc.purchase_head_approved = 1
            pur_req_doc.purchase_head_status = "Approved"
            pur_req_doc.purchase_head_approval_remarks = comments
        elif is_rejected:
            pur_req_doc.rejected = 1
            pur_req_doc.rejected_by = user
            pur_req_doc.purchase_head_status = "Rejected"
            pur_req_doc.reason_for_rejection = rejection_reason
        else:
            frappe.throw(_("Invalid request: either approve or reject must be set."))

        pur_req_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Purchase Requisition updated successfully.",
            "Purchase Requisition": pur_req_doc.name,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error updating Purchase Requisition")
        return {
            "status": "error",
            "message": "Failed to update Purchase Requisition.",
            "error": str(e),
        }
