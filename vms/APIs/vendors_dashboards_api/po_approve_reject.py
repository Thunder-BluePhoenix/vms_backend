import frappe
from frappe import _
from vms.utils.custom_send_mail import custom_sendmail
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def po_approve(data):
    try:
        po_name = data.get("po_name")
        tentative_date = data.get("tentative_date")

        if not po_name or not tentative_date:
            frappe.local.response.http_status_code = 400
            return {"status": "error", "message": _("po_name and tentative_date are required.")}
        
        try:
            formatted_date = datetime.strptime(tentative_date, "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            frappe.local.response.http_status_code = 400
            return {"status": "error", "message": _("Invalid tentative_date format. Expected YYYY-MM-DD.")}

        po = frappe.get_doc("Purchase Order", po_name)

        po.tentative_date = tentative_date
        po.approved_by = frappe.session.user

        po.status = "Approved by Vendor"
        po.approved_from_vendor = 1

        po.save()
        frappe.db.commit()

        subject = f"Vendor - {po.approved_by_name} has Approved the Purchase Order - {po_name}"


        message = f"""
            Dear Purchase Team,<br>
            The Vendor <b>{po.approved_by_name}</b> has <b>Approved</b> the Purchase Order - <b>{po_name}</b>.
            The Tentative date  submitted by Vendor is <b>{formatted_date}</b>.<br>
            Please see the details of the Purchase Order and take necessary action.
        """

        frappe.custom_sendmail(
            recipients=po.email2,
            subject=subject,
            message=message,
            now=True
        )
        
        frappe.local.response.http_status_code = 200
        return {"status": "success", "message": "Purchase Order approved and email sent successfully."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "po_approve API Error")
        frappe.local.response.http_status_code = 400
        return {"status": "error", "message": str(e)}




@frappe.whitelist(allow_guest=True)
def po_reject(data):
    try:
        po_name = data.get("po_name")
        reason_for_rejection = data.get("reason_for_rejection")

        if not po_name or not reason_for_rejection:
            frappe.local.response.http_status_code = 400
            return {"status": "error", "message": _("po_name and reason_for_rejection are required.")}

        po = frappe.get_doc("Purchase Order", po_name)

        po.reason_for_rejection = reason_for_rejection
        po.rejected_by = frappe.session.user
        po.approved_from_vendor = 1

        po.status = "Rejected by Vendor"

        po.save()
        frappe.db.commit()

        subject = f"The Vendor {po.rejected_by_name} has Rejected the Purchase Order - {po_name}"

        message = f"""
            Dear Purchase Team,<br>
            The Vendor <b>{po.rejected_by_name}</b> has <b>Rejected</b> the Purchase Order - <b>{po_name}</b>.<br>
            The Reason for Rejection is: <b>{reason_for_rejection}</b><br>
            Please see the details of the Purchase Order and take necessary action.
        """

        frappe.custom_sendmail(
            recipients=po.email2,
            subject=subject,
            message=message,
            now=True
        )
        
        frappe.local.response.http_status_code = 200
        return {"status": "success", "message": "Purchase Order rejected and email sent successfully."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "po_reject API Error")
        frappe.local.response.http_status_code = 400
        return {"status": "error", "message": str(e)}