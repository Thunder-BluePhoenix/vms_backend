import frappe
from frappe import _
import json
from frappe.utils import cstr, cint


@frappe.whitelist(allow_guest=True)
def get_port_master(search_term=None, page=None, page_size=None):
    try:
        # Validate and set defaults
        page = max(1, cint(page)) if page else 1
        page_size = min(200, max(1, cint(page_size))) if page_size else 10
        search_term = cstr(search_term).strip() if search_term else None
      
        where_conditions = []
        query_params = []
        
    
        if search_term:
            where_conditions.append("""
                (port_code LIKE %s OR port_name LIKE %s OR name LIKE %s)
            """)
            search_pattern = f'%{search_term}%'
            query_params.extend([search_pattern, search_pattern, search_pattern])
        
        # Build WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        count_query = f"""
            SELECT COUNT(*) as total_count
            FROM `tabPort Master`
            {where_clause}
        """
        
        total_count = frappe.db.sql(count_query, query_params, as_dict=True)[0].total_count
        
       
        total_pages = (total_count + page_size - 1) // page_size
        start = (page - 1) * page_size
        
        
        main_query = f"""
            SELECT 
                name,
                port_code,
                port_name,
				state,
                country
            FROM `tabPort Master`
            {where_clause}
            ORDER BY port_name ASC
            LIMIT %s OFFSET %s
        """
        
        final_params = query_params + [page_size, start]
        ports = frappe.db.sql(main_query, final_params, as_dict=True)
        
        return {
            "status": "success",
            "data": ports,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_count,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_port_master: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to fetch port master data",
            "error": str(e)
        }