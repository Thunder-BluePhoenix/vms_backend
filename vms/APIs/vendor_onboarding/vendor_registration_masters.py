import frappe
import json

@frappe.whitelist(allow_guest=True)
def vendor_registration_dropdown_masters():
    try:
        vendor_type = frappe.db.sql("SELECT name FROM `tabVendor Type Master`", as_dict=True)
        vendor_title = frappe.db.sql("SELECT name FROM `tabVendor Title`", as_dict=True)
        country_master = frappe.db.sql("SELECT name FROM `tabCountry Master`", as_dict=True)
        company_master = frappe.db.sql("SELECT name FROM `tabCompany Master`", as_dict=True)
        country_master = frappe.db.sql("SELECT name FROM `tabCountry Master`", as_dict=True)
        incoterm_master = frappe.db.sql("SELECT name FROM `tabIncoterm Master`", as_dict=True)

        return {
            "status": "success",
            "message": "Dropdown masters fetched successfully.",
            "data": {
                "vendor_type": vendor_type,
                "vendor_title": vendor_title,
                "country_master": country_master,
                "company_master": company_master,
                "country_master": country_master,
                "incoterm_master": incoterm_master
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dropdown Master Fetch Error")
        return {
            "status": "error",
            "message": "Failed to fetch dropdown values.",
            "error": str(e)
        }
