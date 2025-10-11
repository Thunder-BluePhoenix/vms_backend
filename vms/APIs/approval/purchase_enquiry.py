import frappe

from vms.APIs.approval.helpers.add_approval_entry import add_approval_entry
from vms.APIs.approval.helpers.get_approval_matrix import get_stage_info
from vms.APIs.approval.helpers.validate_action import validate_action
from vms.utils.approval_utils import get_approval_users_by_role
from vms.utils.verify_user import verify_employee
from vms.utils.get_approver_employee import (
    get_approval_employee,
    get_user_for_role_short,
)
from vms.utils.notification_triggers import NotificationTrigger
from vms.utils.custom_send_mail import custom_sendmail


def update_status(doc, status):
    doc.db_set("approval_status", status)


def get_previous_approver_employee(doc):
    
    try:
        # Get approvals list
        approvals = doc.get("approvals", [])
        
        if not approvals or len(approvals) == 0:
            # No previous approvals, use document owner
            owner_user = doc.owner
            employee_data = frappe.get_all(
                "Employee",
                filters={"user_id": owner_user, "status": "Active"},
                fields=["name"],
                limit=1
            )
            return employee_data[0].name if employee_data else None
        
        # Get the last approval entry
        last_approval = approvals[-1]
        previous_approver_user = last_approval.get("approved_by")
        
        if not previous_approver_user:
            return None
        
        # Get employee for this user
        employee_data = frappe.get_all(
            "Employee",
            filters={"user_id": previous_approver_user, "status": "Active"},
            fields=["name"],
            limit=1
        )
        
        return employee_data[0].name if employee_data else None
        
    except Exception as e:
        frappe.log_error(f"Error getting previous approver employee: {str(e)}")
        return None


def get_next_approver(stage, doc, next_stage=None):
   
    linked_user = ""
    if not next_stage:
        return {
            "linked_user": "",
            "next_stage": "",
        }


    next_role = (
        next_stage.get("role")
        if next_stage
        and next_stage.get("approver_type") == "Role"
        and next_stage.get("role")
        else ""
    )
    
    next_stage_user = (
        next_stage.get("user")
        if next_stage
        and next_stage.get("approver_type") == "User"
        and next_stage.get("user")
        else ""
    )
    
    
    from_hierarchy = next_stage.get("from_hierarchy", 0) if next_stage else 0
    
    
    if next_stage_user:
        linked_user = next_stage_user
        
    
    elif next_role and from_hierarchy:
        
        previous_employee = get_previous_approver_employee(doc)
        
        if previous_employee:
        
            emp = get_user_for_role_short(
                previous_employee,  
                next_role,          
                check_cur_user=False  
            )
            
            if emp:
                linked_user = emp.get("user_id", "")
        
    
    elif next_role:
        company = doc.get("company")
        
        emp = get_approval_employee(
            next_role,
            company_list=[company] if company else [],
            fields=["user_id"],
            doc=doc,
            stage=next_stage,
        )
        
        linked_user = emp.get("user_id") if emp else ""
    
    # If still no approver found, recursively check next stage
    if not linked_user:
        stage_info = get_stage_info(
            "Cart Details",
            doc,
            approval_stage=int(stage.get("approval_stage", 0)) + 1,
        )

        if stage_info.get("next_stage_info"):
            return get_next_approver(
                stage_info["cur_stage_info"],
                doc,
                stage_info["next_stage_info"],
            )

    return {
        "linked_user": linked_user,
        "next_stage": next_stage,
    }


def verify_approver_n_get_info(user, stage, doc, next_stage=None):
    
    cur_role = (
        stage.get("role")
        if stage and stage.get("approver_type") == "Role" and stage.get("role")
        else ""
    )
    
    cur_stage_user = (
        stage.get("user")
        if stage and stage.get("approver_type") == "User" and stage.get("user")
        else ""
    )
    
    
    from_hierarchy = stage.get("from_hierarchy", 0) if stage else 0
    
    
    
    
    if cur_stage_user:
        if cur_stage_user != user:
            frappe.throw("You are not authorized to perform this approval.")
    
   
    elif cur_role and from_hierarchy:
        
        previous_employee = get_previous_approver_employee(doc)
        
        if not previous_employee:
            frappe.throw(
                "Cannot determine previous approver for hierarchy validation.",
                exc=frappe.DoesNotExistError,
            )
        
        
        emp = get_user_for_role_short(
            previous_employee,  
            cur_role,           
            check_cur_user=False  
        )
        
        if not emp:
            frappe.throw(
                f"No employee with role '{cur_role}' found in the reporting hierarchy.",
                exc=frappe.DoesNotExistError,
            )
        
    
        if emp.get("user_id") != user:
            frappe.throw(
                f"You are not authorized to approve at this stage. "
                f"The approver should be in the reporting hierarchy of the previous approver."
            )
    
    
    elif cur_role:
        user_roles = frappe.get_roles(user)
        
        if cur_role not in user_roles:
            allowed_users = get_approval_users_by_role(
                "Cart Details", doc.name, cur_role
            )
            
            if user not in allowed_users:
                frappe.throw(
                    f"You are not authorized to perform this approval. "
                    f"Required role: {cur_role}"
                )
    
    
    return get_next_approver(stage, doc, next_stage)

def send_approval_notification(linked_user, doc, is_approved=True, current_stage=None):
    """Send approval notification - calls your existing email functions"""
    try:
        # Import your existing email functions
        from vms.material.doctype.cart_details.cart_details import (
            send_mail_purchase,
            send_mail_hod,
            send_mail_user
        )
        
        if not linked_user:
            frappe.log_error("No next approver found - skipping notification")
            return
        
        # Your existing logic to determine which email to send
        # This will be called based on approval matrix stages
        stage_name = current_stage.get("approval_stage_name", "") if current_stage else ""
        
        # Determine which email function to call based on stage
        if "Purchase Team" in stage_name:
            send_mail_purchase(doc, method=None)
        elif "Purchase Head" in stage_name or "HOD" in stage_name:
            send_mail_hod(doc, method=None)
        elif "Final" in stage_name or not linked_user:
            send_mail_user(doc, method=None)
        
    except Exception as e:
        frappe.log_error(f"Error sending approval notification: {str(e)}")


def send_rejection_notification(linked_user, doc, rejected_by_user, remark, current_stage):
    """Send rejection notification - calls your existing rejection email"""
    try:
        # Import your existing rejection email function
        from vms.material.doctype.cart_details.cart_details import rejection_mail_to_user
        
        # Set rejection fields
        doc.rejected = 1
        doc.rejected_by = rejected_by_user
        doc.reason_for_rejection = remark
        doc.save(ignore_permissions=True)
        
        # Call your existing rejection email
        rejection_mail_to_user(doc, method=None)
        
    except Exception as e:
        frappe.log_error(f"Error sending rejection notification: {str(e)}")


@frappe.whitelist(methods=["POST"])
def approve_purchase_enquiry(purchase_enquiry_id, action, remark="", required_optional=False):
    
    try:

        validate_action(action)

        is_approved = action == "Approved"
        purchase_enquiry = frappe.get_doc("Cart Details", purchase_enquiry_id)
        current_user = frappe.session.user

        current_role = frappe.get_roles(current_user)
        
        
        

        
        allowed_users = get_approval_users_by_role(
            "Cart Details", purchase_enquiry.name, tuple(current_role)
        )

        if current_user not in allowed_users:
            frappe.throw(
                f"You are not authorized to {action} this Purchase Enquiry. "
                "Please contact the approver."
            )

       
        stage_info = get_stage_info("Cart Details", purchase_enquiry)

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
            purchase_enquiry,
            next_stage=next_stage,
        )

        linked_user = next_info.get("linked_user")
        next_stage = next_info.get("next_stage")
        
    
        purchase_enquiry.remarks = remark
        
        
        if not is_approved:
            new_status = action
        elif not next_stage and is_approved:
            new_status = "Approved"
        elif is_approved and next_stage:
            new_status = next_stage.get("approval_stage_name", "Pending Approval")
        else:
            new_status = cur_stage.get("approval_stage_name", "Pending Approval")

        update_status(purchase_enquiry, new_status)

       
        if not is_approved:
            next_stage = None
            send_rejection_notification(linked_user, purchase_enquiry, current_user, remark, cur_stage)
        else:
            if linked_user:
                send_approval_notification(linked_user, purchase_enquiry, is_approved, next_stage)
            else:
                # Final approval - send user notification
                send_approval_notification(None, purchase_enquiry, is_approved, cur_stage)

        add_approval_entry(
            "Cart Details",
            purchase_enquiry,
            linked_user,
            cur_stage,
            next_stage,
            is_approved,
            action,
            remark,
        )

        purchase_enquiry.save(ignore_permissions=True)

        return {
            "message": "Purchase Enquiry Approval processed successfully",
            "doc_name": purchase_enquiry.name,
            "status": new_status,
            "next_approver": linked_user if is_approved else "",
            "is_workflow_complete": not is_approved or (is_approved and not linked_user)
        }

    except Exception as e:
        frappe.log_error(f"Purchase Enquiry Approval Error: {str(e)}\nTraceback: {frappe.get_traceback()}")
        frappe.throw(str(e))

