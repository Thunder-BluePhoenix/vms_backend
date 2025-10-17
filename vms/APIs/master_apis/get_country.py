import frappe
import json
from frappe import _
from frappe.utils import cstr, cint


@frappe.whitelist(allow_guest=True)
def country_details(data):
    country = data.get("country")

    country_details = frappe.get_doc("Country Master", country)
    mobile_code = None
    if country_details.mobile_code != None:
        mobile_code = country_details.mobile_code
    else:
        mobile_code = "None"

    return mobile_code


@frappe.whitelist(allow_guest=True)
def get_country_master(search_term=None, page=None, page_size=None):
    try:
    
        page = max(1, cint(page)) if page else 1
        page_size = min(200, max(1, cint(page_size))) if page_size else 20
        search_term = cstr(search_term).strip() if search_term else None
      
        where_conditions = []
        query_params = []
        
       
        if search_term:
            where_conditions.append("""
                (country_code LIKE %s OR country_name LIKE %s OR name LIKE %s)
            """)
            search_pattern = f'%{search_term}%'
            query_params.extend([search_pattern, search_pattern, search_pattern])
        
       
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        
        count_query = f"""
            SELECT COUNT(*) as total_count
            FROM `tabCountry Master`
            {where_clause}
        """
        
        total_count = frappe.db.sql(count_query, query_params, as_dict=True)[0].total_count
        
        
        total_pages = (total_count + page_size - 1) // page_size
        start = (page - 1) * page_size
        
        
        main_query = f"""
            SELECT 
                name,
                country_code,
                country_name,
                CONCAT(country_name, ' - ', country_code) as display_text
            FROM `tabCountry Master`
            {where_clause}
            ORDER BY country_name ASC
            LIMIT %s OFFSET %s
        """
        
        final_params = query_params + [page_size, start]
        countries = frappe.db.sql(main_query, final_params, as_dict=True)
        
        return {
            "status": "success",
            "data": countries,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_count,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_country_master: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to fetch country master data",
            "error": str(e)
        }
