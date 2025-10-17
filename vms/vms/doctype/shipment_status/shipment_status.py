# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_fullname
from vms.utils.custom_send_mail import custom_sendmail


class ShipmentStatus(Document):
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
				# List fields you want to track for changes
				fields_to_track = ['shipment_status', 'tracking_status', 'actual_pickup', 'shipment_amount']
				
				for field in fields_to_track:
					if self.get(field) != old_doc.get(field):
						return True
		return False
	
	def send_email_notification(self, is_new=False):
		
		purchase_team_email = self.get('raised_by')
		
		if not purchase_team_email:
			frappe.log_error(
				message="Purchase team email not found in Shipment Status",
				title="Email Notification Failed"
			)
			return
		
		# Prepare email content
		if is_new:
			subject = f"New Shipment Status Created: {self.name}"
			message = self.get_creation_email_content()
		else:
			subject = f"Shipment Status Updated: {self.name}"
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
				title="Shipment Status Email Failed"
			)
	
	def get_creation_email_content(self):
		return f"""
		<p>Dear Purchase Team,</p>
		
		<p>A new Shipment Status has been created:</p>
		
		<table style="border-collapse: collapse; width: 100%; max-width: 600px;">
			<tr>
				<td style="padding: 8px; border: 1px solid #ddd;"><strong>Shipment ID:</strong></td>
				<td style="padding: 8px; border: 1px solid #ddd;">{self.name}</td>
			</tr>
			<tr>
				<td style="padding: 8px; border: 1px solid #ddd;"><strong>Shipment Status:</strong></td>
				<td style="padding: 8px; border: 1px solid #ddd;">{self.get('shipment_status') or 'N/A'}</td>
			</tr>
			<tr>
				<td style="padding: 8px; border: 1px solid #ddd;"><strong>Tracking Status:</strong></td>
				<td style="padding: 8px; border: 1px solid #ddd;">{self.get('tracking_status') or 'N/A'}</td>
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
		
		<p>Please review the shipment details in the system.</p>
		
		<p>Best regards,<br>VMS Team</p>
		"""
	
	def get_update_email_content(self):
	
		old_doc = self.get_doc_before_save()
		changes_html = ""
		
		
		fields_to_track = {
			'shipment_status': 'Shipment Status',
			'tracking_status': 'Tracking Status',
			'actual_pickup': 'Actual Pickup Date',
			'shipment_amount': 'Shipment Amount',
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
		
		<p>Shipment Status <strong>{self.name}</strong> has been updated:</p>
		
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
