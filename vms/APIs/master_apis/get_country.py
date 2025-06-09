import frappe
import json


@frappe.whitelist(allow_guest=True)
def country_details(data):
    country = data.get("country")

    country_details = frappe.get_doc("Country Master", country)
    country_code = country_details.mobile_code

    return country_code