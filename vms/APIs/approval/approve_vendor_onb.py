import frappe

from vms.APIs.approval.helpers.add_approval_entry import add_approval_entry
from vms.APIs.approval.helpers.get_approval_matrix import get_stage_info
from vms.APIs.approval.helpers.validate_action import validate_action
from vms.APIs.approval.helpers.verify_approvar import verify_approver_by_role_short
from vms.utils.get_approver_employee import (
    get_approval_employee,
    get_user_for_role_short,
)
from vms.utils.logger import approval_error
from vms.utils.notification_triggers import NotificationTrigger
from vms.utils.verify_distributor import get_current_user_document


def update_status(doc, status):
    doc.po_status = status
    doc.approval_status = status


def get_next_approver(stage, doc, next_stage=None, sales_organisation_name=None):
    emp_info = None
    if not next_stage:
        return {
            "linked_user": "",
            "next_stage": "",
        }
    cur_role = (
        stage.get("role")
        if stage and stage.get("approver_type") == "Role" and stage.get("role")
        else ""
    )
    next_role = (
        next_stage.get("role")
        if next_stage
        and next_stage.get("approver_type") == "Role"
        and next_stage.get("role")
        else ""
    )

    sales_person = doc.get("sales_person", "")
    from_hierarchy = stage["from_hierarchy"] if stage else None

    next_user = (
        next_stage.get("user")
        if next_stage
        and next_stage.get("approver_type") == "User"
        and next_stage.get("user")
        else None
    )

    if next_user:
        return {"linked_user": next_user, "next_stage": next_stage}

    if cur_role and cur_role.lower() == "distributor":
        sales_person = doc.get("sales_person", "")

        emp_info = get_user_for_role_short(sales_person, next_role, check_cur_user=True)

    elif cur_role and sales_person and from_hierarchy:
        next_user = (
            next_stage.get("user")
            if next_stage
            and next_stage.get("approver_type") == "User"
            and next_stage.get("user")
            else None
        )

        if next_user:
            emp_info = {"linked_user": next_user}
        else:
            emp_info = get_user_for_role_short(
                frappe.get_value("Employee Master", sales_person, "reporting_head"),
                next_role,
                check_cur_user=True,
            )
    else:
        zone = doc.get("zone")
        company = doc.get("company")
        emp = (
            get_approval_employee(
                zone,
                next_stage.role,
                company_list=[company],
                fields=["linked_user"],
            )
            if next_stage
            else None
        )

        emp_info = {
            "linked_user": (
                next_stage.get("user")
                if next_stage
                and next_stage.get("approver_type") == "User"
                and next_stage.get("user")
                else emp.get("linked_user") if emp else ""
            )
        }

    linked_user = emp_info.get("linked_user") if emp_info else ""

    next_stage = next_stage if next_stage else None
    if not linked_user:
        stage_info = get_stage_info(
            "Purchase Order",
            doc,
            sales_organisation_name or "9999",
            approval_stage=int(stage.get("approval_stage")) + 1,
        )

        return get_next_approver(
            stage_info["cur_stage_info"],
            doc,
            stage_info["next_stage_info"],
            sales_organisation_name,
        )

    return {"linked_user": linked_user, "next_stage": next_stage}


def verify_approver_n_get_info(
    user, stage, company_list, doc, next_stage=None, sales_organisation_name=None
):
    emp_info = None

    cur_role = (
        stage.get("role")
        if stage and stage.get("approver_type") == "Role" and stage.get("role")
        else ""
    )

    sales_person = doc.get("sales_person", "")
    from_hierarchy = stage["from_hierarchy"] if stage else None

    if cur_role and cur_role.lower() == "distributor":
        distributor = doc.get("distributor", "")
        distributor_linked_user = frappe.get_value(
            "Distributor Master", distributor, "linked_user"
        )
        user_list = [
            user.user
            for user in frappe.get_all(
                "Linked Users",
                filters={"parenttype": "Distributor Master", "parent": distributor},
                fields=["user"],
            )
        ]

        if user != distributor_linked_user and user not in user_list:
            frappe.throw("You are not authorized to initiate this approval.")
    elif cur_role and sales_person and from_hierarchy:
        emp_info = get_user_for_role_short(sales_person, cur_role, check_cur_user=True)

        if emp_info and emp_info.get("linked_user") != user:
            frappe.throw("You are not authorized to initiate this approval.")
    else:
        zone = doc.get("zone")

        verify_approver_by_role_short(
            user,
            stage,
            zone,
            cur_role,
            company_list,
        )

    return get_next_approver(stage, doc, next_stage, sales_organisation_name)


def send_approval_mail(linked_user, doc):
    user_document, mobile_number = get_current_user_document(linked_user)
    frontend_base_url = frappe.get_value(
        "DMS Settings", "DMS Settings", "frontend_base_url"
    )

    context = {
        "sign_in_url": frontend_base_url + "/sign-in",
        "po_name": doc.get("name"),
        "order_type": doc.get("order_type"),
        "distributor": doc.get("distributor_name"),
        "sales_person": doc.get("sales_person"),
        "sales_org": doc.get("sales_organization"),
        "approval_status": doc.get("approval_status"),
        "doc": doc,
        "from_user": frappe.session.user,
        "for_user": linked_user,
        "doctype": doc.doctype,
        "document_name": doc.name,
        "subject": "Purchase Order Approval",
    }
    whatsapp_context = {
        "dms_approver_phone": mobile_number,
        "dms_order_number": doc.name,
        "dms_utility_approver": linked_user,
        "dms_order_number": doc.name,
        "dms_invoice_amount": doc.total_amount,
        "dms_order_derscription": doc.approval_status,
        "dms_approval_sender_name": frappe.session.user,
        "dms_approval_sender_designation": doc.approval_status,
    }
    notification_obj = NotificationTrigger(context=context)
    notification_obj.send_email(
        linked_user, "Email Template for Purchase Order Approval"
    )
    notification_obj.send_whatsapp_message("Purchase Order Approval", whatsapp_context)
    notification_obj.create_push_notification()

    # custom_send_mail(
    #     "Email Template for Purchase Order Approval", linked_user, email_context
    # )


# vms.APIs.approval.approve_po.approve_purchase_order
@frappe.whitelist(methods=["POST"])
def approve_purchase_order(
    purchase_order_id, action, remark="", required_optional=False
):
    try:
        validate_action(action)

        is_approved = action == "Approved"
        purchase_order = frappe.get_doc("Purchase Order", purchase_order_id)

        business_type = (
            frappe.get_value(
                "Distributor Master", purchase_order.distributor, "business_type"
            )
            == "Joints"
        )
        if (
            purchase_order.sales_organization in ["9100", "3100"]
            and business_type
            and purchase_order.plant_wise
        ):
            current_user = frappe.session.user
            if not any(
                current_user == approver.next_action_by
                for approver in purchase_order.approvals
            ):
                frappe.throw(
                    f"You are not authorized to {action} this Purchase Order. Please contact the approver."
                )
            purchase_order.append(
                "approvals",
                {
                    "for_doc_type": "Purchase Order",
                    "approval_stage": 0,
                    "approval_stage_name": purchase_order.approval_status,
                    "approved_by": current_user,
                    "approval_status": action,
                    "next_approval_stage": 0,
                    "action": action,
                    "next_action_by": "",
                    "remark": remark,
                },
            )
            update_status(purchase_order, action)
            purchase_order.save(ignore_permissions=True)
            return

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
