# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_fullname
from vms.utils.custom_send_mail import custom_sendmail


class ServiceBill(Document):
	def after_insert(self):
		frappe.enqueue(
			self.send_email_notification,
			queue='short',
			timeout=300,
			is_async=True,
			is_new=True
		)
	
	def on_update(self):

		if self.has_value_changed():
			frappe.enqueue(
				self.send_email_notification,
				queue='short',
				timeout=300,
				is_async=True,
				is_new=False
			)
	
	def has_value_changed(self):
		if not self.is_new():
			old_doc = self.get_doc_before_save()
			if old_doc:
				fields_to_track = ['bill_number', 'bill_amount', 'service_bill_status', 'bill_booking_ref_no','service_provider_name']
				
				for field in fields_to_track:
					if self.get(field) != old_doc.get(field):
						return True
		return False
	
	def send_email_notification(self, is_new=False):
		
		purchase_team_email = self.get('raised_by')
		
		if not purchase_team_email:
			frappe.log_error(
				message="Purchase team email not found in Service Bill",
				title="Email Notification Failed"
			)
			return
		
		# Prepare email content
		if is_new:
			subject = f"New Service Bill Created: {self.name}"
			message = self.get_creation_email_content()
		else:
			subject = f"Service Bill Updated: {self.name}"
			message = self.get_update_email_content()
		
		# Send email
		try:
			frappe.custom_sendmail(
				recipients=[purchase_team_email],
				subject=subject,
				message=message,
				now=True  
			)
		except Exception as e:
			frappe.log_error(
				message=f"Error sending email: {str(e)}",
				title="Service Bill Email Failed"
			)
	
	def get_creation_email_content(self):
		return f"""
		<p>Dear Purchase Team,</p>
		
		<p>A new Service Bill has been created:</p>
		
		<table style="border-collapse: collapse; width: 100%; max-width: 600px;">
			<tr>
				<td style="padding: 8px; border: 1px solid #ddd;"><strong>Service Bill ID:</strong></td>
				<td style="padding: 8px; border: 1px solid #ddd;">{self.name}</td>
			</tr>
			<tr>
				<td style="padding: 8px; border: 1px solid #ddd;"><strong>Service Bill Status:</strong></td>
				<td style="padding: 8px; border: 1px solid #ddd;">{self.get('service_bill_status') or 'N/A'}</td>
			</tr>
			<tr>
				<td style="padding: 8px; border: 1px solid #ddd;"><strong>Amount Paid:</strong></td>
				<td style="padding: 8px; border: 1px solid #ddd;">{self.get('amount_paid') or 'N/A'}</td>
			</tr>
			<tr>
				<td style="padding: 8px; border: 1px solid #ddd;"><strong>RFQ Number:</strong></td>
				<td style="padding: 8px; border: 1px solid #ddd;">{self.get('rfq_number') or 'N/A'}</td>
			</tr>
			<tr>
				<td style="padding: 8px; border: 1px solid #ddd;"><strong>Created By:</strong></td>
				<td style="padding: 8px; border: 1px solid #ddd;">{get_fullname(self.owner)}</td>
			</tr>
		</table>
		
		<p>Please review the service bill details in the system.</p>
		
		<p>Best regards,<br>VMS Team</p>
		"""
	
	def get_update_email_content(self):
	
		old_doc = self.get_doc_before_save()
		changes_html = ""
		
		
		fields_to_track = {
			'service_bill_status': 'Service Bill Status',
			'amount_paid': 'Amount Paid',
			'bill_number': 'Bill Number',
			'bill_amount': 'Bill Amount',
			'bill_booking_ref_no': 'Bill Booking Reference No',
			'service_provider_name': 'Service Provider Name'
		}
		
		if old_doc:
			for field, label in fields_to_track.items():
				old_value = old_doc.get(field) or 'Not Set'
				new_value = self.get(field) or 'Not Set'
				
				if old_value != new_value:
					changes_html += f"""
					<tr>
						<td style="padding: 8px; border: 1px solid #ddd;"><strong>{label}:</strong></td>
						<td style="padding: 8px; border: 1px solid #ddd; background-color: #ffebee;">{old_value}</td>
						<td style="padding: 8px; border: 1px solid #ddd; background-color: #e8f5e9;">{new_value}</td>
					</tr>
					"""
		
		return f"""
		<p>Dear Purchase Team,</p>
		
		<p>Service Bill <strong>{self.name}</strong> has been updated:</p>
		
		<table style="border-collapse: collapse; width: 100%; max-width: 700px;">
			<tr>
				<th style="padding: 8px; border: 1px solid #ddd; background-color: #f5f5f5;">Field</th>
				<th style="padding: 8px; border: 1px solid #ddd; background-color: #ffebee;">Old Value</th>
				<th style="padding: 8px; border: 1px solid #ddd; background-color: #e8f5e9;">New Value</th>
			</tr>
			{changes_html}
		</table>
		
		<p>Updated By: {get_fullname(self.modified_by)}</p>
		
		<p>Best regards,<br>VMS Team</p>
		"""
