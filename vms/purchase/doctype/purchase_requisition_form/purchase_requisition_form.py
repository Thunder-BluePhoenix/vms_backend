# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

import frappe
from datetime import datetime



class PurchaseRequisitionForm(Document):
	def after_insert(self):
		try:
			# Find PR Webform that links to this SAP PR
			pr_webform_name = frappe.db.get_value(
				"Purchase Requisition Webform",
				{"purchase_requisition_form_link": self.name},
				"name"
			)
			
			if pr_webform_name:
				from vms.purchase.doctype.cart_aging_track.cart_aging_track import update_aging_track_on_sap_pr_creation
				update_aging_track_on_sap_pr_creation(pr_webform_name, self.name)
		except Exception as e:
			frappe.log_error(
				title=f"Error updating Cart Aging Track on SAP PR creation for {self.name}",
				message=frappe.get_traceback()
			)
	def before_save(doc, method=None):
	# Get current date or use doc date (you can also use doc.transaction_date or any other date field)
		if doc.prf_name_for_sap == None or doc.prf_name_for_sap == "":
			now = datetime.now()
			year_month_prefix = f"P{now.strftime('%y')}{now.strftime('%m')}"  

			# Get max existing count for this prefix
			# Filter by prf_name_for_sap starting with year_month_prefix
			existing_max = frappe.db.sql(
				"""
				SELECT MAX(CAST(SUBSTRING(prf_name_for_sap, 6) AS UNSIGNED))
				FROM `tabPurchase Requisition Form`
				WHERE prf_name_for_sap LIKE %s
				""",
				(year_month_prefix + "%",),
				as_list=True
			)

			max_count = existing_max[0][0] or 0
			new_count = max_count + 1

			# Format new prf_name_for_sap with zero-padded count (6 digits)
			doc.prf_name_for_sap = f"{year_month_prefix}{str(new_count).zfill(5)}"
