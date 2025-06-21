# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PurchaseRequisitionWebform(Document):
	def on_update(self):
		send_pur_req_email(self, method=None)

		field_map = [
			"purchase_requisition_type",
			"plant",
			"company_code_area",
			"company",
			"requisitioner"
		]

		child_field_map = {
			"purchase_requisition_item": "purchase_requisition_item",
			"item_number_of_purchase_requisition": "item_number_of_purchase_requisition",
			"purchase_requisition_date": "purchase_requisition_date",
			"delivery_date": "delivery_date",
			"store_location": "store_location",
			"item_category": "item_category",
			"material_group": "material_group",
			"uom": "uom",
			"cost_center": "cost_center",
			"main_asset_no": "main_asset_no",
			"asset_subnumber": "asset_subnumber",
			"profit_ctr": "profit_ctr",
			"short_text": "short_text",
			"quantity": "quantity",
			"gl_account_number": "gl_account_number",
			"material_code": "material_code",
			"account_assignment_category": "account_assignment_category",
			"purchase_group": "purchase_group",
			"price_of_purchase_requisition": "price_in_purchase_requisition"
		}

		if not self.purchase_requisition_form_link:
			# Create new Purchase Requisition Form
			pur_req_form = frappe.new_doc("Purchase Requisition Form")

			for field in field_map:
				pur_req_form.set(field, self.get(field))

			for item in self.get("purchase_requisition_form_table"):
				new_row = pur_req_form.append("purchase_requisition_form_table", {})
				for src_field, target_field in child_field_map.items():
					new_row.set(target_field, item.get(src_field))

			pur_req_form.save()
			self.db_set("purchase_requisition_form_link", pur_req_form.name)

		else:
			# Update existing Purchase Requisition Form
			pur_req_form = frappe.get_doc("Purchase Requisition Form", self.purchase_requisition_form_link)

			for field in field_map:
				pur_req_form.set(field, self.get(field))

			# Clear existing child table to avoid mismatch
			pur_req_form.set("purchase_requisition_form_table", [])

			for item in self.get("purchase_requisition_form_table"):
				new_row = pur_req_form.append("purchase_requisition_form_table", {})
				for src_field, target_field in child_field_map.items():
					new_row.set(target_field, item.get(src_field))

			pur_req_form.save()


def send_pur_req_email(doc, method=None):
	if doc.requisitioner and not doc.rejected:
		if not doc.hod_approved and not doc.mail_sent_to_hod:
			send_mail_hod_pt(doc, method=None)
			print("send_mail_hod @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		elif doc.hod_approved and not doc.purchase_head_approved and not doc.mail_sent_to_purchase_head:
			send_mail_purchase_head(doc, method=None)
			print("send_mail_purchase @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		elif doc.purchase_head_approved and not doc.ack_mail_to_user:
			send_mail_user(doc, method=None)
			print("send_mail_user @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		else:
			pass
	else:
		pass


def send_mail_hod_pt(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.requisitioner}, "full_name")
		hod = frappe.get_value("Employee", {"user_id": doc.requisitioner}, "reports_to")
		pur_team = frappe.get_all("Employee", filters={"designation": "Purchase Team"}, fields=["user_id"])
		if hod:
			hod_email = frappe.get_value("Employee", hod, "user_id")
			hod_name = frappe.get_value("Employee", hod, "full_name")
			if hod_email:
				subject = f"New Purchase Requisition Raised by {employee_name}"
				message = f"""
					<p>Dear {hod_name},</p>		
					<p>A new <b>Purchase Requisition</b> has been raised by <b>{employee_name}</b>. Please review the details and take necessary actions.</p>
					<p>Thank you!</p>
				"""

				# Combine HOD and Purchase Team emails
				recipient_emails = [hod_email] + [p["user_id"] for p in pur_team if p.get("user_id")]
				recipient_emails = list(set(recipient_emails))

				frappe.sendmail(
					recipients=recipient_emails,
					cc=["rishi.hingad@merillife.com"],
					subject=subject,
					message=message
				)
				# doc.mail_sent_to_hod = 1
				frappe.db.set_value("Purchase Requisition Webform", doc.name, "mail_sent_to_hod", 1)
				frappe.db.set_value("Purchase Requisition Webform", doc.name, "mail_sent_to_purchase_team", 1)
				
				return {
					"status": "success",
					"message": "Email sent to HOD and Purchase Team successfully."
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



def send_mail_purchase_head(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.requisitioner}, "full_name")
		pur_head = frappe.get_all("Employee", filters={"designation": "Purchase Head"}, fields=["user_id"])
		if pur_head:
			subject = f"Purchase Requisition has been Approved by HOD which is Raised by {employee_name}"
			message = f"""
				<p>Dear Purchase Head,</p>		
				<p>A new <b>Purchase Requisition</b> has been raised by <b>{employee_name}</b>. Please review the details and take necessary actions.</p>
				<p>Thank you!</p>
			"""
			
			# Combine HOD and Purchase Team emails
			recipient_emails = [p["user_id"] for p in pur_head if p.get("user_id")]
			recipient_emails = list(set(recipient_emails))

			frappe.sendmail(
				recipients=recipient_emails,
				cc=["rishi.hingad@merillife.com"],
				subject=subject,
				message=message
			)
			# doc.mail_sent_to_hod = 1
			frappe.db.set_value("Purchase Requisition Webform", doc.name, "mail_sent_to_purchase_head", 1)
			
			return {
				"status": "success",
				"message": "Email sent to HOD and Purchase Team successfully."
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
	

def send_mail_user(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.requisitioner}, "full_name")
		hod = frappe.get_value("Employee", {"user_id": doc.requisitioner}, "reports_to")
		hod_email = frappe.get_value("Employee", hod, "user_id")
		subject = f"Purchase Requisition has been Approved by Purchase Head"
		message = f"""
			<p>Dear {employee_name},</p>		
			<p>Your <b>Purchase Requisition</b> has been Approved by <b>Purchase Head</b>. Please review the details and take necessary actions.</p>
			<p>Thank you!</p>
		"""
		frappe.sendmail(
			recipients=[doc.requisitioner, hod_email],
			cc=["rishi.hingad@merillife.com"],
			subject=subject,
			message=message
		)
		# doc.mail_sent_to_hod = 1
		frappe.db.set_value("Purchase Requisition Webform", doc.name, "ack_mail_to_user", 1)
		
		return {
			"status": "success",
			"message": "Email sent to HOD and Purchase Team successfully."
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error sending email to HOD")
		return {
			"status": "error",
			"message": "Failed to send email to HOD.",
			"error": str(e)
		}