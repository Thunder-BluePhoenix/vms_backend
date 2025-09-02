import frappe

from vms.APId.approval.helpers.add_approval_entry import add_approval_entry
from vms.APIs.approval.helpers.get_approval_matrix import get_stage_info
from vms.APIs.approval.helpers.validate_action import validate_action
from vms.utils.approval_utils import get_approval_users_by_role


@frappe.whitelist(methods=["POST"])
def approve_qms(
    qms_id, action, remark="", required_optional=False
):
    try:
        validate_action(action)

        is_approved = action == "Approved"
        qms = frappe.get_doc("Supplier QMS Assessment Form", qms_id)


        
        current_user = frappe.session.user
        allowed_users = get_approval_users_by_role(
                "Suppllier QMS Assessment Form", qms.name
            )

        if current_user not in allowed_users:
            frappe.throw(
                f"You are not authorized to {action} this Supplier QMS. Please contact the approver."
            )
        purchase_order.append(
            "approvals",
            {
                "for_doc_type": "Purchase Order",
                "approval_stage": 0,
                "approval_stage_name": purchase_order.approval_status,
                "approved_by": current_user,
                "approval_status": 1,
                "next_approval_stage": 0,
                "action": action,
                "next_action_by": "",
                "next_action_role": "",
                "remark": remark,
            },
        )
            update_status(purchase_order, action)
            purchase_order.save(ignore_permissions=True)
            return {
                "message": "Doc Approval entry created/updated successfully",
                "doc_name": purchase_order.name,
            }

        sales_organisation_name = get_domastic_sales_org_name_from_company(
            purchase_order.get("company")
        )

        stage_info = get_stage_info(
            "Purchase Order", purchase_order, sales_organisation_name or "9999"
        )

        cur_stage = stage_info["cur_stage_info"]
        next_stage = stage_info["next_stage_info"]
        prev_stage = stage_info["prev_stage_info"]
        next_to_next_stage = stage_info["next_to_next_stage_info"]

        if required_optional:
            if cur_stage and cur_stage.get("is_optional") == 1:
                next_stage = prev_stage
        else:
            if next_stage and next_stage.get("is_optional") == 1:
                next_stage = next_to_next_stage

        current_user = frappe.session.user

        next_info = verify_approver_n_get_info(
            current_user,
            cur_stage,
            [purchase_order.get("company", "")],
            purchase_order,
            next_stage=next_stage,
            sales_organisation_name=sales_organisation_name,
        )

        linked_user = next_info.get("linked_user")
        next_stage = next_info.get("next_stage")
        purchase_order.remarks = remark
        update_status(
            purchase_order,
            (
                action
                if (not is_approved) or (not next_stage and is_approved)
                else (
                    next_stage.approval_stage_name
                    if is_approved and next_stage
                    else cur_stage.approval_stage_name
                )
            ),
        )

        if not is_approved:
            purchase_order.add_transition_states(
                "Purchase Order Rejected",
                f"Purchase Order Rejected by {frappe.session.user}",
            )
        if is_approved and linked_user:
            send_approval_mail(linked_user, purchase_order)

        add_approval_entry(
            "Purchase Order",
            purchase_order,
            linked_user,
            cur_stage,
            next_stage,
            is_approved,
            action,
            remark,
        )

        return {
            "message": "Doc Approval entry created/updated successfully",
            "doc_name": purchase_order.name,
        }
    except Exception as e:
        approval_error([frappe.traceback(), str(e), purchase_order_id, action, remark])
        frappe.throw(e)
