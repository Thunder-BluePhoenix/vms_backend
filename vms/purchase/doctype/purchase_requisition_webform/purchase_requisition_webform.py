# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import uuid


class PurchaseRequisitionWebform(Document):
	def before_save(self):
		set_unique_id(self, method=None)
		# pass
		send_pur_req_email(self, method=None)

	def on_update(self):
		set_purchase_req_id(self)
		field_map = [
			"purchase_requisition_type",
			"plant",
			"company",
			"requisitioner",
			"purchase_group",
			"purchase_requisition_date"
		]

		child_field_map = {
			# Head Fields
			"purchase_requisition_item_head": "purchase_requisition_item_head",
			"item_number_of_purchase_requisition_head": "item_number_of_purchase_requisition_head",
			"purchase_requisition_date_head": "purchase_requisition_date_head",
			"purchase_requisition_type": "purchase_requisition_type",
			"delivery_date_head": "delivery_date_head",
			"store_location_head": "store_location_head",
			"item_category_head": "item_category_head",
			"material_group_head": "material_group_head",
			"uom_head": "uom_head",
			"cost_center_head": "cost_center_head",
			"main_asset_no_head": "main_asset_no_head",
			"asset_subnumber_head": "asset_subnumber_head",
			"profit_ctr_head": "profit_ctr_head",
			"short_text_head": "short_text_head",
			"line_item_number_head": "line_item_number_head",
			"company_code_area_head": "company_code_area_head",
			"c_delivery_date_head": "c_delivery_date_head",
			"quantity_head": "quantity_head",
			"price_of_purchase_requisition_head": "price_of_purchase_requisition_head",
			"gl_account_number_head": "gl_account_number_head",
			"material_code_head": "material_code_head",
			"account_assignment_category_head": "account_assignment_category_head",
			"purchase_group_head": "purchase_group_head",
			"product_name_head": "product_name_head",
			"product_price_head": "product_price_head",
			"final_price_by_purchase_team_head": "final_price_by_purchase_team_head",
			"lead_time_head": "lead_time_head",
			"plant_head": "plant_head",
			"requisitioner_name_head": "requisitioner_name_head",
			"tracking_id_head": "tracking_id_head",
			"desired_vendor_head": "desired_vendor_head",
			"valuation_area_head": "valuation_area_head",
			"fixed_value_head": "fixed_value_head",
			"spit_head": "spit_head",
			"purchase_organisation_head": "purchase_organisation_head",
			"agreement_head": "agreement_head",
			"item_of_head": "item_of_head",
			"mpn_number_head": "mpn_number_head",
			"status_head": "status_head",
			"head_unique_id": "head_unique_id",
			# Subhead Fields
			"sub_head_unique_id": "sub_head_unique_id",
			"purchase_requisition_item_subhead": "purchase_requisition_item_subhead",
			"item_number_of_purchase_requisition_subhead": "item_number_of_purchase_requisition_subhead",
			"purchase_requisition_date_subhead": "purchase_requisition_date_subhead",
			"delivery_date_subhead": "delivery_date_subhead",
			"store_location_subhead": "store_location_subhead",
			"item_category_subhead": "item_category_subhead",
			"material_group_subhead": "material_group_subhead",
			"uom_subhead": "uom_subhead",
			"cost_center_subhead": "cost_center_subhead",
			"main_asset_no_subhead": "main_asset_no_subhead",
			"asset_subnumber_subhead": "asset_subnumber_subhead",
			"profit_ctr_subhead": "profit_ctr_subhead",
			"short_text_subhead": "short_text_subhead",
			"quantity_subhead": "quantity_subhead",
			"price_of_purchase_requisition_subhead": "price_of_purchase_requisition_subhead",
			"gl_account_number_subhead": "gl_account_number_subhead",
			"material_code_subhead": "material_code_subhead",
			"account_assignment_category_subhead": "account_assignment_category_subhead",
			"purchase_group_subhead": "purchase_group_subhead",
			"line_item_number_subhead": "line_item_number_subhead",
			"service_number_subhead": "service_number_subhead",
			"gross_price_subhead": "gross_price_subhead",
			"currency_subhead": "currency_subhead",
			"service_type_subhead": "service_type_subhead",
			"net_value_subhead": "net_value_subhead",
			# Utility
			"is_deleted": "is_deleted",
			"is_created": "is_created"
		}

		if not self.purchase_requisition_form_link:
			pur_req_form = frappe.new_doc("Purchase Requisition Form")
		else:
			pur_req_form = frappe.get_doc("Purchase Requisition Form", self.purchase_requisition_form_link)

		# Update main fields
		for field in field_map:
			if hasattr(pur_req_form, field):
				pur_req_form.set(field, self.get(field))

		# Clear and update child table
		pur_req_form.set("purchase_requisition_form_table", [])
		for item in self.get("purchase_requisition_form_table"):
			new_row = pur_req_form.append("purchase_requisition_form_table", {})
			for src_field, target_field in child_field_map.items():
				new_row.set(target_field, item.get(src_field))

		pur_req_form.save()

		# Link the form
		if not self.purchase_requisition_form_link:
			self.db_set("purchase_requisition_form_link", pur_req_form.name)



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
					subject=subject,
					message=message,
					now=True
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
		# pur_head = frappe.get_all("Employee", filters={"designation": "Purchase Head"}, fields=["user_id"])
		pur_grp_team = frappe.db.get_value("Purchase Group Master", doc.purchase_group, "team")
		pur_head = frappe.get_all(
			"Employee",
			filters={
				"team": pur_grp_team,
				"designation": "Purchase Head"
			},
			fields=["user_id"]
		)

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
				subject=subject,
				message=message,
				now=True
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
			subject=subject,
			message=message,
			now=True
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
	

def set_unique_id(doc, method=None):
	try:
		item_head_map = {}

		# Step 1: Build map of existing head_unique_ids
		for row in doc.purchase_requisition_form_table:
			head_no = str(row.item_number_of_purchase_requisition_head).strip() if row.item_number_of_purchase_requisition_head else None
			if head_no and row.head_unique_id:
				item_head_map[head_no] = row.head_unique_id

		# Step 2: Assign missing unique IDs
		for row in doc.purchase_requisition_form_table:
			head_no = str(row.item_number_of_purchase_requisition_head).strip() if row.item_number_of_purchase_requisition_head else None
			if head_no:
				# Assign head_unique_id (same for head and all subheads under it)
				if not row.head_unique_id:
					if head_no in item_head_map:
						row.head_unique_id = item_head_map[head_no]
					else:
						new_uid = str(uuid.uuid4())[:8]
						item_head_map[head_no] = new_uid
						row.head_unique_id = new_uid

				# Assign sub_head_unique_id only if not already set
				if not row.sub_head_unique_id:
					row.sub_head_unique_id = str(uuid.uuid4())[:8]

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Set Unique ID Error")
		raise


# when purchase req is created then in cart deatils mark as purchase req created
def set_purchase_req_id(doc):
	if doc.cart_details_id:
		cart_details = frappe.get_doc("Cart Details", doc.cart_details_id)
		if not cart_details.purchase_requisition_form_created:
			cart_details.purchase_requisition_form_created = 1
			cart_details.purchase_requisition_form = doc.name
			cart_details.save(ignore_permissions=True)
			
