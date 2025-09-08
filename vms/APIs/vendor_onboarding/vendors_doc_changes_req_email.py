import frappe
from vms.utils.custom_send_mail import custom_sendmail

# Send the Emails to Purchase, Accounts team for approval of Changes in Vendor Document details
# and its next part is present in vendor onboarding.py file (main file). Below function contains both Purchase and Account Team flow.

@frappe.whitelist(allow_guest=True)
def send_doc_change_req_email(ven_onb, remarks):
    try:
        if not ven_onb:
            return {
                "status": "error",
                "message": "Vendor Onboarding ID not found"
            }

        http_server = frappe.conf.get("backend_http")
        vendor_onboarding = frappe.get_doc("Vendor Onboarding", ven_onb)
        vendor_master = frappe.get_doc("Vendor Master", vendor_onboarding.ref_no)

        register_by = frappe.db.get_value(
            "User",
            {"name": vendor_onboarding.registered_by},
            "full_name"
        )

        if vendor_onboarding.register_by_account_team == 0:
            subject = f"Change Request for Vendor: {vendor_master.vendor_name}"

            # Generate action URLs
            allow_url = f"{http_server}/api/method/vms.APIs.vendor_onboarding.vendors_doc_changes_req_email.set_approval_check?vendor_onboarding={vendor_onboarding.name}&action=allow"
            reject_url = f"{http_server}/api/method/vms.APIs.vendor_onboarding.vendors_doc_changes_req_email.set_approval_check?vendor_onboarding={vendor_onboarding.name}&action=reject"

            # Email body
            message = f"""
                <p>Dear {register_by},</p>
                <p>
                    The vendor <b>{vendor_master.vendor_name}</b> has requested changes to its details.  
                    Kindly review the request and take appropriate action by clicking one of the buttons below:
                </p>
                <p>
                    <a href="{allow_url}" style="background-color:green;color:white;padding:8px 16px;
                    text-decoration:none;border-radius:4px;">Allow</a>
                    
                    &nbsp;&nbsp;
                    
                    <a href="{reject_url}" style="background-color:red;color:white;padding:8px 16px;
                    text-decoration:none;border-radius:4px;">Reject</a>
                </p>
                <br>
                <p><b>Remarks from vendor:</b> {remarks}</p>
                <p>Thank you,<br>Vendor Management System</p>
            """

            custom_sendmail(
                recipients=[vendor_onboarding.registered_by],
                cc=[vendor_onboarding.accounts_t_approval],
                subject=subject,
                message=message,
                now=True
            )

            frappe.db.set_value(
                "Vendor Onboarding",
                vendor_onboarding.name,
                {
                    "vendor_remarks": remarks,
                    "change_details_req_mail_sent_to_purchase_team": 1
                }
            )

        elif vendor_onboarding.register_by_account_team == 1:
            subject = f"Change Request for Vendor: {vendor_master.vendor_name}"

            # Generate action URLs
            allow_url = f"{http_server}/api/method/vms.APIs.vendor_onboarding.vendors_doc_changes_req_email.set_approval_check?vendor_onboarding={vendor_onboarding.name}&action=allow"
            reject_url = f"{http_server}/api/method/vms.APIs.vendor_onboarding.vendors_doc_changes_req_email.set_approval_check?vendor_onboarding={vendor_onboarding.name}&action=reject"

            # Email body
            message = f"""
                <p>Dear {register_by},</p>
                <p>
                    The vendor <b>{vendor_master.vendor_name}</b> has requested changes to its details.  
                    Kindly review the request and take appropriate action by clicking one of the buttons below:
                </p>
                <p>
                    <a href="{allow_url}" style="background-color:green;color:white;padding:8px 16px;
                    text-decoration:none;border-radius:4px;">Allow</a>
                    
                    &nbsp;&nbsp;
                    
                    <a href="{reject_url}" style="background-color:red;color:white;padding:8px 16px;
                    text-decoration:none;border-radius:4px;">Reject</a>
                </p>
                <br>
                <p><b>Remarks from vendor:</b> {remarks}</p>
                <p>Thank you,<br>Vendor Management System</p>
            """

            custom_sendmail(
                recipients=[vendor_onboarding.registered_by],
                cc=[vendor_onboarding.accounts_head_approval],
                subject=subject,
                message=message,
                now=True
            )

            frappe.db.set_value(
                "Vendor Onboarding",
                vendor_onboarding.name,
                {
                    "vendor_remarks": remarks,
                    "change_details_req_mail_sent_to_accounts_team": 1
                }
            )        

            return {
                "status": "success",
                "message": "Email sent successfully"
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "send_doc_change_req_email")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def set_approval_check(vendor_onboarding: str, action: str):
    try:
        if not vendor_onboarding or not action:
            return {
                "status": "error",
                "message": "Missing required parameters (vendor_onboarding, action)."
            }

        doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        if doc.register_by_account_team == 0:
            if doc.get("allow_to_change_document_details_by_purchase_team") == 1:
                return {
                    "status": "error",
                    "message": f"This vendor onboarding ({vendor_onboarding}) has already been processed."
                }

            if action == "allow":
                doc.allow_to_change_document_details_by_purchase_team = 1
                status = "Allowed"
            elif action == "reject":
                doc.allow_to_change_document_details_by_purchase_team = 0
                status = "Rejected"
            else:
                return {
                    "status": "error",
                    "message": "Invalid action. Must be 'allow' or 'reject'."
                }
        elif doc.register_by_account_team == 1:
            if doc.get("allow_to_change_document_details_by_accounts_team") == 1:
                return {
                    "status": "error",
                    "message": f"This vendor onboarding ({vendor_onboarding}) has already been processed."
                }

            if action == "allow":
                doc.allow_to_change_document_details_by_accounts_team = 1
                status = "Allowed"
            elif action == "reject":
                doc.allow_to_change_document_details_by_accounts_team = 0
                status = "Rejected"
            else:
                return {
                    "status": "error",
                    "message": "Invalid action. Must be 'allow' or 'reject'."
                }
        
        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Your response has been recorded for Vendor Onboarding {vendor_onboarding}.",
            "action": status
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "set_approval_check")
        return {
            "status": "error",
            "message": "Failed to update.",
            "error": str(e)
        }
