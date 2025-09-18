import frappe
import json

# Vednor Type, Vendor Title, Country, Company, Currency, Incoterm Masters
# sap client code is added for extend vendor to filter the company

@frappe.whitelist(allow_guest=True)
def vendor_registration_dropdown_masters(sap_client_code=None):
    try:
        usr = frappe.session.user
        employee_list = frappe.get_all("Employee", filters={"user_id": usr}, limit_page_length=1)
        if employee_list:
            employee = frappe.get_doc("Employee", employee_list[0].name)
            team = employee.team
        else:
            team = None

        user_list = []
        if team:
            user_list = frappe.get_all("Employee", filters={"team": team, "designation": "Purchase Team"}, fields=["user_id", "full_name"])

        vendor_type = frappe.db.sql("SELECT name  FROM `tabVendor Type Master`", as_dict=True)
        vendor_title = frappe.db.sql("SELECT name FROM `tabVendor Title`", as_dict=True)
        country_master = frappe.db.sql("SELECT name, country_name, mobile_code FROM `tabCountry Master`", as_dict=True)

        # Conditional company master filter
        if sap_client_code:
            company_master = frappe.db.sql("""
                SELECT name, company_name, company_code, description, sap_client_code
                FROM `tabCompany Master`
                WHERE sap_client_code = %s
            """, (sap_client_code,), as_dict=True)
        else:
            company_master = frappe.db.sql("""
                SELECT name, company_name, company_code, description 
                FROM `tabCompany Master`
            """, as_dict=True)

        currency_master = frappe.db.sql("SELECT name, currency_name FROM `tabCurrency Master`", as_dict=True)
        incoterm_master = frappe.db.sql("SELECT name, incoterm_name FROM `tabIncoterm Master`", as_dict=True)
        reconciliation_account = frappe.db.sql("SELECT name, reconcil_account_code, reconcil_account, reconcil_description FROM `tabReconciliation Account`", as_dict=True)

        return {
            "status": "success",
            "message": "Dropdown masters fetched successfully.",
            "data": {
                "vendor_type": vendor_type,
                "vendor_title": vendor_title,
                "country_master": country_master,
                "company_master": company_master,
                "currency_master": currency_master,
                "incoterm_master": incoterm_master,
                "reconciliation_account": reconciliation_account,
                "users_list": user_list
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
  

@frappe.whitelist(allow_guest=True)
def all_address_masters():
    try:
        pincode_master = frappe.db.sql("SELECT name,zone FROM `tabPincode Master`", as_dict=True)
        city_master = frappe.db.sql("SELECT name, city_code, city_name FROM `tabCity Master`", as_dict=True)
        district_master = frappe.db.sql("SELECT name, district_code, district_name FROM `tabDistrict Master`", as_dict=True)
        state_master = frappe.db.sql("SELECT name, state_code, state_name FROM `tabState Master`", as_dict=True)
        country_master = frappe.db.sql("SELECT name, country_name, mobile_code FROM `tabCountry Master`", as_dict=True)
        
        return {
            "status": "success",
            "message": "Dropdown Document masters fetched successfully.",
            "data": {
                "pincode_master": pincode_master,
                "city_master": city_master,
                "district_master": district_master,
                "state_master": state_master,
                "country_master": country_master
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dropdown Document Master Fetch Error")
        return {
            "status": "error",
            "message": "Failed to fetch dropdown Document masters values.",
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def address_filter(pincode=None, city_name=None, district_name=None, state_name=None, country_name=None):
    try:
        result = {
            "pincode": [],
            "city": [],
            "district": [],
            "state": [],
            "country": []
        }

        if pincode:
            pincode_doc = frappe.get_doc("Pincode Master", pincode)

            city = frappe.db.get_value("City Master", pincode_doc.city, ["name", "city_code", "city_name"], as_dict=True) if pincode_doc.city else {}
            district = frappe.db.get_value("District Master", pincode_doc.district, ["name", "district_code", "district_name"], as_dict=True) if pincode_doc.district else {}
            state = frappe.db.get_value("State Master", pincode_doc.state, ["name", "state_code", "state_name"], as_dict=True) if pincode_doc.state else {}
            country = frappe.db.get_value("Country Master", pincode_doc.country, ["name", "country_code", "country_name"], as_dict=True) if pincode_doc.country else {}

            result["pincode"] = [{
                "name": pincode_doc.name,
                "zone": pincode_doc.zone
            }]

            result["city"] = [city] if city else []
            result["district"] = [district] if district else []
            result["state"] = [state] if state else []
            result["country"] = [country] if country else []

        elif city_name:
            city = frappe.get_doc("City Master", city_name)
            result["city"] = [{
                "name": city.name,
                "city_code": city.city_code,
                "city_name": city.city_name
            }]
            result["district"] = [{
                "name": city.district
            }]
            result["state"] = [{
                "name": city.state
            }]
            result["country"] = [{
                "name": city.country
            }]

        elif district_name:
            district = frappe.get_doc("District Master", district_name)
            result["district"] = [{
                "name": district.name,
                "district_code": district.district_code,
                "district_name": district.district_name
            }]
            result["state"] = [{
                "name": district.state
            }]
            result["country"] = [{
                "name": district.country
            }]
            cities = frappe.get_all("City Master", filters={"district": district.name}, fields=["name", "city_code", "city_name"])
            result["city"] = cities

        elif state_name:
            state = frappe.get_doc("State Master", state_name)
            result["state"] = [{
                "name": state.name,
                "state_code": state.state_code,
                "state_name": state.state_name
            }]
            result["country"] = [{
                "name": state.country_name
            }]
            districts = frappe.get_all("District Master", filters={"state": state.name}, fields=["name", "district_code", "district_name"])
            result["district"] = districts
            district_names = [d["name"] for d in districts]
            cities = frappe.get_all("City Master", filters={"district": ["in", district_names]}, fields=["name", "city_code", "city_name"])
            result["city"] = cities

        elif country_name:
            result["country"] = frappe.get_all("Country Master", filters={"name": country_name}, fields=["name", "country_code", "country_name"])
            states = frappe.get_all("State Master", filters={"country_name": country_name}, fields=["name", "state_code", "state_name"])
            result["state"] = states
            state_names = [s["name"] for s in states]
            districts = frappe.get_all("District Master", filters={"state": ["in", state_names]}, fields=["name", "district_code", "district_name"])
            result["district"] = districts
            district_names = [d["name"] for d in districts]
            cities = frappe.get_all("City Master", filters={"district": ["in", district_names]}, fields=["name", "city_code", "city_name"])
            result["city"] = cities

        else:
            return {
                "status": "error",
                "message": "Please provide at least one parameter (city_name, district_name, state_name, or country_name)"
            }


        return {
            "status": "success",
            "message": "Address hierarchy fetched successfully.",
            "data": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Address Filter Error")
        return {
            "status": "error",
            "message": "Failed to fetch address hierarchy.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def vendor_onboarding_document_dropdown_master():
    try:
        gst_vendor_type = frappe.db.sql("SELECT name, registration_ven_code, registration_ven_name FROM `tabGST Registration Type Master`", as_dict=True)
        state_master = frappe.db.sql("SELECT name, state_code, state_name FROM `tabState Master`", as_dict=True)

        return {
            "status": "success",
            "message": "Dropdown masters fetched successfully.",
            "data": {
                "gst_vendor_type": gst_vendor_type,
                "state_master": state_master
            }
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dropdown Document Master Fetch Error")
        return {
            "status": "error",
            "message": "Failed to fetch dropdown document values.",
            "error": str(e)
        }
    
@frappe.whitelist(allow_guest=True)
def vendor_onboarding_payment_dropdown_master():
    try:
        bank_name = frappe.db.sql("SELECT name, bank_code, bank_name FROM `tabBank Master`", as_dict=True)
        currency_master = frappe.db.sql("SELECT name, currency_code, currency_name FROM `tabCurrency Master`", as_dict=True)
        
        return {
            "status": "success",
            "message": "Dropdown Document masters fetched successfully.",
            "data": {
                "bank_name": bank_name,
                "currency_master": currency_master
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dropdown Document Master Fetch Error")
        return {
            "status": "error",
            "message": "Failed to fetch dropdown document values.",
            "error": str(e)
        }
    


