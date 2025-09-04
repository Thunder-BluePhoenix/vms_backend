import frappe



def update_next_approver(doc):
    
    previous_doc = doc.get_doc_before_save()

    cur_approver = (
        doc.get("approvals")[-1].get("next_action_by")
        if len(doc.get("approvals")) > 0
        and doc.get("approvals")[-1].get("next_action_by")
        else ""
    )

    if (
        previous_doc
        and previous_doc.get("next_approver") != cur_approver
        and not doc.flags.is_processed
    ):
        doc.next_approver = cur_approver if cur_approver else ""
        doc.flags.is_processed = True

        doc.save(ignore_permissions=True)
