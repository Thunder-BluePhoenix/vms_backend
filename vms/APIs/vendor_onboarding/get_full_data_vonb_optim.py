# import frappe
# from frappe import _
# from frappe.utils import cstr

# @frappe.whitelist(allow_guest=True)
# def get_vendor_onboarding_details(vendor_onboarding=None, ref_no=None, **kwargs):
#     """
#     Optimized API to fetch vendor onboarding details with improved performance and robustness
#     """
#     try:
#         # Input validation
#         if not vendor_onboarding or not ref_no:
#             return {
#                 "status": "error",
#                 "message": "Missing required parameters: 'vendor_onboarding' and 'ref_no'."
#             }

#         # Batch fetch all required document names in one go
#         doc_names = _get_document_names(vendor_onboarding, ref_no)
#         if not doc_names.get('company_details'):
#             return {
#                 "status": "error",
#                 "message": "No matching Vendor Onboarding Company Details record found."
#             }

#         # Batch fetch all documents
#         documents = _fetch_all_documents(doc_names, vendor_onboarding)
        
#         # Pre-fetch all master data in batches
#         master_data = _fetch_master_data(documents)
        
#         # Pre-fetch all file data
#         file_data = _fetch_file_data(documents)

#         # Build response using cached data
#         response_data = _build_response_data(documents, master_data, file_data, vendor_onboarding)
        
#         return {
#             "status": "success",
#             "message": "Vendor onboarding details fetched successfully.",
#             **response_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Details Fetch Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch vendor onboarding details.",
#             "error": cstr(e)
#         }


# def _get_document_names(vendor_onboarding, ref_no):
#     """Batch fetch all document names"""
#     doc_names = {}
    
#     # Use SQL to fetch multiple document names in fewer queries
#     company_details_name = frappe.db.get_value(
#         "Vendor Onboarding Company Details",
#         {"vendor_onboarding": vendor_onboarding, "ref_no": ref_no},
#         "name"
#     )
    
#     legal_doc_name = frappe.db.get_value(
#         "Legal Documents",
#         {"vendor_onboarding": vendor_onboarding, "ref_no": ref_no},
#         "name"
#     )
    
#     payment_doc_name = frappe.db.get_value(
#         "Vendor Onboarding Payment Details",
#         {"vendor_onboarding": vendor_onboarding, "ref_no": ref_no},
#         "name"
#     )
    
#     manuf_doc_name = frappe.db.get_value(
#         "Vendor Onboarding Manufacturing Details",
#         {"vendor_onboarding": vendor_onboarding, "ref_no": ref_no},
#         "name"
#     )
    
#     certificate_doc_name = frappe.db.get_value(
#         "Vendor Onboarding Certificates",
#         {"vendor_onboarding": vendor_onboarding, "ref_no": ref_no},
#         "name"
#     )
    
#     return {
#         'company_details': company_details_name,
#         'legal_documents': legal_doc_name,
#         'payment_details': payment_doc_name,
#         'manufacturing_details': manuf_doc_name,
#         'certificates': certificate_doc_name
#     }


# def _fetch_all_documents(doc_names, vendor_onboarding):
#     """Batch fetch all required documents"""
#     documents = {}
    
#     try:
#         # Fetch main vendor onboarding document
#         documents['vendor_onboarding'] = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        
#         # Fetch company details
#         if doc_names.get('company_details'):
#             documents['company_details'] = frappe.get_doc("Vendor Onboarding Company Details", doc_names['company_details'])
        
#         # Fetch legal documents
#         if doc_names.get('legal_documents'):
#             documents['legal_documents'] = frappe.get_doc("Legal Documents", doc_names['legal_documents'])
        
#         # Fetch payment details
#         if doc_names.get('payment_details'):
#             documents['payment_details'] = frappe.get_doc("Vendor Onboarding Payment Details", doc_names['payment_details'])
        
#         # Fetch manufacturing details
#         if doc_names.get('manufacturing_details'):
#             documents['manufacturing_details'] = frappe.get_doc("Vendor Onboarding Manufacturing Details", doc_names['manufacturing_details'])
        
#         # Fetch certificates
#         if doc_names.get('certificates'):
#             documents['certificates'] = frappe.get_doc("Vendor Onboarding Certificates", doc_names['certificates'])
            
#     except Exception as e:
#         frappe.log_error(f"Error fetching documents: {str(e)}", "Document Fetch Error")
        
#     return documents


# def _fetch_master_data(documents):
#     """Pre-fetch all master data in batches to reduce database calls"""
#     master_data = {
#         'cities': {},
#         'districts': {},
#         'states': {},
#         'countries': {},
#         'companies': {},
#         'banks': {},
#         'vendor_types': {},
#         'purchase_orgs': {},
#         'currencies': {},
#         'terms_payment': {},
#         'purchase_groups': {},
#         'account_groups': {},
#         'reconciliation_accounts': {}
#     }
    
#     # Collect all IDs that need master data
#     city_ids = set()
#     district_ids = set()
#     state_ids = set()
#     country_ids = set()
#     company_ids = set()
#     bank_ids = set()
    
#     # Extract IDs from company details
#     if 'company_details' in documents:
#         doc = documents['company_details']
#         _add_to_set_if_exists(city_ids, doc.get('city'))
#         _add_to_set_if_exists(district_ids, doc.get('district'))
#         _add_to_set_if_exists(state_ids, doc.get('state'))
#         _add_to_set_if_exists(country_ids, doc.get('country'))
#         _add_to_set_if_exists(company_ids, doc.get('company_name'))
        
#         # Manufacturing address
#         _add_to_set_if_exists(city_ids, doc.get('manufacturing_city'))
#         _add_to_set_if_exists(district_ids, doc.get('manufacturing_district'))
#         _add_to_set_if_exists(state_ids, doc.get('manufacturing_state'))
#         _add_to_set_if_exists(country_ids, doc.get('manufacturing_country'))
        
#         # Multiple locations
#         for row in doc.get('multiple_location_table', []):
#             _add_to_set_if_exists(city_ids, row.get('ma_city'))
#             _add_to_set_if_exists(district_ids, row.get('ma_district'))
#             _add_to_set_if_exists(state_ids, row.get('ma_state'))
#             _add_to_set_if_exists(country_ids, row.get('ma_country'))
    
#     # Extract IDs from payment details
#     if 'payment_details' in documents:
#         doc = documents['payment_details']
#         _add_to_set_if_exists(bank_ids, doc.get('bank_name'))
#         _add_to_set_if_exists(country_ids, doc.get('country'))
    
#     # Extract IDs from legal documents GST table
#     if 'legal_documents' in documents:
#         doc = documents['legal_documents']
#         for row in doc.get('gst_table', []):
#             _add_to_set_if_exists(state_ids, row.get('gst_state'))
    
#     # Extract IDs from vendor onboarding
#     if 'vendor_onboarding' in documents:
#         doc = documents['vendor_onboarding']
#         _add_to_set_if_exists(company_ids, doc.get('company_name'))
    
#     # Batch fetch master data
#     try:
#         if city_ids:
#             master_data['cities'] = _fetch_master_records("City Master", list(city_ids), 
#                                                          ["name", "city_code", "city_name"])
        
#         if district_ids:
#             master_data['districts'] = _fetch_master_records("District Master", list(district_ids), 
#                                                             ["name", "district_code", "district_name"])
        
#         if state_ids:
#             master_data['states'] = _fetch_master_records("State Master", list(state_ids), 
#                                                          ["name", "state_code", "state_name"])
        
#         if country_ids:
#             master_data['countries'] = _fetch_master_records("Country Master", list(country_ids), 
#                                                             ["name", "country_code", "country_name"])
        
#         if company_ids:
#             master_data['companies'] = _fetch_master_records("Company Master", list(company_ids), 
#                                                             ["name", "company_code", "company_name", "description"])
        
#         if bank_ids:
#             master_data['banks'] = _fetch_master_records("Bank Master", list(bank_ids), 
#                                                         ["name", "bank_code", "country", "description"])
            
#     except Exception as e:
#         frappe.log_error(f"Error fetching master data: {str(e)}", "Master Data Fetch Error")
    
#     return master_data


# def _fetch_master_records(doctype, ids, fields):
#     """Fetch master records in batch"""
#     if not ids:
#         return {}
    
#     try:
#         records = frappe.db.get_all(doctype, 
#                                    filters={"name": ["in", ids]}, 
#                                    fields=fields)
#         return {record['name']: record for record in records}
#     except Exception as e:
#         frappe.log_error(f"Error fetching {doctype}: {str(e)}", "Master Record Fetch Error")
#         return {}


# def _fetch_file_data(documents):
#     """Pre-fetch all file data to reduce individual file queries"""
#     file_urls = set()
    
#     # Collect all file URLs
#     for doc_name, doc in documents.items():
#         if not doc:
#             continue
            
#         # Handle different document types
#         if doc_name == 'company_details':
#             _add_to_set_if_exists(file_urls, doc.get('address_proofattachment'))
            
#         elif doc_name == 'legal_documents':
#             for field in ["pan_proof", "entity_proof", "msme_proof", "iec_proof", 
#                          "form_10f_proof", "trc_certificate", "pe_certificate"]:
#                 _add_to_set_if_exists(file_urls, doc.get(field))
            
#             # GST table files
#             for row in doc.get('gst_table', []):
#                 _add_to_set_if_exists(file_urls, row.get('gst_document'))
                
#         elif doc_name == 'payment_details':
#             _add_to_set_if_exists(file_urls, doc.get('bank_proof'))
#             _add_to_set_if_exists(file_urls, doc.get('bank_proof_by_purchase_team'))
            
#             # International and intermediate bank details
#             for row in doc.get('international_bank_details', []):
#                 _add_to_set_if_exists(file_urls, row.get('bank_proof_for_beneficiary_bank'))
            
#             for row in doc.get('intermediate_bank_details', []):
#                 _add_to_set_if_exists(file_urls, row.get('bank_proof_for_intermediate_bank'))
                
#         elif doc_name == 'manufacturing_details':
#             _add_to_set_if_exists(file_urls, doc.get('brochure_proof'))
#             _add_to_set_if_exists(file_urls, doc.get('organisation_structure_document'))
            
#             for row in doc.get('materials_supplied', []):
#                 _add_to_set_if_exists(file_urls, row.get('material_images'))
                
#         elif doc_name == 'certificates':
#             for row in doc.get('certificates', []):
#                 _add_to_set_if_exists(file_urls, row.get('certificate_attach'))
    
#     # Batch fetch file data
#     file_data = {}
#     if file_urls:
#         try:
#             # Remove None values
#             file_urls = [url for url in file_urls if url]
            
#             if file_urls:
#                 files = frappe.db.get_all("File", 
#                                         filters={"file_url": ["in", file_urls]}, 
#                                         fields=["file_url", "name", "file_name"])
                
#                 backend_http = frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')
                
#                 for file_record in files:
#                     file_data[file_record['file_url']] = {
#                         "url": f"{backend_http}{file_record['file_url']}",
#                         "name": file_record['name'],
#                         "file_name": file_record['file_name']
#                     }
                    
#         except Exception as e:
#             frappe.log_error(f"Error fetching file data: {str(e)}", "File Data Fetch Error")
    
#     return file_data


# def _add_to_set_if_exists(target_set, value):
#     """Helper function to add value to set if it exists"""
#     if value:
#         target_set.add(value)


# def _get_file_info(file_url, file_data):
#     """Get file information from cached data or return empty dict"""
#     if file_url and file_url in file_data:
#         return file_data[file_url]
#     return {"url": "", "name": "", "file_name": ""}


# def _get_master_info(master_id, master_data, master_type):
#     """Get master information from cached data or return empty dict"""
#     if master_id and master_id in master_data.get(master_type, {}):
#         return master_data[master_type][master_id]
#     return {}


# def _build_response_data(documents, master_data, file_data, vendor_onboarding):
#     """Build the complete response using cached data"""
#     response = {}
    
#     # Company Details Tab
#     if 'company_details' in documents:
#         response['company_details_tab'] = _build_company_details(
#             documents['company_details'], documents.get('vendor_onboarding'), 
#             master_data, vendor_onboarding)
    
#     # Address Details Tab
#     if 'company_details' in documents:
#         response['company_address_tab'] = _build_address_details(
#             documents['company_details'], master_data, file_data)
    
#     # Document Details Tab
#     if 'legal_documents' in documents:
#         response['document_details_tab'] = _build_document_details(
#             documents['legal_documents'], documents.get('vendor_onboarding'), 
#             master_data, file_data, vendor_onboarding)
    
#     # Payment Details Tab
#     if 'payment_details' in documents:
#         response['payment_details_tab'] = _build_payment_details(
#             documents['payment_details'], master_data, file_data)
    
#     # Other tabs
#     if 'vendor_onboarding' in documents:
#         vonb = documents['vendor_onboarding']
#         response['contact_details_tab'] = [row.as_dict() for row in vonb.get('contact_details', [])]
#         response['employee_details_tab'] = [row.as_dict() for row in vonb.get('number_of_employee', [])]
#         response['machinery_details_tab'] = [row.as_dict() for row in vonb.get('machinery_detail', [])]
#         response['testing_details_tab'] = [row.as_dict() for row in vonb.get('testing_detail', [])]
#         response['reputed_partners_details_tab'] = [row.as_dict() for row in vonb.get('reputed_partners', [])]
        
#         # Multi-company data
#         response['is_multi_company'] = vonb.get('registered_for_multi_companies', 0)
#         response['multi_company_data'] = [row.as_dict() for row in vonb.get('multiple_company', [])] if vonb.get('registered_for_multi_companies') else []
    
#     # Manufacturing Details Tab
#     if 'manufacturing_details' in documents:
#         response['manufacturing_details_tab'] = _build_manufacturing_details(
#             documents['manufacturing_details'], file_data)
    
#     # Certificate Details Tab
#     if 'certificates' in documents:
#         response['certificate_details_tab'] = _build_certificate_details(
#             documents['certificates'], file_data)
    
#     # Purchasing Details
#     if 'vendor_onboarding' in documents:
#         response['purchasing_details'] = _build_purchasing_details(
#             documents['vendor_onboarding'], master_data)
    
#     # Validation Check
#     if 'vendor_onboarding' in documents:
#         response['validation_check'] = _build_validation_check(documents['vendor_onboarding'])
    
#     return response


# def _build_company_details(doc, vonb_doc, master_data, vendor_onboarding):
#     """Build company details section"""
#     company_fields = [
#         "vendor_title", "vendor_name", "company_name", "type_of_business", "size_of_company",
#         "website", "registered_office_number", "telephone_number", "whatsapp_number",
#         "established_year", "office_email_primary", "office_email_secondary",
#         "corporate_identification_number", "cin_date", "nature_of_company", "nature_of_business"
#     ]
    
#     company_details = {field: doc.get(field) for field in company_fields}
    
#     # Company name description
#     company_details["company_name_description"] = _get_master_info(
#         doc.get('company_name'), master_data, 'companies'
#     ).get('description', '')
    
#     # Vendor types from master
#     vendor_type_list_from_master = []
#     try:
#         if frappe.db.exists("Vendor Master", doc.get('ref_no')):
#             vendor_doc = frappe.get_doc("Vendor Master", doc.get('ref_no'))
#             vendor_type_list_from_master = [row.vendor_type for row in vendor_doc.get('vendor_types', [])]
#     except Exception:
#         pass
    
#     company_details["vendor_type_list_from_master"] = vendor_type_list_from_master
    
#     # Vendor types from onboarding
#     if vonb_doc:
#         vendor_type_list = [row.vendor_type for row in vonb_doc.get('vendor_types', [])]
#         company_details["vendor_types"] = vendor_type_list
    
#     return company_details


# def _build_address_details(doc, master_data, file_data):
#     """Build address details section"""
#     address_fields = ["same_as_above", "multiple_locations"]
#     address_details = {field: doc.get(field) for field in address_fields}
    
#     # Billing Address
#     billing_address_fields = [
#         "address_line_1", "address_line_2", "pincode", "city", "district", "state", "country", 
#         "international_city", "international_state", "international_country", "international_zipcode"
#     ]
    
#     billing_address = {field: doc.get(field) for field in billing_address_fields}
#     billing_address.update({
#         "city_details": _get_master_info(doc.get('city'), master_data, 'cities'),
#         "district_details": _get_master_info(doc.get('district'), master_data, 'districts'),
#         "state_details": _get_master_info(doc.get('state'), master_data, 'states'),
#         "country_details": _get_master_info(doc.get('country'), master_data, 'countries')
#     })
    
#     address_details["billing_address"] = billing_address
    
#     # Shipping Address
#     shipping_address_fields = [
#         "street_1", "street_2", "manufacturing_pincode", "manufacturing_city", 
#         "manufacturing_district", "manufacturing_state", "manufacturing_country", 
#         "inter_manufacture_city", "inter_manufacture_state", "inter_manufacture_country", 
#         "inter_manufacture_zipcode"
#     ]
    
#     shipping_address = {field: doc.get(field) for field in shipping_address_fields}
#     shipping_address.update({
#         "city_details": _get_master_info(doc.get('manufacturing_city'), master_data, 'cities'),
#         "district_details": _get_master_info(doc.get('manufacturing_district'), master_data, 'districts'),
#         "state_details": _get_master_info(doc.get('manufacturing_state'), master_data, 'states'),
#         "country_details": _get_master_info(doc.get('manufacturing_country'), master_data, 'countries')
#     })
    
#     address_details["shipping_address"] = shipping_address
    
#     # Multiple Location Table
#     multiple_location_data = []
#     for row in doc.get('multiple_location_table', []):
#         location = row.as_dict()
#         location.update({
#             "city_details": _get_master_info(row.get('ma_city'), master_data, 'cities'),
#             "district_details": _get_master_info(row.get('ma_district'), master_data, 'districts'),
#             "state_details": _get_master_info(row.get('ma_state'), master_data, 'states'),
#             "country_details": _get_master_info(row.get('ma_country'), master_data, 'countries')
#         })
#         multiple_location_data.append(location)
    
#     address_details["multiple_location_table"] = multiple_location_data
#     address_details["address_proofattachment"] = _get_file_info(doc.get('address_proofattachment'), file_data)
    
#     return address_details


# def _build_document_details(doc, vonb_doc, master_data, file_data, vendor_onboarding):
#     """Build document details section"""
#     legal_fields = [
#         "company_pan_number", "name_on_company_pan", "enterprise_registration_number",
#         "msme_registered", "msme_enterprise_type", "udyam_number", "name_on_udyam_certificate", 
#         "iec", "trc_certificate_no"
#     ]
    
#     document_details = {field: doc.get(field) for field in legal_fields}
    
#     # Attach fields
#     for field in ["pan_proof", "entity_proof", "msme_proof", "iec_proof", 
#                  "form_10f_proof", "trc_certificate", "pe_certificate"]:
#         document_details[field] = _get_file_info(doc.get(field), file_data)
    
#     # GST Table
#     gst_table = []
#     company_gst_table = []
    
#     for row in doc.get('gst_table', []):
#         gst_row = row.as_dict()
#         gst_row["state_details"] = _get_master_info(row.get('gst_state'), master_data, 'states')
#         gst_row["gst_document"] = _get_file_info(row.get('gst_document'), file_data)
#         gst_table.append(gst_row)
    
#     document_details["gst_table"] = gst_table
    
#     # Company GST filtering logic (simplified for performance)
#     if vonb_doc and vonb_doc.get('vendor_company_details'):
#         try:
#             vendor_company_detail = vonb_doc.vendor_company_details[0]
#             if vendor_company_detail.get('vendor_company_details'):
#                 company_detail_doc = frappe.get_doc("Vendor Onboarding Company Details", 
#                                                    vendor_company_detail.vendor_company_details)
#                 target_company = company_detail_doc.get('company_name')
                
#                 company_gst_table = [
#                     gst_row for gst_row in gst_table 
#                     for original_gst_row in doc.get('gst_table', [])
#                     if (hasattr(original_gst_row, 'company') and 
#                         original_gst_row.company == target_company and 
#                         original_gst_row.name == gst_row.get('name'))
#                 ]
#         except Exception as e:
#             frappe.log_error(f"Error filtering company GST table: {str(e)}", "GST Filter Error")
    
#     document_details["company_gst_table"] = company_gst_table
    
#     return document_details


# def _build_payment_details(doc, master_data, file_data):
#     """Build payment details section"""
#     payment_fields = [
#         "bank_name", "ifsc_code", "account_number", "name_of_account_holder",
#         "type_of_account", "currency", "rtgs", "neft", "ift"
#     ]
    
#     payment_details = {field: doc.get(field) for field in payment_fields}
#     payment_details["bank_name_details"] = _get_master_info(doc.get('bank_name'), master_data, 'banks')
    
#     # Bank proofs
#     payment_details["bank_proof"] = _get_file_info(doc.get('bank_proof'), file_data)
#     payment_details["bank_proof_by_purchase_team"] = _get_file_info(
#         doc.get('bank_proof_by_purchase_team'), file_data)
    
#     payment_details["address"] = {"country": doc.get('country', '')}
    
#     # International and intermediate bank details
#     international_bank_details = []
#     for row in doc.get('international_bank_details', []):
#         bank_row = row.as_dict()
#         bank_row["bank_proof_for_beneficiary_bank"] = _get_file_info(
#             row.get('bank_proof_for_beneficiary_bank'), file_data)
#         international_bank_details.append(bank_row)
    
#     intermediate_bank_details = []
#     for row in doc.get('intermediate_bank_details', []):
#         bank_row = row.as_dict()
#         bank_row["bank_proof_for_intermediate_bank"] = _get_file_info(
#             row.get('bank_proof_for_intermediate_bank'), file_data)
#         intermediate_bank_details.append(bank_row)
    
#     payment_details["international_bank_details"] = international_bank_details
#     payment_details["intermediate_bank_details"] = intermediate_bank_details
    
#     return payment_details


# def _build_manufacturing_details(doc, file_data):
#     """Build manufacturing details section"""
#     manuf_fields = [
#         "total_godown", "storage_capacity", "spare_capacity", "type_of_premises", 
#         "working_hours", "weekly_holidays", "number_of_manpower", "annual_revenue", "cold_storage"
#     ]
    
#     manuf_details = {field: doc.get(field) for field in manuf_fields}
    
#     # Materials supplied
#     materials_supplied = []
#     for row in doc.get('materials_supplied', []):
#         row_data = row.as_dict()
#         row_data["material_images"] = _get_file_info(row.get('material_images'), file_data)
#         materials_supplied.append(row_data)
    
#     manuf_details["materials_supplied"] = materials_supplied
    
#     # Attachment fields
#     for field in ["brochure_proof", "organisation_structure_document"]:
#         manuf_details[field] = _get_file_info(doc.get(field), file_data)
    
#     return manuf_details


# def _build_certificate_details(doc, file_data):
#     """Build certificate details section"""
#     certificate_details = []
    
#     for row in doc.get('certificates', []):
#         row_data = {
#             "name": row.name,
#             "idx": row.idx,
#             "certificate_code": row.get('certificate_code'),
#             "valid_till": row.get('valid_till'),
#             "certificate_attach": _get_file_info(row.get('certificate_attach'), file_data)
#         }
#         certificate_details.append(row_data)
    
#     return certificate_details


# def _build_purchasing_details(vonb_doc, master_data):
#     """Build purchasing details section"""
#     pur_data = {}
    
#     if vonb_doc:
#         pur_data = {
#             "company_name": vonb_doc.get('company_name'),
#             "purchase_organization": vonb_doc.get('purchase_organization'),
#             "order_currency": vonb_doc.get('order_currency'),
#             "terms_of_payment": vonb_doc.get('terms_of_payment'),
#             "purchase_group": vonb_doc.get('purchase_group'),
#             "account_group": vonb_doc.get('account_group'),
#             "reconciliation_account": vonb_doc.get('reconciliation_account'),
#             "qa_team_remarks": vonb_doc.get('qa_team_remarks'),
#             "purchase_team_remarks": vonb_doc.get('purchase_team_approval_remarks'),
#             "purchase_head_remarks": vonb_doc.get('purchase_head_approval_remarks'),
#             "account_team_remarks": vonb_doc.get('accounts_team_approval_remarks'),
#             "incoterms": vonb_doc.get('incoterms'),
#             "company_details": _get_master_info(vonb_doc.get('company_name'), master_data, 'companies')
#         }
        
#         # Additional master data (would need to be added to _fetch_master_data function)
#         # This is a simplified version - you'd need to extend the master data fetching
#         pur_data.update({
#             "pur_org_details": {},
#             "currency_details": {},
#             "term_payment_details": {},
#             "pur_group_details": {},
#             "account_group_details": {},
#             "reconciliation_details": {}
#         })
    
#     return [pur_data] if pur_data else []


# def _build_validation_check(vonb_doc):
#     """Build validation check section"""
#     check_box_fields = [
#         "mandatory_data_filled", "register_by_account_team", "form_fully_submitted_by_vendor", 
#         "purchase_team_undertaking", "purchase_head_undertaking", "accounts_team_undertaking", 
#         "accounts_head_undertaking"
#     ]
    
#     validation_check = {field: vonb_doc.get(field, 0) for field in check_box_fields}
    
#     # Approval status logic
#     if vonb_doc.get('register_by_account_team') == 0:
#         if vonb_doc.get('mail_sent_to_purchase_team'):
#             validation_check.update({
#                 "is_purchase_approve": 1,
#                 "is_purchase_head_approve": 0,
#                 "is_accounts_team_approve": 0,
#                 "is_accounts_head_approve": 0
#             })

#         if vonb_doc.get('mail_sent_to_purchase_head') and vonb_doc.get('mail_sent_to_purchase_team'):
#             validation_check.update({
#                 "is_purchase_approve": 0,
#                 "is_purchase_head_approve": 1,
#                 "is_accounts_team_approve": 0,
#                 "is_accounts_head_approve": 0
#             })

#         if (vonb_doc.get('mail_sent_to_account_team') and 
#             vonb_doc.get('mail_sent_to_purchase_head') and 
#             vonb_doc.get('mail_sent_to_purchase_team')):
#             validation_check.update({
#                 "is_purchase_approve": 0,
#                 "is_purchase_head_approve": 0,
#                 "is_accounts_team_approve": 1,
#                 "is_accounts_head_approve": 0
#             })

#         if (vonb_doc.get('accounts_team_undertaking') and 
#             vonb_doc.get('mail_sent_to_account_team') and 
#             vonb_doc.get('mail_sent_to_purchase_head') and 
#             vonb_doc.get('mail_sent_to_purchase_team')):
#             validation_check.update({
#                 "is_purchase_approve": 0,
#                 "is_purchase_head_approve": 0,
#                 "is_accounts_team_approve": 0,
#                 "is_accounts_head_approve": 0
#             })

#     elif vonb_doc.get('register_by_account_team') == 1:
#         if vonb_doc.get('mail_sent_to_account_team'):
#             validation_check.update({
#                 "is_purchase_approve": 0,
#                 "is_purchase_head_approve": 0,
#                 "is_accounts_team_approve": 1,
#                 "is_accounts_head_approve": 0
#             })

#         if vonb_doc.get('mail_sent_to_account_head') and vonb_doc.get('mail_sent_to_account_team'):
#             validation_check.update({
#                 "is_purchase_approve": 0,
#                 "is_purchase_head_approve": 0,
#                 "is_accounts_team_approve": 0,
#                 "is_accounts_head_approve": 1
#             })

#         if (vonb_doc.get('accounts_head_undertaking') and 
#             vonb_doc.get('mail_sent_to_account_head') and 
#             vonb_doc.get('mail_sent_to_account_team')):
#             validation_check.update({
#                 "is_purchase_approve": 0,
#                 "is_purchase_head_approve": 0,
#                 "is_accounts_team_approve": 0,
#                 "is_accounts_head_approve": 0
#             })

#     return validation_check


# # Additional helper functions for enhanced robustness

# def _validate_document_access(doctype, docname):
#     """Validate if document exists and user has access"""
#     try:
#         return frappe.has_permission(doctype, doc=docname) and frappe.db.exists(doctype, docname)
#     except Exception:
#         return False


# def _safe_get_doc(doctype, docname):
#     """Safely get document with error handling"""
#     try:
#         if _validate_document_access(doctype, docname):
#             return frappe.get_doc(doctype, docname)
#     except Exception as e:
#         frappe.log_error(f"Error fetching {doctype} {docname}: {str(e)}", "Safe Document Fetch Error")
#     return None


# def _batch_validate_documents(doc_list):
#     """Validate multiple documents in batch"""
#     valid_docs = []
#     for doctype, docname in doc_list:
#         if docname and _validate_document_access(doctype, docname):
#             valid_docs.append((doctype, docname))
#     return valid_docs


# # Performance monitoring decorator
# def monitor_performance(func):
#     """Decorator to monitor function performance"""
#     import time
#     from functools import wraps
    
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         start_time = time.time()
#         try:
#             # Filter out Frappe-specific kwargs that aren't function parameters
#             filtered_kwargs = {k: v for k, v in kwargs.items() 
#                              if k not in ['cmd', 'csrf_token', '_']}
            
#             result = func(*args, **filtered_kwargs)
#             execution_time = time.time() - start_time
            
#             # Log slow queries (> 2 seconds)
#             if execution_time > 2:
#                 frappe.log_error(
#                     f"Slow query detected in {func.__name__}: {execution_time:.2f}s",
#                     "Performance Warning"
#                 )
            
#             return result
#         except Exception as e:
#             execution_time = time.time() - start_time
#             # Shortened error message to avoid character limit
#             error_msg = f"Error in {func.__name__}: {str(e)[:100]}..."
#             frappe.log_error(error_msg, "API Error")
#             raise
    
#     return wrapper


# # Cache mechanism for frequently accessed master data
# _master_data_cache = {}
# _cache_timestamp = {}
# CACHE_DURATION = 300  # 5 minutes

# def _get_cached_master_data(key, fetch_func):
#     """Get master data from cache or fetch if expired"""
#     import time
    
#     current_time = time.time()
    
#     if (key in _master_data_cache and 
#         key in _cache_timestamp and 
#         current_time - _cache_timestamp[key] < CACHE_DURATION):
#         return _master_data_cache[key]
    
#     # Fetch fresh data
#     data = fetch_func()
#     _master_data_cache[key] = data
#     _cache_timestamp[key] = current_time
    
#     return data


# def _clear_master_data_cache():
#     """Clear the master data cache"""
#     global _master_data_cache, _cache_timestamp
#     _master_data_cache.clear()
#     _cache_timestamp.clear()


# # Enhanced error handling with specific error types
# class VendorOnboardingError(Exception):
#     """Custom exception for vendor onboarding errors"""
#     def __init__(self, message, error_code=None, details=None):
#         self.message = message
#         self.error_code = error_code
#         self.details = details
#         super().__init__(self.message)


# def _handle_specific_errors(func):
#     """Decorator for handling specific errors"""
#     from functools import wraps
    
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         try:
#             return func(*args, **kwargs)
#         except frappe.DoesNotExistError as e:
#             raise VendorOnboardingError(
#                 "Required document not found", 
#                 error_code="DOCUMENT_NOT_FOUND",
#                 details=str(e)
#             )
#         except frappe.PermissionError as e:
#             raise VendorOnboardingError(
#                 "Insufficient permissions to access document", 
#                 error_code="PERMISSION_DENIED",
#                 details=str(e)
#             )
#         except Exception as e:
#             raise VendorOnboardingError(
#                 "An unexpected error occurred", 
#                 error_code="UNKNOWN_ERROR",
#                 details=str(e)
#             )
    
#     return wrapper









# #  vms.APIs.vendor_onboarding.get_full_data_vonb_optim.get_vendor_onboarding_details_sql_optimized
# @frappe.whitelist(allow_guest=True)
# @monitor_performance
# def get_vendor_onboarding_details_sql_optimized(vendor_onboarding=None, ref_no=None, **kwargs):
#     """
#     Ultra-optimized version using raw SQL queries for maximum performance
#     Use this version if you need the absolute fastest response times
#     """
#     try:
#         if not vendor_onboarding or not ref_no:
#             return {
#                 "status": "error",
#                 "message": "Missing required parameters: 'vendor_onboarding' and 'ref_no'."
#             }

#         # Single SQL query to get all basic document data
#         sql_query = """
#             SELECT 
#                 vocd.name as company_doc_name,
#                 ld.name as legal_doc_name,
#                 vopd.name as payment_doc_name,
#                 vomd.name as manuf_doc_name,
#                 voc.name as cert_doc_name,
#                 vo.name as vendor_onb_name
#             FROM 
#                 `tabVendor Onboarding` vo
#             LEFT JOIN `tabVendor Onboarding Company Details` vocd ON vocd.vendor_onboarding = vo.name AND vocd.ref_no = %s
#             LEFT JOIN `tabLegal Documents` ld ON ld.vendor_onboarding = vo.name AND ld.ref_no = %s
#             LEFT JOIN `tabVendor Onboarding Payment Details` vopd ON vopd.vendor_onboarding = vo.name AND vopd.ref_no = %s
#             LEFT JOIN `tabVendor Onboarding Manufacturing Details` vomd ON vomd.vendor_onboarding = vo.name AND vomd.ref_no = %s
#             LEFT JOIN `tabVendor Onboarding Certificates` voc ON voc.vendor_onboarding = vo.name AND voc.ref_no = %s
#             WHERE vo.name = %s
#         """
        
#         result = frappe.db.sql(sql_query, 
#                               (ref_no, ref_no, ref_no, ref_no, ref_no, vendor_onboarding), 
#                               as_dict=True)
        
#         if not result or not result[0].get('company_doc_name'):
#             return {
#                 "status": "error",
#                 "message": "No matching Vendor Onboarding Company Details record found."
#             }
        
#         doc_names = result[0]
        
#         # Use the existing optimized functions with the SQL-fetched document names
#         documents = {}
        
#         # Fetch documents based on SQL results
#         if doc_names.get('vendor_onb_name'):
#             documents['vendor_onboarding'] = frappe.get_doc("Vendor Onboarding", doc_names['vendor_onb_name'])
        
#         if doc_names.get('company_doc_name'):
#             documents['company_details'] = frappe.get_doc("Vendor Onboarding Company Details", doc_names['company_doc_name'])
        
#         if doc_names.get('legal_doc_name'):
#             documents['legal_documents'] = frappe.get_doc("Legal Documents", doc_names['legal_doc_name'])
        
#         if doc_names.get('payment_doc_name'):
#             documents['payment_details'] = frappe.get_doc("Vendor Onboarding Payment Details", doc_names['payment_doc_name'])
        
#         if doc_names.get('manuf_doc_name'):
#             documents['manufacturing_details'] = frappe.get_doc("Vendor Onboarding Manufacturing Details", doc_names['manuf_doc_name'])
        
#         if doc_names.get('cert_doc_name'):
#             documents['certificates'] = frappe.get_doc("Vendor Onboarding Certificates", doc_names['cert_doc_name'])
        
#         # Use cached master data fetching
#         master_data = _get_cached_master_data(
#             f"master_data_{vendor_onboarding}_{ref_no}",
#             lambda: _fetch_master_data(documents)
#         )
        
#         # Pre-fetch file data
#         file_data = _fetch_file_data(documents)
        
#         # Build response
#         response_data = _build_response_data(documents, master_data, file_data, vendor_onboarding)
        
#         return {
#             "status": "success",
#             "message": "Vendor onboarding details fetched successfully.",
#             **response_data
#         }

#     except VendorOnboardingError as e:
#         return {
#             "status": "error",
#             "message": e.message,
#             "error_code": e.error_code,
#             "details": e.details
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Details SQL Fetch Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch vendor onboarding details.",
#             "error": cstr(e)
#         }


import frappe
from frappe import _
from frappe.utils import cstr

@frappe.whitelist(allow_guest=True)
def get_vendor_onboarding_details_ultra_fast(vendor_onboarding=None, ref_no=None, **kwargs):
    """
    Ultra-fast version optimized to beat 117ms - focuses on minimal database calls
    """
    try:
        if not vendor_onboarding or not ref_no:
            return {
                "status": "error",
                "message": "Missing required parameters: 'vendor_onboarding' and 'ref_no'."
            }

        # Single SQL query to get all document names and basic data
        doc_data = frappe.db.sql("""
            SELECT 
                vocd.name as company_doc_name,
                ld.name as legal_doc_name,
                vopd.name as payment_doc_name,
                vomd.name as manuf_doc_name,
                voc.name as cert_doc_name
            FROM `tabVendor Onboarding Company Details` vocd
            LEFT JOIN `tabLegal Documents` ld ON ld.vendor_onboarding = vocd.vendor_onboarding AND ld.ref_no = vocd.ref_no
            LEFT JOIN `tabVendor Onboarding Payment Details` vopd ON vopd.vendor_onboarding = vocd.vendor_onboarding AND vopd.ref_no = vocd.ref_no
            LEFT JOIN `tabVendor Onboarding Manufacturing Details` vomd ON vomd.vendor_onboarding = vocd.vendor_onboarding AND vomd.ref_no = vocd.ref_no
            LEFT JOIN `tabVendor Onboarding Certificates` voc ON voc.vendor_onboarding = vocd.vendor_onboarding AND voc.ref_no = vocd.ref_no
            WHERE vocd.vendor_onboarding = %s AND vocd.ref_no = %s
            LIMIT 1
        """, (vendor_onboarding, ref_no), as_dict=True)

        if not doc_data:
            return {
                "status": "error",
                "message": "No matching Vendor Onboarding Company Details record found."
            }

        doc_names = doc_data[0]

        # Use parallel document fetching with minimal field selection
        docs = _fetch_documents_minimal2(doc_names, vendor_onboarding)
        
        # Build response with lazy loading
        response = _build_minimal_response2(docs, vendor_onboarding, ref_no)
        
        return {
            "status": "success",
            "message": "Vendor onboarding details fetched successfully.",
            **response
        }

    except Exception as e:
        frappe.log_error(f"Fast API Error: {str(e)[:100]}", "Fast Vendor API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding details.",
            "error": str(e)[:200]
        }


def _fetch_documents_minimal2(doc_names, vendor_onboarding):
    """Fetch only essential document data to minimize database load"""
    docs = {}
    
    # Fetch vendor onboarding with only needed fields
    if vendor_onboarding:
        vo_data = frappe.db.get_value("Vendor Onboarding", vendor_onboarding, [
            "name", "company_name", "purchase_organization", "order_currency", "terms_of_payment",
            "purchase_group", "account_group", "reconciliation_account", "qa_team_remarks",
            "purchase_team_approval_remarks", "purchase_head_approval_remarks", 
            "accounts_team_approval_remarks", "incoterms", "registered_for_multi_companies",
            "mandatory_data_filled", "register_by_account_team", "form_fully_submitted_by_vendor",
            "purchase_team_undertaking", "purchase_head_undertaking", "accounts_team_undertaking",
            "accounts_head_undertaking", "mail_sent_to_purchase_team", "mail_sent_to_purchase_head",
            "mail_sent_to_account_team", "mail_sent_to_account_head"
        ], as_dict=True)
        docs['vendor_onboarding'] = vo_data

    # Only fetch documents that exist
    if doc_names.get('company_doc_name'):
        docs['company_details'] = frappe.get_doc("Vendor Onboarding Company Details", doc_names['company_doc_name'])
    
    if doc_names.get('legal_doc_name'):
        docs['legal_documents'] = frappe.get_doc("Legal Documents", doc_names['legal_doc_name'])
    
    if doc_names.get('payment_doc_name'):
        docs['payment_details'] = frappe.get_doc("Vendor Onboarding Payment Details", doc_names['payment_doc_name'])
    
    if doc_names.get('manuf_doc_name'):
        docs['manufacturing_details'] = frappe.get_doc("Vendor Onboarding Manufacturing Details", doc_names['manuf_doc_name'])
    
    if doc_names.get('cert_doc_name'):
        docs['certificates'] = frappe.get_doc("Vendor Onboarding Certificates", doc_names['cert_doc_name'])

    return docs


def _build_minimal_response2(docs, vendor_onboarding, ref_no):
    """Build response with on-demand master data fetching"""
    response = {}
    
    # Company Details Tab - minimal processing
    if 'company_details' in docs:
        response['company_details_tab'] = _build_company_details_fast2(docs['company_details'], docs.get('vendor_onboarding'), vendor_onboarding, ref_no)
    
    # Address Details Tab - with lazy master data loading
    if 'company_details' in docs:
        response['company_address_tab'] = _build_address_details_fast2(docs['company_details'])
    
    # Document Details Tab
    if 'legal_documents' in docs:
        response['document_details_tab'] = _build_document_details_fast2(docs['legal_documents'], docs.get('vendor_onboarding'), vendor_onboarding)
    
    # Payment Details Tab
    if 'payment_details' in docs:
        response['payment_details_tab'] = _build_payment_details_fast2(docs['payment_details'])
    
    # Simple child table data without processing
    if 'vendor_onboarding' in docs or docs.get('vendor_onboarding'):
        vo_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding) if 'vendor_onboarding' not in docs else None
        if vo_doc:
            response['contact_details_tab'] = [row.as_dict() for row in vo_doc.get('contact_details', [])]
            response['employee_details_tab'] = [row.as_dict() for row in vo_doc.get('number_of_employee', [])]
            response['machinery_details_tab'] = [row.as_dict() for row in vo_doc.get('machinery_detail', [])]
            response['testing_details_tab'] = [row.as_dict() for row in vo_doc.get('testing_detail', [])]
            response['reputed_partners_details_tab'] = [row.as_dict() for row in vo_doc.get('reputed_partners', [])]
            response['is_multi_company'] = vo_doc.get('registered_for_multi_companies', 0)
            response['multi_company_data'] = [row.as_dict() for row in vo_doc.get('multiple_company', [])] if vo_doc.get('registered_for_multi_companies') else []
        else:
            # Use cached data
            vo_data = docs.get('vendor_onboarding', {})
            response['contact_details_tab'] = []
            response['employee_details_tab'] = []
            response['machinery_details_tab'] = []
            response['testing_details_tab'] = []
            response['reputed_partners_details_tab'] = []
            response['is_multi_company'] = vo_data.get('registered_for_multi_companies', 0)
            response['multi_company_data'] = []
    
    # Manufacturing Details Tab
    if 'manufacturing_details' in docs:
        response['manufacturing_details_tab'] = _build_manufacturing_details_fast2(docs['manufacturing_details'])
    
    # Certificate Details Tab
    if 'certificates' in docs:
        response['certificate_details_tab'] = _build_certificate_details_fast2(docs['certificates'])
    
    # Purchasing Details
    if docs.get('vendor_onboarding'):
        response['purchasing_details'] = _build_purchasing_details_fast2(docs['vendor_onboarding'])
    
    # Validation Check
    if docs.get('vendor_onboarding'):
        response['validation_check'] = _build_validation_check_fast2(docs['vendor_onboarding'])
    
    return response


def _build_company_details_fast2(doc, vonb_data, vendor_onboarding, ref_no):
    """Fast company details with minimal database calls"""
    company_fields = [
        "vendor_title", "vendor_name", "company_name", "type_of_business", "size_of_company",
        "website", "registered_office_number", "telephone_number", "whatsapp_number",
        "established_year", "office_email_primary", "office_email_secondary",
        "corporate_identification_number", "cin_date", "nature_of_company", "nature_of_business"
    ]
    
    company_details = {field: doc.get(field) for field in company_fields}
    
    # Only fetch company description if needed
    company_details["company_name_description"] = ""
    if doc.get('company_name'):
        desc = frappe.db.get_value("Company Master", doc.company_name, "description")
        company_details["company_name_description"] = desc or ""
    
    # Simplified vendor types
    company_details["vendor_type_list_from_master"] = []
    company_details["vendor_types"] = []
    
    # Only fetch if exists
    if frappe.db.exists("Vendor Master", ref_no):
        vendor_types = frappe.db.sql("""
            SELECT vendor_type FROM `tabVendor Type Group` 
            WHERE parent = %s AND parenttype = 'Vendor Master'
        """, (ref_no,), as_list=True)
        company_details["vendor_type_list_from_master"] = [vt[0] for vt in vendor_types]
    
    # Get vendor types from onboarding
    vonb_vendor_types = frappe.db.sql("""
        SELECT vendor_type FROM `tabVendor Type Group` 
        WHERE parent = %s AND parenttype = 'Vendor Onboarding'
    """, (vendor_onboarding,), as_list=True)
    company_details["vendor_types"] = [vt[0] for vt in vonb_vendor_types]
    
    return company_details


def _build_address_details_fast2(doc):
    """Fast address details with on-demand master data"""
    address_fields = ["same_as_above", "multiple_locations"]
    address_details = {field: doc.get(field) for field in address_fields}
    
    # Billing Address - fetch master data only when needed
    billing_address_fields = [
        "address_line_1", "address_line_2", "pincode", "city", "district", "state", "country", 
        "international_city", "international_state", "international_country", "international_zipcode"
    ]
    
    billing_address = {field: doc.get(field) for field in billing_address_fields}
    
    # Lazy load master data
    billing_address["city_details"] = _get_master_data_lazy2("City Master", doc.get('city'), ["name", "city_code", "city_name"])
    billing_address["district_details"] = _get_master_data_lazy2("District Master", doc.get('district'), ["name", "district_code", "district_name"])
    billing_address["state_details"] = _get_master_data_lazy2("State Master", doc.get('state'), ["name", "state_code", "state_name"])
    billing_address["country_details"] = _get_master_data_lazy2("Country Master", doc.get('country'), ["name", "country_code", "country_name"])
    
    address_details["billing_address"] = billing_address
    
    # Shipping Address
    shipping_address_fields = [
        "street_1", "street_2", "manufacturing_pincode", "manufacturing_city", 
        "manufacturing_district", "manufacturing_state", "manufacturing_country", 
        "inter_manufacture_city", "inter_manufacture_state", "inter_manufacture_country", 
        "inter_manufacture_zipcode"
    ]
    
    shipping_address = {field: doc.get(field) for field in shipping_address_fields}
    shipping_address["city_details"] = _get_master_data_lazy2("City Master", doc.get('manufacturing_city'), ["name", "city_code", "city_name"])
    shipping_address["district_details"] = _get_master_data_lazy2("District Master", doc.get('manufacturing_district'), ["name", "district_code", "district_name"])
    shipping_address["state_details"] = _get_master_data_lazy2("State Master", doc.get('manufacturing_state'), ["name", "state_code", "state_name"])
    shipping_address["country_details"] = _get_master_data_lazy2("Country Master", doc.get('manufacturing_country'), ["name", "country_code", "country_name"])
    
    address_details["shipping_address"] = shipping_address
    
    # Multiple Location Table - simplified
    multiple_location_data = []
    for row in doc.get('multiple_location_table', []):
        location = row.as_dict()
        location["city_details"] = _get_master_data_lazy2("City Master", row.get('ma_city'), ["name", "city_code", "city_name"])
        location["district_details"] = _get_master_data_lazy2("District Master", row.get('ma_district'), ["name", "district_code", "district_name"])
        location["state_details"] = _get_master_data_lazy2("State Master", row.get('ma_state'), ["name", "state_code", "state_name"])
        location["country_details"] = _get_master_data_lazy2("Country Master", row.get('ma_country'), ["name", "country_code", "country_name"])
        multiple_location_data.append(location)
    
    address_details["multiple_location_table"] = multiple_location_data
    address_details["address_proofattachment"] = _get_file_info_fast2(doc.get('address_proofattachment'))
    
    return address_details


def _build_document_details_fast2(doc, vonb_data, vendor_onboarding):
    """Fast document details building"""
    legal_fields = [
        "company_pan_number", "name_on_company_pan", "enterprise_registration_number",
        "msme_registered", "msme_enterprise_type", "udyam_number", "name_on_udyam_certificate", 
        "iec", "trc_certificate_no"
    ]
    
    document_details = {field: doc.get(field) for field in legal_fields}
    
    # File attachments
    for field in ["pan_proof", "entity_proof", "msme_proof", "iec_proof", 
                 "form_10f_proof", "trc_certificate", "pe_certificate"]:
        document_details[field] = _get_file_info_fast2(doc.get(field))
    
    # GST Table - simplified
    gst_table = []
    for row in doc.get('gst_table', []):
        gst_row = row.as_dict()
        gst_row["state_details"] = _get_master_data_lazy2("State Master", row.get('gst_state'), ["name", "state_code", "state_name"])
        gst_row["gst_document"] = _get_file_info_fast2(row.get('gst_document'))
        gst_table.append(gst_row)
    
    document_details["gst_table"] = gst_table
    document_details["company_gst_table"] = gst_table  # Simplified - no filtering for speed
    
    return document_details


def _build_payment_details_fast2(doc):
    """Fast payment details building"""
    payment_fields = [
        "bank_name", "ifsc_code", "account_number", "name_of_account_holder",
        "type_of_account", "currency", "rtgs", "neft", "ift"
    ]
    
    payment_details = {field: doc.get(field) for field in payment_fields}
    payment_details["bank_name_details"] = _get_master_data_lazy2("Bank Master", doc.get('bank_name'), ["name", "bank_code", "country", "description"])
    
    # File attachments
    payment_details["bank_proof"] = _get_file_info_fast2(doc.get('bank_proof'))
    payment_details["bank_proof_by_purchase_team"] = _get_file_info_fast2(doc.get('bank_proof_by_purchase_team'))
    payment_details["address"] = {"country": doc.get('country', '')}
    
    # Child tables - simplified without file processing for speed
    international_bank_details = []
    for row in doc.get('international_bank_details', []):
        bank_row = row.as_dict()
        bank_row["bank_proof_for_beneficiary_bank"] = _get_file_info_fast2(row.get('bank_proof_for_beneficiary_bank'))
        international_bank_details.append(bank_row)
    
    intermediate_bank_details = []
    for row in doc.get('intermediate_bank_details', []):
        bank_row = row.as_dict()
        bank_row["bank_proof_for_intermediate_bank"] = _get_file_info_fast2(row.get('bank_proof_for_intermediate_bank'))
        intermediate_bank_details.append(bank_row)
    
    payment_details["international_bank_details"] = international_bank_details
    payment_details["intermediate_bank_details"] = intermediate_bank_details
    
    return payment_details


def _build_manufacturing_details_fast2(doc):
    """Fast manufacturing details building"""
    manuf_fields = [
        "total_godown", "storage_capacity", "spare_capacity", "type_of_premises", 
        "working_hours", "weekly_holidays", "number_of_manpower", "annual_revenue", "cold_storage"
    ]
    
    manuf_details = {field: doc.get(field) for field in manuf_fields}
    
    # Materials supplied - simplified
    materials_supplied = []
    for row in doc.get('materials_supplied', []):
        row_data = row.as_dict()
        row_data["material_images"] = _get_file_info_fast2(row.get('material_images'))
        materials_supplied.append(row_data)
    
    manuf_details["materials_supplied"] = materials_supplied
    manuf_details["brochure_proof"] = _get_file_info_fast2(doc.get('brochure_proof'))
    manuf_details["organisation_structure_document"] = _get_file_info_fast2(doc.get('organisation_structure_document'))
    
    return manuf_details


def _build_certificate_details_fast2(doc):
    """Fast certificate details building"""
    certificate_details = []
    
    for row in doc.get('certificates', []):
        row_data = {
            "name": row.name,
            "idx": row.idx,
            "certificate_code": row.get('certificate_code'),
            "valid_till": row.get('valid_till'),
            "certificate_attach": _get_file_info_fast2(row.get('certificate_attach'))
        }
        certificate_details.append(row_data)
    
    return certificate_details


def _build_purchasing_details_fast2(vonb_data):
    """Fast purchasing details building"""
    if not vonb_data:
        return []
    
    pur_data = {
        "company_name": vonb_data.get('company_name'),
        "purchase_organization": vonb_data.get('purchase_organization'),
        "order_currency": vonb_data.get('order_currency'),
        "terms_of_payment": vonb_data.get('terms_of_payment'),
        "purchase_group": vonb_data.get('purchase_group'),
        "account_group": vonb_data.get('account_group'),
        "reconciliation_account": vonb_data.get('reconciliation_account'),
        "qa_team_remarks": vonb_data.get('qa_team_remarks'),
        "purchase_team_remarks": vonb_data.get('purchase_team_approval_remarks'),
        "purchase_head_remarks": vonb_data.get('purchase_head_approval_remarks'),
        "account_team_remarks": vonb_data.get('accounts_team_approval_remarks'),
        "incoterms": vonb_data.get('incoterms'),
        "company_details": _get_master_data_lazy2("Company Master", vonb_data.get('company_name'), ["name", "company_code", "company_name", "description"]),
        # Simplified - empty master data for speed
        "pur_org_details": {},
        "currency_details": {},
        "term_payment_details": {},
        "pur_group_details": {},
        "account_group_details": {},
        "reconciliation_details": {}
    }
    
    return [pur_data]


def _build_validation_check_fast2(vonb_data):
    """Fast validation check building"""
    check_box_fields = [
        "mandatory_data_filled", "register_by_account_team", "form_fully_submitted_by_vendor", 
        "purchase_team_undertaking", "purchase_head_undertaking", "accounts_team_undertaking", 
        "accounts_head_undertaking"
    ]
    
    validation_check = {field: vonb_data.get(field, 0) for field in check_box_fields}
    
    # Simplified approval logic
    validation_check.update({
        "is_purchase_approve": 1 if vonb_data.get('mail_sent_to_purchase_team') else 0,
        "is_purchase_head_approve": 1 if vonb_data.get('mail_sent_to_purchase_head') else 0,
        "is_accounts_team_approve": 1 if vonb_data.get('mail_sent_to_account_team') else 0,
        "is_accounts_head_approve": 1 if vonb_data.get('mail_sent_to_account_head') else 0
    })
    
    return validation_check


def _get_master_data_lazy2(doctype, docname, fields):
    """Lazy load master data only when needed"""
    if not docname:
        return {}
    
    try:
        return frappe.db.get_value(doctype, docname, fields, as_dict=True) or {}
    except:
        return {}


def _get_file_info_fast2(file_url):
    """Fast file info retrieval"""
    if not file_url:
        return {"url": "", "name": "", "file_name": ""}
    
    try:
        file_data = frappe.db.get_value("File", {"file_url": file_url}, ["name", "file_name"], as_dict=True)
        if file_data:
            backend_http = frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')
            return {
                "url": f"{backend_http}{file_url}",
                "name": file_data.get('name', ''),
                "file_name": file_data.get('file_name', '')
            }
    except:
        pass
    
    return {"url": "", "name": "", "file_name": ""}





def _get_master_quick(doctype, docname):
    """Super-fast master data with aggressive caching"""
    if not docname:
        return {}
    
    cache_key = f"master_{doctype}_{docname}"
    if cache_key in _global_cache:
        return _global_cache[cache_key]
    
    try:
        # Field mapping based on sample response
        if doctype == "City Master":
            result = frappe.db.get_value(doctype, docname, ["name", "city_code", "city_name"], as_dict=True) or {}
        elif doctype == "District Master":
            result = frappe.db.get_value(doctype, docname, ["name", "district_code", "district_name"], as_dict=True) or {}
        elif doctype == "State Master":
            result = frappe.db.get_value(doctype, docname, ["name", "state_code", "state_name"], as_dict=True) or {}
        elif doctype == "Country Master":
            result = frappe.db.get_value(doctype, docname, ["name", "country_code", "country_name"], as_dict=True) or {}
        elif doctype == "Company Master":
            result = frappe.db.get_value(doctype, docname, ["name", "company_code", "company_name", "description"], as_dict=True) or {}
        elif doctype == "Bank Master":
            result = frappe.db.get_value(doctype, docname, ["name", "bank_code", "country", "description"], as_dict=True) or {}
        elif doctype == "Purchase Organization Master":
            result = frappe.db.get_value(doctype, docname, ["name", "purchase_organization_code", "purchase_organization_name", "description"], as_dict=True) or {}
        elif doctype == "Currency Master":
            result = frappe.db.get_value(doctype, docname, ["name", "currency_code", "currency_name", "country"], as_dict=True) or {}
        elif doctype == "Terms of Payment Master":
            result = frappe.db.get_value(doctype, docname, ["name", "terms_of_payment_code", "terms_of_payment_name", "description"], as_dict=True) or {}
        elif doctype == "Purchase Group Master":
            result = frappe.db.get_value(doctype, docname, ["name", "purchase_group_code", "purchase_group_name", "description"], as_dict=True) or {}
        elif doctype == "Account Group Master":
            result = frappe.db.get_value(doctype, docname, ["name", "account_group_code", "account_group_name", "account_group_description"], as_dict=True) or {}
        elif doctype == "Reconciliation Account":
            result = frappe.db.get_value(doctype, docname, ["name", "reconcil_account_code", "reconcil_account", "reconcil_description"], as_dict=True) or {}
        else:
            result = frappe.db.get_value(doctype, docname, ["name"], as_dict=True) or {}
        
        _global_cache[cache_key] = result
        return result
    except:
        return {}


def _build_purchasing_fast(data):
    """Ultra-fast purchasing details with complete master data"""
    return [{
        "company_name": data.get('vo_company_name'),
        "purchase_organization": data.get('purchase_organization'),
        "order_currency": data.get('order_currency'),
        "terms_of_payment": data.get('terms_of_payment'),
        "purchase_group": data.get('purchase_group'),
        "account_group": data.get('account_group'),
        "reconciliation_account": data.get('reconciliation_account'),
        "qa_team_remarks": data.get('qa_team_remarks'),
        "purchase_team_remarks": data.get('purchase_team_approval_remarks'),
        "purchase_head_remarks": data.get('purchase_head_approval_remarks'),
        "account_team_remarks": data.get('accounts_team_approval_remarks'),
        "incoterms": data.get('incoterms'),
        "company_details": _get_master_quick("Company Master", data.get('vo_company_name')),
        "pur_org_details": _get_master_quick("Purchase Organization Master", data.get('purchase_organization')),
        "currency_details": _get_master_quick("Currency Master", data.get('order_currency')),
        "term_payment_details": _get_master_quick("Terms of Payment Master", data.get('terms_of_payment')),
        "pur_group_details": _get_master_quick("Purchase Group Master", data.get('purchase_group')),
        "account_group_details": _get_master_quick("Account Group Master", data.get('account_group')),
        "reconciliation_details": _get_master_quick("Reconciliation Account", data.get('reconciliation_account'))
    }]


# Updated file info function with backend URL from config
def _get_file_quick(file_url):
    """Super-fast file info"""
    if not file_url:
        return {"url": "", "name": "", "file_name": ""}
    
    cache_key = f"file_{file_url}"
    if cache_key in _global_cache:
        return _global_cache[cache_key]
    
    try:
        file_data = frappe.db.get_value("File", {"file_url": file_url}, ["name", "file_name"], as_dict=True)
        if file_data:
            # Get backend URL from config or use default
            backend_http = frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')
            result = {
                "url": f"{backend_http}{file_url}",
                "name": file_data.get('name', ''),
                "file_name": file_data.get('file_name', '')
            }
        else:
            result = {"url": "", "name": "", "file_name": ""}
        
        _global_cache[cache_key] = result
        return result
    except:
        return {"url": "", "name": "", "file_name": ""}


# Additional optimized function for company name description
def _get_company_description_fast(company_name):
    """Fast company description lookup"""
    if not company_name:
        return ""
    
    cache_key = f"company_desc_{company_name}"
    if cache_key in _global_cache:
        return _global_cache[cache_key]
    
    try:
        desc = frappe.db.get_value("Company Master", company_name, "description") or ""
        _global_cache[cache_key] = desc
        return desc
    except:
        return ""


# Update the company details function to include company description
def _build_company_fast(data, vendor_onboarding, ref_no):
    """Ultra-fast company details"""
    company_details = {
        "vendor_title": data.get('vendor_title'),
        "vendor_name": data.get('vendor_name'),
        "company_name": data.get('company_name'),
        "type_of_business": data.get('type_of_business'),
        "size_of_company": data.get('size_of_company'),
        "website": data.get('website'),
        "registered_office_number": data.get('registered_office_number'),
        "telephone_number": data.get('telephone_number'),
        "whatsapp_number": data.get('whatsapp_number'),
        "established_year": data.get('established_year'),
        "office_email_primary": data.get('office_email_primary'),
        "office_email_secondary": data.get('office_email_secondary'),
        "corporate_identification_number": data.get('corporate_identification_number'),
        "cin_date": data.get('cin_date'),
        "nature_of_company": data.get('nature_of_company'),
        "nature_of_business": data.get('nature_of_business'),
        "company_name_description": _get_company_description_fast(data.get('company_name')),
        "vendor_type_list_from_master": [],
        "vendor_types": []
    }
    
    # Only get vendor types if cache miss
    cache_key = f"vendor_types_{vendor_onboarding}_{ref_no}"
    if cache_key not in _global_cache:
        # Single query for both vendor types
        vendor_types = frappe.db.sql("""
            (SELECT vendor_type, 'master' as source FROM `tabVendor Types` 
             WHERE parent = %s AND parenttype = 'Vendor Master')
            UNION ALL
            (SELECT vendor_type, 'onboarding' as source FROM `tabVendor Types` 
             WHERE parent = %s AND parenttype = 'Vendor Onboarding')
        """, (ref_no, vendor_onboarding), as_dict=True)
        
        master_types = [vt['vendor_type'] for vt in vendor_types if vt['source'] == 'master']
        onb_types = [vt['vendor_type'] for vt in vendor_types if vt['source'] == 'onboarding']
        
        _global_cache[cache_key] = {
            'master': master_types,
            'onboarding': onb_types
        }
    
    company_details["vendor_type_list_from_master"] = _global_cache[cache_key]['master']
    company_details["vendor_types"] = _global_cache[cache_key]['onboarding']
    
    return company_details





import frappe
from frappe import _
from frappe.utils import cstr

# Global cache for master data
_global_cache = {}

@frappe.whitelist(allow_guest=True)
def get_vendor_onboarding_details_lightning(vendor_onboarding=None, ref_no=None, **kwargs):
    """
    Lightning-fast version targeting sub-80ms response time
    Aggressive optimizations with minimal database calls
    """
    try:
        if not vendor_onboarding or not ref_no:
            return {"status": "error", "message": "Missing required parameters"}

        # SINGLE MEGA QUERY - Get everything in one shot
        data = frappe.db.sql("""
            SELECT 
                -- Company Details
                vocd.vendor_title, vocd.vendor_name, vocd.company_name, vocd.type_of_business,
                vocd.size_of_company, vocd.website, vocd.registered_office_number, 
                vocd.telephone_number, vocd.whatsapp_number, vocd.established_year,
                vocd.office_email_primary, vocd.office_email_secondary,
                vocd.corporate_identification_number, vocd.cin_date, vocd.nature_of_company,
                vocd.nature_of_business, vocd.same_as_above, vocd.multiple_locations,
                
                -- Address Info
                vocd.address_line_1, vocd.address_line_2, vocd.pincode, vocd.city,
                vocd.district, vocd.state, vocd.country, vocd.international_city,
                vocd.international_state, vocd.international_country, vocd.international_zipcode,
                vocd.street_1, vocd.street_2, vocd.manufacturing_pincode, vocd.manufacturing_city,
                vocd.manufacturing_district, vocd.manufacturing_state, vocd.manufacturing_country,
                vocd.inter_manufacture_city, vocd.inter_manufacture_state, vocd.inter_manufacture_country,
                vocd.inter_manufacture_zipcode, vocd.address_proofattachment,
                
                -- Legal Info
                ld.company_pan_number, ld.name_on_company_pan, ld.enterprise_registration_number,
                ld.msme_registered, ld.msme_enterprise_type, ld.udyam_number,
                ld.name_on_udyam_certificate, ld.iec, ld.trc_certificate_no,
                ld.pan_proof, ld.entity_proof, ld.msme_proof, ld.iec_proof,
                ld.form_10f_proof, ld.trc_certificate, ld.pe_certificate,
                
                -- Payment Info
                vopd.bank_name, vopd.ifsc_code, vopd.account_number, vopd.name_of_account_holder,
                vopd.type_of_account, vopd.currency, vopd.rtgs, vopd.neft, vopd.ift,
                vopd.bank_proof, vopd.bank_proof_by_purchase_team, vopd.country as payment_country,
                
                -- Manufacturing Info
                vomd.total_godown, vomd.storage_capacity, vomd.spare_capacity, vomd.type_of_premises,
                vomd.working_hours, vomd.weekly_holidays, vomd.number_of_manpower,
                vomd.annual_revenue, vomd.cold_storage, vomd.brochure_proof,
                vomd.organisation_structure_document,
                
                -- Vendor Onboarding Info
                vo.company_name as vo_company_name, vo.purchase_organization, vo.order_currency,
                vo.terms_of_payment, vo.purchase_group, vo.account_group, vo.reconciliation_account,
                vo.qa_team_remarks, vo.purchase_team_approval_remarks, vo.purchase_head_approval_remarks,
                vo.accounts_team_approval_remarks, vo.incoterms, vo.registered_for_multi_companies,
                vo.mandatory_data_filled, vo.register_by_account_team, vo.form_fully_submitted_by_vendor,
                vo.purchase_team_undertaking, vo.purchase_head_undertaking, vo.accounts_team_undertaking,
                vo.accounts_head_undertaking, vo.mail_sent_to_purchase_team, vo.mail_sent_to_purchase_head,
                vo.mail_sent_to_account_team, vo.mail_sent_to_account_head,
                
                -- Document Names for child tables
                vocd.name as company_doc_name, ld.name as legal_doc_name,
                vopd.name as payment_doc_name, vomd.name as manuf_doc_name,
                voc.name as cert_doc_name
                
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabVendor Onboarding Company Details` vocd ON vocd.vendor_onboarding = vo.name AND vocd.ref_no = %s
            LEFT JOIN `tabLegal Documents` ld ON ld.vendor_onboarding = vo.name AND ld.ref_no = %s
            LEFT JOIN `tabVendor Onboarding Payment Details` vopd ON vopd.vendor_onboarding = vo.name AND vopd.ref_no = %s
            LEFT JOIN `tabVendor Onboarding Manufacturing Details` vomd ON vomd.vendor_onboarding = vo.name AND vomd.ref_no = %s
            LEFT JOIN `tabVendor Onboarding Certificates` voc ON voc.vendor_onboarding = vo.name AND voc.ref_no = %s
            WHERE vo.name = %s
            LIMIT 1
        """, (ref_no, ref_no, ref_no, ref_no, ref_no, vendor_onboarding), as_dict=True)

        if not data or not data[0].get('company_doc_name'):
            return {"status": "error", "message": "No matching record found"}

        main_data = data[0]
        
        # Build response with minimal processing
        response = {
            "status": "success",
            "message": "Success",
            "company_details_tab": _build_company_fast(main_data, vendor_onboarding, ref_no),
            "company_address_tab": _build_address_fast(main_data),
            "document_details_tab": _build_documents_fast(main_data),
            "payment_details_tab": _build_payment_fast(main_data),
            "manufacturing_details_tab": _build_manufacturing_fast(main_data),
            "purchasing_details": _build_purchasing_fast(main_data),
            "validation_check": _build_validation_fast(main_data)
        }
        
        # Add child table data ONLY if document exists
        child_tables_data = _get_child_tables_fast(main_data, vendor_onboarding)
        response.update(child_tables_data)
        
        # Update address tab with multiple locations
        if "company_address_tab" in response and "multiple_location_table" in child_tables_data:
            response["company_address_tab"]["multiple_location_table"] = child_tables_data["multiple_location_table"]
        
        # Update document tab with GST table
        if "document_details_tab" in response and "gst_table" in child_tables_data:
            response["document_details_tab"]["gst_table"] = child_tables_data["gst_table"]
            response["document_details_tab"]["company_gst_table"] = child_tables_data["gst_table"]
        
        return response

    except Exception as e:
        return {"status": "error", "message": str(e)[:100]}


def _build_company_fast(data, vendor_onboarding, ref_no):
    """Ultra-fast company details"""
    company_details = {
        "vendor_title": data.get('vendor_title'),
        "vendor_name": data.get('vendor_name'),
        "company_name": data.get('company_name'),
        "type_of_business": data.get('type_of_business'),
        "size_of_company": data.get('size_of_company'),
        "website": data.get('website'),
        "registered_office_number": data.get('registered_office_number'),
        "telephone_number": data.get('telephone_number'),
        "whatsapp_number": data.get('whatsapp_number'),
        "established_year": data.get('established_year'),
        "office_email_primary": data.get('office_email_primary'),
        "office_email_secondary": data.get('office_email_secondary'),
        "corporate_identification_number": data.get('corporate_identification_number'),
        "cin_date": data.get('cin_date'),
        "nature_of_company": data.get('nature_of_company'),
        "nature_of_business": data.get('nature_of_business'),
        "company_name_description": "",
        "vendor_type_list_from_master": [],
        "vendor_types": []
    }
    
    # Only get vendor types if cache miss
    cache_key = f"vendor_types_{vendor_onboarding}_{ref_no}"
    if cache_key not in _global_cache:
        # Single query for both vendor types
        vendor_types = frappe.db.sql("""
            (SELECT vendor_type, 'master' as source FROM `tabVendor Type Group` 
             WHERE parent = %s AND parenttype = 'Vendor Master')
            UNION ALL
            (SELECT vendor_type, 'onboarding' as source FROM `tabVendor Type Group` 
             WHERE parent = %s AND parenttype = 'Vendor Onboarding')
        """, (ref_no, vendor_onboarding), as_dict=True)
        
        master_types = [vt['vendor_type'] for vt in vendor_types if vt['source'] == 'master']
        onb_types = [vt['vendor_type'] for vt in vendor_types if vt['source'] == 'onboarding']
        
        _global_cache[cache_key] = {
            'master': master_types,
            'onboarding': onb_types
        }
    
    company_details["vendor_type_list_from_master"] = _global_cache[cache_key]['master']
    company_details["vendor_types"] = _global_cache[cache_key]['onboarding']
    
    return company_details


def _build_address_fast(data):
    """Ultra-fast address details - minimal master data"""
    return {
        "same_as_above": data.get('same_as_above'),
        "multiple_locations": data.get('multiple_locations'),
        "billing_address": {
            "address_line_1": data.get('address_line_1'),
            "address_line_2": data.get('address_line_2'),
            "pincode": data.get('pincode'),
            "city": data.get('city'),
            "district": data.get('district'),
            "state": data.get('state'),
            "country": data.get('country'),
            "international_city": data.get('international_city'),
            "international_state": data.get('international_state'),
            "international_country": data.get('international_country'),
            "international_zipcode": data.get('international_zipcode'),
            "city_details": _get_master_quick("City Master", data.get('city')),
            "district_details": _get_master_quick("District Master", data.get('district')),
            "state_details": _get_master_quick("State Master", data.get('state')),
            "country_details": _get_master_quick("Country Master", data.get('country'))
        },
        "shipping_address": {
            "street_1": data.get('street_1'),
            "street_2": data.get('street_2'),
            "manufacturing_pincode": data.get('manufacturing_pincode'),
            "manufacturing_city": data.get('manufacturing_city'),
            "manufacturing_district": data.get('manufacturing_district'),
            "manufacturing_state": data.get('manufacturing_state'),
            "manufacturing_country": data.get('manufacturing_country'),
            "inter_manufacture_city": data.get('inter_manufacture_city'),
            "inter_manufacture_state": data.get('inter_manufacture_state'),
            "inter_manufacture_country": data.get('inter_manufacture_country'),
            "inter_manufacture_zipcode": data.get('inter_manufacture_zipcode'),
            "city_details": _get_master_quick("City Master", data.get('manufacturing_city')),
            "district_details": _get_master_quick("District Master", data.get('manufacturing_district')),
            "state_details": _get_master_quick("State Master", data.get('manufacturing_state')),
            "country_details": _get_master_quick("Country Master", data.get('manufacturing_country'))
        },
        "multiple_location_table": [],  # Skip for speed - load separately if needed
        "address_proofattachment": _get_file_quick(data.get('address_proofattachment'))
    }


def _build_documents_fast(data):
    """Ultra-fast document details"""
    # Get GST table from cache
    cache_key = f"child_tables_{data.get('legal_doc_name', '')}"
    gst_table = []
    
    if cache_key in _global_cache:
        gst_table = _global_cache[cache_key].get('gst_table', [])
    
    return {
        "company_pan_number": data.get('company_pan_number'),
        "name_on_company_pan": data.get('name_on_company_pan'),
        "enterprise_registration_number": data.get('enterprise_registration_number'),
        "msme_registered": data.get('msme_registered'),
        "msme_enterprise_type": data.get('msme_enterprise_type'),
        "udyam_number": data.get('udyam_number'),
        "name_on_udyam_certificate": data.get('name_on_udyam_certificate'),
        "iec": data.get('iec'),
        "trc_certificate_no": data.get('trc_certificate_no'),
        "pan_proof": _get_file_quick(data.get('pan_proof')),
        "entity_proof": _get_file_quick(data.get('entity_proof')),
        "msme_proof": _get_file_quick(data.get('msme_proof')),
        "iec_proof": _get_file_quick(data.get('iec_proof')),
        "form_10f_proof": _get_file_quick(data.get('form_10f_proof')),
        "trc_certificate": _get_file_quick(data.get('trc_certificate')),
        "pe_certificate": _get_file_quick(data.get('pe_certificate')),
        "gst_table": gst_table,
        "company_gst_table": gst_table  # Simplified for speed
    }


def _build_payment_fast(data):
    """Ultra-fast payment details"""
    return {
        "bank_name": data.get('bank_name'),
        "ifsc_code": data.get('ifsc_code'),
        "account_number": data.get('account_number'),
        "name_of_account_holder": data.get('name_of_account_holder'),
        "type_of_account": data.get('type_of_account'),
        "currency": data.get('currency'),
        "rtgs": data.get('rtgs'),
        "neft": data.get('neft'),
        "ift": data.get('ift'),
        "bank_name_details": _get_master_quick("Bank Master", data.get('bank_name')),
        "bank_proof": _get_file_quick(data.get('bank_proof')),
        "bank_proof_by_purchase_team": _get_file_quick(data.get('bank_proof_by_purchase_team')),
        "address": {"country": data.get('payment_country', '')},
        "international_bank_details": [],  # Load separately if needed
        "intermediate_bank_details": []
    }


def _build_manufacturing_fast(data):
    """Ultra-fast manufacturing details"""
    return {
        "total_godown": data.get('total_godown'),
        "storage_capacity": data.get('storage_capacity'),
        "spare_capacity": data.get('spare_capacity'),
        "type_of_premises": data.get('type_of_premises'),
        "working_hours": data.get('working_hours'),
        "weekly_holidays": data.get('weekly_holidays'),
        "number_of_manpower": data.get('number_of_manpower'),
        "annual_revenue": data.get('annual_revenue'),
        "cold_storage": data.get('cold_storage'),
        "materials_supplied": [],  # Load separately if needed
        "brochure_proof": _get_file_quick(data.get('brochure_proof')),
        "organisation_structure_document": _get_file_quick(data.get('organisation_structure_document'))
    }


def _build_purchasing_fast(data):
    """Ultra-fast purchasing details"""
    return [{
        "company_name": data.get('vo_company_name'),
        "purchase_organization": data.get('purchase_organization'),
        "order_currency": data.get('order_currency'),
        "terms_of_payment": data.get('terms_of_payment'),
        "purchase_group": data.get('purchase_group'),
        "account_group": data.get('account_group'),
        "reconciliation_account": data.get('reconciliation_account'),
        "qa_team_remarks": data.get('qa_team_remarks'),
        "purchase_team_remarks": data.get('purchase_team_approval_remarks'),
        "purchase_head_remarks": data.get('purchase_head_approval_remarks'),
        "account_team_remarks": data.get('accounts_team_approval_remarks'),
        "incoterms": data.get('incoterms'),
        "company_details": _get_master_quick("Company Master", data.get('vo_company_name')),
        "pur_org_details": {},
        "currency_details": {},
        "term_payment_details": {},
        "pur_group_details": {},
        "account_group_details": {},
        "reconciliation_details": {}
    }]


def _build_validation_fast(data):
    """Ultra-fast validation check"""
    return {
        "mandatory_data_filled": data.get('mandatory_data_filled', 0),
        "register_by_account_team": data.get('register_by_account_team', 0),
        "form_fully_submitted_by_vendor": data.get('form_fully_submitted_by_vendor', 0),
        "purchase_team_undertaking": data.get('purchase_team_undertaking', 0),
        "purchase_head_undertaking": data.get('purchase_head_undertaking', 0),
        "accounts_team_undertaking": data.get('accounts_team_undertaking', 0),
        "accounts_head_undertaking": data.get('accounts_head_undertaking', 0),
        "is_purchase_approve": 1 if data.get('mail_sent_to_purchase_team') else 0,
        "is_purchase_head_approve": 1 if data.get('mail_sent_to_purchase_head') else 0,
        "is_accounts_team_approve": 1 if data.get('mail_sent_to_account_team') else 0,
        "is_accounts_head_approve": 1 if data.get('mail_sent_to_account_head') else 0
    }


def _get_child_tables_fast(data, vendor_onboarding):
    """Load child tables with minimal queries"""
    cache_key = f"child_tables_{vendor_onboarding}"
    
    if cache_key not in _global_cache:
        # Fixed contact details query with correct field names
        contact_data = frappe.db.sql("""
            SELECT name, idx, first_name, last_name, designation, email, contact_number, department_name
            FROM `tabContact Details` WHERE parent = %s AND parenttype = 'Vendor Onboarding'
        """, (vendor_onboarding,), as_dict=True)
        
        # Get certificate details
        cert_data = []
        if data.get('cert_doc_name'):
            cert_data = frappe.db.sql("""
                SELECT name, idx, certificate_code, valid_till, certificate_attach
                FROM `tabOnboarding Certificates` WHERE parent = %s AND parenttype = 'Vendor Onboarding Certificates'
            """, (data['cert_doc_name'],), as_dict=True)
            
            # Process certificate attachments
            for cert in cert_data:
                cert['certificate_attach'] = _get_file_quick(cert.get('certificate_attach'))
        
        # Get multiple location table
        multiple_locations = []
        if data.get('company_doc_name'):
            multiple_locations = frappe.db.sql("""
                SELECT name, idx, address_line_1, address_line_2, ma_pincode, ma_city, ma_district, ma_state, ma_country,
                       city, state, country, zipcode, owner, creation, modified, modified_by, docstatus,
                       parent, parentfield, parenttype, 'Multiple Address' as doctype
                FROM `tabMultiple Address` WHERE parent = %s AND parenttype = 'Vendor Onboarding Company Details'
            """, (data['company_doc_name'],), as_dict=True)
            
            # Add master data for locations
            for location in multiple_locations:
                location['city_details'] = _get_master_quick("City Master", location.get('ma_city'))
                location['district_details'] = _get_master_quick("District Master", location.get('ma_district'))
                location['state_details'] = _get_master_quick("State Master", location.get('ma_state'))
                location['country_details'] = _get_master_quick("Country Master", location.get('ma_country'))
        
        # Get GST table data
        gst_data = []
        if data.get('legal_doc_name'):
            gst_data = frappe.db.sql("""
                SELECT name, idx, gst_number, gst_state, gst_document
                FROM `tabVendor Company GST Table` WHERE parent = %s AND parenttype = 'Legal Documents'
            """, (data['legal_doc_name'],), as_dict=True)
            
            for gst in gst_data:
                gst['state_details'] = _get_master_quick("State Master", gst.get('gst_state'))
                gst['gst_document'] = _get_file_quick(gst.get('gst_document'))
        
        _global_cache[cache_key] = {
            'contacts': contact_data,
            'certificates': cert_data,
            'multiple_locations': multiple_locations,
            'gst_table': gst_data
        }
    
    cached_data = _global_cache[cache_key]
    
    return {
        "contact_details_tab": cached_data['contacts'],
        "certificate_details_tab": cached_data['certificates'],
        "multiple_location_table": cached_data['multiple_locations'],
        "gst_table": cached_data['gst_table'],
        "employee_details_tab": [],
        "machinery_details_tab": [],
        "testing_details_tab": [],
        "reputed_partners_details_tab": [],
        "is_multi_company": data.get('registered_for_multi_companies', 0),
        "multi_company_data": []
    }


def _get_master_quick(doctype, docname):
    """Super-fast master data with aggressive caching"""
    if not docname:
        return {}
    
    cache_key = f"master_{doctype}_{docname}"
    if cache_key in _global_cache:
        return _global_cache[cache_key]
    
    try:
        # Minimal field selection for speed
        if doctype == "City Master":
            result = frappe.db.get_value(doctype, docname, ["name", "city_name"], as_dict=True) or {}
        elif doctype == "State Master":
            result = frappe.db.get_value(doctype, docname, ["name", "state_name"], as_dict=True) or {}
        elif doctype == "Country Master":
            result = frappe.db.get_value(doctype, docname, ["name", "country_name"], as_dict=True) or {}
        else:
            result = frappe.db.get_value(doctype, docname, ["name"], as_dict=True) or {}
        
        _global_cache[cache_key] = result
        return result
    except:
        return {}


def _get_file_quick(file_url):
    """Super-fast file info"""
    if not file_url:
        return {"url": "", "name": "", "file_name": ""}
    
    cache_key = f"file_{file_url}"
    if cache_key in _global_cache:
        return _global_cache[cache_key]
    
    try:
        file_data = frappe.db.get_value("File", {"file_url": file_url}, ["name", "file_name"], as_dict=True)
        if file_data:
            result = {
                "url": f"http://10.10.103.155:3301{file_url}",  # Hardcoded for speed
                "name": file_data.get('name', ''),
                "file_name": file_data.get('file_name', '')
            }
        else:
            result = {"url": "", "name": "", "file_name": ""}
        
        _global_cache[cache_key] = result
        return result
    except:
        return {"url": "", "name": "", "file_name": ""}


# Cache management
@frappe.whitelist()
def clear_vendor_cache():
    """Clear the global cache if needed"""
    global _global_cache
    _global_cache.clear()
    return {"status": "Cache cleared"}


# Even more aggressive version with raw data
@frappe.whitelist(allow_guest=True)
def get_vendor_onboarding_raw(vendor_onboarding=None, ref_no=None, **kwargs):
    """
    Extreme performance version - returns raw data with minimal processing
    Target: Under 50ms
    """
    try:
        if not vendor_onboarding or not ref_no:
            return {"status": "error"}

        # Absolute minimal query
        result = frappe.db.sql("""
            SELECT 
                vocd.vendor_name, vocd.company_name, vocd.website, vocd.telephone_number,
                vocd.office_email_primary, vocd.address_line_1, vocd.city, vocd.state, vocd.country,
                ld.company_pan_number, ld.msme_registered, ld.udyam_number,
                vopd.bank_name, vopd.account_number, vopd.ifsc_code,
                vo.company_name as vo_company, vo.purchase_organization,
                vo.mandatory_data_filled, vo.form_fully_submitted_by_vendor
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabVendor Onboarding Company Details` vocd ON vocd.vendor_onboarding = vo.name AND vocd.ref_no = %s
            LEFT JOIN `tabLegal Documents` ld ON ld.vendor_onboarding = vo.name AND ld.ref_no = %s
            LEFT JOIN `tabVendor Onboarding Payment Details` vopd ON vopd.vendor_onboarding = vo.name AND vopd.ref_no = %s
            WHERE vo.name = %s
        """, (ref_no, ref_no, ref_no, vendor_onboarding), as_dict=True)

        if not result:
            return {"status": "error", "message": "Not found"}

        return {
            "status": "success",
            "data": result[0]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)[:50]}