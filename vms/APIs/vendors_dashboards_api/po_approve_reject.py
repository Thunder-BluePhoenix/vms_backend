import frappe
from frappe import _



@frappe.whitelist()
def po_approve(data):
    po_name = data.get("po_name")
    po = frappe.get_doc("Purchase Order", po_name)
    tentative_date = data.get("tentative_date")

    po.tentative_date = tentative_date
    po.approved_by = frappe.session.user

    po.status = "Approved"

    po.save()
    frappe.db.commit()


@frappe.whitelist()
def po_reject(data):
    po_name = data.get("po_name")
    po = frappe.get_doc("Purchase Order", po_name)
    reason_for_rejection = data.get("reason_for_rejection")


    po.reason_for_rejection = reason_for_rejection
    po.rejected_by = frappe.session.user

    po.status = "Rejected"

    po.save()
    frappe.db.commit()