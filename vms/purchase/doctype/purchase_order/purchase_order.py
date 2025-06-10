# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta, date
from frappe.utils.jinja import render_template



class PurchaseOrder(Document):
	def validate(self):
		for item in self.po_items:
			it_qty = item.quantity or "0"
			it_rate = item.rate or "0"
			qty = float(it_qty)
			rate = float(it_rate)
			item.price = float(qty*rate)







@frappe.whitelist(allow_guest=True)
def get_po_printfomat(po_name):
	if not po_name:
		frappe.throw("Missing Purchase Order name")

	po_doc = frappe.get_doc("Purchase Order", po_name)
	pf_name = frappe.db.get_single_value("Print Format Settings", "purchase_order_print_format")

	pdf_content = frappe.get_print(
		doctype="Purchase Order",
		name=po_doc.name,
		print_format=pf_name,
		as_pdf=True
	)

	frappe.local.response.filename = f"{po_doc.name}.pdf"
	frappe.local.response.filecontent = pdf_content
	frappe.local.response.type = "download"

#  send_email(message, subject, customer_email, pdf, f"{doc.name}.pdf")
        


@frappe.whitelist(allow_guest=True)
def get_po_whole(po_name):
	if not po_name:
		frappe.throw("Missing Purchase Order name")

	po_doc = frappe.get_doc("Purchase Order", po_name)

	return po_doc.ad_dict()