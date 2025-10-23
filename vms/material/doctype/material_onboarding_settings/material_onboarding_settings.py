# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import string

BASE62 = string.digits + string.ascii_uppercase + string.ascii_lowercase



class MaterialOnboardingSettings(Document):

	def before_save(self):
		self.update_max_counter()


	def update_max_counter(self):
		length = self.requestor_id_char_number or 7
		try:
			length = int(length)
		except ValueError:
			length = 7

		base_chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
		max_counter = len(base_chars) ** length - 1

		self.max_request_id_counter = max_counter
		if not float(self.last_request_id_counter) or float(self.last_request_id_counter) > float(max_counter):
			self.last_request_id_counter = max_counter


@frappe.whitelist()
def validate_request_id_counters():
    doc = frappe.get_single("Material Onboarding Settings")
    length = doc.requestor_id_char_number or 7
    try:
        length = int(length)
    except ValueError:
        length = 7

    base_chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
    max_counter = len(base_chars) ** length - 1

    doc.max_request_id_counter = max_counter

    # Find the highest counter used in Requestor Master
    highest_id = frappe.db.sql("""
        SELECT request_id
        FROM `tabRequestor Master`
        WHERE LENGTH(request_id) = %s
        ORDER BY request_id DESC
        LIMIT 1
    """, length, as_dict=True)

    if highest_id:
        # Convert base62 string to int
        highest_counter = 0
        for i, char in enumerate(reversed(highest_id[0]['request_id'])):
            highest_counter += base_chars.index(char) * (len(base_chars) ** i)
        # Ensure last_request_id_counter is never below this
        if not doc.last_request_id_counter or doc.last_request_id_counter > max_counter:
            doc.last_request_id_counter = max_counter
        if doc.last_request_id_counter > highest_counter:
            doc.last_request_id_counter = highest_counter
    else:
        # No records in DB
        doc.last_request_id_counter = max_counter

    doc.save(ignore_permissions=True)
