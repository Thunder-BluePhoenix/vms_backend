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


