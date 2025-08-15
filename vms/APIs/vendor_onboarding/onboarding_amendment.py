import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.file_manager import save_file
import json



@frappe.whitelist()
def vendor_onboarding_amendment():
    usr = frappe.session