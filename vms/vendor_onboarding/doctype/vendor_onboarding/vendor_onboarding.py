# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
import json

class VendorOnboarding(Document):
	def after_insert(self):
		exp_doc = frappe.get_doc("Vendor Onboarding Settings") or None

		if exp_doc != None:
			exp_t_sec = float(exp_doc.vendor_onboarding_form_validity)
			
		else:
			exp_t_sec = 604800
			
		# Enqueue a background job to handle vendor onboarding expiration
		exp_d_sec = exp_t_sec + 800
		frappe.enqueue(
			method=self.handle_expiration,
			queue='default',
			timeout=exp_d_sec,
			now=False,
			job_name=f'vendor_onboarding_time_expiration_{self.name}',
			# enqueue_after_commit = False
		)

	def handle_expiration(self):
		exp_doc = frappe.get_doc("Vendor Onboarding Settings") or None

		if exp_doc != None:
			exp_t_sec = float(exp_doc.vendor_onboarding_form_validity)
			
		else:
			exp_t_sec = 604800
		time.sleep(exp_t_sec)
		if self.form_fully_submitted_by_vendor == 0:
			self.db_set('expired', 1, update_modified=False)
			self.db_set('onboarding_form_status', "Expired", update_modified=False)

		else:
			pass

		# exp_d_sec = exp_t_sec + 300
		frappe.db.commit()
