# import frappe
# from frappe import _
# import math

# @frappe.whitelist(allow_guest = True)
# def get_vendors_with_pagination(
#     page=1, 
#     page_size=20, 
#     search_field=None, 
#     search_param=None, 
#     company_name=None
# ):
#     """
#     API to fetch vendor masters with pagination, search filters and advanced analytics
    
#     Parameters:
#     - page: Current page number (default: 1)
#     - page_size: Number of records per page (default: 20) 
#     - search_field: Field to search in (e.g., 'vendor_name', 'office_email_primary')
#     - search_param: Search value
#     - company_name: Filter by specific company name from multiple_company_data
    
#     Returns:
#     - vendors: List of vendor data with all fields
#     - pagination: Pagination metadata
#     - analytics: Vendor counts and analytics
#     - company_analytics: Company-wise vendor counts
#     """
    
#     try:
#         # Validate pagination parameters
#         page = max(int(page), 1)
#         page_size = max(min(int(page_size), 100), 1)  # Max 100 records per page
        
#         # Build base query
#         conditions = []
#         values = {}
        
#         # Search filter logic
#         if search_field and search_param:
#             # Validate search field exists in Vendor Master doctype
#             valid_search_fields = [
#                 'vendor_name', 'office_email_primary', 'office_email_secondary', 
#                 'mobile_number', 'search_term', 'country', 'first_name', 'last_name'
#             ]
            
#             if search_field in valid_search_fields:
#                 conditions.append(f"vm.{search_field} LIKE %(search_param)s")
#                 values['search_param'] = f"%{search_param}%"
        
#         # Company filter from multiple_company_data table
#         company_join = ""
#         if company_name:
#             company_join = """
#             INNER JOIN `tabMultiple Company Data` mcd 
#             ON vm.name = mcd.parent 
#             INNER JOIN `tabCompany Master` cm 
#             ON mcd.company_name = cm.name
#             """
#             conditions.append("cm.company_name = %(company_name)s")
#             values['company_name'] = company_name
        
#         # Build WHERE clause
#         where_clause = ""
#         if conditions:
#             where_clause = "WHERE " + " AND ".join(conditions)
        
#         # Calculate total count for pagination
#         count_query = f"""
#         SELECT COUNT(DISTINCT vm.name) as total_count
#         FROM `tabVendor Master` vm
#         {company_join}
#         {where_clause}
#         """
        
#         total_count = frappe.db.sql(count_query, values, as_dict=True)[0]['total_count']
#         total_pages = math.ceil(total_count / page_size)
        
#         # Calculate offset
#         offset = (page - 1) * page_size
        
#         # Main query to fetch all vendor data fields
#         main_query = f"""
#         SELECT DISTINCT vm.*
#         FROM `tabVendor Master` vm
#         {company_join}
#         {where_clause}
#         ORDER BY vm.modified DESC
#         LIMIT %(page_size)s OFFSET %(offset)s
#         """
        
#         values.update({
#             'page_size': page_size,
#             'offset': offset
#         })
        
#         vendors = frappe.db.sql(main_query, values, as_dict=True)
        
#         # Enrich vendor data with related information
#         enriched_vendors = []
#         for vendor in vendors:
#             # Get multiple company data
#             vendor['multiple_company_data'] = frappe.db.sql("""
#                 SELECT mcd.*, cm.company_name as company_display_name
#                 FROM `tabMultiple Company Data` mcd
#                 LEFT JOIN `tabCompany Master` cm ON mcd.company_name = cm.name
#                 WHERE mcd.parent = %(vendor_name)s
#             """, {'vendor_name': vendor['name']}, as_dict=True)
            
#             # Get vendor onboarding records
#             vendor['vendor_onb_records'] = frappe.db.sql("""
#                 SELECT vor.*
#                 FROM `tabVendor Onboarding Records` vor
#                 WHERE vor.parent = %(vendor_name)s
#             """, {'vendor_name': vendor['name']}, as_dict=True)
            
#             # Get vendor types
#             vendor['vendor_types'] = frappe.db.sql("""
#                 SELECT vt.*
#                 FROM `tabVendor Type for Account` vt
#                 WHERE vt.parent = %(vendor_name)s
#             """, {'vendor_name': vendor['name']}, as_dict=True)
            
#             enriched_vendors.append(vendor)
        
#         # Calculate analytics
#         analytics = calculate_vendor_analytics()
        
#         # Calculate company-wise analytics
#         company_analytics = calculate_company_wise_analytics(company_name)
        
#         # Build pagination metadata
#         pagination = {
#             'current_page': page,
#             'page_size': page_size,
#             'total_records': total_count,
#             'total_pages': total_pages,
#             'has_next': page < total_pages,
#             'has_previous': page > 1,
#             'next_page': page + 1 if page < total_pages else None,
#             'previous_page': page - 1 if page > 1 else None
#         }
        
#         return {
#             'success': True,
#             'data': {
#                 'vendors': enriched_vendors,
#                 'pagination': pagination,
#                 'analytics': analytics,
#                 'company_analytics': company_analytics
#             }
#         }
        
#     except Exception as e:
#         frappe.log_error(f"Error in get_vendors_with_pagination: {str(e)}")
#         return {
#             'success': False,
#             'error': str(e)
#         }


# def calculate_vendor_analytics():
#     """Calculate comprehensive vendor analytics"""
    
#     # Total vendor count
#     total_vendors = frappe.db.count('Vendor Master')
    
#     # Imported vendors (via_data_import = 1)
#     imported_vendors = frappe.db.count('Vendor Master', {'via_data_import': 1})
    
#     # Registered via VMS (via_data_import = 0)
#     vms_registered = frappe.db.count('Vendor Master', {'via_data_import': 0})
    
#     # Get vendors with approved onboarding and categorize by registration team
#     approved_by_accounts = 0
#     approved_by_purchase = 0
    
#     # Query to get vendors with approved onboarding records
#     approved_vendors_query = """
#     SELECT DISTINCT 
#         vm.name,
#         vor.vendor_onboarding_no,
#         vo.register_by_account_team
#     FROM `tabVendor Master` vm
#     INNER JOIN `tabVendor Onboarding Records` vor ON vm.name = vor.parent
#     INNER JOIN `tabVendor Onboarding` vo ON vor.vendor_onboarding_no = vo.name
#     WHERE vor.onboarding_form_status = 'Approved'
#     """
    
#     approved_vendors = frappe.db.sql(approved_vendors_query, as_dict=True)
    
#     for vendor in approved_vendors:
#         if vendor.get('register_by_account_team') == 1:
#             approved_by_accounts += 1
#         else:
#             approved_by_purchase += 1
    
#     return {
#         'total_vendors': total_vendors,
#         'imported_vendors': imported_vendors,
#         'vms_registered': vms_registered,
#         'approved_by_accounts_team': approved_by_accounts,
#         'approved_by_purchase_team': approved_by_purchase,
#         'approval_breakdown': {
#             'accounts_team': approved_by_accounts,
#             'purchase_team': approved_by_purchase,
#             'total_approved': approved_by_accounts + approved_by_purchase
#         }
#     }


# def calculate_company_wise_analytics(filter_company=None):
#     """Calculate vendor counts per company"""
    
#     company_filter = ""
#     if filter_company:
#         company_filter = "WHERE cm.company_name = %(filter_company)s"
    
#     query = f"""
#     SELECT 
#         cm.company_name,
#         COUNT(DISTINCT mcd.parent) as vendor_count
#     FROM `tabCompany Master` cm
#     LEFT JOIN `tabMultiple Company Data` mcd ON cm.name = mcd.company_name
#     {company_filter}
#     GROUP BY cm.company_name
#     ORDER BY vendor_count DESC
#     """
    
#     values = {}
#     if filter_company:
#         values['filter_company'] = filter_company
    
#     company_stats = frappe.db.sql(query, values, as_dict=True)
    
#     return {
#         'company_wise_counts': company_stats,
#         'total_companies': len(company_stats),
#         'filtered_company': filter_company
#     }


# @frappe.whitelist() 
# def get_vendor_search_fields():
#     """
#     Returns available fields for searching vendors
#     """
#     return {
#         'success': True,
#         'data': {
#             'search_fields': [
#                 {'value': 'vendor_name', 'label': 'Vendor Name'},
#                 {'value': 'office_email_primary', 'label': 'Primary Email'},
#                 {'value': 'office_email_secondary', 'label': 'Secondary Email'},
#                 {'value': 'mobile_number', 'label': 'Mobile Number'},
#                 {'value': 'search_term', 'label': 'Search Term'},
#                 {'value': 'country', 'label': 'Country'},
#                 {'value': 'first_name', 'label': 'First Name'},
#                 {'value': 'last_name', 'label': 'Last Name'}
#             ]
#         }
#     }


# @frappe.whitelist()
# def get_company_list():
#     """
#     Returns list of all companies for filtering
#     """
#     try:
#         companies = frappe.db.sql("""
#             SELECT *
#             FROM `tabCompany Master`
#             ORDER BY company_name
#         """, as_dict=True)
        
#         return {
#             'success': True,
#             'data': {
#                 'companies': companies
#             }
#         }
        
#     except Exception as e:
#         return {
#             'success': False,
#             'error': str(e)
#         }


# @frappe.whitelist()
# def get_vendor_detail(vendor_id):
#     """
#     Get detailed information for a specific vendor
#     """
#     try:
#         # Get basic vendor info
#         vendor = frappe.get_doc('Vendor Master', vendor_id)
        
#         # Get onboarding records with detailed status
#         onboarding_records = []
#         for record in vendor.vendor_onb_records:
#             onb_doc = frappe.get_doc('Vendor Onboarding', record.vendor_onboarding_no)
            
#             # Combine record data with onboarding doc data
#             combined_record = record.as_dict()
#             combined_record.update({
#                 'register_by_account_team': onb_doc.register_by_account_team,
#                 'onboarding_doc_data': onb_doc.as_dict()  # Include all onboarding fields
#             })
#             onboarding_records.append(combined_record)
        
#         return {
#             'success': True,
#             'data': {
#                 'vendor': vendor.as_dict(),
#                 'onboarding_records': onboarding_records
#             }
#         }
        
#     except Exception as e:
#         return {
#             'success': False,
#             'error': str(e)
#         }

# import frappe
# from frappe import _
# import math

import frappe
from frappe import _
import math
from frappe.utils import cstr, cint







@frappe.whitelist(allow_guest = True)
def get_vendors_with_pagination(
    page=1, 
    page_size=20, 
    search_filters=None,
    company_name=None,
    onboarding_form=None,
    via_data_import=None
):
    """
    API to fetch vendor masters with pagination, multiple search filters and advanced analytics
    
    Parameters:
    - page: Current page number (default: 1)
    - page_size: Number of records per page (default: 20) 
    - search_filters: JSON string with multiple search fields and parameters
      Example: '{"vendor_name": ["ABC", "XYZ"], "office_email_primary": ["@gmail.com", "@yahoo.com"]}'
    - company_name: Filter by specific company name from multiple_company_data
    - onboarding_form: Filter by onboarding form status in vendor_onb_records
    - via_data_import: Filter by via_data_import field (1/true for imported vendors)
    
    Returns:
    - vendors: List of vendor data with all fields
    - pagination: Pagination metadata
    - analytics: Vendor counts and analytics
    - company_analytics: Company-wise vendor counts
    """
    
    try:
        import json
        
        # Validate pagination parameters
        page = max(int(page), 1)
        page_size = max(min(int(page_size), 100), 1)  # Max 100 records per page
        
        # Build base query
        conditions = []
        values = {}
        
        # Parse search filters
        if search_filters:
            try:
                if isinstance(search_filters, str):
                    search_filters = json.loads(search_filters)
                
                # Validate search fields exist in Vendor Master doctype
                valid_search_fields = [
                    'vendor_name', 'office_email_primary', 'office_email_secondary', 
                    'mobile_number', 'search_term', 'country', 'first_name', 'last_name',
                    'registered_by', 'status', 'onboarding_form_status', 'remarks'
                ]
                
                search_conditions = []
                param_counter = 0
                
                for field, params in search_filters.items():
                    if field in valid_search_fields and params:
                        # Ensure params is a list
                        if not isinstance(params, list):
                            params = [params]
                        
                        field_conditions = []
                        for param in params:
                            if param and str(param).strip():  # Skip empty params
                                param_key = f"search_param_{param_counter}"
                                field_conditions.append(f"vm.{field} LIKE %({param_key})s")
                                values[param_key] = f"%{str(param).strip()}%"
                                param_counter += 1
                        
                        if field_conditions:
                            # Use OR between parameters for the same field
                            search_conditions.append(f"({' OR '.join(field_conditions)})")
                
                if search_conditions:
                    # Use AND between different fields
                    conditions.append(f"({' AND '.join(search_conditions)})")
                    
            except (json.JSONDecodeError, TypeError) as e:
                frappe.log_error(f"Invalid search_filters format: {str(e)}")
        
        # Company filter from multiple_company_data table
        company_join = ""
        if company_name:
            company_join = """
            INNER JOIN `tabMultiple Company Data` mcd 
            ON vm.name = mcd.parent 
            INNER JOIN `tabCompany Master` cm 
            ON mcd.company_name = cm.name
            """
            conditions.append("cm.company_name LIKE %(company_name)s")
            values['company_name'] = f"%{company_name}%"
        
        # Onboarding form filter from vendor_onb_records table
        onboarding_join = ""
        if onboarding_form:
            onboarding_join = """
            INNER JOIN `tabVendor Onboarding Records` vor 
            ON vm.name = vor.parent
            """
            conditions.append("vor.onboarding_form_status = %(onboarding_form)s")
            values['onboarding_form'] = onboarding_form
        
        # Via data import filter
        if via_data_import is not None:
            # Handle various truthy values (1, "1", True, "true", etc.)
            if str(via_data_import).lower() in ['1', 'true', 'yes']:
                conditions.append("vm.via_data_import = 1")
            else:
                conditions.append("(vm.via_data_import = 0 OR vm.via_data_import IS NULL)")
        
        # Combine all joins
        all_joins = f"{company_join} {onboarding_join}"
        
        # Build WHERE clause
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Calculate total count for pagination
        count_query = f"""
        SELECT COUNT(DISTINCT vm.name) as total_count
        FROM `tabVendor Master` vm
        {all_joins}
        {where_clause}
        """
        
        total_count = frappe.db.sql(count_query, values, as_dict=True)[0]['total_count']
        total_pages = math.ceil(total_count / page_size)
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Main query to fetch all vendor data fields
        main_query = f"""
        SELECT DISTINCT vm.*
        FROM `tabVendor Master` vm
        {all_joins}
        {where_clause}
        ORDER BY vm.modified DESC
        LIMIT %(page_size)s OFFSET %(offset)s
        """
        
        values.update({
            'page_size': page_size,
            'offset': offset
        })
        
        vendors = frappe.db.sql(main_query, values, as_dict=True)
        
        # Enrich vendor data with related information
        # Get child table information once for efficiency
        bank_meta = frappe.get_meta("Vendor Bank Details")
        bank_child_tables = {}
        for field in bank_meta.fields:
            if field.fieldtype == "Table":
                bank_child_tables[field.fieldname] = field.options

                

        enriched_vendors = []
        for vendor in vendors:
            # Get multiple company data
            # vendor['multiple_company_data'] = frappe.db.sql("""
            #     SELECT mcd.*, cm.company_name as company_display_name
            #     FROM `tabMultiple Company Data` mcd
            #     LEFT JOIN `tabCompany Master` cm ON mcd.company_name = cm.name
            #     WHERE mcd.parent = %(vendor_name)s
            # """, {'vendor_name': vendor['name']}, as_dict=True)

            # Get multiple company data with applied company filter
            company_data_conditions = ["mcd.parent = %(vendor_name)s"]
            company_data_values = {'vendor_name': vendor['name']}

            # Apply company_name filter
            if company_name:
                company_data_conditions.append("cm.company_name LIKE %(company_name_filter)s")
                company_data_values['company_name_filter'] = f"%{company_name}%"

            company_data_where = " AND ".join(company_data_conditions)

            vendor['multiple_company_data'] = frappe.db.sql(f"""
                SELECT mcd.*, cm.company_name as company_display_name
                FROM `tabMultiple Company Data` mcd
                LEFT JOIN `tabCompany Master` cm ON mcd.company_name = cm.name
                WHERE {company_data_where}
            """, company_data_values, as_dict=True)
            
            # Get vendor onboarding records
            # vendor['vendor_onb_records'] = frappe.db.sql("""
            #     SELECT vor.*
            #     FROM `tabVendor Onboarding Records` vor
            #     WHERE vor.parent = %(vendor_name)s
            # """, {'vendor_name': vendor['name']}, as_dict=True)

            # Get vendor onboarding records with applied filters
            vendor_onb_conditions = ["vor.parent = %(vendor_name)s"]
            vendor_onb_values = {'vendor_name': vendor['name']}

            # Always join with Vendor Onboarding to fetch company_name
            vendor_onb_join = """
                LEFT JOIN `tabVendor Onboarding` vo 
                ON vor.vendor_onboarding_no = vo.name
            """

            # Apply onboarding_form filter (check both status fields using OR)
            if onboarding_form:
                vendor_onb_conditions.append(
                    "(vor.onboarding_status = %(onboarding_form_filter)s OR vor.onboarding_form_status = %(onboarding_form_filter)s)"
                )
                vendor_onb_values['onboarding_form_filter'] = onboarding_form

            # Apply company_name filter
            if company_name:
                vendor_onb_conditions.append("vo.company_name LIKE %(company_name_filter)s")
                vendor_onb_values['company_name_filter'] = f"%{company_name}%"

            # Build the complete query
            vendor_onb_where = " AND ".join(vendor_onb_conditions)

            vendor['vendor_onb_records'] = frappe.db.sql(f"""
                SELECT vor.*, vo.company_name as onboarding_company_name
                FROM `tabVendor Onboarding Records` vor
                {vendor_onb_join}
                WHERE {vendor_onb_where}
            """, vendor_onb_values, as_dict=True)
            
            # Get vendor types.Vendor Type Group
            vendor['vendor_types'] = frappe.db.sql("""
                SELECT vt.*
                FROM `tabVendor Type Group` vt
                WHERE vt.parent = %(vendor_name)s
            """, {'vendor_name': vendor['name']}, as_dict=True)
            
            # Get bank details with child tables
            bank_details = frappe.db.sql("""
                SELECT bd.*
                FROM `tabVendor Bank Details` bd
                INNER JOIN `tabVendor Master` vm ON vm.bank_details = bd.name
                WHERE vm.name = %(vendor_name)s
                LIMIT 1
            """, {'vendor_name': vendor['name']}, as_dict=True)


            # vendor['vendor_company_details'] = frappe.db.sql("""
            #     SELECT ivc.*, cm.name as meril_company_name
            #     FROM `tabImported Vendor Company` ivc
            #     LEFT JOIN `tabCompany Master` cm ON ivc.meril_company_name = cm.name
            #     WHERE ivc.parent = %(vendor_name)s
            # """, {'vendor_name': vendor['name']}, as_dict=True)
            # Get vendor company details with applied company filter
            vendor_company_conditions = ["ivc.parent = %(vendor_name)s"]
            vendor_company_values = {'vendor_name': vendor['name']}

            # Apply company_name filter
            if company_name:
                vendor_company_conditions.append("cm.company_name LIKE %(company_name_filter)s")
                vendor_company_values['company_name_filter'] = f"%{company_name}%"

            vendor_company_where = " AND ".join(vendor_company_conditions)

            vendor['vendor_company_details'] = frappe.db.sql(f"""
                SELECT ivc.*, cm.company_name as meril_company_name
                FROM `tabImported Vendor Company` ivc
                LEFT JOIN `tabCompany Master` cm ON ivc.meril_company_name = cm.name
                WHERE {vendor_company_where}
            """, vendor_company_values, as_dict=True)

            
            if bank_details:
                bank_doc = bank_details[0]
                bank_doc_name = bank_doc['name']
                
                # Fetch data for each child table
                for table_fieldname, child_doctype in bank_child_tables.items():
                    bank_doc[table_fieldname] = frappe.db.sql("""
                        SELECT *
                        FROM `tab{child_doctype}`
                        WHERE parent = %(parent)s
                        ORDER BY idx
                    """.format(child_doctype=child_doctype), 
                    {'parent': bank_doc_name}, as_dict=True)
                
                vendor['bank_details'] = bank_doc
            else:
                vendor['bank_details'] = None
            
            enriched_vendors.append(vendor)
        
        # Calculate analytics
        analytics = calculate_vendor_analytics()
        
        # Calculate company-wise analytics (no filtering - always show all companies)
        company_analytics = calculate_company_wise_analytics()
        
        # Calculate search result analytics
        search_analytics = calculate_search_analytics(search_filters, company_name, values, all_joins, where_clause, onboarding_form, via_data_import)
        
        # Build pagination metadata
        pagination = {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'previous_page': page - 1 if page > 1 else None
        }
        
        return {
            'success': True,
            'data': {
                'vendors': enriched_vendors,
                'pagination': pagination,
                'analytics': analytics,
                'company_analytics': company_analytics,
                'search_analytics': search_analytics,
                'applied_filters': {
                    'search_filters': search_filters,
                    'company_name': company_name,
                    'onboarding_form': onboarding_form,
                    'via_data_import': via_data_import
                }
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendors_with_pagination: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def calculate_search_analytics(search_filters, company_name, query_values, all_joins, where_clause, onboarding_form=None, via_data_import=None):
    """Calculate detailed analytics for search results"""
    
    try:
        # If no filters applied, return basic stats
        if not search_filters and not company_name and not onboarding_form and via_data_import is None:
            return {
                'search_applied': False,
                'message': 'No search filters applied - showing all vendors'
            }
        
        # Get total count with current filters (already calculated in main function)
        # We'll recalculate to get detailed breakdown
        
        # Count by registration type with current filters
        imported_query = f"""
        SELECT COUNT(DISTINCT vm.name) as count
        FROM `tabVendor Master` vm
        {all_joins}
        {where_clause + ' AND' if where_clause else 'WHERE'} vm.via_data_import = 1
        """
        
        vms_registered_query = f"""
        SELECT COUNT(DISTINCT vm.name) as count
        FROM `tabVendor Master` vm
        {all_joins}
        {where_clause + ' AND' if where_clause else 'WHERE'} (vm.via_data_import = 0 OR vm.via_data_import IS NULL)
        """
        
        # Count by approval status with current filters
        # Need to handle case where onboarding join might already be present
        onboarding_join_for_approval = ""
        if "tabVendor Onboarding Records" not in all_joins:
            onboarding_join_for_approval = """
            INNER JOIN `tabVendor Onboarding Records` vor ON vm.name = vor.parent
            INNER JOIN `tabVendor Onboarding` vo ON vor.vendor_onboarding_no = vo.name
            """
        else:
            onboarding_join_for_approval = """
            INNER JOIN `tabVendor Onboarding` vo ON vor.vendor_onboarding_no = vo.name
            """
        
        approved_by_accounts_query = f"""
        SELECT COUNT(DISTINCT vm.name) as count
        FROM `tabVendor Master` vm
        {all_joins}
        {onboarding_join_for_approval}
        {where_clause + ' AND' if where_clause else 'WHERE'} vor.onboarding_form_status = 'Approved' AND vo.register_by_account_team = 1
        """
        
        approved_by_purchase_query = f"""
        SELECT COUNT(DISTINCT vm.name) as count
        FROM `tabVendor Master` vm
        {all_joins}
        {onboarding_join_for_approval}
        {where_clause + ' AND' if where_clause else 'WHERE'} vor.onboarding_form_status = 'Approved' AND vo.register_by_account_team = 0
        """
        
        # Execute queries with error handling
        try:
            imported_count = frappe.db.sql(imported_query, query_values, as_dict=True)[0]['count']
        except Exception as e:
            frappe.log_error(f"Error in imported_count query: {str(e)}")
            imported_count = 0
            
        try:
            vms_registered_count = frappe.db.sql(vms_registered_query, query_values, as_dict=True)[0]['count']
        except Exception as e:
            frappe.log_error(f"Error in vms_registered_count query: {str(e)}")
            vms_registered_count = 0
            
        try:
            approved_accounts_count = frappe.db.sql(approved_by_accounts_query, query_values, as_dict=True)[0]['count']
        except Exception as e:
            frappe.log_error(f"Error in approved_accounts_count query: {str(e)}")
            approved_accounts_count = 0
            
        try:
            approved_purchase_count = frappe.db.sql(approved_by_purchase_query, query_values, as_dict=True)[0]['count']
        except Exception as e:
            frappe.log_error(f"Error in approved_purchase_count query: {str(e)}")
            approved_purchase_count = 0
        
        # Count by status with current filters
        status_breakdown = {}
        if where_clause or all_joins:
            try:
                status_query = f"""
                SELECT 
                    COALESCE(vm.status, 'Not Set') as status_value,
                    COUNT(DISTINCT vm.name) as count
                FROM `tabVendor Master` vm
                {all_joins}
                {where_clause if where_clause else ''}
                GROUP BY vm.status
                ORDER BY count DESC
                """
                status_results = frappe.db.sql(status_query, query_values, as_dict=True)
                status_breakdown = {item['status_value']: item['count'] for item in status_results}
            except Exception as e:
                frappe.log_error(f"Error in status_breakdown query: {str(e)}")
                status_breakdown = {}
        
        # Count by onboarding status with current filters
        onboarding_status_breakdown = {}
        if where_clause or all_joins:
            try:
                onboarding_status_query = f"""
                SELECT 
                    COALESCE(vm.onboarding_form_status, 'Not Set') as onboarding_status,
                    COUNT(DISTINCT vm.name) as count
                FROM `tabVendor Master` vm
                {all_joins}
                {where_clause if where_clause else ''}
                GROUP BY vm.onboarding_form_status
                ORDER BY count DESC
                """
                onboarding_results = frappe.db.sql(onboarding_status_query, query_values, as_dict=True)
                onboarding_status_breakdown = {item['onboarding_status']: item['count'] for item in onboarding_results}
            except Exception as e:
                frappe.log_error(f"Error in onboarding_status_breakdown query: {str(e)}")
                onboarding_status_breakdown = {}
        
        # Breakdown by search fields if search filters are applied
        field_breakdown = {}
        if search_filters:
            try:
                for field, params in search_filters.items():
                    if isinstance(params, list) and params:
                        field_counts = {}
                        for param in params:
                            if param and str(param).strip():
                                # Count vendors matching this specific parameter
                                # Use simpler query for field breakdown to avoid complex join issues
                                param_query = f"""
                                SELECT COUNT(DISTINCT vm.name) as count
                                FROM `tabVendor Master` vm
                                WHERE vm.{field} LIKE %s
                                """
                                
                                try:
                                    param_count = frappe.db.sql(param_query, [f"%{param}%"], as_dict=True)[0]['count']
                                    field_counts[str(param)] = param_count
                                except Exception as e:
                                    frappe.log_error(f"Error in field breakdown for {field}-{param}: {str(e)}")
                                    field_counts[str(param)] = 0
                        
                        if field_counts:
                            field_breakdown[field] = field_counts
            except Exception as e:
                frappe.log_error(f"Error in field_breakdown: {str(e)}")
                field_breakdown = {}
        
        # Count active filters
        active_filters = []
        if search_filters:
            active_filters.extend(list(search_filters.keys()))
        if company_name:
            active_filters.append('company_name')
        if onboarding_form:
            active_filters.append('onboarding_form')
        if via_data_import is not None:
            active_filters.append('via_data_import')
        
        return {
            'search_applied': True,
            'filtered_counts': {
                'imported_vendors': imported_count,
                'vms_registered': vms_registered_count,
                'approved_by_accounts_team': approved_accounts_count,
                'approved_by_purchase_team': approved_purchase_count,
                'total_approved': approved_accounts_count + approved_purchase_count
            },
            'status_breakdown': status_breakdown,
            'onboarding_status_breakdown': onboarding_status_breakdown,
            'field_breakdown': field_breakdown,
            'search_summary': {
                'fields_searched': list(search_filters.keys()) if search_filters else [],
                'company_filter_applied': bool(company_name),
                'onboarding_form_filter_applied': bool(onboarding_form),
                'via_data_import_filter_applied': via_data_import is not None,
                'active_filters': active_filters,
                'total_search_criteria': len(active_filters)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in calculate_search_analytics: {str(e)}")
        return {
            'search_applied': bool(search_filters or company_name or onboarding_form or via_data_import is not None),
            'error': 'Could not calculate search analytics',
            'message': str(e)
        }


def calculate_vendor_analytics():
    """Calculate comprehensive vendor analytics"""
    
    # Total vendor count
    total_vendors = frappe.db.count('Vendor Master')
    
    # Imported vendors (via_data_import = 1)
    imported_vendors = frappe.db.count('Vendor Master', {'via_data_import': 1})
    
    # Registered via VMS (via_data_import = 0)
    vms_registered = frappe.db.count('Vendor Master', {'created_from_registration': 1})

    total_vc_code = frappe.db.count("Vendor Code", filters={"vendor_code": ["is", "set"]})

    
    # Get vendors with approved onboarding and categorize by registration team
    approved_by_accounts = 0
    approved_by_purchase = 0
    
    # Query to get vendors with approved onboarding records
    approved_vendors_query = """
    SELECT DISTINCT 
        vm.name,
        vor.vendor_onboarding_no,
        vo.register_by_account_team
    FROM `tabVendor Master` vm
    INNER JOIN `tabVendor Onboarding Records` vor ON vm.name = vor.parent
    INNER JOIN `tabVendor Onboarding` vo ON vor.vendor_onboarding_no = vo.name
    WHERE vor.onboarding_form_status = 'Approved'
    """
    
    approved_vendors = frappe.db.sql(approved_vendors_query, as_dict=True)
    
    for vendor in approved_vendors:
        if vendor.get('register_by_account_team') == 1:
            approved_by_accounts += 1
        else:
            approved_by_purchase += 1
    
    return {
        'total_vendors': total_vendors,
        'total_vc_code':total_vc_code,
        'imported_vendors': imported_vendors,
        'vms_registered': vms_registered,
        'approved_by_accounts_team': approved_by_accounts,
        'approved_by_purchase_team': approved_by_purchase,
        'approved_by_any': approved_by_accounts + approved_by_purchase ,
        'approval_breakdown': {
            'accounts_team': approved_by_accounts,
            'purchase_team': approved_by_purchase,
            'total_approved': approved_by_accounts + approved_by_purchase
        }
    }


def calculate_company_wise_analytics(filter_company=None):
    """Calculate comprehensive vendor counts and analytics per company"""
    
    try:
        # Get all companies with comprehensive vendor analytics for each
        companies_query = """
        SELECT 
            cm.name as company_id,
            cm.company_name,
            cm.company_code,
            cm.company_short_form,
            COUNT(DISTINCT mcd.parent) as total_vendors
        FROM `tabCompany Master` cm
        LEFT JOIN `tabMultiple Company Data` mcd ON cm.name = mcd.company_name
        GROUP BY cm.name, cm.company_name, cm.company_code
        ORDER BY total_vendors DESC, cm.company_name ASC
        """
        
        companies = frappe.db.sql(companies_query, as_dict=True)
        
        # For each company, get detailed analytics
        enhanced_company_stats = []
        
        for company in companies:
            company_name = company['company_id']
            
            if company['total_vendors'] > 0:  # Only calculate if company has vendors
                
                # Get vendor code count for this company
                vendor_code_count_query = """
                SELECT 
                    COUNT(DISTINCT vm.name) as vendors_with_code
                FROM `tabVendor Master` vm
                INNER JOIN `tabMultiple Company Data` mcd ON vm.name = mcd.parent
                INNER JOIN `tabCompany Vendor Code` cvc ON mcd.company_vendor_code = cvc.name
                INNER JOIN `tabVendor Code` vc ON cvc.name = vc.parent
                WHERE mcd.company_name = %(company_name)s 
                AND vc.vendor_code IS NOT NULL 
                AND vc.vendor_code != ''
                """
                
                vendor_code_result = frappe.db.sql(vendor_code_count_query, 
                                                  {'company_name': company_name}, as_dict=True)
                vendors_with_code = vendor_code_result[0]['vendors_with_code'] if vendor_code_result else 0
                
                # Get imported vs VMS registered counts for this company
                # Get imported vs VMS registered counts for this company
                registration_breakdown_query = """
                    SELECT 
                        vm.via_data_import,
                        vm.created_from_registration,
                        COUNT(DISTINCT vm.name) as count
                    FROM `tabVendor Master` vm
                    INNER JOIN `tabMultiple Company Data` mcd ON vm.name = mcd.parent
                    WHERE mcd.company_name = %(company_name)s
                    GROUP BY vm.via_data_import, vm.created_from_registration
                """

                registration_results = frappe.db.sql(
                    registration_breakdown_query, 
                    {'company_name': company_name}, 
                    as_dict=True
                )

                imported_count = 0
                vms_registered_count = 0
                both_imported_and_vms_registered = 0

                for result in registration_results:
                    via_data_import = cint(result.get('via_data_import') or 0)
                    created_from_registration = cint(result.get('created_from_registration') or 0)
                    count = cint(result.get('count') or 0)

                    # Case 1: via_data_import only
                    if via_data_import and not created_from_registration:
                        imported_count += count

                    # Case 2: created_from_registration only
                    elif created_from_registration and not via_data_import:
                        vms_registered_count += count

                    # Case 3: both checked
                    elif via_data_import and created_from_registration:
                        both_imported_and_vms_registered += count
                       

                
                # Get approval team breakdown for this company
                approval_breakdown_query = """
                SELECT 
                    vo.register_by_account_team,
                    COUNT(DISTINCT vm.name) as count
                FROM `tabVendor Master` vm
                INNER JOIN `tabMultiple Company Data` mcd ON vm.name = mcd.parent
                INNER JOIN `tabVendor Onboarding Records` vor ON vm.name = vor.parent
                INNER JOIN `tabVendor Onboarding` vo ON vor.vendor_onboarding_no = vo.name
                WHERE mcd.company_name = %(company_name)s 
                AND vor.onboarding_form_status = 'Approved'
                GROUP BY vo.register_by_account_team
                """
                
                approval_results = frappe.db.sql(approval_breakdown_query, 
                                                {'company_name': company_name}, as_dict=True)
                
                approved_by_accounts = 0
                approved_by_purchase = 0
                for result in approval_results:
                    if result['register_by_account_team'] == 1:
                        approved_by_accounts = result['count']
                    else:
                        approved_by_purchase = result['count']
                
                # Get status breakdown for this company
                status_breakdown_query = """
                SELECT 
                    COALESCE(vm.status, 'Not Set') as status_value,
                    COUNT(DISTINCT vm.name) as count
                FROM `tabVendor Master` vm
                INNER JOIN `tabMultiple Company Data` mcd ON vm.name = mcd.parent
                WHERE mcd.company_name = %(company_name)s
                GROUP BY vm.status
                ORDER BY count DESC
                """
                
                status_results = frappe.db.sql(status_breakdown_query, 
                                             {'company_name': company_name}, as_dict=True)
                status_breakdown = {item['status_value']: item['count'] for item in status_results}
                
                # Get onboarding status breakdown for this company
                onboarding_status_query = """
                SELECT 
                    COALESCE(vm.onboarding_form_status, 'Not Set') as onboarding_status,
                    COUNT(DISTINCT vm.name) as count
                FROM `tabVendor Master` vm
                INNER JOIN `tabMultiple Company Data` mcd ON vm.name = mcd.parent
                WHERE mcd.company_name = %(company_name)s
                GROUP BY vm.onboarding_form_status
                ORDER BY count DESC
                """
                
                onboarding_results = frappe.db.sql(onboarding_status_query, 
                                                  {'company_name': company_name}, as_dict=True)
                onboarding_breakdown = {item['onboarding_status']: item['count'] for item in onboarding_results}
                
                # Get vendor types breakdown for this company
                vendor_types_query = """
                SELECT 
                    vt.vendor_type,
                    COUNT(DISTINCT vm.name) as count
                FROM `tabVendor Master` vm
                INNER JOIN `tabMultiple Company Data` mcd ON vm.name = mcd.parent
                INNER JOIN `tabVendor Type Group` vt ON vm.name = vt.parent
                WHERE mcd.company_name = %(company_name)s
                GROUP BY vt.vendor_type
                ORDER BY count DESC
                """
                
                vendor_types_results = frappe.db.sql(vendor_types_query, 
                                                    {'company_name': company_name}, as_dict=True)
                vendor_types_breakdown = {item['vendor_type']: item['count'] for item in vendor_types_results}
                
            else:
                # No vendors for this company
                vendors_with_code = 0
                imported_count = vms_registered_count = 0
                approved_by_accounts = approved_by_purchase = 0
                status_breakdown = {}
                onboarding_breakdown = {}
                vendor_types_breakdown = {}
            
            # Build comprehensive company analytics
            company_analytics = {
                'company_id': company['company_id'],
                'company_name': company['company_name'],
                'company_code': company.get('company_code'),
                'company_short_form': company.get('company_short_form'),
                'total_vendors': company['total_vendors'],
                'vendors_with_company_code': vendors_with_code,
                'registration_breakdown': {
                    'imported_vendors': imported_count,
                    'vms_registered': vms_registered_count,
                    'both_registered_and_import': both_imported_and_vms_registered
                },
                'approval_breakdown': {
                    'approved_by_accounts_team': approved_by_accounts,
                    'approved_by_purchase_team': approved_by_purchase,
                    'total_approved': approved_by_accounts + approved_by_purchase
                },
                'status_breakdown': status_breakdown,
                'onboarding_status_breakdown': onboarding_breakdown,
                'vendor_types_breakdown': vendor_types_breakdown,
                'analytics_summary': {
                    'has_vendors': company['total_vendors'] > 0,
                    'approval_rate': round((approved_by_accounts + approved_by_purchase) / company['total_vendors'] * 100, 1) if company['total_vendors'] > 0 else 0,
                    'import_rate': round(imported_count / company['total_vendors'] * 100, 1) if company['total_vendors'] > 0 else 0,
                    'vendor_code_rate': round(vendors_with_code / company['total_vendors'] * 100, 1) if company['total_vendors'] > 0 else 0
                }
            }
            
            enhanced_company_stats.append(company_analytics)
        
        return {
            'company_wise_analytics': enhanced_company_stats,
            'total_companies': len(companies),
            'companies_with_vendors': len([c for c in enhanced_company_stats if c['total_vendors'] > 0]),
            'companies_without_vendors': len([c for c in enhanced_company_stats if c['total_vendors'] == 0]),
            'summary': {
                'total_vendors_across_companies': sum(c['total_vendors'] for c in enhanced_company_stats),
                'avg_vendors_per_company': round(sum(c['total_vendors'] for c in enhanced_company_stats) / len(companies), 1) if companies else 0,
                'total_vendors_with_codes': sum(c['vendors_with_company_code'] for c in enhanced_company_stats)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in calculate_company_wise_analytics: {str(e)}")
        return {
            'company_wise_analytics': [],
            'total_companies': 0,
            'error': 'Could not calculate company analytics',
            'message': str(e)
        }


@frappe.whitelist() 
def get_vendor_search_fields():
    """
    Returns available fields for searching vendors
    """
    return {
        'success': True,
        'data': {
            'search_fields': [
                {'value': 'vendor_name', 'label': 'Vendor Name'},
                {'value': 'office_email_primary', 'label': 'Primary Email'},
                {'value': 'office_email_secondary', 'label': 'Secondary Email'},
                {'value': 'mobile_number', 'label': 'Mobile Number'},
                {'value': 'search_term', 'label': 'Search Term'},
                {'value': 'country', 'label': 'Country'},
                {'value': 'first_name', 'label': 'First Name'},
                {'value': 'last_name', 'label': 'Last Name'}
            ]
        }
    }


@frappe.whitelist()
def get_company_list():
    """
    Returns list of all companies for filtering
    """
    try:
        companies = frappe.db.sql("""
            SELECT *
            FROM `tabCompany Master`
            ORDER BY company_name
        """, as_dict=True)
        
        return {
            'success': True,
            'data': {
                'companies': companies
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@frappe.whitelist()
def get_vendor_detail(vendor_id):
    """
    Get detailed information for a specific vendor
    """
    try:
        # Get basic vendor info
        vendor = frappe.get_doc('Vendor Master', vendor_id)
        
        # Get onboarding records with detailed status
        onboarding_records = []
        for record in vendor.vendor_onb_records:
            onb_doc = frappe.get_doc('Vendor Onboarding', record.vendor_onboarding_no)
            
            # Combine record data with onboarding doc data
            combined_record = record.as_dict()
            combined_record.update({
                'register_by_account_team': onb_doc.register_by_account_team,
                'onboarding_doc_data': onb_doc.as_dict()  # Include all onboarding fields
            })
            onboarding_records.append(combined_record)
        
        return {
            'success': True,
            'data': {
                'vendor': vendor.as_dict(),
                'onboarding_records': onboarding_records
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    



@frappe.whitelist(allow_guest=True)
def get_vendor_bank_details(vendor_id):
    try:
        if not vendor_id:
            return {"success": False, "message": "Vendor ID is required"}
        
        # Single SQL query for maximum speed
        result = frappe.db.sql("""
            SELECT bd.*
            FROM `tabVendor Bank Details` bd
            INNER JOIN `tabVendor Master` vm ON vm.bank_details = bd.name
            WHERE vm.name = %s
            LIMIT 1
        """, (vendor_id,), as_dict=True)
        
        if not result:
            return {"success": False, "message": "No bank details found"}
        
        return {
            "success": True,
            "data": result[0]
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_bank_details: {str(e)}")
        return {
            "success": False,
            "message": "Error fetching bank details"
        }