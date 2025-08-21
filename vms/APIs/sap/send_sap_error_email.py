import frappe
import json
from vms.utils.custom_send_mail import custom_sendmail

@frappe.whitelist(allow_guest=False)
def send_sap_error_email(doctype, docname):
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

        def pretty_json(raw_data):
            try:
                return f"<pre>{json.dumps(json.loads(raw_data), indent=4)}</pre>"
            except Exception:
                return f"<pre>{raw_data}</pre>"

        # --- Vendor Onboarding ---
        if doctype == "Vendor Onboarding":
            logs = frappe.get_all(
                "VMS SAP Logs",
                filters={"vendor_onboarding_link": docname},
                fields=["name", "sap_response", "creation"],
                order_by="creation desc",
                limit=1
            )
            if logs:
                sap_response = pretty_json(logs[0].sap_response)
                subject = f"Vendor Onboarding {docname} has SAP Error"
                message = f"""
                    Dear IT Head,<br><br>
                    The Vendor Onboarding document <b>{docname}</b> has encountered a SAP error.<br><br>
                    <b>SAP Response:</b><br>{sap_response}<br><br>
                    Please look into this as soon as possible.<br><br>
                    Thank you,<br>
                    VMS Team
                """

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
                subject = f"Purchase Requisition {docname} has SAP Error"
                message = f"""
                    Dear IT Head,<br><br>
                    The Purchase Requisition document <b>{docname}</b> has encountered a SAP error.<br><br>
                    <b>ERP Response:</b><br>{erp_response}<br><br>
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
                subject = f"Purchase Order {docname} has SAP Error"
                message = f"""
                    Dear IT Head,<br><br>
                    The Purchase Order document <b>{docname}</b> has encountered a SAP error.<br><br>
                    <b>ERP Response:</b><br>{erp_response}<br><br>
                    Please look into this as soon as possible.<br><br>
                    Thank you,<br>
                    VMS Team
                """

        if not subject or not message:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": f"No SAP logs found for {doctype} {docname}"
            }

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

        frappe.custom_sendmail(
            recipients=recipient_emails,
            subject=subject,
            message=message
        )

        return {
            "status": "success",
            "message": f"Error email sent to IT Head(s) for {doctype} {docname}."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send SAP Error Email Failed")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": "Failed to send SAP error email.",
            "error": str(e)
        }

