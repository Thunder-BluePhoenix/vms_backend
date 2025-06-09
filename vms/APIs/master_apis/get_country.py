import frappe
import json


@frappe.whitelist(allow_guest=True)
def country_details(data):
    country = data.get("country")

    country_details = frappe.get_doc("Country Master", country)
    mobile_code = None
    if country_details.mobile_code != None:
        mobile_code = country_details.mobile_code
    else:
        mobile_code = "None"

    return mobile_code