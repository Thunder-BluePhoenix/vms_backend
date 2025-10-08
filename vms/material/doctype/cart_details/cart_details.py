# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
import json
from vms.utils.custom_send_mail import custom_sendmail
from datetime import datetime
from vms.utils.execute_if_allowed import execute_if_allowed
from vms.utils.next_approver import update_next_approver
from vms.utils.notification_triggers import NotificationTrigger
from vms.APIs.approval.helpers.get_approval_matrix import get_stage_info
from vms.utils.get_approver_employee import (
    get_approval_employee,
    get_user_for_role_short,
)
from vms.utils.approval_utils import get_approval_next_role
from vms.utils.verify_user import get_current_user_document

class CartDetails(Document):
    def after_insert(self):
        self.add_first_in_approval_workflow()
        self.update_next_approver_role()
        
        exp_doc = frappe.get_doc("Cart Ageing Settings") or None

        if exp_doc != None:
            exp_t_sec = float(exp_doc.cart_check_duration)
        else:
            exp_t_sec = 10800
            
        # Enqueue a background job to handle vendor onboarding expiration
        exp_d_sec = exp_t_sec + 800
        frappe.enqueue(
            method=self.alternate_pt,
            queue='default',
            timeout=exp_d_sec,
            now=False,
            job_name=f'cart_expiration_{self.name}',
            # enqueue_after_commit = False
        )
        
        # sent_asa_form_link(self, method=None)

    def alternate_pt(self):
        exp_doc = frappe.get_doc("Cart Ageing Settings") or None

        if exp_doc != None:
            exp_t_sec = float(exp_doc.cart_check_duration)
        else:
            exp_t_sec = 10800

        exp_d_sec = exp_t_sec + 800
        time.sleep(exp_t_sec)
        if self.purchase_team_acknowledgement == 0 or self.asked_to_modify == 0:
            send_mail_alternate_purchase(self, method=None)

            frappe.enqueue(
                method=self.alternate_pt_ph,
                queue='default',
                timeout=exp_d_sec,
                now=False,
                job_name=f'cart_expiration_{self.name}',
                # enqueue_after_commit = False
            )
            
    def alternate_pt_ph(self):
        exp_doc = frappe.get_doc("Cart Ageing Settings") or None

        if exp_doc != None:
            exp_t_sec = float(exp_doc.cart_check_duration)
        else:
            exp_t_sec = 10800

        time.sleep(exp_t_sec)
        if self.purchase_team_acknowledgement == 0 or self.asked_to_modify == 0:
            send_mail_purchase_hod(self, method=None)
        else:
            pass

        # exp_d_sec = exp_t_sec + 300
        frappe.db.commit()
        
    def on_update(self):
        send_purchase_inquiry_email(self, method=None)
        self.update_next_approver_role()
        update_next_approver(self)

    def update_next_approver_role(self):
        approvals = self.get("approvals") or []
        if not approvals:
            self.db_set("next_approver_role", "")
            return

        last = approvals[-1]
        updated = last.get("next_action_role", "")

        if not updated:
            self.db_set("next_approver_role", updated)
            return

        if updated != self.get("next_approver_role", ""):
            self.db_set("next_approver_role", updated)

    def add_first_in_approval_workflow(self, approval_stage=None):
        try:
            stage_info = get_stage_info(
                "Cart Details", self, approval_stage
            )
            if not stage_info or not stage_info.get("cur_stage_info"):
                frappe.log_error(f"No approval matrix found for {self.name}")
                self.approval_status = "Pending Review"
                self.save(ignore_permissions=True)
                return
            
            self.approval_matrix = stage_info.get("approval_matrix", "")
            cur_stage = stage_info["cur_stage_info"]

            role = cur_stage.get("role", "") if cur_stage else ""
            from_hierarchy = cur_stage.get("from_hierarchy") if cur_stage else None

            approver = cur_stage.get("user") if cur_stage else ""
            stage_count = (
                cur_stage.get("approval_stage") if cur_stage.get("approval_stage") else 0
            )

            next_approver_role = ""
            next_approver_role = get_approval_next_role(cur_stage)

            if not next_approver_role and not approver:
                company = self.get("company")
                
                emp = (
                    get_approval_employee(
                        cur_stage.role,
                        company_list=[company],
                        fields=["user_id"],
                        doc=self,
                    )
                    if cur_stage
                    else None
                )

                approver = (
                    cur_stage.get("user")
                    if cur_stage
                    and cur_stage.get("approver_type") == "User"
                    and cur_stage.get("user")
                    else emp.get("user_id") if emp else ""
                )
                
                if not approver:
                    return self.add_first_in_approval_workflow(cur_stage.get("approval_stage") + 1)

            self.approval_status = cur_stage.get("approval_stage_name") or ""
            self.append(
                "approvals",
                {
                    "for_doc_type": "Cart Details",
                    "approval_stage": 0,
                    "approval_stage_name": cur_stage.get("approval_stage_name"),
                    "approved_by": "",
                    "approval_status": 0,
                    "next_approval_stage": stage_count,
                    "action": "",
                    "next_action_by": "" if next_approver_role else approver,
                    "next_action_role": next_approver_role,
                    "remark": "",
                },
            )

            self.save(ignore_permissions=True)

        except frappe.DoesNotExistError:
            frappe.log_error(f"No approval matrix configured for {self.name}")
            self.approval_status = "Pending Review"
            self.save(ignore_permissions=True)
            return

        except Exception as e:
            frappe.log_error(f"Approval workflow error: {str(e)}")
            self.approval_status = "Pending Review"  
            self.save(ignore_permissions=True)
            return


def send_purchase_inquiry_email(doc, method=None):
	if doc.user and not doc.rejected:
		if not doc.purchase_team_approved and not doc.mail_sent_to_purchase_team:
			send_mail_purchase(doc, method=None)
			# print("send_mail_purchase @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		elif doc.purchase_team_approved and not doc.hod_approved and not doc.mail_sent_to_hod:
			send_mail_hod(doc, method=None)
			# print("send_mail_hod @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		elif doc.hod_approved and not doc.ack_mail_to_user:
			send_mail_user(doc, method=None)
			# print("send_mail_user @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		else:
			pass
	elif doc.user and doc.rejected:
		rejection_mail_to_user(doc, method=None)
		# print("send_rejection_mail_user @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
	else:
		pass

	if doc.purchase_team_approved or doc.rejected :
		doc.is_approval = 1
	else: 
		doc.is_approval = 0
	

def send_mail_hod(doc, method=None):
	try:
		http_server = frappe.conf.get("backend_http")
		employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
		hod = frappe.get_value("Employee", {"user_id": doc.user}, "reports_to")
		if hod:
			hod_email = frappe.get_value("Employee", hod, "user_id")
			hod_name = frappe.get_value("Employee", hod, "full_name")
			if hod_email:
				approve_url = f"{http_server}/api/method/vms.material.doctype.cart_details.cart_details.hod_approval_check?cart_id={doc.name}&user={doc.user}&action=approve"
				reject_url = f"{http_server}/api/method/vms.material.doctype.cart_details.cart_details.hod_approval_check?cart_id={doc.name}&user={doc.user}&action=reject"
				
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
							<th>Final Price</th>
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
							<td>{row.final_price_by_purchase_team or ''}</td>
						</tr>
					"""

				table_html += "</table>"

				subject = f"Purchase Team Approved Cart Details Submitted by {employee_name}"

				# Message for HOD with buttons
				hod_message = f"""
					<p>Dear {hod_name},</p>		
					<p>A new cart details submission has been made by <b>{employee_name}</b> which is approved by Purchase Team.</p>
					<p>Please review the details and take necessary actions.</p>
					<p><b>Cart ID:</b> {doc.name}</p>
					<p><b>Cart Date:</b> {doc.cart_date}</p>
					<p><b>Cart Products:</b></p>
					{table_html}
					<br>
					<div style="margin: 20px 0px; text-align: center;">
						<a href="{approve_url}" style="display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px;">
							Approve
						</a>
						<a href="{reject_url}" style="display: inline-block; padding: 10px 20px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 4px;">
							Reject
						</a>
					</div>
					<p>Thank you!</p>
				"""

				# Message for user (without buttons)
				user_message = f"""
					<p>Dear {employee_name},</p>
					<p>Your cart has been approved by Purchase Team and sent to your HOD <b>{hod_name}</b> for further approval.</p>
					<p><b>Cart ID:</b> {doc.name}</p>
					<p><b>Cart Date:</b> {doc.cart_date}</p>
					<p><b>Cart Products:</b></p>
					{table_html}
					<p>Thank you!</p>
				"""

				# Send to HOD
				frappe.custom_sendmail(
					recipients=[hod_email],
					subject=subject,
					message=hod_message,
					now=True
				)

				# Send to User separately (without buttons)
				frappe.custom_sendmail(
					recipients=[doc.user],
					subject=subject,
					message=user_message,
					now=True
				)

				# Set flag
				frappe.db.set_value("Cart Details", doc.name, "mail_sent_to_hod", 1)

				return {
					"status": "success",
					"message": "Email sent to HOD and user successfully."
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

				subject = f"New Cart Details Submitted by {employee_name}"
				message = f"""
					<p>Dear Purchase Team,</p>		
					<p>A new cart details submission has been made by <b>{employee_name}</b>.</p>
					<p> please review the details and take necessary actions.</p>
					<p><b>Cart ID:</b> {doc.name}</p>
					<p><b>Cart Date:</b> {doc.cart_date}</p>
					<p><b>Cart Products:</b></p>
					{table_html}
					<p>Thank you!</p>
				"""
				frappe.custom_sendmail(recipients=[purchase_team_email], subject=subject, message=message, now=True)

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

		subject = f"HOD Approved the Cart Details Submitted by {employee_name}"
		message = f"""
			<p>Dear {employee_name},</p>		
			<p>Your cart details has been approved by HOD</b>.</p>
			<p><b>Cart ID:</b> {doc.name}</p>
			<p><b>Cart Date:</b> {doc.cart_date}</p>
			<p><b>Cart Products:</b></p>Your cart details has been approved by HOD0
			{table_html}
			<p>Thank you!</p>
		"""
		frappe.custom_sendmail(recipients=[doc.user], cc=[hod_email], subject=subject, message=message, now=True)

		# doc.ack_mail_to_user = 1
		frappe.db.set_value("Cart Details", doc.name, "ack_mail_to_user", 1)
		
		return {
			"status": "success",
			"message": "Email sent to User successfully."
		}
			
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error sending email to User")
		return {
			"status": "error",
			"message": "Failed to send email to User.",
			"error": str(e)
		}
	

# rejection mail to user
@frappe.whitelist(allow_guest=True)
def rejection_mail_to_user(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
		hod = frappe.get_value("Employee", {"user_id": doc.user}, "reports_to")
		if hod:
			hod_email = frappe.get_value("Employee", hod, "user_id")
			rejected_by = frappe.get_value("Employee", {"user_id": doc.rejected_by}, "full_name")

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

		subject = f"Your Cart Details Rejected by {rejected_by}"
		message = f"""
			<p>Dear {employee_name},</p>		
			<p>Your cart details has been rejected by {rejected_by}</b>.</p>
			<p><b>Cart ID:</b> {doc.name}</p>
			<p><b>Cart Date:</b> {doc.cart_date}</p>
			<p><b>Cart Products:</b></p>
			{table_html}
			<p>Thank you!</p>
		"""
		frappe.custom_sendmail(recipients=[doc.user], cc=[hod_email], subject=subject, message=message, now=True)

		# doc.ack_mail_to_user = 1
		frappe.db.set_value("Cart Details", doc.name, "ack_mail_to_user", 1)
		
		return {
			"status": "success",
			"message": "Email sent to User successfully."
		}
			
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error sending email to User")
		return {
			"status": "error",
			"message": "Failed to send email to User.",
			"error": str(e)
		}




# hod Approval Flow	
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

		# Prevent multiple submissions
		if doc.hod_approval_status in ["Approved", "Rejected"]:
			return {
				f"This cart has already been <b>{doc.hod_approval_status}",
				"Further action is not required.",
				f"Cart ID: {cart_id}"
			}

		if action == "approve":
			doc.hod_approved = 1
			doc.hod_approval_status = "Approved"
			doc.hod_approval_remarks = "Approved by HOD"
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

		return {
			"Thank you!",
			f"Your response has been recorded for Cart ID: {cart_id}",
			f"Status: {doc.hod_approval_status}"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error updating Cart Details (HOD Approval)")
		return {
			"status": "error",
			"message": "Failed to update Cart Details.",
			"error": str(e)
		}







def send_mail_alternate_purchase(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
		purchase_team_email = frappe.get_value("Category Master", doc.category_type, "alternative_purchase_team")
		
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

				subject = f"New Cart Details Submitted by {employee_name}"
				message = f"""
					<p>Dear Purchase Team,</p>		
					<p>A new cart details submission has been made by <b>{employee_name}</b>.</p>
					<p> please review the details and take necessary actions.</p>
					<p><b>Cart ID:</b> {doc.name}</p>
					<p><b>Cart Date:</b> {doc.cart_date}</p>
					<p><b>Cart Products:</b></p>
					{table_html}
					<p>Thank you!</p>
				"""
				frappe.custom_sendmail(recipients=[purchase_team_email], subject=subject, message=message, now=True)

				# doc.mail_sent_to_purchase_team = 1
				frappe.db.set_value("Cart Details", doc.name, "mailed_to_alternate_purchase_team", 1)
				
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




def send_mail_purchase_hod(doc, method=None):
	try:
		employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
		purchase_team_email = frappe.get_value("Category Master", doc.category_type, "purchase_team_user")
		pur_team = frappe.get_value("Employee", {"user_id": purchase_team_email}, "team")
		
		if purchase_team_email and pur_team:
			# Fetch all employees with same team and Purchase Head designation
			purchase_heads = frappe.get_all(
				"Employee",
				filters={
					"team": pur_team,
					"designation": "Purchase Head",
					"status": "Active"  # Only active employees
				},
				fields=["user_id", "full_name"]
			)
			
			if not purchase_heads:
				return {
					"status": "error",
					"message": "No Purchase Head found in the team.",
					"error": "No employees with 'Purchase Head' designation found in the team."
				}
			
			# Extract user_ids (email addresses) from purchase heads
			purchase_head_emails = [emp.user_id for emp in purchase_heads if emp.user_id]
			
			if not purchase_head_emails:
				return {
					"status": "error",
					"message": "No email addresses found for Purchase Heads.",
					"error": "Purchase Heads don't have valid user_id (email) configured."
				}
			
			# Build the table HTML
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

			subject = f"Cart Approval Required - Pending Review by {employee_name}"
			message = f"""
				<p>Dear Purchase Head,</p>		
				<p>A cart submission by <b>{employee_name}</b> is pending review and requires your approval.</p>
				<p>The purchase team has not yet reviewed this cart, so it has been escalated to you for further action.</p>
				<p>Please review the cart details below and take necessary actions:</p>
				<p><b>Cart ID:</b> {doc.name}</p>
				<p><b>Cart Date:</b> {doc.cart_date}</p>
				<p><b>Submitted by:</b> {employee_name}</p>
				<p><b>Team:</b> {pur_team}</p>
				<p><b>Cart Products:</b></p>
				{table_html}
				<p>Please approve or provide further instructions for this cart submission.</p>
				<p>Thank you!</p>
			"""
			
			# Send email to all Purchase Heads
			frappe.custom_sendmail(
				recipients=purchase_head_emails, 
				subject=subject, 
				message=message, 
				now=True
			)

			# Update the document to mark email as sent
			frappe.db.set_value("Cart Details", doc.name, "mailed_to_purchase_head", 1)
			
			return {
				"status": "success",
				"message": f"Email sent to {len(purchase_head_emails)} Purchase Head(s) successfully.",
				"recipients": purchase_head_emails
			}
		
		return {
			"status": "error",
			"message": "Purchase Team information not found.",
			"error": "Either purchase team email or team information is missing."
		}
			
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error sending email to Purchase Heads")
		return {
			"status": "error",
			"message": "Failed to send email to Purchase Heads.",
			"error": str(e)
		}