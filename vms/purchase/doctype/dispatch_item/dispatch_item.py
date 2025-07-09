# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class DispatchItem(Document):
	def on_update(self, method=None):
		calculate_pending_qty(self, method=None)
		try:
			for row in self.purchase_number:
				if not row.purchase_number:
					continue

				po = frappe.get_doc("Purchase Order", row.purchase_number)

				for item in po.po_items:
					# Skip if item already added
					if any(existing.row_id == item.name for existing in self.items):
						continue

					self.append("items", {
						"row_id": item.name,
						"po_number": po.name,
						"product_code": item.product_code,
						"product_name": item.product_name,
						"description": item.short_text,
						"quantity": item.quantity,
						"hsnsac": item.hsnsac,
						"uom": item.uom,
						"rate": item.rate,
						"amount": item.price,
						"pending_qty": item.pending_qty
					})

			# self.save(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "DispatchItem after_insert Error")


# calculating Pending Qty 
def calculate_pending_qty(doc, method=None):
	try:
		for row in doc.items:
			row.pending_qty = int(row.quantity) - int(row.dispatch_qty)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Pending Qty Calculation Error")
