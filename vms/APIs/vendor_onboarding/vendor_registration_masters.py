import frappe
import json

# Vednor Type, Vendor Title, Country, Company, Currency, Incoterm Masters
@frappe.whitelist(allow_guest=True)
def vendor_registration_dropdown_masters():
    try:
        vendor_type = frappe.db.sql("SELECT name  FROM `tabVendor Type Master`", as_dict=True)
        vendor_title = frappe.db.sql("SELECT name FROM `tabVendor Title`", as_dict=True)
        country_master = frappe.db.sql("SELECT name, country_name FROM `tabCountry Master`", as_dict=True)
        company_master = frappe.db.sql("SELECT name, company_name FROM `tabCompany Master`", as_dict=True)
        currency_master = frappe.db.sql("SELECT name, currency_name FROM `tabCurrency Master`", as_dict=True)
        incoterm_master = frappe.db.sql("SELECT name, incoterm_name FROM `tabIncoterm Master`", as_dict=True)

        return {
            "status": "success",
            "message": "Dropdown masters fetched successfully.",
            "data": {
                "vendor_type": vendor_type,
                "vendor_title": vendor_title,
                "country_master": country_master,
                "company_master": company_master,
                "currency_master": currency_master,
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

# Type of Business, Company Nature, Business Nature Masters
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

# Filters the city, district, state and country Masters    
import frappe

@frappe.whitelist(allow_guest=True)
def address_filter(city_name=None, district_name=None, state_name=None, country_name=None):
    try:
        result = {}

        if city_name:
            city = frappe.get_doc("City Master", city_name)
            result["city"] = city.name
            result["district"] = city.district
            result["state"] = city.state
            result["country"] = city.country

        elif district_name:
            district = frappe.get_doc("District Master", district_name)
            result["district"] = district.name
            result["state"] = district.state
            result["country"] = district.country

        elif state_name:
            state = frappe.get_doc("State Master", state_name)
            result["state"] = state.name
            result["country"] = state.country

        elif country_name:
            result["country"] = country_name

        else:
            return {
                "status": "error",
                "message": "Please provide at least one parameter (city_name, district_name, state_name, or country_name)"
            }
        

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Address Filter Error")
        return {
            "status": "error",
            "message": "Failed to fetch address hierarchy.",
            "error": str(e)
        }

