import frappe
import string
import random
from frappe.model.document import Document
from frappe.utils import get_url
from frappe.utils.pdf import get_pdf
import io
import base64

class CompanyVendorCode(Document):
	def on_update(self):
		vend = frappe.get_doc("Vendor Master", self.vendor_ref_no)
		found = False
		for mcd in vend.multiple_company_data:
			if mcd.company_name == self.company_name:
				mcd.company_vendor_code = self.name
				found = True
				break

		if not found:
			vend.append("multiple_company_data", {
				"company_vendor_code": self.name
			})
		# vend.db_update()
		
		# Collect all vendor code data for PDF
		vendor_code_data = self.collect_vendor_code_data(vend)
		
		if not frappe.db.exists("User", vend.office_email_primary):
			# User doesn't exist - create user and send email with PDF
			password = self.generate_random_password()
			
			# Create new user without sending welcome email
			new_user = frappe.new_doc("User")
			new_user.email = vend.office_email_primary
			new_user.first_name = vend.vendor_name or "Vendor"
			new_user.send_welcome_email = 0
			new_user.module_profile = "Vendor"
			new_user.role_profile_name = "Vendor"
			new_user.new_password = password
			
			new_user.insert(ignore_permissions=True)
			
			# Send email with credentials and PDF
			self.send_vendor_email_with_pdf(
				email=vend.office_email_primary,
				username=vend.office_email_primary,
				password=password,
				vendor_name=vend.vendor_name or "Vendor",
				vendor_code_data=vendor_code_data,
				is_new_user=True
			)
			
			# Update vendor master
			vend.user_create = 1
			vend.save(ignore_permissions=True)
			frappe.db.commit()
			
			frappe.msgprint(f"User created and email sent successfully for vendor: {vend.vendor_name}")
		else:
			# User already exists - just send email with PDF (no credentials)
			self.send_vendor_email_with_pdf(
				email=vend.office_email_primary,
				username=vend.office_email_primary,
				password=None,
				vendor_name=vend.vendor_name or "Vendor",
				vendor_code_data=vendor_code_data,
				is_new_user=False
			)
			vend.user_create = 1
			vend.save(ignore_permissions=True)
			frappe.db.commit()
			
			frappe.msgprint(f"Email with vendor code data sent successfully for vendor: {vend.vendor_name}")

	def collect_vendor_code_data(self, vendor_doc):
		"""Collect all vendor code data from multiple company data"""
		all_vendor_data = []
		
		try:
			# Check if multiple_company_data exists and has data
			if not hasattr(vendor_doc, 'multiple_company_data') or not vendor_doc.multiple_company_data:
				frappe.logger().info("No multiple_company_data found in vendor document")
				return all_vendor_data
			
			# Iterate through multiple_company_data table
			for company_data_row in vendor_doc.multiple_company_data:
				if hasattr(company_data_row, 'company_vendor_code') and company_data_row.company_vendor_code:
					try:
						# Fetch Company Vendor Code document
						company_vendor_code_doc = frappe.get_doc("Company Vendor Code", company_data_row.company_vendor_code)
						
						# Check if vendor_code table exists and has data
						if hasattr(company_vendor_code_doc, 'vendor_code') and company_vendor_code_doc.vendor_code:
							# Iterate through vendor_code table in Company Vendor Code doc
							for vendor_code_row in company_vendor_code_doc.vendor_code:
								vendor_info = {
									'company_name': getattr(company_vendor_code_doc, 'company_description', ''),
									'state': getattr(vendor_code_row, 'state', ''),
									'gst_no': getattr(vendor_code_row, 'gst_no', ''),
									'vendor_code': getattr(vendor_code_row, 'vendor_code', '')
								}
								all_vendor_data.append(vendor_info)
						else:
							frappe.logger().info(f"No vendor_code data found in Company Vendor Code {company_data_row.company_vendor_code}")
							
					except Exception as e:
						frappe.logger().error(f"Error fetching Company Vendor Code {company_data_row.company_vendor_code}: {str(e)}")
						continue
						
		except Exception as e:
			frappe.logger().error(f"Error in collect_vendor_code_data: {str(e)}")
		
		print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22",all_vendor_data)		
		
		return all_vendor_data

	def generate_random_password(self, length=8):
		"""Generate a random password with mix of letters and numbers"""
		characters = string.ascii_letters + string.digits
		password = ''.join(random.choice(characters) for _ in range(length))
		return password

	def create_vendor_data_pdf(self, vendor_name, vendor_code_data):
		"""Create PDF with vendor code data"""
		html_content = f"""
		<html>
		<head>
			<style>
				body {{ font-family: Arial, sans-serif; margin: 20px; }}
				h1 {{ color: #333; text-align: center; }}
				h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
				table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
				th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
				th {{ background-color: #f5f5f5; font-weight: bold; }}
				tr:nth-child(even) {{ background-color: #f9f9f9; }}
				.header {{ text-align: center; margin-bottom: 30px; }}
				.footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
			</style>
		</head>
		<body>
			<div class="header">
				<h1>Vendor Code Information</h1>
				<h2>Vendor: {vendor_name}</h2>
				<p>Generated on: {frappe.utils.now_datetime().strftime('%d-%m-%Y %H:%M:%S')}</p>
			</div>
			
			<table>
				<thead>
					<tr>
						<th>S.No.</th>
						<th>Company Name</th>
						<th>State</th>
						<th>GST Number</th>
						<th>Vendor Code</th>
					</tr>
				</thead>
				<tbody>
		"""
		
		if vendor_code_data:
			for idx, data in enumerate(vendor_code_data, 1):
				# Ensure data is a dictionary and handle safely
				if isinstance(data, dict):
					html_content += f"""
						<tr>
							<td>{idx}</td>
							<td>{data.get('company_name', '')}</td>
							<td>{data.get('state', '')}</td>
							<td>{data.get('gst_no', '')}</td>
							<td>{data.get('vendor_code', '')}</td>
						</tr>
					"""
				else:
					frappe.logger().warning(f"Invalid data format in vendor_code_data at index {idx}: {data}")
					html_content += f"""
						<tr>
							<td>{idx}</td>
							<td colspan="4" style="text-align: center; font-style: italic;">Invalid data format</td>
						</tr>
					"""
		else:
			html_content += """
				<tr>
					<td colspan="5" style="text-align: center; font-style: italic;">No vendor code data available</td>
				</tr>
			"""
		
		html_content += """
				</tbody>
			</table>
			
			<div class="footer">
				<p>This document contains confidential vendor information. Please handle with care.</p>
			</div>
		</body>
		</html>
		"""
		
		# Generate PDF
		pdf_content = get_pdf(html_content)
		return pdf_content

	def send_vendor_email_with_pdf(self, email, username, password, vendor_name, vendor_code_data, is_new_user=True):
		"""Send email with credentials (if new user) and PDF attachment"""
		try:
			conf = frappe.conf
			home_url = conf.get("frontend_http")
			# home_url = get_url()
			
			# Debug logging
			frappe.logger().info(f"Sending email to: {email}")
			frappe.logger().info(f"Vendor code data count: {len(vendor_code_data) if vendor_code_data else 0}")
			frappe.logger().info(f"Vendor code data type: {type(vendor_code_data)}")
			
			# Create PDF attachment
			pdf_content = self.create_vendor_data_pdf(vendor_name, vendor_code_data)
			
			# Prepare email content based on whether it's a new user or existing user
			if is_new_user:
				subject = "Your Vendor Portal Access Credentials & Code Information"
				credentials_section = f"""
				<div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
					<h3 style="margin-top: 0;">Login Credentials:</h3>
					<p><strong>Username:</strong> {username}</p>
					<p><strong>Password:</strong> {password}</p>
					<p><strong>Portal URL:</strong> <a href="{home_url}" target="_blank">{home_url}</a></p>
				</div>
				
				<p><strong>Important Security Notes:</strong></p>
				<ul>
					<li>Please change your password after your first login</li>
					<li>Keep your credentials secure and confidential</li>
					<li>Do not share your login details with anyone</li>
				</ul>
				"""
			else:
				subject = "Updated Vendor Code Information"
				credentials_section = f"""
				<div style="background-color: #e8f4fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
					<h3 style="margin-top: 0;">Portal Access:</h3>
					<p>You can access your vendor portal at: <a href="{home_url}" target="_blank">{home_url}</a></p>
					<p>Use your existing login credentials to access the portal.</p>
				</div>
				"""
			
			message = f"""
			<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
				<h2 style="color: #333;">{'Welcome to Our Vendor Portal' if is_new_user else 'Vendor Information Update'}</h2>
				
				<p>Dear {vendor_name},</p>
				
				<p>{'Your vendor portal account has been created successfully.' if is_new_user else 'Your vendor code information has been updated.'}</p>
				
				{credentials_section}
				
				<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
					<h4 style="margin-top: 0; color: #856404;">Vendor Code Information</h4>
					<p style="color: #856404;">Please find attached a PDF document containing all your vendor code information across different companies and states. This includes your GST numbers and assigned vendor codes.</p>
				</div>
				
				<p>If you have any questions or need assistance, please contact our support team.</p>
				
				<p>Best regards,<br>
				Your Company Team</p>
			</div>
			"""
			
			# Prepare attachment
			filename = f"Vendor_Code_Info_{vendor_name.replace(' ', '_')}_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}.pdf"
			
			attachments = [{
				'fname': filename,
				'fcontent': pdf_content
			}]
			
			# Send email
			frappe.sendmail(
				recipients=[email],
				subject=subject,
				message=message,
				attachments=attachments,
				now=True
			)
			
			frappe.logger().info(f"Email with PDF attachment sent successfully to {email}")
			
		except Exception as e:
			frappe.logger().error(f"Failed to send email with PDF to {email}: {str(e)}")
			# Instead of throwing error, just log it and show message
			frappe.msgprint(f"Warning: Email could not be sent. Error: {str(e)}", alert=True)
			frappe.logger().error(f"Full error details: {frappe.get_traceback()}")


