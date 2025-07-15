import frappe

@frappe.whitelist(allow_guest=True)
def vendor_list(rfq_type):
    pass