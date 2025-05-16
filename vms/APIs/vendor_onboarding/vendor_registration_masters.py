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


@frappe.whitelist(allow_guest=True)
def vendor_onboarding_company_dropdown_master():
    try:
        type_of_business = frappe.db.sql("SELECT name FROM `tabType of Business`", as_dict=True)
        company_nature_master = frappe.db.sql("SELECT name FROM `tabCompany Nature Master`", as_dict=True)
        business_nature_master = frappe.db.sql("SELECT name FROM `tabBusiness Nature Master`", as_dict=True)
        
        return {
            "status": "success",
            "message": "Dropdown company masters fetched successfully.",
            "data": {
                "type_of_business": type_of_business,
                "company_nature_master": company_nature_master,
                "business_nature_master": business_nature_master
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dropdown company Master Fetch Error")
        return {
            "status": "error",
            "message": "Failed to fetch dropdown company masters values.",
            "error": str(e)
        }
    
@frappe.whitelist(allow_guest=True)
def address_filter(city_name=None):
    if not city_name:
        return {
            "status": "error",
            "message": "City name is required."
        }

    try:
        # filter city
        district = frappe.db.get_value("City Master", city_name, "district")

        # filter district
        state = frappe.db.get_value("District Master", district, "state")

        # filter state
        country = frappe.db.get_value("State Master", state, "country")

        return {
            "status": "success",
            "data": {
                "city": city_name,
                "district": district,
                "state": state,
                "country": country
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Address Filter Error")
        return {
            "status": "error",
            "message": "Failed to fetch address hierarchy.",
            "error": str(e)
        }
