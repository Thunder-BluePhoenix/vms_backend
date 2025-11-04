import frappe
import json
from frappe import _

# Not in Used
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
    
# this api is used for purchase team Approval
@frappe.whitelist(allow_guest=True)
def sent_approval_to_purchase_team(name):
    try:
        if not name:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "'name' is required."
            }

        doc = frappe.get_doc("Purchase Requisition Webform", name)

        # sending email to Purchase team for Approval
        employee_name = frappe.get_value("Employee", {"user_id": doc.requisitioner}, "full_name")

        pur_team_email = None
        pur_team_name = None
        pur_team = None

        if doc.cart_details_id:
            cart_details = frappe.get_doc("Cart Details", doc.cart_details_id)
            pur_team = cart_details.dedicated_purchase_team

        if pur_team:
            pur_team_email = pur_team
            pur_team_name = frappe.get_value("Employee", {"user_id": pur_team}, "full_name")

            if pur_team_email:
                subject = f"New Purchase Requisition Raised by {employee_name}"
                message = f"""
                    <p>Dear {pur_team_name},</p>		

                    <p>A new <b>Purchase Requisition</b> has been raised by <b>{employee_name}</b>. Kindly review the details and take the necessary action.</p>

                    <p>Thank you.<br>
                    Best regards,<br>
                    VMS Team</p>
                """

                frappe.custom_sendmail(
                    recipients=pur_team_email,
                    subject=subject,
                    message=message,
                    now=True
                )

                frappe.db.set_value("Purchase Requisition Webform", name, "mail_sent_to_purchase_team", 1)

        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": f"Mail sent to Purchase Team Successfully for Purchase Requisition '{name}'."
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Submit PR Form Error")
        return {
            "status": "error",
            "message": "Failed to submit the Purchase Requisition Webform.",
            "error": str(e)
        }
    

# Update the PR, Approved and sent to sap
@frappe.whitelist(allow_guest=True)
def purchase_team_approval_check(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        pur_req = data.get("name")
        user = frappe.session.user
        is_approved = int(data.get("approve"))
        # is_rejected = int(data.get("reject"))
        # rejection_reason = data.get("rejected_reason")
        # comments = data.get("comments")

        # if is_approved and is_rejected:
        #     frappe.throw(_("Cannot approve and reject at the same time."))

        # Fetch cart details document
        pur_req_doc = frappe.get_doc("Purchase Requisition Webform", pur_req)
        
        if is_approved:
            pur_req_doc.purchase_team_approved = 1
            pur_req_doc.purchase_team_status = "Approved"
            pur_req_doc.purchase_team_approval = user
            pur_req_doc.purchase_team_approval_remarks = "Approved By Purchase Team"
            pur_req_doc.form_is_submitted = 1
        
        # elif is_rejected:
        #     pur_req_doc.rejected = 1
        #     pur_req_doc.rejected_by = user
        #     pur_req_doc.purchase_head_status = "Rejected"
        #     pur_req_doc.reason_for_rejection = rejection_reason

        else:
            frappe.throw(_("Invalid request: approve must be set."))


        employee_name = frappe.get_value("Employee", {"user_id": pur_req_doc.requisitioner}, "full_name")
        subject = f"Purchase Requisition has been Approved by Purchase Team"
		
        message = f"""
			<p>Dear {employee_name},</p>		

			<p>Your <b>Purchase Requisition {pur_req_doc.name}</b> has been approved by the <b>Purchase Team</b>. Kindly review the details and take the necessary action.</p>

			<p>Thank you.<br>
			Best regards,<br>
			VMS Team</p>
		"""

		
        frappe.custom_sendmail(
			recipients=[pur_req_doc.requisitioner],
			subject=subject,
			message=message,
			now=True
		)
		
        pur_req_doc.ack_mail_to_user = 1

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
