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
		update_dispatch_qty(self, method=None)
		update_po_sign(self, method=None)
		print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", update_dispatch_qty(self, method=None))
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
			# frappe.db.commit()

			frappe.enqueue(
				method=self.handle_notification,
				queue='default',
				timeout=exp_d_sec,
				now=False,
				job_name=f'dispatch_order_notification_trigger_{self.name}',
			)
			# frappe.db.commit()


	def handle_notification(self):
		print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:", self.name)
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
			# exp_t_sec = exp_t_sec if exp_t_sec > 0 else 0 

			# exp_d_sec = exp_t_sec + 800

		time.sleep(exp_t_sec)

		# function to send mail()
		send_mail_to_vendor(self)

		self.sent_notification_triggered = 0
		self.sent_notification_to_vendor = 1
		# self.save()
		frappe.db.commit()


def send_mail_to_vendor(doc, method=None):
	try:
		vendor_code = frappe.get_doc("Purchase Order", doc.name).vendor_code
		if not vendor_code:
			return {"status": "error", "message": "No Vendor Code found In Purchase Order."}
		
		vendor_ref_doc = frappe.get_doc("Company Vendor Code", vendor_code).vendor_ref_no
		if not vendor_ref_doc:
			return {"status": "error", "message": "No matching Company Vendor Code found for vendor_code."}
		
		vendor_master_doc = frappe.get_doc("Vendor Master", vendor_ref_doc)

		vendor_email = vendor_master_doc.office_email_primary or vendor_master_doc.office_email_secondary
		vendor_name = vendor_master_doc.vendor_name
		if not vendor_email:
			return {"status": "error", "message": "No email found for vendor."}
		
		print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", vendor_email)

		if vendor_email:
			subject = "Send the notification for dispatch item" + doc.name
			message = "Send the notification for dispatch item"
			frappe.sendmail(
				recipients=vendor_email,
				subject=subject,
				message=message
			)

			return {
				"status": "success",
				"message": "Mail Sent Successfully"
			}
	
		else:
			return {
				"status": "error",
				"message": "No email found for vendor."
			}
	
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Failed to Send Mail")
		return {
			"status": "error",
			"message": "Failed to Send Mail",
			"error": str(e)
		}	









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

	return po_doc.as_dict()



# update dispatch qty in po
def update_dispatch_qty(doc, method=None):
	try:

		if doc.dispatched != 1:
			return
		dispatch_totals = {} 

		# Step 1: Get all relevant dispatches for this PO
		for dispatch_row in doc.dispatch_ids:
			if dispatch_row.dispatch_id:
				dispatch_item = frappe.get_doc("Dispatch Item", dispatch_row.dispatch_id)

				for dispatch_item_row in dispatch_item.items:
					if dispatch_item_row.po_number == doc.name:
						code = dispatch_item_row.product_code
						qty = int(dispatch_item_row.dispatch_qty or 0)
						if code in dispatch_totals:
							dispatch_totals[code] += qty
						else:
							dispatch_totals[code] = qty

		# Step 2: Update PO items based on fresh totals
		for po_item_row in doc.po_items:
			code = po_item_row.product_code
			if code in dispatch_totals:
				total_dispatch = dispatch_totals[code]

				po_item_row.dispatch_qty = total_dispatch
				po_item_row.db_set("dispatch_qty", total_dispatch)

				po_item_row.pending_qty = int(po_item_row.quantity or 0) - total_dispatch
				po_item_row.db_set("pending_qty", po_item_row.pending_qty)

		# Step 3: Update PO status
		if all((int(row.dispatch_qty or 0) >= int(row.quantity or 0)) for row in doc.po_items):
			doc.db_set("po_dispatch_status", "Completed")
			doc.db_set("status", "Dispatched")
		else:
			doc.db_set("po_dispatch_status", "Partial")

		if doc.email:
			employee = frappe.db.get_value("Employee", {"user_id": doc.email}, ["name", "full_name"], as_dict=True)
			if employee:
				employee_name = employee.full_name
				table_rows = ""
				for row in doc.po_items:
					table_rows += f"""
						<tr>
							<td>{row.product_code or ''}</td>
							<td>{row.product_name or ''}</td>
							<td>{row.material_code or ''}</td>
							<td>{row.quantity or ''}</td>
							<td>{row.rate or ''}</td>
							<td>{row.pending_qty or ''}</td>
							<td>{row.dispatch_qty or ''}</td>
							<td>{row.price or ''}</td>
							<td>{frappe.format_value(row.po_date or '', {'fieldtype': 'Date'})}</td>
							<td>{row.delivery_date or ''}</td>
						</tr>
					"""

				email_body = f"""
					<p>Dear {employee_name},</p>
					<p>The dispatch quantities for the following items in Purchase Order <b>{doc.name}</b> have been updated.</p>
					<table border="1" cellpadding="5" cellspacing="0">
						<tr>
							<th>Product Code</th>
							<th>Product Name</th>
							<th>Material Code</th>
							<th>Quantity</th>
							<th>Rate</th>
							<th>Pending Qty</th>
							<th>Dispatch Qty</th>
							<th>Net Amount</th>
							<th>PO Date</th>
							<th>Delivery Date</th>
						</tr>
						{table_rows}
					</table>
					<p>Regards,<br>VMS Team</p>
				"""

				frappe.sendmail(
					recipients=doc.email,
					subject=f"Dispatch Quantities Updated for PO {doc.name}",
					message=email_body,
					now=True
				)

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Update Dispatch Qty Error")
		raise





def update_po_sign(doc, method=None):
	if doc.approval_1 != None:
		sign_rec1 = frappe.get_value("Signature Record", {"sap_text_name":doc.approval_1}, "sap_signature")
		# print("sign_rec1")
		# doc.sign_of_approval1 = sign_rec1
		doc.db_set("sign_of_approval1", sign_rec1)

	if doc.approval_2 != None:
		sign_rec2 = frappe.get_value("Signature Record", {"sap_text_name":doc.approval_2}, "sap_signature")
		# print("sign_rec2")
		# doc.sign_of_approval2 = sign_rec2
		doc.db_set("sign_of_approval2", sign_rec2)

	if doc.approval_3 != None:
		sign_rec3 = frappe.get_value("Signature Record", {"sap_text_name":doc.approval_3}, "sap_signature")
		# print("sign_rec3")
		# doc.sign_of_approval3 = sign_rec3
		doc.db_set("sign_of_approval3", sign_rec3)
