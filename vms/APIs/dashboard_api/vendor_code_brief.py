import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_comp_ven_code(v_id, company):
    """
    API to fetch Company Vendor Code doctype data based on vendor master ID and company name
    
    Parameters:
    - v_id: Vendor Master document name (e.g., "V-25000001")
    - company: Company name to filter by
    
    Returns:
    - All fields from Company Vendor Code doctype
    - Related vendor and company information
    """
    
    try:
        # Validate required parameters
        if not v_id or not company:
            return {
                'success': False,
                'error': 'Both v_id (vendor master ID) and company parameters are required'
            }
        
        # Verify vendor master exists
        if not frappe.db.exists('Vendor Master', v_id):
            return {
                'success': False,
                'error': f'Vendor Master with ID "{v_id}" does not exist'
            }
        
        # Find Company Vendor Code records matching the criteria
        # The logic: Find records where vendor_master = v_id AND company_name = company
        company_vendor_codes_query = """
        SELECT cvc.*
        FROM `tabCompany Vendor Code` cvc
        WHERE cvc.vendor_ref_no = %(vendor_id)s 
        AND cvc.company_name = %(company_name)s
        """
        
        company_vendor_codes = frappe.db.sql(
            company_vendor_codes_query, 
            {
                'vendor_id': v_id,
                'company_name': company
            }, 
            as_dict=True
        )
        
        if not company_vendor_codes:
            return {
                'success': False,
                'error': f'No Company Vendor Code found for Vendor "{v_id}" and Company "{company}"'
            }
        
        # Enhance the data with related information
        enriched_data = []
        
        for record in company_vendor_codes:
            # Get related vendor master information
            vendor_info = frappe.db.get_value(
                'Vendor Master', 
                record['vendor_ref_no'], 
                ['vendor_name', 'office_email_primary', 'mobile_number', 'country'],
                as_dict=True
            )
            
            # Get related company master information  
            company_info = frappe.db.get_value(
                'Company Master',
                record['company_name'],
                ['company_name', 'company_code', 'sap_client_code'],
                as_dict=True
            )
            
            # Get state information if available
            state_info = None
            if record.get('state'):
                state_info = frappe.db.get_value(
                    'State Master',
                    record['state'],
                    ['state_name', 'state_code'],
                    as_dict=True
                )
            
            # Get vendor code table data - this is the key addition
            vendor_code_table_data = []
            if record.get('name'):
                vendor_codes_query = """
                SELECT vc.*
                FROM `tabVendor Code` vc
                WHERE vc.parent = %(company_vendor_code_id)s
                ORDER BY vc.idx
                """
                vendor_codes = frappe.db.sql(
                    vendor_codes_query, 
                    {'company_vendor_code_id': record['name']}, 
                    as_dict=True
                )
                vendor_code_table_data = vendor_codes
            
            # Combine all information
            enriched_record = {
                'company_vendor_code_data': record,
                'vendor_info': vendor_info,
                'company_info': company_info,
                'state_info': state_info,
                'vendor_code_table': vendor_code_table_data,  # New table data
                'metadata': {
                    'record_found': True,
                    'vendor_id_searched': v_id,
                    'company_searched': company,
                    'created_on': record.get('creation'),
                    'modified_on': record.get('modified'),
                    'created_by': record.get('owner'),
                    'modified_by': record.get('modified_by'),
                    'total_vendor_codes': len(vendor_code_table_data)
                }
            }
            
            enriched_data.append(enriched_record)
        
        return {
            'success': True,
            'data': {
                'company_vendor_codes': enriched_data,
                'total_records': len(enriched_data),
                'search_criteria': {
                    'vendor_master_id': v_id,
                    'company_name': company
                }
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_comp_ven_code API: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_vendor_company_codes_all(v_id):
    """
    API to fetch all Company Vendor Code records for a specific vendor across all companies
    
    Parameters:
    - v_id: Vendor Master document name
    
    Returns:
    - All Company Vendor Code records for the vendor
    """
    
    try:
        if not v_id:
            return {
                'success': False,
                'error': 'Vendor Master ID (v_id) is required'
            }
        
        # Verify vendor master exists
        if not frappe.db.exists('Vendor Master', v_id):
            return {
                'success': False,
                'error': f'Vendor Master with ID "{v_id}" does not exist'
            }
        
        # Get all Company Vendor Code records for this vendor
        all_codes_query = """
        SELECT cvc.*
        FROM `tabCompany Vendor Code` cvc
        WHERE cvc.vendor_ref_no = %(vendor_id)s
        ORDER BY cvc.company_name, cvc.creation DESC
        """
        
        all_codes = frappe.db.sql(all_codes_query, {'vendor_id': v_id}, as_dict=True)
        
        if not all_codes:
            return {
                'success': True,
                'data': {
                    'company_vendor_codes': [],
                    'total_records': 0,
                    'message': f'No Company Vendor Codes found for Vendor "{v_id}"'
                }
            }
        
        # Enhance with related data
        enriched_data = []
        companies_involved = set()
        
        for record in all_codes:
            # Get vendor info (same for all records)
            vendor_info = frappe.db.get_value(
                'Vendor Master', 
                record['vendor_ref_no'], 
                ['vendor_name', 'office_email_primary', 'mobile_number'],
                as_dict=True
            )
            
            # Get company info
            company_info = frappe.db.get_value(
                'Company Master',
                record['company_name'],
                ['company_name', 'company_code'],
                as_dict=True
            )
            
            # Track companies involved
            if company_info:
                companies_involved.add(company_info['company_name'])
            
            # Get state info if available
            state_info = None
            if record.get('state'):
                state_info = frappe.db.get_value(
                    'State Master',
                    record['state'],
                    ['state_name', 'state_code'],
                    as_dict=True
                )
            
            # Get vendor code table data
            vendor_code_table_data = []
            if record.get('name'):
                vendor_codes_query = """
                SELECT vc.*
                FROM `tabVendor Code` vc
                WHERE vc.parent = %(company_vendor_code_id)s
                ORDER BY vc.idx
                """
                vendor_codes = frappe.db.sql(
                    vendor_codes_query, 
                    {'company_vendor_code_id': record['name']}, 
                    as_dict=True
                )
                vendor_code_table_data = vendor_codes
            
            enriched_record = {
                'company_vendor_code_data': record,
                'vendor_info': vendor_info,
                'company_info': company_info,
                'state_info': state_info,
                'vendor_code_table': vendor_code_table_data
            }
            
            enriched_data.append(enriched_record)
        
        return {
            'success': True,
            'data': {
                'company_vendor_codes': enriched_data,
                'total_records': len(enriched_data),
                'companies_involved': list(companies_involved),
                'total_companies': len(companies_involved),
                'vendor_id': v_id
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_company_codes_all API: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_company_all_vendor_codes(company):
    """
    API to fetch all Company Vendor Code records for a specific company across all vendors
    
    Parameters:
    - company: Company name
    
    Returns:
    - All Company Vendor Code records for the company with pagination support
    """
    
    try:
        if not company:
            return {
                'success': False,
                'error': 'Company name is required'
            }
        
        # Get all Company Vendor Code records for this company
        company_codes_query = """
        SELECT cvc.*
        FROM `tabCompany Vendor Code` cvc
        WHERE cvc.company_name = %(company_name)s
        ORDER BY cvc.vendor_ref_no, cvc.creation DESC
        """
        
        company_codes = frappe.db.sql(company_codes_query, {'company_name': company}, as_dict=True)
        
        if not company_codes:
            return {
                'success': True,
                'data': {
                    'company_vendor_codes': [],
                    'total_records': 0,
                    'message': f'No Company Vendor Codes found for Company "{company}"'
                }
            }
        
        # Enhance with related data
        enriched_data = []
        vendors_involved = set()
        
        for record in company_codes:
            # Get vendor info
            vendor_info = frappe.db.get_value(
                'Vendor Master', 
                record['vendor_ref_no'], 
                ['vendor_name', 'office_email_primary', 'mobile_number', 'status'],
                as_dict=True
            )
            
            # Track vendors involved
            if vendor_info:
                vendors_involved.add(record['vendor_ref_no'])
            
            # Get company info (same for all records)
            company_info = frappe.db.get_value(
                'Company Master',
                record['company_name'],
                ['company_name', 'company_code'],
                as_dict=True
            )
            
            # Get state info if available
            state_info = None
            if record.get('state'):
                state_info = frappe.db.get_value(
                    'State Master',
                    record['state'],
                    ['state_name', 'state_code'],
                    as_dict=True
                )
            
            # Get vendor code table data
            vendor_code_table_data = []
            if record.get('name'):
                vendor_codes_query = """
                SELECT vc.*
                FROM `tabVendor Code` vc
                WHERE vc.parent = %(company_vendor_code_id)s
                ORDER BY vc.idx
                """
                vendor_codes = frappe.db.sql(
                    vendor_codes_query, 
                    {'company_vendor_code_id': record['name']}, 
                    as_dict=True
                )
                vendor_code_table_data = vendor_codes
            
            enriched_record = {
                'company_vendor_code_data': record,
                'vendor_info': vendor_info,
                'company_info': company_info,
                'state_info': state_info,
                'vendor_code_table': vendor_code_table_data
            }
            
            enriched_data.append(enriched_record)
        
        return {
            'success': True,
            'data': {
                'company_vendor_codes': enriched_data,
                'total_records': len(enriched_data),
                'vendors_involved': list(vendors_involved),
                'total_vendors': len(vendors_involved),
                'company_name': company
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_company_all_vendor_codes API: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }