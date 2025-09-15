import frappe

from vms.APIs.approval.helpers.add_approval_entry import add_approval_entry
from vms.APIs.approval.helpers.get_approval_matrix import get_stage_info
from vms.APIs.approval.helpers.validate_action import validate_action
from vms.utils.approval_utils import get_approval_users_by_role
from vms.utils.verify_user import verify_employee
from vms.utils.get_approver_employee import get_approval_employee
from vms.utils.notification_triggers import NotificationTrigger
from vms.utils.custom_send_mail import custom_sendmail


def update_status(doc, status):
    # doc.db_set("status", status)
    doc.db_set("approval_status", status)


def get_next_approver(stage, doc, next_stage=None):

    if not next_stage:
        return {
            "linked_user": "",
            "next_stage": "",
        }

    
    next_user = (
        next_stage.get("user")
        if next_stage
        and next_stage.get("approver_type") == "User"
        and next_stage.get("user")
        else None
    )

    if next_user:
        return {"linked_user": next_user, "next_stage": next_stage}

    
    next_role = (
        next_stage.get("role")
        if next_stage
        and next_stage.get("approver_type") == "Role"
        and next_stage.get("role")
        else ""
    )

    if next_role:

        company = doc.get("company")
        
        
        # in get_approval_employee this funciton we need to handle team speical case for the comapny
        emp = get_approval_employee(
            next_role,
            company_list=[company] if company else [],
            fields=["user_id"],
            doc=doc,
        )

        linked_user = emp.get("user_id") if emp else ""
        
        if linked_user:
            return {"linked_user": linked_user, "next_stage": next_stage}

    
    linked_user = ""
    if not linked_user:
        stage_info = get_stage_info(
            "Vendor Onboarding",
            doc,
            approval_stage=int(stage.get("approval_stage", 0)) + 1,
        )

        if stage_info.get("next_stage_info"):
            return get_next_approver(
                stage_info["cur_stage_info"],
                doc,
                stage_info["next_stage_info"],
            )

    return {"linked_user": "", "next_stage": None}


def verify_approver_n_get_info(user, stage, doc, next_stage=None):
    
    cur_role = (
        stage.get("role")
        if stage and stage.get("approver_type") == "Role" and stage.get("role")
        else ""
    )

    
    if cur_role:
        user_roles = frappe.get_roles(user)
        
        if cur_role not in user_roles:
            allowed_users = get_approval_users_by_role(
                "Vendor Onboarding", doc.name, cur_role
            )
            
            if user not in allowed_users:
                frappe.throw(f"You are not authorized to perform this approval. Required role: {cur_role}")

    elif stage and stage.get("approver_type") == "User":
        stage_user = stage.get("user")
        if stage_user and stage_user != user:
            frappe.throw("You are not authorized to perform this approval.")

    return get_next_approver(stage, doc, next_stage)



def send_approval_notification(linked_user, doc, is_approved=True, current_stage=None):
    try:
    
        if not linked_user:
            frappe.log_error("No next approver found - skipping notification")
            return
        
    
        to_user = frappe.get_doc("User", linked_user)
        

        current_approver = frappe.get_doc("User", frappe.session.user)
        current_stage_name = current_stage.get("approval_stage_name", "Unknown Stage") if current_stage else "Unknown Stage"
        
        subject = f"Vendor Onboarding Approval Required - {doc.get('name', 'N/A')}"
        action_message = "Please review this Vendor Onboarding document and provide your approval or feedback."
        
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin: 0; font-size: 24px;">Vendor Onboarding Approval Required</h2>
            </div>
            
            <div style="margin-bottom: 20px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">Dear {to_user.full_name or to_user.first_name or 'User'},</p>
                
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    {action_message}
                </p>
            </div>
            
            <div style="background-color: #fff; border: 1px solid #dee2e6; border-radius: 6px; padding: 20px; margin-bottom: 20px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px 0; font-weight: bold; color: #555; width: 40%;">Document Name:</td>
                        <td style="padding: 10px 0; color: #333;">{doc.get('name', 'N/A')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Document Type:</td>
                        <td style="padding: 10px 0; color: #333;">{doc.doctype}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Vendor Name:</td>
                        <td style="padding: 10px 0; color: #333;">{doc.get('vendor_name', 'N/A')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Current Status:</td>
                        <td style="padding: 10px 0; color: #333;">
                            <span style="background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-size: 14px;">
                                {doc.get('approval_status', 'Pending Approval')}
                            </span>
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Last Action By:</td>
                        <td style="padding: 10px 0; color: #333;">{current_approver.full_name or current_approver.first_name} ({current_stage_name})</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Action Date:</td>
                        <td style="padding: 10px 0; color: #333;">{frappe.format(frappe.utils.now(), 'Datetime')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Priority:</td>
                        <td style="padding: 10px 0; color: #333;">
                            <span style="background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-size: 14px;">
                                High
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div style="border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px;">
                <p style="font-size: 14px; color: #666; margin: 0;">
                    This is an automated notification from the Vendor Management System. Please do not reply to this email.
                </p>
                <p style="font-size: 12px; color: #999; margin: 5px 0 0 0;">
                    If you have any questions, please contact the system administrator.
                </p>
            </div>
        </div>
        """
        

        frappe.custom_sendmail(
            recipients=[to_user.name],
            cc = current_approver.email if current_approver else None,
            subject=subject,
            message=email_body,
            now=True
        )
        
        # Optional: Create notification log
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "email_content": email_body,
                "for_user": to_user.name,
                "type": "Alert",
                "document_type": doc.doctype,
                "document_name": doc.name,
                "from_user": frappe.session.user
            }).insert(ignore_permissions=True)
        except:
            pass 
        
        frappe.log_error(f"Vendor Onboarding approval notification sent successfully to {to_user.name}")
        
    except Exception as e:
        frappe.log_error(f"Error sending vendor onboarding approval notification: {str(e)}")


@frappe.whitelist(methods=["POST"])
def approve_vendor_onb(onboard_id, action, remark="",required_optional=False):
    try:

        validate_action(action)

        is_approved = action == "Approved"
        ven_onb = frappe.get_doc("Vendor Onboarding", onboard_id)
        current_user = frappe.session.user

        current_role = frappe.get_roles(current_user)
        
        allowed_users = get_approval_users_by_role(
            "Vendor Onboarding", ven_onb.name, tuple(current_role)
        )

        if current_user not in allowed_users:
            frappe.throw(
                f"You are not authorized to {action} this Vendor Onboarding. Please contact the approver."
            )

       
        stage_info = get_stage_info("Vendor Onboarding", ven_onb)

        cur_stage = stage_info.get("cur_stage_info")
        next_stage = stage_info.get("next_stage_info")
        prev_stage = stage_info.get("prev_stage_info")
        next_to_next_stage = stage_info.get("next_to_next_stage_info")

        
        if required_optional:
            if cur_stage and cur_stage.get("is_optional") == 1:
                next_stage = prev_stage
        else:
            if next_stage and next_stage.get("is_optional") == 1:
                next_stage = next_to_next_stage

        
        next_info = verify_approver_n_get_info(
            current_user,
            cur_stage,
            ven_onb,
            next_stage=next_stage,
        )

        linked_user = next_info.get("linked_user")
        next_stage = next_info.get("next_stage")
        
    
        ven_onb.remarks = remark 
        
    
        if not is_approved:
            new_status = action  
        elif not next_stage and is_approved:
            new_status = "Approved"  
        elif is_approved and next_stage:
            new_status = next_stage.get("approval_stage_name", "Pending Approval")
        else:
            new_status = cur_stage.get("approval_stage_name", "Pending Approval")

        update_status(ven_onb, new_status)

    
        if not is_approved:
            
            # linked_user = ""
            next_stage = None
            
            
            # send_rejection_notification(linked_user, ven_onb, current_user, remark, cur_stage)
        else:
            
            if linked_user:  
                #while sending this we need to check the team of employe wise special case for bella mam team
                send_approval_notification(linked_user, ven_onb, is_approved, cur_stage)
            

        add_approval_entry(
            "Vendor Onboarding",
            ven_onb,
            linked_user,
            cur_stage,
            next_stage,
            is_approved,
            action,
            remark,
        )

        ven_onb.save(ignore_permissions=True)

        return {
            "message": "Vendor Onboarding Approval processed successfully",
            "doc_name": ven_onb.name,
            "status": new_status,
            "next_approver": linked_user if is_approved else "",
            "is_workflow_complete": not is_approved or (is_approved and not linked_user)
        }

    except Exception as e:
        frappe.log_error(f"Vendor Onboarding Approval Error: {str(e)}\nTraceback: {frappe.get_traceback()}")
        frappe.throw(str(e))

