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
import time



class PurchaseOrder(Document):
	def validate(self):
		for item in self.po_items:
			it_qty = item.quantity or "0"
			it_rate = item.rate or "0"
			qty = float(it_qty)
			rate = float(it_rate)
			item.price = float(qty*rate)

	def on_update(self):
		if self.approved_from_vendor == 1 and self.sent_notification_triggered == 0 and self.po_dispatch_status != "Completed" and self.sent_notification_to_vendor == 0:
			notf_sett_doc = frappe.get_doc("Dispatch Notification Setting")
			
			
			delivery_date = get_datetime(self.delivery_date)
			delivery_date = delivery_date.replace(hour=23, minute=50, second=50, microsecond=0)
			
			
			current_date = now_datetime()
			
			
			total_seconds = int((delivery_date - current_date).total_seconds())

			# print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@TS:", total_seconds)
			
			notf_time_sec = int(notf_sett_doc.dispatch_notification)
			exp_t_sec = None
			exp_d_sec = None
			if total_seconds < notf_time_sec :
				exp_t_sec = int(float(total_seconds)*24/100)
				exp_d_sec = exp_t_sec + 800

			# Time after which to trigger the notification
			else:
				exp_t_sec = total_seconds - notf_time_sec
				# exp_t_sec = exp_t_sec if exp_t_sec > 0 else 0 

				exp_d_sec = exp_t_sec + 800

			# print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", exp_t_sec ,exp_d_sec)
			self.sent_notification_triggered = 1

			frappe.enqueue(
				method=self.handle_notification,
				queue='default',
				timeout=exp_d_sec,
				now=False,
				job_name=f'Dispatch Order notification Trigger {self.name}',
			)
			frappe.db.commit()


	def handle_notification(self):
		notf_sett_doc = frappe.get_doc("Dispatch Notification Setting")
			
			
		delivery_date = get_datetime(self.delivery_date)
		delivery_date = delivery_date.replace(hour=23, minute=50, second=50, microsecond=0)
		
		
		current_date = now_datetime()
		
		
		total_seconds = int((delivery_date - current_date).total_seconds())

		# print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@TS:", total_seconds)
		
		notf_time_sec = int(notf_sett_doc.dispatch_notification)
		exp_t_sec = None
		# exp_d_sec = None
		if total_seconds < notf_time_sec :
			exp_t_sec = int(float(total_seconds)*24/100)
			# exp_d_sec = exp_t_sec + 800

		
		else:
			exp_t_sec = total_seconds - notf_time_sec
			exp_t_sec = exp_t_sec if exp_t_sec > 0 else 0 

			# exp_d_sec = exp_t_sec + 800

		time.sleep(exp_t_sec)

		# function to send mail()

		self.sent_notification_triggered = 0
		self.sent_notification_to_vendor = 1
		self.save()
		frappe.db.commit()







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