# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CartDetails(Document):
	def on_update(self):
		send_purchase_inquiry_email(self, method=None)


def send_purchase_inquiry_email(doc, method=None):
	if doc.user and not doc.rejected:
		if not doc.hod_approved and not doc.mail_sent_to_hod:
			send_mail_hod(doc, method=None)
			print("send_mail_hod @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		elif doc.hod_approved and not doc.purchase_team_approved and not doc.mail_sent_to_purchase_team:
			send_mail_purchase(doc, method=None)
			print("send_mail_purchase @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		elif doc.purchase_team_approved and not doc.ack_mail_to_user:
			send_mail_user(doc, method=None)
			print("send_mail_user @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		else:
			pass
	else:
		pass

def send_mail_hod(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
		hod = frappe.get_value("Employee", {"user_id": doc.user}, "reports_to")
		if hod:
			hod_email = frappe.get_value("Employee", hod, "user_id")
			hod_name = frappe.get_value("Employee", hod, "full_name")
			if hod_email:
				approve_url = f"{frappe.utils.get_url()}/api/method/vms.material.doctype.cart_details.cart_details.hod_approval_check?cart_id={doc.name}&user={doc.user}&action=approve"
				reject_url = f"{frappe.utils.get_url()}/api/method/vms.material.doctype.cart_details.cart_details.hod_approval_check?cart_id={doc.name}&user={doc.user}&action=reject"
				
				table_html = """
					<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
						<tr>
							<th>Asset Code</th>
							<th>Product Name</th>
							<th>Product Quantity</th>
							<th>UOM</th>
							<th>Product Price</th>
							<th>Lead Time</th>
							<th>User Specifications</th>
						</tr>
				"""

				for row in doc.cart_product:
					table_html += f"""
						<tr>
							<td>{row.assest_code or ''}</td>
							<td>{frappe.db.get_value("VMS Product Master", row.product_name, "product_name") or ''}</td>
							<td>{row.product_quantity or ''}</td>
							<td>{row.uom or ''}</td>
							<td>{row.product_price or ''}</td>
							<td>{row.lead_time or ''}</td> 
							<td>{row.user_specifications or ''}</td>
						</tr>
					"""

				table_html += "</table>"

				subject = f"New Cart Details Submitted by {employee_name}"
				message = f"""
					<p>Dear {hod_name},</p>		
					<p>A new cart details submission has been made by <b>{employee_name}</b>.</p>
					<p> please review the details and take necessary actions.</p>
					<p><b>Cart ID:</b> {doc.name}</p>
					<p><b>Cart Date:</b> {doc.cart_date}</p>
					<p><b>Cart Products:</b></p>
					{table_html}
					<br>
					<p style="margin: 15px 0px;">
						<a href="{approve_url}" style="padding: 8px 15px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px;">Approve</a>
					</p>
					<p style="margin: 15px 0px;">
						<a href="{reject_url}" style="padding: 8px 15px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 4px;">Reject</a>
					</p>
					<p>Thank you!</p>
				"""
				frappe.sendmail(recipients=[hod_email], subject=subject, message=message, now=True)

				# doc.mail_sent_to_hod = 1
				frappe.db.set_value("Cart Details", doc.name, "mail_sent_to_hod", 1)
				
				return {
					"status": "success",
					"message": "Email sent to HOD successfully."
				}
		
		return {
			"status": "error",
			"message": "HOD email or user email not found.",
			"error": "No email address associated with the HOD."
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error sending email to HOD")
		return {
			"status": "error",
			"message": "Failed to send email to HOD.",
			"error": str(e)
		}


def send_mail_purchase(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
		purchase_team_email = frappe.get_value("Category Master", doc.category_type, "purchase_team_user")
		
		if purchase_team_email:
				table_html = """
					<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
						<tr>
							<th>Asset Code</th>
							<th>Product Name</th>
							<th>Product Quantity</th>
							<th>UOM</th>
							<th>Product Price</th>
							<th>Lead Time</th>
							<th>User Specifications</th>
						</tr>
				"""

				for row in doc.cart_product:
					table_html += f"""
						<tr>
							<td>{row.assest_code or ''}</td>
							<td>{frappe.db.get_value("VMS Product Master", row.product_name, "product_name") or ''}</td>
							<td>{row.product_quantity or ''}</td>
							<td>{row.uom or ''}</td>
							<td>{row.product_price or ''}</td>
							<td>{row.lead_time or ''}</td> 
							<td>{row.user_specifications or ''}</td>
						</tr>
					"""

				table_html += "</table>"

				subject = f"HOD Approved the Cart Details Submitted by {employee_name}"
				message = f"""
					<p>Dear Purchase Team,</p>		
					<p>A new cart details submission has been made by <b>{employee_name}</b> which is approved by HOD</b>.</p>
					<p> please review the details and take necessary actions.</p>
					<p><b>Cart ID:</b> {doc.name}</p>
					<p><b>Cart Date:</b> {doc.cart_date}</p>
					<p><b>Cart Products:</b></p>
					{table_html}
					<p>Thank you!</p>
				"""
				frappe.sendmail(recipients=[purchase_team_email], subject=subject, message=message, now=True)

				# doc.mail_sent_to_purchase_team = 1
				frappe.db.set_value("Cart Details", doc.name, "mail_sent_to_purchase_team", 1)
				
				return {
					"status": "success",
					"message": "Email sent to Purchase Team successfully."
				}
		return{
			"status": "error",
			"message": "Purchase Team email not found.",
			"error": "No email address associated with the Purchase Team."
		}
			
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error sending email to Purchase Team")
		return {
			"status": "error",
			"message": "Failed to send email to Purchase Team.",
			"error": str(e)
		}

def send_mail_user(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
		hod = frappe.get_value("Employee", {"user_id": doc.user}, "reports_to")
		if hod:
			hod_email = frappe.get_value("Employee", hod, "user_id")

		table_html = """
			<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
				<tr>
					<th>Asset Code</th>
					<th>Product Name</th>
					<th>Product Quantity</th>
					<th>UOM</th>
					<th>Product Price</th>
					<th>Lead Time</th>
					<th>User Specifications</th>
				</tr>
		    """

		for row in doc.cart_product:
			table_html += f"""
				<tr>
					<td>{row.assest_code or ''}</td>
					<td>{frappe.db.get_value("VMS Product Master", row.product_name, "product_name") or ''}</td>
					<td>{row.product_quantity or ''}</td>
					<td>{row.uom or ''}</td>
					<td>{row.product_price or ''}</td>
					<td>{row.lead_time or ''}</td> 
					<td>{row.user_specifications or ''}</td>
				</tr>
			"""

		table_html += "</table>"

		subject = f"Purchase Team Approved the Cart Details Submitted by {employee_name}"
		message = f"""
			<p>Dear {employee_name},</p>		
			<p>Your cart details has been approved by Purchase Team</b>.</p>
			<p><b>Cart ID:</b> {doc.name}</p>
			<p><b>Cart Date:</b> {doc.cart_date}</p>
			<p><b>Cart Products:</b></p>
			{table_html}
			<p>Thank you!</p>
		"""
		frappe.sendmail(recipients=[doc.user], cc=[hod_email], subject=subject, message=message, now=True)

		# doc.ack_mail_to_user = 1
		frappe.db.set_value("Cart Details", doc.name, "ack_mail_to_user", 1)
		
		return {
			"status": "success",
			"message": "Email sent to Purchase Team successfully."
		}
			
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error sending email to Purchase Team")
		return {
			"status": "error",
			"message": "Failed to send email to Purchase Team.",
			"error": str(e)
		}
	
@frappe.whitelist(allow_guest=True)
def hod_approval_check():
	try:
		cart_id = frappe.form_dict.get("cart_id")
		user = frappe.form_dict.get("user")
		action = frappe.form_dict.get("action")
		comments = frappe.form_dict.get("comments") or ""
		reason_for_rejection = frappe.form_dict.get("rejection_reason") or ""

		if not cart_id or not user or not action:
			return {
				"status": "error",
				"message": "Missing required parameters."
			}

		doc = frappe.get_doc("Cart Details", cart_id)

		if action == "approve":
			doc.hod_approved = 1
			doc.hod_approval_status = "Approved"
			doc.hod_approval_remarks = comments
		elif action == "reject":
			doc.rejected = 1
			doc.rejected_by = user
			doc.hod_approval_status = "Rejected"
			doc.reason_for_rejection = reason_for_rejection
		else:
			return {
				"status": "error",
				"message": "Invalid action. Must be 'approve' or 'reject'."
			}

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return """
			<html>
				<body style="text-align: center; padding: 50px; font-family: Arial;">
					<h2>Thank you!</h2>
					<p>Your response has been recorded for Cart ID: <b>{}</b>.</p>
				</body>
			</html>
		""".format(cart_id)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error updating Cart Details (HOD Approval)")
		return {
			"status": "error",
			"message": "Failed to update Cart Details.",
			"error": str(e)
		}