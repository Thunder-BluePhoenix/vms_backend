import frappe
from frappe import _


@frappe.whitelist(allow_guest=False)
def filtering_po_details_pt(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del = None):
    """
    Main filtering API with pagination and comprehensive search
    """
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access.",
                "code": 404
            }

        # Base filters
        conditions = []
        values = {}

        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "po": []
            }

        pur_grp = frappe.get_all("Purchase Group Master", {"team": team}, pluck="purchase_group_code")
       
        user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "po": []
            }

        conditions.append("po.purchase_group IN %(purchase_group)s")
        values["purchase_group"] = pur_grp

        # Add additional filters if provided
        if company:
            conditions.append("po.company_code = %(company)s")
            values["company"] = company
            
      
            
        if status:
            conditions.append("po.vendor_status = %(status)s")
            values["status"] = status

        # Add search filter with relevance scoring
        if search:
            search_condition = """(
                po.name LIKE %(search)s OR
           
                po.po_no LIKE %(search)s
            )"""
            conditions.append(search_condition)
            values["search"] = f"%{search}%"

        filter_clause = " AND ".join(conditions)

        # Total count for pagination
        total_count = frappe.db.sql(f"""
            SELECT COUNT(*) AS count
            FROM `tabPurchase Order` po
            WHERE {filter_clause}
        """, values)[0][0]

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values["limit"] = page_length
        values["offset"] = offset

        # Order by relevance if search is provided
        order_clause = "po.creation DESC"
        if search:
            # Use parameterized query for security
            order_clause = """
                CASE 
                    WHEN po.name LIKE %(search_start)s THEN 1
                  
                    ELSE 4
                END,
                po.creation DESC
            """
            values["search_start"] = f"{search}%"

        # Final query - Get all required fields
        po_docs = frappe.db.sql(f"""
            SELECT 
                po.name,
                po.po_no,
                po.company_code,
                po.creation,
                po.modified
            FROM `tabPurchase Order` po
            WHERE {filter_clause}
            ORDER BY {order_clause}
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        return {
            "status": "success",
            "message": "Paginated and filtered po records fetched successfully.",
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "total_po": po_docs,
            "search_term": search
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Total po Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch po onboarding data.",
            "error": str(e),
            "po": []
        }
    

@frappe.whitelist()
def get_po_against_all_vc(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access.",
                "code": 404
            }

        # Base filters
        
        conditions = []
        values = {}

        # Check if user has Vendor role
        
        try:
            vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": usr})
            vendor_code_data = collect_vendor_code_data(vendor_master, method=None)
            
            if not vendor_code_data:
                return {
                    "status": "success",
                    "message": "No vendor codes found for the user.",
                    "total_count": 0,
                    "page_no": int(page_no) if page_no else 1,
                    "page_length": int(page_length) if page_length else 5,
                    "total_po": [],
                    "search_term": search
                }
            
            # Extract vendor codes
            vendor_codes = [vc['vendor_code'] for vc in vendor_code_data if vc.get('vendor_code')]
            
            if not vendor_codes:
                return {
                    "status": "success",
                    "message": "No valid vendor codes found for the user.",
                    "total_count": 0,
                    "page_no": int(page_no) if page_no else 1,
                    "page_length": int(page_length) if page_length else 5,
                    "total_po": [],
                    "search_term": search
                }
            
            # Add vendor code filter
            conditions.append("po.vendor_code IN %(vendor_codes)s")
            values["vendor_codes"] = vendor_codes
            
        except frappe.DoesNotExistError:
            return {"status": "error", "message": "Vendor Master not found for the user."}

        # Add additional filters if provided
        if company:
            conditions.append("po.company_code = %(company)s")
            values["company"] = company
            
        if status:
            conditions.append("po.vendor_status = %(status)s")
            values["status"] = status

        # Add search filter with relevance scoring
        if search:
            search_condition = """(
                po.name LIKE %(search)s OR
                po.po_no LIKE %(search)s
            )"""
            conditions.append(search_condition)
            values["search"] = f"%{search}%"

        filter_clause = " AND ".join(conditions)

        # Total count for pagination
        total_count = frappe.db.sql(f"""
            SELECT COUNT(*) AS count
            FROM `tabPurchase Order` po
            WHERE {filter_clause}
        """, values)[0][0]

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values["limit"] = page_length
        values["offset"] = offset

        # Order by relevance if search is provided
        order_clause = "po.creation DESC"
        if search:
            # Use parameterized query for security
            order_clause = """
                CASE 
                    WHEN po.name LIKE %(search_start)s THEN 1
                    ELSE 4
                END,
                po.creation DESC
            """
            values["search_start"] = f"{search}%"

        # Final query - Get all required fields
        po_docs = frappe.db.sql(f"""
            SELECT 
                po.name,
                po.po_no,
                po.company_code,
                po.vendor_code,
                po.creation,
                po.modified
            FROM `tabPurchase Order` po
            WHERE {filter_clause}
            ORDER BY {order_clause}
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        return {
            "status": "success",
            "message": "Paginated and filtered po records fetched successfully.",
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "total_po": po_docs,
            "search_term": search,
            "vendor_codes_used": vendor_codes
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Total po Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch po onboarding data.",
            "error": str(e),
            "po": []
        }


def get_all_vc_against_vendor():
    user = frappe.session.user
    vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": user})
    vendor_code = collect_vendor_code_data(vendor_master, method=None)
    response = {
        'vendor_codes': vendor_code,
        'designation': 'Vendor'
    }
    return response


def collect_vendor_code_data(vendor_doc, method=None):
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
                                'company_name': getattr(company_vendor_code_doc, 'company_name', ''),
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
    
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22", all_vendor_data)	
    
    return all_vendor_data