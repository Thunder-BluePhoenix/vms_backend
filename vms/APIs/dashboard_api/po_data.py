import frappe
import json


@frappe.whitelist(allow_guest = True)
def get_po():
    all_po = frappe.get_all("Purchase Order", fields ="*")
    return all_po