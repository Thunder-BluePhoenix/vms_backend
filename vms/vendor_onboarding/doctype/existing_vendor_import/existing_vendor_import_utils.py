# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import json
import pandas as pd
from frappe.utils import cstr, flt, cint, validate_email_address
import re


class VendorImportUtils:
	"""Utility class for vendor import operations"""
	
	@staticmethod
	def validate_email(email):
		"""Validate email format"""
		if not email:
			return True, ""
		
		try:
			validate_email_address(email, throw=True)
			return True, ""
		except:
			return False, f"Invalid email format: {email}"
	
	@staticmethod
	def validate_gst(gst_no):
		"""Validate GST number format"""
		if not gst_no:
			return True, ""
		
		gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
		if not re.match(gst_pattern, str(gst_no).strip()):
			return False, f"Invalid GST format: {gst_no}"
		
		return True, ""
	
	@staticmethod
	def validate_pan(pan_no):
		"""Validate PAN number format"""
		if not pan_no:
			return True, ""
		
		pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
		if not re.match(pan_pattern, str(pan_no).strip()):
			return False, f"Invalid PAN format: {pan_no}"
		
		return True, ""
	
	@staticmethod
	def validate_phone(phone_no):
		"""Validate phone number format"""
		if not phone_no:
			return True, ""
		
		# Remove all non-digit characters
		digits_only = re.sub(r'\D', '', str(phone_no))
		
		# Check if it's a valid length (10-15 digits)
		if len(digits_only) < 10 or len(digits_only) > 15:
			return False, f"Invalid phone number: {phone_no}"
		
		return True, ""
	
	@staticmethod
	def validate_pincode(pincode):
		"""Validate pincode format"""
		if not pincode:
			return True, ""
		
		# Indian pincode should be 6 digits
		pincode_str = str(pincode).strip()
		if not pincode_str.isdigit() or len(pincode_str) != 6:
			return False, f"Invalid pincode format: {pincode}"
		
		return True, ""
	
	@staticmethod
	def clean_vendor_data(row):
		"""Clean and standardize vendor data"""
		cleaned_row = {}
		
		for key, value in row.items():
			# Clean key
			clean_key = str(key).strip()
			
			# Clean value
			if pd.isna(value) or value == '' or str(value).lower() in ['null', 'none', 'n/a', 'na']:
				cleaned_row[clean_key] = None
			else:
				cleaned_row[clean_key] = str(value).strip()
		
		return cleaned_row
	
	@staticmethod
	def generate_field_mapping():
		"""Generate field mapping between CSV and DocType fields"""
		return {
			# Vendor Master fields
			'vendor_master': {
				'Vendor Name': 'vendor_name',
				'Primary Email': 'office_email_primary',
				'Email-Id': 'office_email_primary',  # Alternative field
				'Secondary Email': 'office_email_secondary',
				'Contact No': 'mobile_number',
				'Country': 'country',
				'Check': 'payee_in_document'
			},
			
			# Company Vendor Code fields
			'company_vendor_code': {
				'C.Code': 'company_code',
				'Vendor Code': 'vendor_code',
				'GSTN No': 'gst_no',
				'State': 'state'
			},
			
			# Company Details fields
			'company_details': {
				'Vendor Name': 'vendor_name',
				'GSTN No': 'gst',
				'PAN No': 'company_pan_number',
				'Primary Email': 'office_email_primary',
				'Secondary Email': 'office_email_secondary',
				'Contact No': 'telephone_number',
				'Address01': 'address_line_1',
				'Address02': 'address_line_2',
				'City': 'city',
				'State': 'state',
				'Country': 'country',
				'Pincode': 'pincode',
				'Nature Of Services': 'nature_of_business',
				'Type of Industry': 'type_of_business'
			},
			
			# Payment Details fields
			'payment_details': {
				'Bank Name': 'bank_name',
				'IFSC Code': 'ifsc_code',
				'Account Number': 'account_number',
				'Name of Account Holder': 'name_of_account_holder',
				'Type of Account': 'type_of_account',
				'Terms of Payment': 'terms_of_payment',
				'Purchase Group': 'purchase_group',
				'Purchase Organization': 'purchase_organization',
				'Account Group': 'account_group',
				'Incoterm': 'incoterms',
				'Reconciliation Account': 'reconciliation_account'
			},
			
			# International Banking fields
			'international_banking': {
				'Beneficiary Name': 'beneficiary_name',
				'Beneficiary Swift Code': 'beneficiary_swift_code',
				'Beneficiary IBAN No.': 'beneficiary_iban_no',
				'Beneficiary ABA No.': 'beneficiary_aba_no',
				'Beneficiary Bank Address': 'beneficiary_bank_address',
				'Beneficiary Bank Name': 'beneficiary_bank_name',
				'Beneficiary Account No.': 'beneficiary_account_no',
				'Beneficiary ACH No.': 'beneficiary_ach_no',
				'Beneficiary Routing No.': 'beneficiary_routing_no',
				'Beneficiary Currency': 'beneficiary_currency'
			},
			
			# Intermediate Banking fields
			'intermediate_banking': {
				'Intermediate Name': 'intermediate_name',
				'Intermediate Bank Name': 'intermediate_bank_name',
				'Intermediate Swift Code': 'intermediate_swift_code',
				'Intermediate IBAN No.': 'intermediate_iban_no',
				'Intermediate ABA No.': 'intermediate_aba_no',
				'Intermediate Bank Address': 'intermediate_bank_address',
				'Intermediate Account No.': 'intermediate_account_no',
				'Intermediate ACH No.': 'intermediate_ach_no',
				'Intermediate Routing No.': 'intermediate_routing_no',
				'Intermediate Currency': 'intermediate_currency'
			}
		}
	
	@staticmethod
	def create_payment_details_record(vendor_ref_no, row):
		"""Create vendor onboarding payment details record"""
		
		try:
			# Check if payment details already exist
			existing_payment = frappe.db.exists("Vendor Onboarding Payment Details", {
				"vendor_onboarding": vendor_ref_no
			})
			
			if existing_payment:
				payment_doc = frappe.get_doc("Vendor Onboarding Payment Details", existing_payment)
			else:
				payment_doc = frappe.new_doc("Vendor Onboarding Payment Details")
				payment_doc.vendor_onboarding = vendor_ref_no
			
			# Map banking details
			field_mapping = VendorImportUtils.generate_field_mapping()
			payment_mapping = field_mapping['payment_details']
			
			for csv_field, doc_field in payment_mapping.items():
				if csv_field in row and row[csv_field]:
					setattr(payment_doc, doc_field, row[csv_field])
			
			# Add domestic bank details
			if not hasattr(payment_doc, 'domestic_bank_details') or not payment_doc.domestic_bank_details:
				payment_doc.append("domestic_bank_details", {
					"bank_name": row.get('Bank Name'),
					"ifsc_code": row.get('IFSC Code'),
					"account_number": row.get('Account Number'),
					"name_of_account_holder": row.get('Name of Account Holder'),
					"type_of_account": row.get('Type of Account')
				})
			
			# Add international bank details if available
			intl_mapping = field_mapping['international_banking']
			intl_data = {}
			for csv_field, doc_field in intl_mapping.items():
				if csv_field in row and row[csv_field]:
					intl_data[doc_field] = row[csv_field]
			
			if intl_data and any(intl_data.values()):
				if not hasattr(payment_doc, 'international_bank_details') or not payment_doc.international_bank_details:
					payment_doc.append("international_bank_details", intl_data)
			
			# Add intermediate bank details if available
			inter_mapping = field_mapping['intermediate_banking']
			inter_data = {}
			for csv_field, doc_field in inter_mapping.items():
				if csv_field in row and row[csv_field]:
					inter_data[doc_field] = row[csv_field]
			
			if inter_data and any(inter_data.values()):
				if not hasattr(payment_doc, 'intermediate_bank_details') or not payment_doc.intermediate_bank_details:
					payment_doc.append("intermediate_bank_details", inter_data)
			
			payment_doc.save(ignore_permissions=True)
			return payment_doc.name
			
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), f"Error creating payment details: {str(e)}")
			return None
	
	@staticmethod
	def validate_master_data(row):
		"""Validate master data references"""
		errors = []
		warnings = []
		
		# Validate Company Code
		company_code = row.get('C.Code')
		if company_code:
			company_exists = frappe.db.exists("Company Master", {"company_code": str(company_code)})
			if not company_exists:
				warnings.append(f"Company with code {company_code} not found in Company Master")
		
		# Validate State
		state = row.get('State')
		if state:
			state_exists = frappe.db.exists("State Master", {"state_name": state})
			if not state_exists:
				warnings.append(f"State '{state}' not found in State Master")
		
		# Validate City
		city = row.get('City')
		if city:
			city_exists = frappe.db.exists("City Master", {"city_name": city})
			if not city_exists:
				warnings.append(f"City '{city}' not found in City Master")
		
		# Validate Country
		country = row.get('Country')
		if country and country not in ['IN', 'India', '']:
			country_exists = frappe.db.exists("Country Master", {"country_name": country})
			if not country_exists:
				warnings.append(f"Country '{country}' not found in Country Master")
		
		# Validate Purchase Group
		purchase_group = row.get('Purchase Group')
		if purchase_group:
			pg_exists = frappe.db.exists("Purchase Group Master", {"purchase_group_code": purchase_group})
			if not pg_exists:
				warnings.append(f"Purchase Group '{purchase_group}' not found in Purchase Group Master")
		
		# Validate Purchase Organization
		purchase_org = row.get('Purchase Organization')
		if purchase_org:
			po_exists = frappe.db.exists("Purchase Organization Master", {"purchase_organization_code": purchase_org})
			if not po_exists:
				warnings.append(f"Purchase Organization '{purchase_org}' not found in Purchase Organization Master")
		
		return errors, warnings
	
	@staticmethod
	def generate_import_summary_html(results, vendor_data):
		"""Generate comprehensive import summary HTML"""
		
		total_records = len(vendor_data)
		valid_records = results.get('valid_records', 0)
		invalid_records = results.get('invalid_records', 0)
		success_rate = (valid_records / total_records * 100) if total_records > 0 else 0
		
		html = f"""
		<div class="import-summary-container">
			<div class="row">
				<div class="col-12">
					<div class="card border-primary">
						<div class="card-header bg-primary text-white">
							<h5 class="mb-0"><i class="fa fa-chart-bar"></i> Import Summary</h5>
						</div>
						<div class="card-body">
							<div class="row text-center">
								<div class="col-md-2">
									<div class="metric-box">
										<h3 class="text-primary">{total_records}</h3>
										<p class="text-muted">Total Records</p>
									</div>
								</div>
								<div class="col-md-2">
									<div class="metric-box">
										<h3 class="text-success">{valid_records}</h3>
										<p class="text-muted">Valid</p>
									</div>
								</div>
								<div class="col-md-2">
									<div class="metric-box">
										<h3 class="text-danger">{invalid_records}</h3>
										<p class="text-muted">Invalid</p>
									</div>
								</div>
								<div class="col-md-2">
									<div class="metric-box">
										<h3 class="text-info">{success_rate:.1f}%</h3>
										<p class="text-muted">Success Rate</p>
									</div>
								</div>
								<div class="col-md-2">
									<div class="metric-box">
										<h3 class="text-warning">{len(results.get('warnings', []))}</h3>
										<p class="text-muted">Warnings</p>
									</div>
								</div>
								<div class="col-md-2">
									<div class="metric-box">
										<h3 class="text-dark">{len(results.get('errors', []))}</h3>
										<p class="text-muted">Errors</p>
									</div>
								</div>
							</div>
							
							<div class="progress mt-3" style="height: 20px;">
								<div class="progress-bar bg-success" role="progressbar" 
									 style="width: {success_rate}%" 
									 aria-valuenow="{success_rate}" 
									 aria-valuemin="0" 
									 aria-valuemax="100">
									{success_rate:.1f}%
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
		
		<style>
			.metric-box {{
				padding: 15px;
				border-radius: 8px;
				background: #f8f9fa;
				margin: 5px;
				transition: transform 0.2s;
			}}
			
			.metric-box:hover {{
				transform: translateY(-2px);
				box-shadow: 0 4px 8px rgba(0,0,0,0.1);
			}}
			
			.import-summary-container .card {{
				border-radius: 10px;
				box-shadow: 0 4px 6px rgba(0,0,0,0.1);
			}}
		</style>
		"""
		
		return html
	
	@staticmethod
	def get_duplicate_vendors(vendor_data):
		"""Check for duplicate vendors in the dataset"""
		duplicates = []
		vendor_names = {}
		vendor_codes = {}
		
		for idx, row in enumerate(vendor_data, 1):
			vendor_name = row.get('Vendor Name', '').strip()
			vendor_code = row.get('Vendor Code', '').strip()
			
			# Check for duplicate vendor names
			if vendor_name in vendor_names:
				duplicates.append({
					'type': 'Vendor Name',
					'value': vendor_name,
					'rows': [vendor_names[vendor_name], idx]
				})
			else:
				vendor_names[vendor_name] = idx
			
			# Check for duplicate vendor codes within same company
			company_code = row.get('C.Code', '').strip()
			key = f"{vendor_code}_{company_code}"
			if key in vendor_codes:
				duplicates.append({
					'type': 'Vendor Code + Company',
					'value': f"{vendor_code} (Company: {company_code})",
					'rows': [vendor_codes[key], idx]
				})
			else:
				vendor_codes[key] = idx
		
		return duplicates


@frappe.whitelist()
def validate_csv_data(docname):
	"""API method to validate CSV data"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.vendor_data:
		return {"error": "No vendor data found"}
	
	vendor_data = json.loads(doc.vendor_data)
	
	# Use utility class for validation
	utils = VendorImportUtils()
	results = doc.validate_vendor_data(vendor_data)
	
	# Check for duplicates
	duplicates = utils.get_duplicate_vendors(vendor_data)
	if duplicates:
		results['duplicates'] = duplicates
	
	return results


@frappe.whitelist()
def get_import_statistics(docname):
	"""Get detailed import statistics"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.vendor_data:
		return {"error": "No vendor data found"}
	
	vendor_data = json.loads(doc.vendor_data)
	
	stats = {
		"total_records": len(vendor_data),
		"companies": {},
		"states": {},
		"vendor_types": {},
		"gst_types": {}
	}
	
	for row in vendor_data:
		# Company statistics
		company = str(row.get('C.Code', 'Unknown'))
		stats["companies"][company] = stats["companies"].get(company, 0) + 1
		
		# State statistics
		state = row.get('State', 'Unknown')
		stats["states"][state] = stats["states"].get(state, 0) + 1
		
		# Vendor type statistics
		vendor_type = row.get('Vendor Type', 'Unknown')
		stats["vendor_types"][vendor_type] = stats["vendor_types"].get(vendor_type, 0) + 1
		
		# GST type statistics
		gst_type = row.get('Vendor GST Classification', 'Unknown')
		stats["gst_types"][gst_type] = stats["gst_types"].get(gst_type, 0) + 1
	
	return stats