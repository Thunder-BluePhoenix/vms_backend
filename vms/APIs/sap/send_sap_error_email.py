import frappe
import json
from vms.utils.custom_send_mail import custom_sendmail
from frappe.utils import nowtime
from frappe.utils import now_datetime

# @frappe.whitelist(allow_guest=False)
# def send_sap_error_email(doctype, docname):
#     try:
#         if not doctype or not docname:
#             frappe.local.response["http_status_code"] = 404
#             return {
#                 "status": "error",
#                 "message": "Please provide doctype and docname."
#             }

#         sap_response = None
#         erp_response = None
#         subject = ""
#         message = ""

#         def pretty_json(raw_data):
#             try:
#                 return f"<pre>{json.dumps(json.loads(raw_data), indent=4)}</pre>"
#             except Exception:
#                 return f"<pre>{raw_data}</pre>"

#         # --- Vendor Onboarding ---
#         if doctype == "Vendor Onboarding":
#             logs = frappe.get_all(
#                 "VMS SAP Logs",
#                 filters={"vendor_onboarding_link": docname},
#                 fields=["name", "sap_response", "creation"],
#                 order_by="creation desc",
#                 limit=1
#             )
#             if logs:
#                 sap_response = pretty_json(logs[0].sap_response)
#                 subject = f"Vendor Onboarding {docname} has SAP Error"
#                 message = f"""
#                     Dear IT Head,<br><br>
#                     The Vendor Onboarding document <b>{docname}</b> has encountered a SAP error.<br><br>
#                     <b>SAP Response:</b><br>{sap_response}<br><br>
#                     Please look into this as soon as possible.<br><br>
#                     Thank you,<br>
#                     VMS Team
#                 """

#         # --- Purchase Requisition Form ---
#         elif doctype == "Purchase Requisition Form":
#             logs = frappe.get_all(
#                 "Purchase SAP Logs",
#                 filters={"purchase_requisition_link": docname},
#                 fields=["name", "erp_response", "creation"],
#                 order_by="creation desc",
#                 limit=1
#             )
#             if logs:
#                 erp_response = pretty_json(logs[0].erp_response)
#                 subject = f"Purchase Requisition {docname} has SAP Error"
#                 message = f"""
#                     Dear IT Head,<br><br>
#                     The Purchase Requisition document <b>{docname}</b> has encountered a SAP error.<br><br>
#                     <b>ERP Response:</b><br>{erp_response}<br><br>
#                     Please look into this as soon as possible.<br><br>
#                     Thank you,<br>
#                     VMS Team
#                 """

#         # --- Purchase Order ---
#         elif doctype == "Purchase Order":
#             logs = frappe.get_all(
#                 "Purchase SAP Logs",
#                 filters={"purchase_order_link": docname},
#                 fields=["name", "erp_response", "creation"],
#                 order_by="creation desc",
#                 limit=1
#             )
#             if logs:
#                 erp_response = pretty_json(logs[0].erp_response)
#                 subject = f"Purchase Order {docname} has SAP Error"
#                 message = f"""
#                     Dear IT Head,<br><br>
#                     The Purchase Order document <b>{docname}</b> has encountered a SAP error.<br><br>
#                     <b>ERP Response:</b><br>{erp_response}<br><br>
#                     Please look into this as soon as possible.<br><br>
#                     Thank you,<br>
#                     VMS Team
#                 """

#         if not subject or not message:
#             frappe.local.response["http_status_code"] = 404
#             return {
#                 "status": "error",
#                 "message": f"No SAP logs found for {doctype} {docname}"
#             }

#         recipients = frappe.get_all(
#             "Has Role",
#             filters={"role": "IT Head"},
#             fields=["parent"]
#         )
#         recipient_emails = [
#             frappe.db.get_value("User", r.parent, "email")
#             for r in recipients if frappe.db.get_value("User", r.parent, "email")
#         ]

#         if not recipient_emails:
#             frappe.local.response["http_status_code"] = 404
#             return {
#                 "status": "error",
#                 "message": "No recipients found with role IT Head."
#             }

#         frappe.custom_sendmail(
#             recipients=recipient_emails,
#             subject=subject,
#             message=message,
#             now=True
#         )

#         return {
#             "status": "success",
#             "message": f"Error email sent to IT Head(s) for {doctype} {docname}."
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Send SAP Error Email Failed")
#         frappe.local.response["http_status_code"] = 500
#         return {
#             "status": "error",
#             "message": "Failed to send SAP error email.",
#             "error": str(e)
#         }


@frappe.whitelist(allow_guest=False)
def send_sap_error_email(doctype, docname, remarks=None):
    try:
        if not doctype or not docname:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "Please provide doctype and docname."
            }

        sap_response = None
        erp_response = None
        subject = ""
        message = ""
        vendor_details = ""

        def pretty_json(raw_data):
            try:
                return f"<pre>{json.dumps(json.loads(raw_data), indent=4)}</pre>"
            except Exception:
                return f"<pre>{raw_data}</pre>"

        recipients = frappe.get_all(
            "Has Role",
            filters={"role": "IT Head"},
            fields=["parent"]
        )
        recipient_emails = [
            frappe.db.get_value("User", r.parent, "email")
            for r in recipients if frappe.db.get_value("User", r.parent, "email")
        ]


        if not recipient_emails:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "No recipients found with role IT Head."
            }

        # --- Vendor Onboarding ---
        if doctype == "Vendor Onboarding":
            ven_onb = frappe.get_doc("Vendor Onboarding", docname)
            vendor_master = frappe.get_doc("Vendor Master", ven_onb.ref_no)
            vendor_details = f"Vendor Name: {vendor_master.vendor_name}, Onboarding ID: {ven_onb.name}"
            cc = [ven_onb.registered_by, frappe.session.user, ven_onb.purchase_t_approval, ven_onb.purchase_h_approval, ven_onb.accounts_t_approval, ven_onb.accounts_head_approval]

            logs = frappe.get_all(
                "VMS SAP Logs",
                filters={"vendor_onboarding_link": docname},
                fields=["name", "sap_response", "creation"],
                order_by="creation desc",
                limit=1
            )

            if logs:
                sap_response = pretty_json(logs[0].sap_response)

            if ven_onb.sap_error_mail_sent == 0:
                subject = f"Vendor Onboarding {docname} - SAP Error"
                message = f"""
                    Dear IT Head,<br><br>
                    The Vendor Onboarding document <b>{docname}</b> has encountered a SAP error.<br><br>
                    <b>SAP Response:</b><br>{sap_response or f'⚠️ No SAP logs were found.<br>{vendor_details}'}<br>
                    <strong>Remarks: {remarks}</strong><br><br>
                    Please look into this as soon as possible.<br><br>
                    Thank you,<br>
                    VMS Team
                """
                custom_sendmail(
                    recipients=recipient_emails,
                    cc=cc,
                    subject=subject,
                    message=message,
                    now=True
                )
                frappe.db.set_value("Vendor Onboarding", docname, {"sap_error_mail_sent": 1,"sap_error_mail_sent_time": now_datetime()})

                return {
                    "status": "success",
                    "message": f"SAP Error email sent to IT Head(s) for Vendor Onboarding {docname}."
                }

            else:
                frappe.local.response["http_status_code"] = 409
                return {
                    "status": "skipped",
                    "message": f"SAP Error email already sent earlier for Vendor Onboarding {docname}."
                }

        # --- Purchase Requisition Form ---
        elif doctype == "Purchase Requisition Form":
            logs = frappe.get_all(
                "Purchase SAP Logs",
                filters={"purchase_requisition_link": docname},
                fields=["name", "erp_response", "creation"],
                order_by="creation desc",
                limit=1
            )

            if logs:
                erp_response = pretty_json(logs[0].erp_response)

            subject = f"Purchase Requisition {docname} - SAP Error"
            message = f"""
                Dear IT Head,<br><br>
                The Purchase Requisition document <b>{docname}</b> has encountered a SAP error.<br><br>
                <b>ERP Response:</b><br>{erp_response or '⚠️ No SAP logs were found for this document.'}<br><br>
                Please look into this as soon as possible.<br><br>
                Thank you,<br>
                VMS Team
            """

        # --- Purchase Order ---
        elif doctype == "Purchase Order":
            logs = frappe.get_all(
                "Purchase SAP Logs",
                filters={"purchase_order_link": docname},
                fields=["name", "erp_response", "creation"],
                order_by="creation desc",
                limit=1
            )

            if logs:
                erp_response = pretty_json(logs[0].erp_response)

            subject = f"Purchase Order {docname} - SAP Error"
            message = f"""
                Dear IT Head,<br><br>
                The Purchase Order document <b>{docname}</b> has encountered a SAP error.<br><br>
                <b>ERP Response:</b><br>{erp_response or '⚠️ No SAP logs were found for this document.'}<br><br>
                Please look into this as soon as possible.<br><br>
                Thank you,<br>
                VMS Team
            """

        # --- fallback ---
        else:
            subject = f"{doctype} {docname} - SAP Error"
            message = f"""
                Dear IT Head,<br><br>
                The document <b>{doctype} {docname}</b> has encountered a SAP error.<br><br>
                ⚠️ No SAP logs were found for this document.<br>
                <strong>Remarks: {remarks} <strong><br><br>
                Please look into this as soon as possible.<br><br>
                Thank you,<br>
                VMS Team
            """

        # --- Common send for all other doctypes ---
        custom_sendmail(
            recipients=recipient_emails,
            subject=subject,
            message=message,
            now=True
        )

        return {
            "status": "success",
            "message": f"SAP Error email sent to IT Head(s) for {doctype} {docname}."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send SAP Error Email Failed")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": "Failed to send SAP error email.",
            "error": str(e)
        }


# In vendor onb, uncheck the SAP Error email check if onboarding status is not change form sap error to Approved within one hour
def uncheck_sap_error_email():
    try:
        vendor_list = frappe.get_all(
            "Vendor Onboarding",
            filters={"onboarding_form_status": "SAP Error", "sap_error_mail_sent": 1},
            fields=["name", "sap_error_mail_sent_time"]
        )

        current_time = now_datetime()

        for ven in vendor_list:
            if not ven.sap_error_mail_sent_time:
                continue

            sent_time = ven.sap_error_mail_sent_time
            time_diff = current_time - sent_time

            if time_diff.total_seconds() >= 3600:  
                frappe.logger().info(f"Unchecking SAP Error Email for: {ven.name}")
                frappe.db.set_value(
                    "Vendor Onboarding",
                    ven.name,
                    {
                        "sap_error_mail_sent": 0,
                        "sap_error_mail_sent_time": None
                    }
                )

        return {"status": "success"}

    except Exception as e:
        frappe.logger().error(f"Error in uncheck_sap_error_email: {str(e)}")
        return {"status": "error", "message": str(e)}
