import frappe
from frappe import _

@frappe.whitelist(allow_guest = True)
def get_qms_details(vendor_onboarding):
    vn_onb = frappe.get_doc("")
    pass