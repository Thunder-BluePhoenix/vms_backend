# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime


class SupplierQMSAssessmentForm(Document):
	def on_update(self):
		# set_unique_data(self, method=None)
		# set_qms_form_link(self, method=None)
		set_qms_form_link_unique_data(self, method=None)

	# def before_save(self):
	# 	# set_qms_form_link(self, method=None)
	# 	set_unique_data(self, method=None)




@frappe.whitelist(allow_guest=True)
def set_qms_form_link(doc, method=None):

	if doc.vendor_onboarding != None:
		ven_onb = frappe.get_doc("Vendor Onboarding", doc.vendor_onboarding)
		ven_onb.qms_form_link = doc.unique_name
		ven_onb.qms_form_filled = 1
		ven_onb.save()
		frappe.db.commit()



def set_unique_data(doc, method=None):
	if doc.unique_name == None or doc.unique_name == "":
		now = datetime.now()
		year_month_prefix = f"QMS{now.strftime('%y')}{now.strftime('%m')}"
		
		existing_max = frappe.db.sql(
			"""
			SELECT MAX(CAST(SUBSTRING(unique_name, 8) AS UNSIGNED))
			FROM `tabSupplier QMS Assessment Form`
			WHERE unique_name LIKE %s
			""",
			(year_month_prefix + "%",),
			as_list=True
		)
		
		max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
		new_count = max_count + 1
		unique_name = f"{year_month_prefix}{str(new_count).zfill(5)}"

		frappe.db.set_value("Supplier QMS Assessment Form", doc.name, "unique_name", unique_name)





@frappe.whitelist(allow_guest=True)
def set_qms_form_link_unique_data(doc, method=None):
	# unique_name = None
	if doc.unique_name == None or doc.unique_name == "":
		now = datetime.now()
		year_month_prefix = f"QMS{now.strftime('%y')}{now.strftime('%m')}"
		
		existing_max = frappe.db.sql(
			"""
			SELECT MAX(CAST(SUBSTRING(unique_name, 8) AS UNSIGNED))
			FROM `tabSupplier QMS Assessment Form`
			WHERE unique_name LIKE %s
			""",
			(year_month_prefix + "%",),
			as_list=True
		)
		
		max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
		new_count = max_count + 1
		unique_name = f"{year_month_prefix}{str(new_count).zfill(5)}"

		frappe.db.set_value("Supplier QMS Assessment Form", doc.name, "unique_name", unique_name)
		if doc.vendor_onboarding != None:
			ven_onb = frappe.get_doc("Vendor Onboarding", doc.vendor_onboarding)
			frappe.db.set_value("Vendor Onboarding", ven_onb.name, "qms_form_link", unique_name)
			frappe.db.set_value("Vendor Onboarding", ven_onb.name, "qms_form_filled", 1)
			# ven_onb.qms_form_link = unique_name
			# ven_onb.qms_form_filled = 1
			# ven_onb.save()
			frappe.db.commit()

	