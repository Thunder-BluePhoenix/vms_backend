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
    """Update document status fields"""
    doc.db_set("status", status)
    doc.db_set("approval_status", status)


def get_next_approver(stage, doc, next_stage=None):
    """Get the next approver for the approval stage"""
    if not next_stage:
        return {
            "linked_user": "",
            "next_stage": "",
        }

    # Check if next stage has a specific user assigned
    next_user = (
        next_stage.get("user")
        if next_stage
        and next_stage.get("approver_type") == "User"
        and next_stage.get("user")
        else None
    )

    if next_user:
        return {"linked_user": next_user, "next_stage": next_stage}

    # If it's a role-based approval, get user by role
    next_role = (
        next_stage.get("role")
        if next_stage
        and next_stage.get("approver_type") == "Role"
        and next_stage.get("role")
        else ""
    )

    if next_role:
        # For VMS, we can get approver based on department/company
        company = doc.get("company")
        
        
        emp = get_approval_employee(
            next_role,
            company_list=[company] if company else [],
            fields=["user_id"],
        )

        linked_user = emp.get("user_id") if emp else ""
        
        if linked_user:
            return {"linked_user": linked_user, "next_stage": next_stage}

    # If no approver found, try to get next available stage
    if not linked_user:
        stage_info = get_stage_info(
            "Supplier QMS Assessment Form",
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


def verify_approver_and_get_next(user, stage, doc, next_stage=None):
    
    cur_role = (
        stage.get("role")
        if stage and stage.get("approver_type") == "Role" and stage.get("role")
        else ""
    )


    # For role-based approval, verify user has the required role
    if cur_role:
        # Check if user has the required role for approval
        user_roles = frappe.get_roles(user)
        
        if cur_role not in user_roles:
            # Additional check: see if user is specifically assigned for this document
            allowed_users = get_approval_users_by_role(
                "Supplier QMS Assessment Form", doc.name,cur_role
            )
            
            if user not in allowed_users:
                frappe.throw(f"You are not authorized to perform this approval. Required role: {cur_role}")

    # For user-specific approval, verify it's the right user
    elif stage and stage.get("approver_type") == "User":
        stage_user = stage.get("user")
        if stage_user and stage_user != user:
            frappe.throw("You are not authorized to perform this approval.")


    return get_next_approver(stage, doc, next_stage)


def send_approval_notification(linked_user, doc):
    try:
        onbording_doc = doc.get("vendor_onboarding")
        if onbording_doc:
            onboarding = frappe.get_doc("Vendor Onboarding", onbording_doc)
            registered_by = onboarding.get("registered_by")

        if doc.status == "Approved":
            onbording_doc = doc.get("vendor_onboarding")
            if onbording_doc:
                onboarding = frappe.get_doc("Vendor Onboarding", onbording_doc)
                to_user = registered_by
                cc = frappe.get_doc("User", linked_user)
        else:
            to_user = linked_user
            cc = registered_by
        
        subject = f"QMS Assessment Approval Required - {doc.get('name', 'N/A')}"
        
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin: 0; font-size: 24px;">QMS Assessment Approval Required</h2>
            </div>
            
            <div style="margin-bottom: 20px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">Dear {to_user.full_name or to_user.first_name or 'User'},</p>
                
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    A QMS Assessment document requires your approval. Please review the details below:
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
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Current Status:</td>
                        <td style="padding: 10px 0; color: #333;">
                            <span style="background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-size: 14px;">
                                {doc.get('approval_status', 'Pending Approval')}
                            </span>
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Submitted By:</td>
                        <td style="padding: 10px 0; color: #333;">{from_user.full_name or from_user.first_name or frappe.session.user}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px 0; font-weight: bold; color: #555;">Creation Date:</td>
                        <td style="padding: 10px 0; color: #333;">{frappe.format(doc.get('creation'), 'Datetime') if doc.get('creation') else 'N/A'}</td>
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
            
            <div style="margin-bottom: 20px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    <strong>Action Required:</strong> Please review this QMS Assessment document and provide your approval or feedback.
                </p>
                
                <p style="font-size: 14px; line-height: 1.6; color: #666;">
                    <strong>Note:</strong> This document is awaiting your approval to proceed with the next steps in the QMS process.
                </p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{frappe.utils.get_url()}/app/qms-assessment/{doc.name}" 
                   style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Review Document
                </a>
            </div>
            
            <div style="border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px;">
                <p style="font-size: 14px; color: #666; margin: 0;">
                    This is an automated notification from the QMS System. Please do not reply to this email.
                </p>
                <p style="font-size: 12px; color: #999; margin: 5px 0 0 0;">
                    If you have any questions, please contact the system administrator.
                </p>
            </div>
        </div>
        """
        
        # Send email using frappe.sendmail
        frappe.custom.sendmail(
            recipients=[to_user],
            cc=[cc],
            subject=subject,
            message=email_body,
            now=True
        )
        
        # Optional: Create a simple push notification
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "email_content": email_body,
                "for_user": linked_user,
                "type": "Alert",
                "document_type": doc.doctype,
                "document_name": doc.name,
                "from_user": frappe.session.user
            }).insert(ignore_permissions=True)
        except:
            pass  # If Notification Log doctype doesn't exist, skip this
        
        frappe.log_error(f"Approval notification sent successfully to {linked_user}")
        
    except Exception as e:
        frappe.log_error(f"Error sending approval notification: {str(e)}")


@frappe.whitelist(methods=["POST"])
def approve_qms(qms_id, action, remark="", required_optional=False):
    """Main function to approve/reject QMS Assessment Form"""
    try:
        # Validate the action
        validate_action(action)

        is_approved = action == "Approved"
        qms = frappe.get_doc("Supplier QMS Assessment Form", qms_id)
        current_user = frappe.session.user
        
        current_role = frappe.get_all(
                        "Has Role",
                        filters={"parent": current_user},
                        fields=["role"],
                        pluck="role" 
                    )
        
        


        # Check if current user is authorized
        allowed_users = get_approval_users_by_role(
            "Supplier QMS Assessment Form", qms.name, tuple(current_role)
        )
        

        if current_user not in allowed_users:
            frappe.throw(
                f"You are not authorized to {action} this QMS Assessment. Please contact the approver."
            )


        # Get approval stage information
        stage_info = get_stage_info("Supplier QMS Assessment Form", qms)
        

        cur_stage = stage_info.get("cur_stage_info")
        next_stage = stage_info.get("next_stage_info")
        prev_stage = stage_info.get("prev_stage_info")
        next_to_next_stage = stage_info.get("next_to_next_stage_info")
        

        # Handle optional stages
        if required_optional:
            if cur_stage and cur_stage.get("is_optional") == 1:
                next_stage = prev_stage
        else:
            if next_stage and next_stage.get("is_optional") == 1:
                next_stage = next_to_next_stage

        # Verify approver and get next stage info
        next_info = verify_approver_and_get_next(
            current_user,
            cur_stage,
            qms,
            next_stage=next_stage,
        )

        linked_user = next_info.get("linked_user")
        next_stage = next_info.get("next_stage")
        
        # Update document
        qms.remarks = remark
        
        # Determine status based on approval state
        if not is_approved:
            new_status = action  # "Rejected"
        elif not next_stage and is_approved:
            new_status = "Approved"  # Final approval
        elif is_approved and next_stage:
            new_status = next_stage.get("approval_stage_name", "Pending Approval")
        else:
            new_status = cur_stage.get("approval_stage_name", "Pending Approval")

        update_status(qms, new_status)

        # Add transition state for rejection
        if not is_approved:
            qms.add_transition_states(
                "QMS Assessment Rejected",
                f"QMS Assessment Rejected by {frappe.session.user}",
            )

        # Send notification to next approver
        if is_approved and linked_user:
            send_approval_notification(linked_user, qms)

            # Add approval entry to track the approval flow
        add_approval_entry(
            "Supplier QMS Assessment Form",
            qms,
            linked_user,
            cur_stage,
            next_stage,
            is_approved,
            action,
            remark,
        )


        qms.save(ignore_permissions=True)

        return {
            "message": "QMS Approval processed successfully",
            "doc_name": qms.name,
            "status": new_status,
            "next_approver": linked_user,
        }

    except Exception as e:
        # approval_error([frappe.traceback(), str(e), qms_id, action, remark])
        frappe.throw(str(e))


# Additional utility functions for VMS-specific approval logic

def get_qms_approval_hierarchy(qms_doc):
    """Get the approval hierarchy for QMS based on assessment type and value"""
    assessment_type = qms_doc.get("assessment_type")
    total_value = qms_doc.get("total_assessment_value", 0)
    
    # Define approval hierarchy based on your business rules
    if assessment_type == "Critical Supplier":
        return "critical_supplier_approval"
    elif total_value > 1000000:  # High value assessments
        return "high_value_approval"
    else:
        return "standard_approval"


def check_qms_prerequisites(qms_doc):
    """Check if all prerequisites are met before approval"""
    prerequisites = []
    
    # Check if all required assessments are completed
    if not qms_doc.get("quality_score"):
        prerequisites.append("Quality assessment score is required")
    
    if not qms_doc.get("compliance_score"):
        prerequisites.append("Compliance assessment score is required")
    
    # Check if supporting documents are attached
    if not qms_doc.get("attachments"):
        prerequisites.append("Supporting documents are required")
    
    if prerequisites:
        frappe.throw("Prerequisites not met: " + "; ".join(prerequisites))
    
    return True