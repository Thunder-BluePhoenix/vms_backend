# existing_vendor_import_utils.py
# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import json
import pandas as pd
from frappe.utils import cstr, flt, cint, validate_email_address, today
import re


class VendorImportUtils:
	"""Utility class for vendor import operations"""
	
	@staticmethod
	def safe_str_strip(value):
		"""Safely convert value to string and strip whitespace"""
		if value is None or pd.isna(value):
			return ""
		
		str_value = str(value).strip()
		if str_value.lower() in ['nan', 'none', 'null', '']:
			return ""
		
		return str_value
	
	@staticmethod
	def validate_email(email):
		"""Validate email format"""
		email_str = VendorImportUtils.safe_str_strip(email)
		if not email_str:
			return True, ""
		
		try:
			validate_email_address(email_str, throw=True)
			return True, ""
		except:
			return False, f"Invalid email format: {email_str}"
	
	@staticmethod
	def validate_gst(gst_no):
		"""Validate GST number format"""
		gst_str = VendorImportUtils.safe_str_strip(gst_no)
		if not gst_str:
			return True, ""
		
		gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
		if not re.match(gst_pattern, gst_str):
			return False, f"Invalid GST format: {gst_str}"
		
		return True, ""
	
	@staticmethod
	def validate_pan(pan_no):
		"""Validate PAN number format"""
		pan_str = VendorImportUtils.safe_str_strip(pan_no)
		if not pan_str:
			return True, ""
		
		pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
		if not re.match(pan_pattern, pan_str):
			return False, f"Invalid PAN format: {pan_str}"
		
		return True, ""
	
	@staticmethod
	def validate_phone(phone_no):
		"""Validate phone number format"""
		phone_str = VendorImportUtils.safe_str_strip(phone_no)
		if not phone_str:
			return True, ""
		
		# Remove all non-digit characters
		digits_only = re.sub(r'\D', '', phone_str)
		
		# Check if it's a valid length (10-15 digits)
		if len(digits_only) < 10 or len(digits_only) > 15:
			return False, f"Invalid phone number: {phone_str}"
		
		return True, ""
	
	@staticmethod
	def validate_pincode(pincode):
		"""Validate pincode format"""
		pincode_str = VendorImportUtils.safe_str_strip(pincode)
		if not pincode_str:
			return True, ""
		
		# Indian pincode should be 6 digits
		if not pincode_str.isdigit() or len(pincode_str) != 6:
			return False, f"Invalid pincode format: {pincode_str}"
		
		return True, ""
	
	@staticmethod
	def validate_vendor_code(vendor_code):
		"""Validate vendor code format"""
		vendor_code_str = VendorImportUtils.safe_str_strip(vendor_code)
		if not vendor_code_str:
			return False, "Vendor code is required"
		
		if len(vendor_code_str) < 3:
			return False, f"Vendor code too short: {vendor_code_str}"
		
		return True, ""
	
	@staticmethod
	def validate_company_code(company_code):
		"""Validate company code format and existence"""
		company_code_str = VendorImportUtils.safe_str_strip(company_code)
		if not company_code_str:
			return False, "Company code is required"
		
		# Check if company exists
		company_exists = frappe.db.exists("Company Master", {"company_code": company_code_str})
		if not company_exists:
			return False, f"Company with code {company_code_str} not found"
		
		return True, ""
	
	@staticmethod
	def clean_vendor_data(row):
		"""Clean and standardize vendor data"""
		cleaned_row = {}
		
		for key, value in row.items():
			# Clean key
			clean_key = str(key).strip()
			
			# Clean value - handle float/int conversion properly
			if pd.isna(value) or value == '' or str(value).lower() in ['null', 'none', 'n/a', 'na', 'nan']:
				cleaned_row[clean_key] = None
			else:
				# Convert to string first, then strip
				cleaned_row[clean_key] = str(value).strip()
		
		return cleaned_row
	
	@staticmethod
	def normalize_vendor_name(vendor_name):
		"""Normalize vendor name for duplicate detection"""
		vendor_name_str = VendorImportUtils.safe_str_strip(vendor_name)
		if not vendor_name_str:
			return ""
		
		# Convert to lowercase, remove extra spaces, remove special characters
		normalized = re.sub(r'[^\w\s]', '', vendor_name_str.lower())
		normalized = re.sub(r'\s+', ' ', normalized).strip()
		
		# Remove common suffixes for better matching
		suffixes = ['pvt ltd', 'private limited', 'ltd', 'limited', 'inc', 'incorporated']
		for suffix in suffixes:
			if normalized.endswith(suffix):
				normalized = normalized.replace(suffix, '').strip()
		
		return normalized
	
	@staticmethod
	def generate_field_mapping():
		"""Generate field mapping between CSV and DocType fields"""
		return {
			# Vendor Master fields
			'vendor_master': {
				'Vendor Name': 'vendor_name',
				'Primary Email': 'office_email_primary',
				'Email-Id': 'office_email_primary',
				'Secondary Email': 'office_email_secondary',
				'Contact No': 'mobile_number',
				'Country': 'country',
				'Check': 'payee_in_document'
			},
			
			# Company Vendor Code fields
			'company_vendor_code': {
				'Vendor Code': 'vendor_code',
				'C.Code': 'company_code',
				'Company Code': 'company_code',
				'State': 'state',
				'GSTN No': 'gst_no',
				'GST No': 'gst_no'
			},
			
			# Company Details fields
			'company_details': {
				'Vendor Name': 'company_name',
				'GSTN No': 'gst',
				'PAN No': 'company_pan_number',
				'Address01': 'address_line_1',
				'Address02': 'address_line_2',
				'Address03': 'address_line_3',
				'City': 'city',
				'Pincode': 'pincode',
				'Country': 'country',
				'Contact No': 'telephone_number',
				'Nature of Business': 'nature_of_business',
				'Type of Business': 'type_of_business',
				'CIN': 'corporate_identification_number',
				'Established Year': 'established_year'
			},
			
			# Multiple Company Data fields
			'multiple_company_data': {
				'Purchase Organization': 'purchase_organization',
				'Account Group': 'account_group',
				'Terms of Payment': 'terms_of_payment',
				'Purchase Group': 'purchase_group',
				'Order Currency': 'order_currency',
				'Incoterm': 'incoterms',
				'Reconciliation Account': 'reconciliation_account'
			},
			
			# Payment Details fields
			'payment_details': {
				'Bank Name': 'bank_name',
				'IFSC Code': 'ifsc_code',
				'Account Number': 'account_number',
				'Name of Account Holder': 'name_of_account_holder',
				'Type of Account': 'type_of_account'
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
				'Beneficiary Currency': 'beneficiary_currency',
				'Intermediate Swift Code': 'intermediate_swift_code',
				'Intermediate Bank Name': 'intermediate_bank_name',
				'Intermediate IBAN No.': 'intermediate_iban_no',
				'Intermediate ABA No.': 'intermediate_aba_no',
				'Intermediate Bank Address': 'intermediate_bank_address',
				'Intermediate Account No.': 'intermediate_account_no',
				'Intermediate ACH No.': 'intermediate_ach_no',
				'Intermediate Routing No.': 'intermediate_routing_no',
				'Intermediate Currency': 'intermediate_currency'
			},
			
			# Additional fields
			'additional_fields': {
				'Vendor GST Classification': 'vendor_gst_classification',
				'Nature of Services': 'nature_of_services',
				'Vendor Type': 'vendor_type',
				'Remarks': 'remarks',
				'Contact Person': 'contact_person',
				'HOD': 'hod',
				'Enterprise Registration No': 'enterprise_registration_no'
			}
		}
	




	@staticmethod
	def extract_banker_details(row):
		"""Extract banker details for Vendor Bank Details doctype (domestic banking info)"""
		
		banker_data = {}
		
		# Map banker detail fields based on Banker Details child doctype
		field_mapping = {
			'bank_name': 'bank_name',
			'ifsc_code': 'ifsc_code', 
			'account_number': 'account_number',
			'name_of_account_holder': 'name_of_account_holder',
			'type_of_account': 'type_of_account'
		}
		
		for csv_field, doc_field in field_mapping.items():
			value = VendorImportUtils.get_flexible_field_value(row, csv_field)
			if value:
				banker_data[doc_field] = value
		
		# Add vendor name as company name if available
		if 'vendor_name' in row and row['vendor_name']:
			banker_data['company_name'] = VendorImportUtils.safe_str_strip(row['vendor_name'])
		
		return banker_data

	@staticmethod
	def extract_international_bank_details_for_vendor_bank(row):
		"""Extract international bank details specific to Vendor Bank Details doctype"""
		
		intl_data = {}
		
		# Map international bank fields based on International Bank Details child doctype
		# Reference the actual child doctype fields from the schema
		field_mapping = {
			'beneficiary_name': 'beneficiary_name',
			'beneficiary_swift_code': 'beneficiary_swift_code',
			'beneficiary_iban_no': 'beneficiary_iban_no', 
			'beneficiary_aba_no': 'beneficiary_aba_no',
			'beneficiary_bank_address': 'beneficiary_bank_address',
			'beneficiary_bank_name': 'beneficiary_bank_name',
			'beneficiary_account_no': 'beneficiary_account_no',
			'beneficiary_ach_no': 'beneficiary_ach_no',
			'beneficiary_routing_no': 'beneficiary_routing_no',
			'beneficiary_currency': 'beneficiary_currency'
		}
		
		for csv_field, doc_field in field_mapping.items():
			value = VendorImportUtils.get_flexible_field_value(row, csv_field)
			if value:
				intl_data[doc_field] = value
		
		# Add company name if available (meril_company_name field in child doctype)
		# if 'vendor_name' in row and row['vendor_name']:
		# 	intl_data['meril_company_name'] = VendorImportUtils.safe_str_strip(row['vendor_name'])
		
		return intl_data

	@staticmethod
	def extract_intermediate_bank_details(row):
		"""Extract intermediate bank details for Vendor Bank Details doctype"""
		
		intermediate_data = {}
		
		# Map intermediate bank fields
		field_mapping = {
			'intermediate_swift_code': 'intermediate_swift_code',
			'intermediate_bank_name': 'intermediate_bank_name',
			'intermediate_iban_no': 'intermediate_iban_no',
			'intermediate_aba_no': 'intermediate_aba_no',
			'intermediate_bank_address': 'intermediate_bank_address',
			'intermediate_account_no': 'intermediate_account_no',
			'intermediate_ach_no': 'intermediate_ach_no',
			'intermediate_routing_no': 'intermediate_routing_no',
			'intermediate_currency': 'intermediate_currency'
		}
		
		for csv_field, doc_field in field_mapping.items():
			value = VendorImportUtils.get_flexible_field_value(row, csv_field)
			if value:
				intermediate_data[doc_field] = value
		
		# Add company name if available
		# if 'vendor_name' in row and row['vendor_name']:
		# 	intermediate_data['meril_company_name'] = VendorImportUtils.safe_str_strip(row['vendor_name'])
		
		return intermediate_data
	
	@staticmethod
	def get_flexible_field_value(row, target_field):
		"""Get field value with flexible header matching (case-insensitive, space-insensitive)"""
		
		# Define field aliases for flexible matching
		field_aliases = {
			'bank_key':['bank key', 'Bank Key', 'BankKey', 'bank_key'],
			'bank_name': ['Bank Name', 'BANK_NAME', 'bank_name', 'BankName', 'Bank', 'BANK'],
			'ifsc_code': ['IFSC Code', 'IFSC_CODE', 'ifsc_code', 'IFSC', 'Bank Code', 'BANK_CODE'],
			'account_number': ['Account Number', 'ACCOUNT_NUMBER', 'account_number', 'Account No', 'ACCOUNT_NO', 'Acc No'],
			'name_of_account_holder': ['Name of Account Holder', 'Account Holder Name', 'ACCOUNT_HOLDER_NAME', 'Acc Holder Name'],
			'type_of_account': ['Type of Account', 'Account Type', 'TYPE_OF_ACCOUNT', 'ACCOUNT_TYPE'],
			'beneficiary_name': ['Beneficiary Name', 'BENEFICIARY_NAME', 'beneficiary_name'],
			'beneficiary_swift_code': ['Beneficiary Swift Code', 'BENEFICIARY_SWIFT_CODE', 'Swift Code'],
			'beneficiary_iban_no': ['Beneficiary IBAN No', 'BENEFICIARY_IBAN_NO', 'IBAN No'],
			'currency': ['Currency', 'CURRENCY', 'Order Currency', 'ORDER_CURRENCY'],
			'beneficiary_aba_no': ['Beneficiary ABA No', 'ABA No', 'BENEFICIARY_ABA_NO'],
			'beneficiary_bank_address': ['Beneficiary Bank Address', 'Bank Address', 'BENEFICIARY_BANK_ADDRESS'],
			'beneficiary_bank_name': ['Beneficiary Bank Name', 'BENEFICIARY_BANK_NAME'],
			'beneficiary_account_no': ['Beneficiary Account No', 'BENEFICIARY_ACCOUNT_NO'],
			'beneficiary_currency': ['Beneficiary Currency', 'BENEFICIARY_CURRENCY'],
			'intermediate_swift_code': ['Intermediate Swift Code', 'INTERMEDIATE_SWIFT_CODE'],
			'intermediate_bank_name': ['Intermediate Bank Name', 'INTERMEDIATE_BANK_NAME'],
			'intermediate_iban_no': ['Intermediate IBAN No', 'INTERMEDIATE_IBAN_NO'],
			'intermediate_aba_no': ['Intermediate ABA No', 'INTERMEDIATE_ABA_NO'],
			'intermediate_bank_address': ['Intermediate Bank Address', 'INTERMEDIATE_BANK_ADDRESS'],
			'intermediate_account_no': ['Intermediate Account No', 'INTERMEDIATE_ACCOUNT_NO'],
			'intermediate_currency': ['Intermediate Currency', 'INTERMEDIATE_CURRENCY']
		}
		
		# Get possible field names for this target field
		possible_names = field_aliases.get(target_field, [target_field])
		
		# Try to find the value using various field name variations
		for field_name in possible_names:
			if field_name in row and row[field_name]:
				value = VendorImportUtils.safe_str_strip(row[field_name])
				if value:
					return value
		
		# If no exact match, try case-insensitive and space-insensitive matching
		for key, value in row.items():
			key_normalized = str(key).lower().replace(' ', '_').replace('-', '_')
			
			for possible_name in possible_names:
				possible_normalized = str(possible_name).lower().replace(' ', '_').replace('-', '_')
				if key_normalized == possible_normalized:
					return VendorImportUtils.safe_str_strip(value) if value else None
		
		return None


	# STANDALONE PAYMENT DETAILS UTILITIES
# Replace/Add these methods in existing_vendor_import_utils.py

	@staticmethod
	def create_standalone_payment_details_record(vendor_master_name, vendor_name, company_code, row):
		"""Create standalone payment details without vendor onboarding dependency"""
		
		try:
			# Generate unique reference number
			ref_no = VendorImportUtils.generate_standalone_payment_ref(vendor_name, company_code)
			
			frappe.log_error(f"Creating standalone payment details for: {vendor_name}, Company: {company_code}, Ref: {ref_no}", "Payment Debug")
			
			# Check if payment details already exist
			existing_payment = frappe.db.exists("Vendor Bank Details", {
				"ref_no": ref_no
			})
			
			if existing_payment:
				payment_doc = frappe.get_doc("Vendor Bank Details", existing_payment)
				action = "updated"
			else:
				payment_doc = frappe.new_doc("Vendor Bank Details")
				payment_doc.ref_no = ref_no
				action = "created"
			
			# Set basic information (no vendor_onboarding field needed)
			payment_doc.vendor_master = vendor_master_name
			payment_doc.vendor_name = vendor_name
			payment_doc.company_code = company_code
			
			# Track populated fields for logging
			populated_fields = []
			
			# Map basic payment fields directly
			basic_payment_fields = {
				'bank_name': 'bank_name',
				'ifsc_code': 'ifsc_code',
				'account_number': 'account_number',
				'name_of_account_holder': 'name_of_account_holder',
				'type_of_account': 'type_of_account',
				'currency': 'currency',
				'rtgs': 'rtgs',
				'neft': 'neft',
				'ift': 'ift'
			}
			
			for csv_field, doc_field in basic_payment_fields.items():
				value = VendorImportUtils.get_flexible_field_value(row, csv_field)
				if value:
					setattr(payment_doc, doc_field, value)
					populated_fields.append(f"{doc_field}: {value}")
			
			# Handle domestic bank details (child table)
			domestic_data = VendorImportUtils.extract_domestic_bank_details(row)
			if domestic_data and any(domestic_data.values()):
				# Clear existing domestic bank details
				payment_doc.set('domestic_bank_details', [])
				# Add new domestic bank detail
				payment_doc.append("domestic_bank_details", domestic_data)
				populated_fields.append(f"Domestic Bank: {domestic_data}")
				frappe.log_error(f"Added domestic bank details: {domestic_data}", "Payment Debug")
			
			# Handle international bank details (child table)
			intl_data = VendorImportUtils.extract_international_bank_details(row)
			if intl_data and any(intl_data.values()):
				# Clear existing international bank details
				payment_doc.set('international_bank_details', [])
				# Add new international bank detail
				payment_doc.append("international_bank_details", intl_data)
				populated_fields.append(f"International Bank: {intl_data}")
				frappe.log_error(f"Added international bank details: {intl_data}", "Payment Debug")
			
			# Set import metadata
			payment_doc.created_from_import = 1
			payment_doc.import_date = frappe.utils.now()
			payment_doc.import_source = "Existing Vendor Import"
			payment_doc.standalone_payment_details = 1  # Flag to identify standalone records
			
			# Save only if we have populated fields
			if populated_fields:
				payment_doc.save(ignore_permissions=True)
				frappe.db.commit()
				frappe.log_error(f"Successfully {action} standalone payment details: {payment_doc.name}, Fields: {populated_fields}", "Payment Success")
				return {
					'name': payment_doc.name,
					'action': action,
					'ref_no': ref_no,
					'populated_fields': populated_fields
				}
			else:
				frappe.log_error(f"No payment data found for {vendor_name} in row: {list(row.keys())}", "Payment Debug")
				return None
			
		except Exception as e:
			frappe.log_error(f"Error creating standalone payment details for {vendor_name}: {str(e)}\nRow data: {row}", "Payment Error")
			return None

	@staticmethod
	def generate_standalone_payment_ref(vendor_name, company_code=""):
		"""Generate unique reference number for standalone payment details"""
		
		try:
			# Create vendor abbreviation (first 6 chars, alphanumeric only)
			vendor_abbr = ''.join(c for c in vendor_name.upper() if c.isalnum())[:6]
			if not vendor_abbr:
				vendor_abbr = "VENDOR"
			
			# Company code abbreviation
			comp_abbr = company_code[:4] if company_code else "COMP"
			
			# Timestamp
			now = frappe.utils.now_datetime()
			timestamp = now.strftime("%y%m%d")
			
			# Base reference
			base_ref = f"PAY-{vendor_abbr}-{comp_abbr}-{timestamp}"
			
			# Ensure uniqueness by adding sequence number
			ref_no = base_ref
			counter = 1
			while frappe.db.exists("Vendor Bank Details", {"ref_no": ref_no}):
				ref_no = f"{base_ref}-{counter:03d}"
				counter += 1
			
			return ref_no
			
		except Exception as e:
			frappe.log_error(f"Error generating standalone payment ref: {str(e)}")
			# Fallback to timestamp-only reference
			timestamp = frappe.utils.now_datetime().strftime("%Y%m%d%H%M%S")
			return f"PAY-IMPORT-{timestamp}"

	@staticmethod
	def validate_standalone_payment_data(row):
		"""Validate if row contains sufficient data for payment details creation"""
		
		validation_result = {
			"has_payment_data": False,
			"missing_fields": [],
			"available_fields": {},
			"data_quality": "none"
		}
		
		# Required fields for basic payment details
		required_fields = ['bank_name', 'ifsc_code', 'account_number']
		optional_fields = ['name_of_account_holder', 'type_of_account']
		international_fields = ['beneficiary_name', 'beneficiary_swift_code', 'beneficiary_iban_no']
		
		# Check required fields
		available_required = 0
		for field in required_fields:
			value = VendorImportUtils.get_flexible_field_value(row, field)
			if value:
				validation_result["available_fields"][field] = value
				available_required += 1
			else:
				validation_result["missing_fields"].append(field)
		
		# Check optional fields
		for field in optional_fields:
			value = VendorImportUtils.get_flexible_field_value(row, field)
			if value:
				validation_result["available_fields"][field] = value
		
		# Check international fields
		intl_count = 0
		for field in international_fields:
			value = VendorImportUtils.get_flexible_field_value(row, field)
			if value:
				validation_result["available_fields"][field] = value
				intl_count += 1
		
		# Determine data quality
		if available_required >= 2:  # At least 2 out of 3 required fields
			validation_result["has_payment_data"] = True
			if available_required == 3:
				validation_result["data_quality"] = "excellent"
			else:
				validation_result["data_quality"] = "good"
		elif available_required >= 1 or intl_count >= 2:
			validation_result["has_payment_data"] = True
			validation_result["data_quality"] = "partial"
		else:
			validation_result["data_quality"] = "insufficient"
		
		return validation_result

	# Enhanced field extraction methods for standalone use
	@staticmethod
	def extract_domestic_bank_details(row):
		"""Extract domestic bank details optimized for standalone payment records"""
		
		domestic_data = {}
		
		# Primary field mapping
		field_mapping = {
			'bank_name': 'bank_name',
			'ifsc_code': 'ifsc_code',
			'account_number': 'account_number',
			'name_of_account_holder': 'name_of_account_holder',
			'type_of_account': 'type_of_account'
		}
		
		for csv_field, doc_field in field_mapping.items():
			value = VendorImportUtils.get_flexible_field_value(row, csv_field)
			if value:
				domestic_data[doc_field] = value
		
		# Add default company name if available from vendor data
		if 'vendor_name' in row and row['vendor_name']:
			domestic_data['company_name'] = VendorImportUtils.safe_str_strip(row['vendor_name'])
		
		return domestic_data

	@staticmethod
	def extract_international_bank_details(row):
		"""Extract international bank details optimized for standalone payment records"""
		
		intl_data = {}
		
		# International field mapping
		field_mapping = {
			'beneficiary_name': 'beneficiary_name',
			'beneficiary_swift_code': 'beneficiary_swift_code',
			'beneficiary_iban_no': 'beneficiary_iban_no',
			'beneficiary_aba_no': 'beneficiary_aba_no',
			'beneficiary_bank_address': 'beneficiary_bank_address',
			'beneficiary_bank_name': 'beneficiary_bank_name',
			'beneficiary_account_no': 'beneficiary_account_no',
			'beneficiary_currency': 'beneficiary_currency',
			'intermediate_swift_code': 'intermediate_swift_code',
			'intermediate_bank_name': 'intermediate_bank_name',
			'intermediate_iban_no': 'intermediate_iban_no',
			'intermediate_aba_no': 'intermediate_aba_no',
			'intermediate_bank_address': 'intermediate_bank_address',
			'intermediate_account_no': 'intermediate_account_no',
			'intermediate_currency': 'intermediate_currency'
		}
		
		for csv_field, doc_field in field_mapping.items():
			value = VendorImportUtils.get_flexible_field_value(row, csv_field)
			if value:
				intl_data[doc_field] = value
		
		# Add company name if available
		# if 'vendor_name' in row and row['vendor_name']:
		# 	intl_data['meril_company_name'] = VendorImportUtils.safe_str_strip(row['vendor_name'])
		
		return intl_data

	# Add API method for testing standalone payment creation
	@frappe.whitelist()
	def test_standalone_payment_creation(docname, row_index=0):
		"""Test method to debug standalone payment creation for a specific row"""
		
		doc = frappe.get_doc("Existing Vendor Import", docname)
		
		if not doc.vendor_data:
			return {"error": "No vendor data found"}
		
		vendor_data = json.loads(doc.vendor_data)
		field_mapping = json.loads(doc.field_mapping) if doc.field_mapping else {}
		
		if row_index >= len(vendor_data):
			return {"error": f"Row index {row_index} out of range"}
		
		# Get the specific row
		row = vendor_data[row_index]
		mapped_row = doc.apply_field_mapping(row, field_mapping)
		
		# Test payment data validation
		validation = VendorImportUtils.validate_standalone_payment_data(row)
		
		# Try to create payment details if validation passes
		result = {
			"row_data": row,
			"mapped_data": mapped_row,
			"validation": validation
		}
		
		if validation["has_payment_data"]:
			vendor_master_name = "TEST_VENDOR_MASTER"  # You can get actual vendor master
			vendor_name = mapped_row.get('vendor_name', 'Test Vendor')
			company_code = mapped_row.get('company_code', 'TEST')
			
			payment_result = VendorImportUtils.create_standalone_payment_details_record(
				vendor_master_name, vendor_name, company_code, row
			)
			result["payment_creation"] = payment_result
		
		return result
	
	@staticmethod
	def create_payment_details_record(vendor_ref_no, vendor_onboarding_ref, row):
		"""Create Vendor Bank Details record"""
		
		try:
			# Check if payment details already exist
			existing_payment = frappe.db.exists("Vendor Bank Details", {
				"vendor_onboarding": vendor_onboarding_ref
			})
			
			if existing_payment:
				payment_doc = frappe.get_doc("Vendor Bank Details", existing_payment)
			else:
				payment_doc = frappe.new_doc("Vendor Bank Details")
				payment_doc.ref_no = vendor_ref_no
				payment_doc.vendor_onboarding = vendor_onboarding_ref
			
			# Map banking details
			field_mapping = VendorImportUtils.generate_field_mapping()
			payment_mapping = field_mapping['payment_details']
			
			for csv_field, doc_field in payment_mapping.items():
				if csv_field in row and row[csv_field]:
					value = VendorImportUtils.safe_str_strip(row[csv_field])
					if value:
						setattr(payment_doc, doc_field, value)
			
			# Add domestic bank details
			bank_details_exist = False
			if hasattr(payment_doc, 'domestic_bank_details') and payment_doc.domestic_bank_details:
				# Check if bank details already exist
				for bank_detail in payment_doc.domestic_bank_details:
					account_number = VendorImportUtils.safe_str_strip(row.get('Account Number'))
					ifsc_code = VendorImportUtils.safe_str_strip(row.get('IFSC Code'))
					if (bank_detail.account_number == account_number and 
						bank_detail.ifsc_code == ifsc_code):
						bank_details_exist = True
						break
			
			if not bank_details_exist and row.get('Bank Name'):
				payment_doc.append("domestic_bank_details", {
					"bank_name": VendorImportUtils.safe_str_strip(row.get('Bank Name')),
					"ifsc_code": VendorImportUtils.safe_str_strip(row.get('IFSC Code')),
					"account_number": VendorImportUtils.safe_str_strip(row.get('Account Number')),
					"name_of_account_holder": VendorImportUtils.safe_str_strip(row.get('Name of Account Holder')),
					"type_of_account": VendorImportUtils.safe_str_strip(row.get('Type of Account'))
				})
			
			# Add international bank details if available
			intl_mapping = field_mapping['international_banking']
			intl_data = {}
			for csv_field, doc_field in intl_mapping.items():
				if csv_field in row and row[csv_field]:
					value = VendorImportUtils.safe_str_strip(row[csv_field])
					if value:
						intl_data[doc_field] = value
			
			if intl_data and any(intl_data.values()):
				# Check if international details already exist
				intl_exists = False
				if hasattr(payment_doc, 'international_bank_details') and payment_doc.international_bank_details:
					for intl_detail in payment_doc.international_bank_details:
						if intl_detail.beneficiary_account_no == intl_data.get('beneficiary_account_no'):
							intl_exists = True
							break
				
				if not intl_exists:
					payment_doc.append("international_bank_details", intl_data)
			
			payment_doc.save(ignore_permissions=True)
			return payment_doc.name
			
		except Exception as e:
			frappe.log_error(f"Error creating payment details: {str(e)}")
			return None
	
	@staticmethod
	def create_summary_html(results):
		"""Create HTML summary of import results"""
		
		total_records = results.get('total_records', 0)
		valid_records = results.get('valid_records', 0)
		invalid_records = results.get('invalid_records', 0)
		success_rate = (valid_records / total_records * 100) if total_records > 0 else 0
		
		html = f"""
		<div class="import-summary-container">
			<div class="row">
				<div class="col-12">
					<div class="card border-primary">
						<div class="card-header bg-primary text-white">
							<h5 class="mb-0"><i class="fa fa-chart-line"></i> Import Summary</h5>
						</div>
						<div class="card-body">
							<div class="row text-center">
								<div class="col-md-2">
									<div class="metric-box">
										<h3 class="text-primary">{total_records}</h3>
										<p class="text-muted">Total</p>
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
		vendor_emails = {}
		
		for idx, row in enumerate(vendor_data, 1):
			vendor_name = VendorImportUtils.safe_str_strip(row.get('Vendor Name', ''))
			vendor_code = VendorImportUtils.safe_str_strip(row.get('Vendor Code', ''))
			email = VendorImportUtils.safe_str_strip(row.get('Primary Email', '') or row.get('Email-Id', ''))
			
			# Normalize vendor name for better duplicate detection
			normalized_name = VendorImportUtils.normalize_vendor_name(vendor_name)
			
			# Check for duplicate vendor names
			if normalized_name and normalized_name in vendor_names:
				duplicates.append({
					'type': 'Vendor Name',
					'value': vendor_name,
					'rows': [vendor_names[normalized_name], idx]
				})
			elif normalized_name:
				vendor_names[normalized_name] = idx
			
			# Check for duplicate vendor codes within same company
			company_code = VendorImportUtils.safe_str_strip(row.get('C.Code', ''))
			key = f"{vendor_code}_{company_code}"
			if vendor_code and company_code:
				if key in vendor_codes:
					duplicates.append({
						'type': 'Vendor Code + Company',
						'value': f"{vendor_code} (Company: {company_code})",
						'rows': [vendor_codes[key], idx]
					})
				else:
					vendor_codes[key] = idx
			
			# Check for duplicate emails
			if email:
				email_normalized = email.lower()
				if email_normalized in vendor_emails:
					duplicates.append({
						'type': 'Email Address',
						'value': email,
						'rows': [vendor_emails[email_normalized], idx]
					})
				else:
					vendor_emails[email_normalized] = idx
		
		return duplicates
	
	@staticmethod
	def validate_row_data(row, row_number):
		"""Validate a single row of vendor data"""
		errors = []
		warnings = []
		
		# Required field validation
		vendor_name = VendorImportUtils.safe_str_strip(row.get('Vendor Name', ''))
		if not vendor_name:
			errors.append(f"Row {row_number}: Vendor name is required")
		
		vendor_code = VendorImportUtils.safe_str_strip(row.get('Vendor Code', ''))
		if not vendor_code:
			warnings.append(f"Row {row_number}: Vendor code is missing")
		else:
			is_valid, msg = VendorImportUtils.validate_vendor_code(vendor_code)
			if not is_valid:
				errors.append(f"Row {row_number}: {msg}")
		
		company_code = VendorImportUtils.safe_str_strip(row.get('C.Code', '') or row.get('Company Code', ''))
		if company_code:
			is_valid, msg = VendorImportUtils.validate_company_code(company_code)
			if not is_valid:
				warnings.append(f"Row {row_number}: {msg}")
		
		# Email validation
		email = VendorImportUtils.safe_str_strip(row.get('Primary Email', '') or row.get('Email-Id', ''))
		if email:
			is_valid, msg = VendorImportUtils.validate_email(email)
			if not is_valid:
				errors.append(f"Row {row_number}: {msg}")
		
		# GST validation
		gst_no = VendorImportUtils.safe_str_strip(row.get('GSTN No', '') or row.get('GST No', ''))
		if gst_no:
			is_valid, msg = VendorImportUtils.validate_gst(gst_no)
			if not is_valid:
				warnings.append(f"Row {row_number}: {msg}")
		
		# PAN validation
		pan_no = VendorImportUtils.safe_str_strip(row.get('PAN No', ''))
		if pan_no:
			is_valid, msg = VendorImportUtils.validate_pan(pan_no)
			if not is_valid:
				warnings.append(f"Row {row_number}: {msg}")
		
		# Phone validation
		phone = VendorImportUtils.safe_str_strip(row.get('Contact No', ''))
		if phone:
			is_valid, msg = VendorImportUtils.validate_phone(phone)
			if not is_valid:
				warnings.append(f"Row {row_number}: {msg}")
		
		# Pincode validation
		pincode = VendorImportUtils.safe_str_strip(row.get('Pincode', ''))
		if pincode:
			is_valid, msg = VendorImportUtils.validate_pincode(pincode)
			if not is_valid:
				warnings.append(f"Row {row_number}: {msg}")
		
		return {
			'errors': errors,
			'warnings': warnings,
			'is_valid': len(errors) == 0
		}
	
	@staticmethod
	def get_master_data_suggestions(field_name, value):
		"""Get suggestions for master data fields"""
		if not value:
			return []
		
		suggestions = []
		value_str = VendorImportUtils.safe_str_strip(value)
		
		try:
			if field_name == 'state':
				states = frappe.get_all("State Master", 
					filters={'state_name': ['like', f'%{value_str}%']}, 
					fields=['name', 'state_name'], 
					limit=5)
				suggestions = [{'value': s.name, 'label': s.state_name} for s in states]
			
			elif field_name == 'city':
				cities = frappe.get_all("City Master", 
					filters={'city_name': ['like', f'%{value_str}%']}, 
					fields=['name', 'city_name'], 
					limit=5)
				suggestions = [{'value': c.name, 'label': c.city_name} for c in cities]
			
			elif field_name == 'company_code':
				companies = frappe.get_all("Company Master", 
					filters={'company_code': ['like', f'%{value_str}%']}, 
					fields=['name', 'company_code', 'company_name'], 
					limit=5)
				suggestions = [{'value': c.name, 'label': f"{c.company_code} - {c.company_name}"} for c in companies]
			
			elif field_name == 'purchase_organization':
				pos = frappe.get_all("Purchase Organization Master", 
					filters={'purchase_organization_name': ['like', f'%{value_str}%']}, 
					fields=['name', 'purchase_organization_name'], 
					limit=5)
				suggestions = [{'value': p.name, 'label': p.purchase_organization_name} for p in pos]
			
		except Exception as e:
			frappe.log_error(f"Error getting suggestions for {field_name}: {str(e)}")
		
		return suggestions
	
	@staticmethod
	def create_missing_masters(row):
		"""Create missing master data entries"""
		created_masters = []
		
		try:
			# Create state if not exists
			state = VendorImportUtils.safe_str_strip(row.get('State', ''))
			if state:
				state_exists = frappe.db.exists("State Master", {"state_name": state})
				if not state_exists:
					state_doc = frappe.new_doc("State Master")
					state_doc.state_name = state
					state_doc.state_code = state[:2].upper()
					state_doc.insert(ignore_permissions=True)
					created_masters.append(f"State: {state}")
			
			# Create city if not exists
			city = VendorImportUtils.safe_str_strip(row.get('City', ''))
			if city:
				city_exists = frappe.db.exists("City Master", {"city_name": city})
				if not city_exists:
					city_doc = frappe.new_doc("City Master")
					city_doc.city_name = city
					city_doc.insert(ignore_permissions=True)
					created_masters.append(f"City: {city}")
			
			# Create pincode if not exists
			pincode = VendorImportUtils.safe_str_strip(row.get('Pincode', ''))
			if pincode:
				pincode_exists = frappe.db.exists("Pincode Master", {"pincode": pincode})
				if not pincode_exists:
					pincode_doc = frappe.new_doc("Pincode Master")
					pincode_doc.pincode = pincode
					pincode_doc.insert(ignore_permissions=True)
					created_masters.append(f"Pincode: {pincode}")
			
		except Exception as e:
			frappe.log_error(f"Error creating missing masters: {str(e)}")
		
		return created_masters


# API Methods for utilities
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
		company = VendorImportUtils.safe_str_strip(row.get('C.Code', 'Unknown'))
		if not company:
			company = 'Unknown'
		stats["companies"][company] = stats["companies"].get(company, 0) + 1
		
		# State statistics
		state = VendorImportUtils.safe_str_strip(row.get('State', 'Unknown'))
		if not state:
			state = 'Unknown'
		stats["states"][state] = stats["states"].get(state, 0) + 1
		
		# Vendor type statistics
		vendor_type = VendorImportUtils.safe_str_strip(row.get('Vendor Type', 'Unknown'))
		if not vendor_type:
			vendor_type = 'Unknown'
		stats["vendor_types"][vendor_type] = stats["vendor_types"].get(vendor_type, 0) + 1
		
		# GST type statistics
		gst_type = VendorImportUtils.safe_str_strip(row.get('Vendor GST Classification', 'Unknown'))
		if not gst_type:
			gst_type = 'Unknown'
		stats["gst_types"][gst_type] = stats["gst_types"].get(gst_type, 0) + 1
	
	return stats


@frappe.whitelist()
def get_field_suggestions(field_name, value):
	"""Get field suggestions for auto-complete"""
	return VendorImportUtils.get_master_data_suggestions(field_name, value)


@frappe.whitelist()
def validate_single_field(field_name, value):
	"""Validate a single field value"""
	utils = VendorImportUtils()
	
	if field_name == 'email':
		return utils.validate_email(value)
	elif field_name == 'gst':
		return utils.validate_gst(value)
	elif field_name == 'pan':
		return utils.validate_pan(value)
	elif field_name == 'phone':
		return utils.validate_phone(value)
	elif field_name == 'pincode':
		return utils.validate_pincode(value)
	elif field_name == 'vendor_code':
		return utils.validate_vendor_code(value)
	elif field_name == 'company_code':
		return utils.validate_company_code(value)
	else:
		return True, ""


@frappe.whitelist()
def clean_import_data(docname):
	"""Clean and standardize import data"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.vendor_data:
		return {"error": "No vendor data found"}
	
	vendor_data = json.loads(doc.vendor_data)
	utils = VendorImportUtils()
	
	cleaned_data = []
	for row in vendor_data:
		cleaned_row = utils.clean_vendor_data(row)
		cleaned_data.append(cleaned_row)
	
	# Update document with cleaned data
	doc.vendor_data = json.dumps(cleaned_data, indent=2, default=str)
	doc.save()
	
	return {"message": "Data cleaned successfully", "total_records": len(cleaned_data)}


@frappe.whitelist()
def create_missing_master_data(docname):
	"""Create missing master data entries"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.vendor_data:
		return {"error": "No vendor data found"}
	
	vendor_data = json.loads(doc.vendor_data)
	utils = VendorImportUtils()
	
	all_created_masters = []
	
	for idx, row in enumerate(vendor_data, 1):
		try:
			created_masters = utils.create_missing_masters(row)
			if created_masters:
				all_created_masters.extend([f"Row {idx}: {master}" for master in created_masters])
		except Exception as e:
			frappe.log_error(f"Error creating masters for row {idx}: {str(e)}")
	
	return {
		"message": "Missing master data created successfully",
		"created_masters": all_created_masters
	}


@frappe.whitelist()
def get_duplicate_analysis(docname):
	"""Get detailed duplicate analysis"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.vendor_data:
		return {"error": "No vendor data found"}
	
	vendor_data = json.loads(doc.vendor_data)
	utils = VendorImportUtils()
	
	duplicates = utils.get_duplicate_vendors(vendor_data)
	
	# Categorize duplicates
	duplicate_analysis = {
		"total_duplicates": len(duplicates),
		"by_type": {},
		"detailed_duplicates": duplicates
	}
	
	for duplicate in duplicates:
		dup_type = duplicate['type']
		if dup_type not in duplicate_analysis["by_type"]:
			duplicate_analysis["by_type"][dup_type] = 0
		duplicate_analysis["by_type"][dup_type] += 1
	
	return duplicate_analysis


@frappe.whitelist()
def export_validation_report(docname):
	"""Export detailed validation report"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.vendor_data:
		return {"error": "No vendor data found"}
	
	vendor_data = json.loads(doc.vendor_data)
	utils = VendorImportUtils()
	
	validation_report = []
	
	for idx, row in enumerate(vendor_data, 1):
		row_validation = utils.validate_row_data(row, idx)
		
		validation_report.append({
			"Row Number": idx,
			"Vendor Name": VendorImportUtils.safe_str_strip(row.get('Vendor Name', '')),
			"Vendor Code": VendorImportUtils.safe_str_strip(row.get('Vendor Code', '')),
			"Company Code": VendorImportUtils.safe_str_strip(row.get('C.Code', '')),
			"Is Valid": "Yes" if row_validation['is_valid'] else "No",
			"Errors": "; ".join(row_validation['errors']) if row_validation['errors'] else "",
			"Warnings": "; ".join(row_validation['warnings']) if row_validation['warnings'] else ""
		})
	
	# Convert to DataFrame and return as Excel
	from io import BytesIO
	import pandas as pd
	
	df = pd.DataFrame(validation_report)
	
	output = BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, sheet_name='Validation Report', index=False)
		
		# Add summary sheet
		summary_data = {
			"Metric": ["Total Records", "Valid Records", "Invalid Records", "Success Rate"],
			"Value": [
				len(vendor_data),
				sum(1 for r in validation_report if r["Is Valid"] == "Yes"),
				sum(1 for r in validation_report if r["Is Valid"] == "No"),
				f"{sum(1 for r in validation_report if r['Is Valid'] == 'Yes') / len(vendor_data) * 100:.1f}%"
			]
		}
		summary_df = pd.DataFrame(summary_data)
		summary_df.to_excel(writer, sheet_name='Summary', index=False)
	
	output.seek(0)
	
	# Save file
	from frappe.utils.file_manager import save_file
	filename = f"validation_report_{doc.name}.xlsx"
	file_doc = save_file(filename, output.read(), doc.doctype, doc.name, is_private=0)
	
	return {
		"file_url": file_doc.file_url,
		"file_name": filename
	}


@frappe.whitelist()
def get_import_recommendations(docname):
	"""Get recommendations for improving import data quality"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.vendor_data:
		return {"error": "No vendor data found"}
	
	vendor_data = json.loads(doc.vendor_data)
	field_mapping = json.loads(doc.field_mapping) if doc.field_mapping else {}
	
	recommendations = []
	
	# Check field mapping completeness
	mapped_fields = sum(1 for v in field_mapping.values() if v)
	total_fields = len(field_mapping)
	mapping_completeness = (mapped_fields / total_fields * 100) if total_fields > 0 else 0
	
	if mapping_completeness < 80:
		recommendations.append({
			"type": "Field Mapping",
			"priority": "High",
			"message": f"Only {mapping_completeness:.1f}% of fields are mapped. Consider mapping more fields for better data quality.",
			"action": "Review field mapping and map important fields"
		})
	
	# Check for missing required fields
	required_fields = ['vendor_name', 'vendor_code', 'company_code']
	mapped_required = [field for field in required_fields if field in field_mapping.values()]
	
	if len(mapped_required) < len(required_fields):
		missing_required = [field for field in required_fields if field not in mapped_required]
		recommendations.append({
			"type": "Required Fields",
			"priority": "Critical",
			"message": f"Missing required field mappings: {', '.join(missing_required)}",
			"action": "Map all required fields before processing"
		})
	
	# Check data quality
	utils = VendorImportUtils()
	total_errors = 0
	total_warnings = 0
	
	for idx, row in enumerate(vendor_data, 1):
		validation = utils.validate_row_data(row, idx)
		total_errors += len(validation['errors'])
		total_warnings += len(validation['warnings'])
	
	if total_errors > 0:
		recommendations.append({
			"type": "Data Quality",
			"priority": "High",
			"message": f"Found {total_errors} validation errors across {len(vendor_data)} records",
			"action": "Fix validation errors in CSV file before importing"
		})
	
	if total_warnings > len(vendor_data) * 0.1:  # More than 10% of records have warnings
		recommendations.append({
			"type": "Data Quality",
			"priority": "Medium",
			"message": f"Found {total_warnings} validation warnings. Consider reviewing data quality",
			"action": "Review and fix warning issues for better data quality"
		})
	
	# Check for duplicates
	duplicates = utils.get_duplicate_vendors(vendor_data)
	if duplicates:
		recommendations.append({
			"type": "Duplicates",
			"priority": "Medium",
			"message": f"Found {len(duplicates)} potential duplicate entries",
			"action": "Review duplicate entries and decide on merge or skip strategy"
		})
	
	return {
		"recommendations": recommendations,
		"total_recommendations": len(recommendations),
		"mapping_completeness": mapping_completeness,
		"data_quality_score": max(0, 100 - (total_errors * 10) - (total_warnings * 2))
	}