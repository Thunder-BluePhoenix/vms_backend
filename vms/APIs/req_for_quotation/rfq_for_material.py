import frappe
import json

@frappe.whitelist(allow_guest=False)
def add_pr_number():
    pass