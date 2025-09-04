import frappe


def add_approval_entry(
    doctype, doc, next_action_by, cur_stage, next_stage, is_approved, action, remark
):
    try:
        current_user = frappe.session.user

        doc.append(
            "approvals",
            {
                "for_doc_type": doctype,
                "approval_stage": cur_stage.approval_stage,
                "approval_stage_name": cur_stage.approval_stage_name,
                "approved_by": current_user,
                "approval_status": 1 if not next_stage and is_approved else 0,
                "next_approval_stage": (
                    next_stage.approval_stage
                    if next_stage and is_approved
                    else cur_stage.approval_stage + (1 if is_approved else 0)
                ),
                "action": action,
                "next_action_by": (
                    "" if not is_approved else next_action_by if next_action_by else ""
                ),
                "remark": remark,
            },
        )

        doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.logger("add_approval_entry").error(
            [
                doctype,
                doc,
                next_action_by,
                cur_stage,
                next_stage,
                is_approved,
                action,
                remark,
                e,
            ]
        )
        frappe.throw(e)
