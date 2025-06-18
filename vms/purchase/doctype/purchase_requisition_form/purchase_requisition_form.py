# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

import frappe
from datetime import datetime



class PurchaseRequisitionForm(Document):
	def before_save(doc, method=None):
	# Get current date or use doc date (you can also use doc.transaction_date or any other date field)
		if doc.prf_name_for_sap == None or doc.prf_name_for_sap == "":
			now = datetime.now()
			year_month_prefix = f"P{now.strftime('%y')}{now.strftime('%m')}"  # e.g. PRF2506

			# Get max existing count for this prefix
			# Filter by prf_name_for_sap starting with year_month_prefix
			existing_max = frappe.db.sql(
				"""
				SELECT MAX(CAST(SUBSTRING(prf_name_for_sap, 8) AS UNSIGNED))
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
