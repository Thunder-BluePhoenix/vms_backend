import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.file_manager import save_file
import json



# @frappe.whitelist(allow_guest=True)
# def purchase_team_check(data):

#     if isinstance(data, str):
#             data = json.loads(data)

#     onb_name=data.get("onboard_id")
#     usr= data.get("user")
#     approved=data.get("approve")
#     rejected=data.get("reject")
#     rej_reason=data.get("rejected_reason")
    

#     onb = frappe.get_doc("Vendor Onboarding", onb_name)
#     if approved == 1 and rejected == 0:
#         onb.purchase_t_approval = usr
#         onb.purchase_team_undertaking = 1
#     elif approved == 0 and rejected == 1:
#         onb.rejected = 1
#         onb.rejected_by = usr
#         onb.purchase_t_approval = usr
#         onb.reason_for_rejection = rej_reason

#     onb.save()
#     frappe.db.commit()
    
        


# import json
# import frappe
# from frappe import _

@frappe.whitelist(allow_guest=True)
def purchase_team_check(data):
   

    try:
        if isinstance(data, str):
            data = json.loads(data)

        # Validate required fields
        # required_fields = ["onboard_id", "user", "approve", "reject"]
        # for field in required_fields:
        #     if not data.get(field):
        #         frappe.throw(_(f"Missing required field: {field}"))

        onboard_id = data.get("onboard_id")
        user = data.get("user")
        is_approved = int(data.get("approve"))
        is_rejected = int(data.get("reject"))
        rejection_reason = data.get("rejected_reason")
        comments = data.get("comments")
        # reconciliation_account = data.get("reconciliation_account") or ""

        if is_approved and is_rejected:
            frappe.throw(_("Cannot approve and reject at the same time."))

        # Fetch onboarding document
        onb_doc = frappe.get_doc("Vendor Onboarding", onboard_id)
        # if onb_doc.register_by_account_team == 0:
        if is_approved:
            onb_doc.purchase_t_approval = user
            onb_doc.purchase_team_undertaking = 1
            onb_doc.purchase_team_approval_remarks = comments
            message = _("Onboarding approved by Purchase Team.")
        elif is_rejected:
            if not rejection_reason:
                frappe.throw(_("Rejection reason is required."))
            onb_doc.rejected = 1
            onb_doc.rejected_by = user
            onb_doc.rejected_by_designation = "Rejected By Purchase Team"
            onb_doc.purchase_t_approval = user
            onb_doc.reason_for_rejection = rejection_reason
            message = _("Onboarding rejected by Purchase Team.")
        else:
            frappe.throw(_("Invalid request: either approve or reject must be set."))

        if onb_doc.payment_detail:
            payment_detail = frappe.get_doc("Vendor Onboarding Payment Details", onb_doc.payment_detail)

            if "bank_proof_by_purchase_team" in frappe.request.files:
                file = frappe.request.files["bank_proof_by_purchase_team"]
                saved = save_file(file.filename, file.stream.read(), payment_detail.doctype, payment_detail.name, is_private=0)
                payment_detail.bank_proof_by_purchase_team = saved.file_url
                payment_detail.save(ignore_permissions=True)

        onb_doc.save(ignore_permissions=True)
        frappe.db.commit()

        # elif onb_doc.register_by_account_team == 1:
        #     if is_approved:
        #         onb_doc.accounts_t_approval = user
        #         onb_doc.accounts_team_undertaking = 1
        #         onb_doc.accounts_team_approval_remarks = comments
        #         onb_doc.reconciliation_account = reconciliation_account
        #         message = _("Onboarding approved by Accounts Team.")
        #     elif is_rejected:
        #         if not rejection_reason:
        #             frappe.throw(_("Rejection reason is required."))
        #         onb_doc.rejected = 1
        #         onb_doc.rejected_by = user
        #         onb_doc.rejected_by_designation = "Rejected By Accounts Team"
        #         onb_doc.accounts_t_approval = user
        #         onb_doc.reason_for_rejection = rejection_reason
        #         message = _("Onboarding rejected by Accounts Team.")
        #     else:
        #         frappe.throw(_("Invalid request: either approve or reject must be set."))

        #     onb_doc.save(ignore_permissions=True)
        #     frappe.db.commit()

        return {
            "success": True,
            "message": message,
            "onboarding_id": onboard_id
        }

    except frappe.ValidationError as ve:
        frappe.local.response["http_status_code"] = 400
        return {
            "success": False,
            "message": str(ve)
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Purchase Team Approval Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "success": False,
            "message": _("An unexpected error occurred. Please try again later.")
        }









@frappe.whitelist(allow_guest=True)
def accounts_team_check(data):
   

    try:
        if isinstance(data, str):
            data = json.loads(data)

        # Validate required fields
        # required_fields = ["onboard_id", "user", "approve", "reject"]
        # for field in required_fields:
        #     if not data.get(field):
        #         frappe.throw(_(f"Missing required field: {field}"))

        onboard_id = data.get("onboard_id")
        user = data.get("user")
        is_approved = int(data.get("approve"))
        
        is_rejected = int(data.get("reject"))
        rejection_reason = data.get("rejected_reason")
        comments = data.get("comments")
        reconciliation_account = data.get("reconciliation_account")
        if is_approved and is_rejected:
            frappe.throw(_("Cannot approve and reject at the same time."))

        # Fetch onboarding document
        onb_doc = frappe.get_doc("Vendor Onboarding", onboard_id)

        if is_approved:
            onb_doc.accounts_t_approval = user
            onb_doc.accounts_team_undertaking = 1
            onb_doc.accounts_team_approval_remarks = comments
            onb_doc.reconciliation_account = reconciliation_account
            message = _("Onboarding approved by Accounts Team.")
        elif is_rejected:
            if not rejection_reason:
                frappe.throw(_("Rejection reason is required."))
            onb_doc.rejected = 1
            onb_doc.rejected_by = user
            onb_doc.rejected_by_designation = "Rejected By Accounts Team"
            onb_doc.accounts_t_approval = user
            onb_doc.reason_for_rejection = rejection_reason
            message = _("Onboarding rejected by Accounts Team.")
        else:
            frappe.throw(_("Invalid request: either approve or reject must be set."))

        onb_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "message": message,
            "onboarding_id": onboard_id
        }

    except frappe.ValidationError as ve:
        frappe.local.response["http_status_code"] = 400
        return {
            "success": False,
            "message": str(ve)
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Purchase Accounts Approval Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "success": False,
            "message": _("An unexpected error occurred. Please try again later.")
        }









@frappe.whitelist(allow_guest=True)
def purchase_head_check(data):
   

    try:
        if isinstance(data, str):
            data = json.loads(data)

        # Validate required fields
        # required_fields = ["onboard_id", "user", "approve", "reject"]
        # for field in required_fields:
        #     if not data.get(field):
        #         frappe.throw(_(f"Missing required field: {field}"))

        onboard_id = data.get("onboard_id")
        user = data.get("user")
        is_approved = int(data.get("approve"))
        is_rejected = int(data.get("reject"))
        rejection_reason = data.get("rejected_reason")
        comments = data.get("comments")
        # reconciliation_account = data.get("reconciliation_account") or ""

        if is_approved and is_rejected:
            frappe.throw(_("Cannot approve and reject at the same time."))

        # Fetch onboarding document
        onb_doc = frappe.get_doc("Vendor Onboarding", onboard_id)

        # if onb_doc.register_by_account_team == 0:
        if is_approved:
            onb_doc.purchase_h_approval = user
            onb_doc.purchase_head_undertaking = 1
            onb_doc.purchase_head_approval_remarks = comments
            message = _("Onboarding approved by Purchase Head.")
        elif is_rejected:
            if not rejection_reason:
                frappe.throw(_("Rejection reason is required."))
            onb_doc.rejected = 1
            onb_doc.rejected_by = user
            onb_doc.rejected_by_designation = "Rejected By Purchase Head"
            onb_doc.purchase_h_approval = user
            onb_doc.reason_for_rejection = rejection_reason
            message = _("Onboarding rejected by Purchase Head.")
        else:
            frappe.throw(_("Invalid request: either approve or reject must be set."))

        onb_doc.save(ignore_permissions=True)
        frappe.db.commit()

        # elif onb_doc.register_by_account_team == 1:
        #     if is_approved:
        #         onb_doc.accounts_head_approval = user
        #         onb_doc.accounts_head_undertaking = 1
        #         onb_doc.accounts_head_approval_remarks = comments
        #         onb_doc.reconciliation_account = reconciliation_account
        #         message = _("Onboarding approved by Accounts Team.")
        #     elif is_rejected:
        #         if not rejection_reason:
        #             frappe.throw(_("Rejection reason is required."))
        #         onb_doc.rejected = 1
        #         onb_doc.rejected_by = user
        #         onb_doc.rejected_by_designation = "Rejected By Accounts Head"
        #         onb_doc.accounts_head_approval = user
        #         onb_doc.reason_for_rejection = rejection_reason
        #         message = _("Onboarding rejected by Accounts Head.")
        #     else:
        #         frappe.throw(_("Invalid request: either approve or reject must be set."))

        #     onb_doc.save(ignore_permissions=True)
        #     frappe.db.commit()

        return {
            "success": True,
            "message": message,
            "onboarding_id": onboard_id
        }

    except frappe.ValidationError as ve:
        frappe.local.response["http_status_code"] = 400
        return {
            "success": False,
            "message": str(ve)
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Purchase Head Approval Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "success": False,
            "message": _("An unexpected error occurred. Please try again later.")
        }









# Accounts team approval flow -----------------------------------------

# @frappe.whitelist(allow_guest=True)
# def accounts_team_approval(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)

#         onboard_id = data.get("onboard_id")
#         user = data.get("user")
#         is_approved = int(data.get("approve")) 
#         is_rejected = int(data.get("reject"))
#         rejection_reason = data.get("rejected_reason")
#         comments = data.get("comments")
#         reconciliation_account = data.get("reconciliation_account")

#         if is_approved and is_rejected:
#             frappe.throw(_("Cannot approve and reject at the same time."))

#         # Fetch onboarding document
#         onb_doc = frappe.get_doc("Vendor Onboarding", onboard_id)

#         if is_approved:
#             onb_doc.accounts_t_approval = user
#             onb_doc.accounts_team_undertaking = 1
#             onb_doc.accounts_team_approval_remarks = comments
#             onb_doc.reconciliation_account = reconciliation_account
#             message = _("Onboarding approved by Accounts Team.")
#         elif is_rejected:
#             if not rejection_reason:
#                 frappe.throw(_("Rejection reason is required."))
#             onb_doc.rejected = 1
#             onb_doc.rejected_by = user
#             onb_doc.rejected_by_designation = "Rejected By Accounts Team"
#             onb_doc.accounts_t_approval = user
#             onb_doc.reason_for_rejection = rejection_reason
#             message = _("Onboarding rejected by Accounts Team.")
#         else:
#             frappe.throw(_("Invalid request: either approve or reject must be set."))

#         onb_doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "success": True,
#             "message": message,
#             "onboarding_id": onboard_id
#         }

#     except frappe.ValidationError as ve:
#         frappe.local.response["http_status_code"] = 400
#         return {
#             "success": False,
#             "message": str(ve)
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Purchase Accounts Approval Error")
#         frappe.local.response["http_status_code"] = 500
#         return {
#             "success": False,
#             "message": _("An unexpected error occurred. Please try again later.")
#   }
    


@frappe.whitelist(allow_guest=True)
def accounts_head_check(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        onboard_id = data.get("onboard_id")
        user = data.get("user")
        is_approved = int(data.get("approve")) 
        is_rejected = int(data.get("reject"))
        rejection_reason = data.get("rejected_reason")
        comments = data.get("comments")
        reconciliation_account = data.get("reconciliation_account")
        
        if is_approved and is_rejected:
            frappe.throw(_("Cannot approve and reject at the same time."))

        # Fetch onboarding document
        onb_doc = frappe.get_doc("Vendor Onboarding", onboard_id)

        if is_approved:
            onb_doc.accounts_head_approval = user
            onb_doc.accounts_head_undertaking = 1
            onb_doc.accounts_head_approval_remarks = comments
            onb_doc.reconciliation_account = reconciliation_account
            message = _("Onboarding approved by Accounts Team.")
        elif is_rejected:
            if not rejection_reason:
                frappe.throw(_("Rejection reason is required."))
            onb_doc.rejected = 1
            onb_doc.rejected_by = user
            onb_doc.rejected_by_designation = "Rejected By Accounts Head"
            onb_doc.accounts_head_approval = user
            onb_doc.reason_for_rejection = rejection_reason
            message = _("Onboarding rejected by Accounts Head.")
        else:
            frappe.throw(_("Invalid request: either approve or reject must be set."))

        onb_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "message": message,
            "onboarding_id": onboard_id
        }

    except frappe.ValidationError as ve:
        frappe.local.response["http_status_code"] = 400
        return {
            "success": False,
            "message": str(ve)
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Purchase Accounts Approval Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "success": False,
            "message": _("An unexpected error occurred. Please try again later.")
        }