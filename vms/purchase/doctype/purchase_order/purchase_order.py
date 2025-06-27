# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta, date
from frappe.utils.jinja import render_template
from frappe.utils import today, getdate
from frappe.utils import now_datetime, get_datetime
import datetime



class PurchaseOrder(Document):
	def validate(self):
		for item in self.po_items:
			it_qty = item.quantity or "0"
			it_rate = item.rate or "0"
			qty = float(it_qty)
			rate = float(it_rate)
			item.price = float(qty*rate)

	def on_update(self):
		if self.approved_from_vendor == 1:
			notf_sett_doc = frappe.get_doc("Dispatch Notification Setting")

			delivery_date = get_datetime(self.delivery_date)
			current_date = now_datetime()


			total_seconds = (delivery_date - current_date).total_seconds()

			print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", total_seconds)
			
			notf_time_sec = float(notf_sett_doc.dispatch_notification)

			# Time after which to trigger the notification
			exp_t_sec = total_seconds - notf_time_sec
			exp_t_sec = exp_t_sec if exp_t_sec > 0 else 0 

			exp_d_sec = exp_t_sec + 800

			print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", exp_t_sec ,exp_d_sec)

			frappe.enqueue(
				method=self.handle_notification,
				queue='default',
				timeout=exp_d_sec,
				now=False,
				job_name=f'Dispatch Order notification Trigger {self.name}',
			)


# def handle_notification(self):
# 	pass







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