import frappe
import json


@frappe.whitelist(allow_guest = True)
def get_po():
    all_po = frappe.get_all("Purchase Order", fields ="*", order_by = "modified desc")
    return all_po



@frappe.whitelist(allow_guest = True)
def get_po_details(data):
    po_name = data.get("po_name")
    po = frappe.get_doc("Purchase Order", po_name)
    return po.as_dict()

@frappe.whitelist(allow_guest = True)
def filtering_data(data):
    pass