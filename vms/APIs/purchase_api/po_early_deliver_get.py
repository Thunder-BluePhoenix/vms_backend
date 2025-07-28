import frappe
import json

from frappe.utils import today, get_first_day, get_last_day



# @frappe.whitelist(allow_guest=False)
# def filtering_po_details(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None):
#     """
#     Main filtering API with pagination and comprehensive search
#     """
#     try:
#         if usr is None:
#             usr = frappe.session.user
#         elif usr != frappe.session.user:
#             return {
#                 "status": "error",
#                 "message": "User mismatch or unauthorized access.",
#                 "code": 404
#             }

#         # Base filters
#         conditions = []
#         values = {}

#         team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
#         if not team:
#             return {
#                 "status": "error",
#                 "message": "No Employee record found for the user.",
#                 "po": []
#             }

#         pur_grp = frappe.get_all("Purchase Group Master", {"team": team}, pluck="purchase_group_code")
       
#         user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
#         if not user_ids:
#             return {
#                 "status": "error",
#                 "message": "No users found in the same team.",
#                 "po": []
#             }

#         conditions.append("po.purchase_group IN %(purchase_group)s")
#         values["purchase_group"] = pur_grp

#         # Add additional filters if provided
#         if company:
#             conditions.append("po.company_code = %(company)s")
#             values["company"] = company
            
#         if refno:
#             conditions.append("po.ref_no = %(refno)s")
#             values["refno"] = refno
            
#         if status:
#             conditions.append("po.vendor_status = %(status)s")
#             values["status"] = status

#         # Add search filter with relevance scoring
#         if search:
#             search_condition = """(
#                 po.name LIKE %(search)s OR
#                 po.supplier LIKE %(search)s OR
#                 po.supplier_name LIKE %(search)s OR
#                 po.ref_no LIKE %(search)s OR
#                 po.title LIKE %(search)s OR
#                 po.remarks LIKE %(search)s OR
#                 po.po_no LIKE %(search)s
#             )"""
#             conditions.append(search_condition)
#             values["search"] = f"%{search}%"

#         filter_clause = " AND ".join(conditions)

#         # Total count for pagination
#         total_count = frappe.db.sql(f"""
#             SELECT COUNT(*) AS count
#             FROM `tabPurchase Order` po
#             WHERE {filter_clause}
#         """, values)[0][0]

#         # Pagination
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         offset = (page_no - 1) * page_length
#         values["limit"] = page_length
#         values["offset"] = offset

#         # Order by relevance if search is provided
#         order_clause = "po.creation DESC"
#         if search:
#             order_clause = f"""
#                 CASE 
#                     WHEN po.name LIKE '{search}%' THEN 1
#                     WHEN po.supplier_name LIKE '{search}%' THEN 2
#                     WHEN po.ref_no LIKE '{search}%' THEN 3
#                     ELSE 4
#                 END,
#                 po.creation DESC
#             """

#         # Final query - SELECT * to get all fields
#         po_docs = frappe.db.sql(f"""
#             SELECT po.name
#             FROM `tabPurchase Order` po
#             WHERE {filter_clause}
#             ORDER BY {order_clause}
#             LIMIT %(limit)s OFFSET %(offset)s
#         """, values, as_dict=True)

#         return {
#             "status": "success",
#             "message": "Paginated and filtered po records fetched successfully.",
#             "total_count": total_count,
#             "page_no": page_no,
#             "page_length": page_length,
#             "total_po": po_docs,
#             "search_term": search
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Total po Details API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch po onboarding data.",
#             "error": str(e),
#             "po": []
#         }







import frappe
import json

from frappe.utils import today, get_first_day, get_last_day


@frappe.whitelist(allow_guest=False)
def get_po_search_suggestions(query="", limit=10, company=None, status=None, usr=None):
    """
    Get search suggestions for PO as user types (like Frappe link field)
    """
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return []

        if not query or len(query.strip()) < 2:
            return []

        query = query.strip()

        # Get user's team and purchase groups (same security as main API)
        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return []

        pur_grp = frappe.get_all("Purchase Group Master", {"team": team}, pluck="purchase_group_code")
        if not pur_grp:
            return []

        # Base conditions for user access
        conditions = ["po.purchase_group IN %(purchase_group)s"]
        values = {"purchase_group": pur_grp}

        # Add optional filters
        if company:
            conditions.append("po.company_code = %(company)s")
            values["company"] = company
            
        if status:
            conditions.append("po.vendor_status = %(status)s")
            values["status"] = status

        # Add search conditions
        search_condition = """(
            po.name LIKE %(query_start)s OR
            po.supplier_name LIKE %(query_start)s OR
            po.supplier LIKE %(query_start)s OR
            po.ref_no LIKE %(query_start)s OR
            po.po_no LIKE %(query_start)s OR
            po.name LIKE %(query_any)s OR
            po.supplier_name LIKE %(query_any)s OR
            po.supplier LIKE %(query_any)s OR
            po.ref_no LIKE %(query_any)s OR
            po.po_no LIKE %(query_any)s
        )"""
        
        conditions.append(search_condition)
        values["query_start"] = f"{query}%"  # Starts with query
        values["query_any"] = f"%{query}%"   # Contains query
        values["limit"] = int(limit)

        where_clause = " AND ".join(conditions)

        # Get suggestions with relevance ordering
        suggestions = frappe.db.sql(f"""
            SELECT 
                po.name,
                po.supplier_name,
                po.supplier,
                po.ref_no,
                po.po_no,
                po.vendor_status,
                
                po.company_code,
                CASE 
                    WHEN po.name LIKE %(query_start)s THEN 1
                    WHEN po.supplier_name LIKE %(query_start)s THEN 2
                    WHEN po.ref_no LIKE %(query_start)s THEN 3
                    WHEN po.po_no LIKE %(query_start)s THEN 4
                    ELSE 5
                END as relevance_score
            FROM `tabPurchase Order` po
            WHERE {where_clause}
            ORDER BY relevance_score, po.creation DESC
            LIMIT %(limit)s
        """, values, as_dict=True)

        # Format suggestions for frontend
        formatted_suggestions = []
        for row in suggestions:
            # Create display label
            label = row.name
            if row.supplier_name:
                label += f" - {row.supplier_name}"
            if row.ref_no:
                label += f" ({row.ref_no})"
            
            formatted_suggestions.append({
                "value": row.name,
                "label": label,
                "supplier_name": row.supplier_name or "",
                "ref_no": row.ref_no or "",
                "status": row.vendor_status or "",
                "total": row.total or 0,
                "company": row.company_code or ""
            })

        return formatted_suggestions

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO Search Suggestions API Error")
        return []

















@frappe.whitelist(allow_guest=False)
def filtering_po_earlydel_details(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, early_delivery="1", include_items=True, usr=None):
    """
    Main filtering API with pagination and comprehensive search
    Now includes filter for POs with early delivery requested items
    Also returns complete Purchase Order Item table data
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

        # Add early delivery filter
        if early_delivery and early_delivery.lower() in ['1', 'true', 'yes']:
            early_delivery_condition = """
                EXISTS (
                    SELECT 1 FROM `tabPurchase Order Item` poi 
                    WHERE poi.parent = po.name 
                    AND poi.requested_for_earlydelivery = 1
                )
            """
            conditions.append(early_delivery_condition)

        filter_clause = " AND ".join(conditions)

        # Total count for pagination
        total_count = frappe.db.sql(f"""
            SELECT COUNT(DISTINCT po.name) AS count
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

        # Final query - Get all required fields with early delivery info
        po_docs = frappe.db.sql(f"""
            SELECT DISTINCT
                po.*,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM `tabPurchase Order Item` poi 
                        WHERE poi.parent = po.name 
                        AND poi.requested_for_earlydelivery = 1
                    ) THEN 1 
                    ELSE 0 
                END as has_early_delivery_items,
                (
                    SELECT COUNT(*) FROM `tabPurchase Order Item` poi 
                    WHERE poi.parent = po.name 
                    AND poi.requested_for_earlydelivery = 1
                ) as early_delivery_items_count,
                (
                    SELECT COUNT(*) FROM `tabPurchase Order Item` poi 
                    WHERE poi.parent = po.name
                ) as total_items_count
            FROM `tabPurchase Order` po
            WHERE {filter_clause}
            ORDER BY {order_clause}
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        # Get PO names for fetching items
        po_names = [po.name for po in po_docs]
        
        # Fetch all items for the returned POs
        po_items_data = {}
        if include_items and po_names:
            # Get all items for these POs - using SELECT *
            items_query = """
                SELECT poi.*
                FROM `tabPurchase Order Item` poi 
                WHERE poi.parent IN %(po_names)s
                ORDER BY poi.parent, poi.idx
            """
            
            all_items = frappe.db.sql(items_query, {"po_names": po_names}, as_dict=True)
            
            # Group items by parent (PO name)
            for item in all_items:
                parent = item.parent
                if parent not in po_items_data:
                    po_items_data[parent] = []
                po_items_data[parent].append(item)

        # Add items data to each PO
        for po in po_docs:
            po['items'] = po_items_data.get(po.name, [])
            
            # Add summary statistics for items
            po['items_summary'] = {
                'total_items': len(po['items']),
                'early_delivery_items': len([item for item in po['items'] if item.get('requested_for_earlydelivery')]),
                'regular_items': len([item for item in po['items'] if not item.get('requested_for_earlydelivery')]),
                'total_qty': sum([item.get('qty', 0) for item in po['items']]),
                'total_amount': sum([item.get('amount', 0) for item in po['items']]),
                'early_delivery_amount': sum([item.get('amount', 0) for item in po['items'] if item.get('requested_for_earlydelivery')])
            }

        return {
            "status": "success",
            "message": "Paginated and filtered po records with items fetched successfully.",
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "total_po": po_docs,
            "search_term": search,
            "early_delivery_filter": early_delivery,
            "items_included": include_items,
            "summary": {
                "total_pos": len(po_docs),
                "total_items": sum([po['items_summary']['total_items'] for po in po_docs]),
                "total_early_delivery_items": sum([po['items_summary']['early_delivery_items'] for po in po_docs]),
                "total_amount": sum([po.get('total', 0) or 0 for po in po_docs])
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Total po Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch po onboarding data.",
            "error": str(e),
            "po": []
        }


@frappe.whitelist(allow_guest=False)
def get_po_items_only(po_name, usr=None):
    """
    Get only items for a specific PO (lighter alternative)
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

        # Check user access
        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "items": []
            }

        pur_grp = frappe.get_all("Purchase Group Master", {"team": team}, pluck="purchase_group_code")
        
        # Verify PO access
        po_access = frappe.db.sql("""
            SELECT 1 FROM `tabPurchase Order` 
            WHERE name = %(po_name)s AND purchase_group IN %(purchase_group)s
        """, {"po_name": po_name, "purchase_group": pur_grp})
        
        if not po_access:
            return {
                "status": "error",
                "message": "No access to this Purchase Order.",
                "items": []
            }

        # Get all items for this PO - using SELECT *
        po_items = frappe.db.sql("""
            SELECT poi.*
            FROM `tabPurchase Order Item` poi
            WHERE poi.parent = %(po_name)s
            ORDER BY poi.idx
        """, {"po_name": po_name}, as_dict=True)

        # Calculate summary
        total_items = len(po_items)
        early_delivery_items = len([item for item in po_items if item.get('requested_for_earlydelivery')])
        
        return {
            "status": "success",
            "message": "PO items fetched successfully.",
            "po_name": po_name,
            "items": po_items,
            "summary": {
                "total_items": total_items,
                "early_delivery_items": early_delivery_items,
                "regular_items": total_items - early_delivery_items,
                "total_qty": sum([item.get('qty', 0) for item in po_items]),
                "total_amount": sum([item.get('amount', 0) for item in po_items]),
                "early_delivery_amount": sum([item.get('amount', 0) for item in po_items if item.get('requested_for_earlydelivery')])
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO Items Only API Error")
        return {
            "status": "error",
            "message": "Failed to fetch PO items.",
            "error": str(e),
            "items": []
        }
    















import frappe
from frappe import _

# Cache for user roles to avoid repeated database calls
_user_roles_cache = {}

def get_cached_user_roles(user):
    """Cache user roles to avoid repeated database queries"""
    if user not in _user_roles_cache:
        _user_roles_cache[user] = set(frappe.get_roles(user))
    return _user_roles_cache[user]

@frappe.whitelist(allow_guest=True)
def filtering_po_details(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
    """
    Optimized main filtering API with pagination and comprehensive search
    """
    try:
        # Validate user session
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access.",
                "code": 404
            }

        # Use cached roles for better performance
        user_roles = get_cached_user_roles(usr)
       
        # Route to appropriate function based on role
        if "Vendor" in user_roles:
            return get_po_against_all_vc_optimized(
                page_no=page_no, 
                page_length=page_length, 
                company=company, 
                refno=refno, 
                status=status, 
                search=search, 
                usr=usr, 
                early_del=early_del
            )
        else:
            return filtering_po_details_pt_optimized(
                page_no=page_no, 
                page_length=page_length, 
                company=company, 
                refno=refno, 
                status=status, 
                search=search, 
                usr=usr, 
                early_del=early_del
            )
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "filtering_po_details API Error")
        return {
            "status": "error",
            "message": "Failed to filter PO details.",
            "error": str(e),
            "code": 500
        }


@frappe.whitelist(allow_guest=False)
def filtering_po_details_pt_optimized(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
    """
    Optimized version of filtering_po_details_pt with single query approach
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

        # Get team and purchase groups in a single optimized query
        team_data = frappe.db.sql("""
            SELECT 
                e.team,
                GROUP_CONCAT(DISTINCT pgm.purchase_group_code) as purchase_groups
            FROM `tabEmployee` e
            LEFT JOIN `tabPurchase Group Master` pgm ON pgm.team = e.team
            WHERE e.user_id = %(user)s
            GROUP BY e.team
        """, {"user": usr}, as_dict=True)

        if not team_data:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "po": []
            }

        team = team_data[0].team
        purchase_groups = team_data[0].purchase_groups.split(',') if team_data[0].purchase_groups else []

        if not purchase_groups:
            return {
                "status": "error",
                "message": "No purchase groups found for the team.",
                "po": []
            }

        # Build optimized query with single execution
        conditions = ["po.purchase_group IN %(purchase_groups)s"]
        values = {"purchase_groups": purchase_groups}

        # Add filters
        if company:
            conditions.append("po.company_code = %(company)s")
            values["company"] = company
            
        if status:
            conditions.append("po.vendor_status = %(status)s")
            values["status"] = status

        # Optimized search with full-text indexing consideration
        if search:
            conditions.append("(po.name LIKE %(search)s OR po.po_no LIKE %(search)s)")
            values["search"] = f"%{search}%"

        filter_clause = " AND ".join(conditions)

        # Single query to get both count and data
        if search:
            # With search relevance ordering
            query = f"""
                SELECT 
                    po.name,
                    po.po_no,
                    po.company_code,
                    po.creation,
                    po.modified,
                    COUNT(*) OVER() as total_count,
                    CASE 
                        WHEN po.name LIKE %(search_start)s THEN 1
                        WHEN po.po_no LIKE %(search_start)s THEN 2
                        ELSE 3
                    END as relevance
                FROM `tabPurchase Order` po
                WHERE {filter_clause}
                ORDER BY relevance, po.creation DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """
            values["search_start"] = f"{search}%"
        else:
            query = f"""
                SELECT 
                    po.name,
                    po.po_no,
                    po.company_code,
                    po.creation,
                    po.modified,
                    COUNT(*) OVER() as total_count
                FROM `tabPurchase Order` po
                WHERE {filter_clause}
                ORDER BY po.creation DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """

        # Pagination setup
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        values["limit"] = page_length
        values["offset"] = (page_no - 1) * page_length

        # Execute single query
        results = frappe.db.sql(query, values, as_dict=True)
        
        total_count = results[0].total_count if results else 0
        
        # Remove total_count from individual records
        po_docs = []
        for result in results:
            po_doc = {k: v for k, v in result.items() if k != 'total_count' and k != 'relevance'}
            po_docs.append(po_doc)

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
        frappe.log_error(frappe.get_traceback(), "filtering_po_details_pt_optimized API Error")
        return {
            "status": "error",
            "message": "Failed to fetch po data.",
            "error": str(e),
            "po": []
        }


@frappe.whitelist()
def get_po_against_all_vc_optimized(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
    """
    Heavily optimized vendor PO filtering with single query approach
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

        # Check vendor role using cached roles
        user_roles = get_cached_user_roles(usr)
        if "Vendor" not in user_roles:
            return {"status": "error", "message": "User does not have the Vendor role."}

        # Get all vendor codes in a single optimized query
        vendor_codes_query = """
            SELECT DISTINCT cvc_child.vendor_code
            FROM `tabVendor Master` vm
            JOIN `tabMultiple Company Data` mcd ON mcd.parent = vm.name
            JOIN `tabCompany Vendor Code` cvc ON cvc.name = mcd.company_vendor_code
            JOIN `tabVendor Code` cvc_child ON cvc_child.parent = cvc.name
            WHERE vm.office_email_primary = %(user)s
            AND cvc_child.vendor_code IS NOT NULL
            AND cvc_child.vendor_code != ''
        """
        
        vendor_codes_result = frappe.db.sql(vendor_codes_query, {"user": usr}, as_dict=True)
        vendor_codes = [row.vendor_code for row in vendor_codes_result if row.vendor_code]

        if not vendor_codes:
            return {
                "status": "success",
                "message": "No vendor codes found for the user.",
                "total_count": 0,
                "page_no": int(page_no) if page_no else 1,
                "page_length": int(page_length) if page_length else 5,
                "total_po": [],
                "search_term": search
            }

        # Build query conditions
        conditions = ["po.vendor_code IN %(vendor_codes)s"]
        values = {"vendor_codes": vendor_codes}

        if company:
            conditions.append("po.company_code = %(company)s")
            values["company"] = company
            
        if status:
            conditions.append("po.vendor_status = %(status)s")
            values["status"] = status

        if search:
            conditions.append("(po.name LIKE %(search)s OR po.po_no LIKE %(search)s)")
            values["search"] = f"%{search}%"

        filter_clause = " AND ".join(conditions)

        # Single optimized query with pagination and count
        if search:
            query = f"""
                SELECT 
                    po.name,
                    po.po_no,
                    po.company_code,
                    po.vendor_code,
                    po.creation,
                    po.modified,
                    COUNT(*) OVER() as total_count,
                    CASE 
                        WHEN po.name LIKE %(search_start)s THEN 1
                        WHEN po.po_no LIKE %(search_start)s THEN 2
                        ELSE 3
                    END as relevance
                FROM `tabPurchase Order` po
                WHERE {filter_clause}
                ORDER BY relevance, po.creation DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """
            values["search_start"] = f"{search}%"
        else:
            query = f"""
                SELECT 
                    po.name,
                    po.po_no,
                    po.company_code,
                    po.vendor_code,
                    po.creation,
                    po.modified,
                    COUNT(*) OVER() as total_count
                FROM `tabPurchase Order` po
                WHERE {filter_clause}
                ORDER BY po.creation DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        values["limit"] = page_length
        values["offset"] = (page_no - 1) * page_length

        # Execute query
        results = frappe.db.sql(query, values, as_dict=True)
        
        total_count = results[0].total_count if results else 0
        
        # Clean up results
        po_docs = []
        for result in results:
            po_doc = {k: v for k, v in result.items() if k not in ['total_count', 'relevance']}
            po_docs.append(po_doc)

        return {
            "status": "success",
            "message": "Paginated and filtered po records fetched successfully.",
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "total_po": po_docs,
            "search_term": search,
            "vendor_codes_count": len(vendor_codes)
        }

    except frappe.DoesNotExistError:
        return {"status": "error", "message": "Vendor Master not found for the user."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_po_against_all_vc_optimized API Error")
        return {
            "status": "error",
            "message": "Failed to fetch po data.",
            "error": str(e),
            "po": []
        }


@frappe.whitelist()
def get_all_vc_against_vendor_optimized():
    """
    Optimized function to get all vendor codes for a vendor user
    """
    user = frappe.session.user
    
    # Single query to get all vendor code data
    vendor_data_query = """
        SELECT 
            cvc.company_name,
            cvc_child.state,
            cvc_child.gst_no,
            cvc_child.vendor_code
        FROM `tabVendor Master` vm
        JOIN `tabMultiple Company Data` mcd ON mcd.parent = vm.name
        JOIN `tabCompany Vendor Code` cvc ON cvc.name = mcd.company_vendor_code
        JOIN `tabVendor Code` cvc_child ON cvc_child.parent = cvc.name
        WHERE vm.office_email_primary = %(user)s
        AND cvc_child.vendor_code IS NOT NULL
        AND cvc_child.vendor_code != ''
        ORDER BY cvc.company_name, cvc_child.vendor_code
    """
    
    vendor_codes = frappe.db.sql(vendor_data_query, {"user": user}, as_dict=True)
    
    return {
        'vendor_codes': vendor_codes,
        'designation': 'Vendor'
    }


def collect_vendor_code_data_optimized(vendor_doc):
    """
    Optimized version using single query instead of multiple document fetches
    """
    try:
        # Single query to get all vendor code data for this vendor
        query = """
            SELECT 
                cvc.company_name,
                vc.state,
                vc.gst_no,
                vc.vendor_code
            FROM `tabMultiple Company Data` mcd
            JOIN `tabCompany Vendor Code` cvc ON cvc.name = mcd.company_vendor_code
            JOIN `tabVendor Code` vc ON vc.parent = cvc.name
            WHERE mcd.parent = %(vendor_name)s
            AND vc.vendor_code IS NOT NULL
            AND vc.vendor_code != ''
        """
        
        vendor_data = frappe.db.sql(query, {"vendor_name": vendor_doc.name}, as_dict=True)
        
        return vendor_data
        
    except Exception as e:
        frappe.logger().error(f"Error in collect_vendor_code_data_optimized: {str(e)}")
        return []


# Additional performance optimization utility
def create_database_indexes():
    """
    Create database indexes for better query performance
    Run this once during deployment
    """
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_po_vendor_code ON `tabPurchase Order` (vendor_code)",
        "CREATE INDEX IF NOT EXISTS idx_po_company_code ON `tabPurchase Order` (company_code)", 
        "CREATE INDEX IF NOT EXISTS idx_po_vendor_status ON `tabPurchase Order` (vendor_status)",
        "CREATE INDEX IF NOT EXISTS idx_po_purchase_group ON `tabPurchase Order` (purchase_group)",
        "CREATE INDEX IF NOT EXISTS idx_po_creation ON `tabPurchase Order` (creation DESC)",
        "CREATE INDEX IF NOT EXISTS idx_po_search ON `tabPurchase Order` (name, po_no)",
        "CREATE INDEX IF NOT EXISTS idx_employee_user_team ON `tabEmployee` (user_id, team)",
        "CREATE INDEX IF NOT EXISTS idx_vendor_master_email ON `tabVendor Master` (office_email_primary)"
    ]
    
    for index_sql in indexes:
        try:
            frappe.db.sql(index_sql)
            frappe.db.commit()
        except Exception as e:
            frappe.logger().error(f"Error creating index: {index_sql}, Error: {str(e)}")







# @frappe.whitelist(allow_guest=True)
# def filtering_po_details(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
#     """
#     Main filtering API with pagination and comprehensive search
#     """
#     try:
#         if usr is None:
#             usr = frappe.session.user
#         elif usr != frappe.session.user:
#             return {
#                 "status": "error",
#                 "message": "User mismatch or unauthorized access.",
#                 "code": 404
#             }

#         user_doc = frappe.get_doc('User', usr)
#         user_roles = frappe.get_roles(user_doc.name)
       
#         # Check if user has Vendor role and route accordingly
#         if "Vendor" in user_roles:
#             return get_po_against_all_vc(
#                 page_no=page_no, 
#                 page_length=page_length, 
#                 company=company, 
#                 refno=refno, 
#                 status=status, 
#                 search=search, 
#                 usr=usr, 
#                 early_del=early_del
#             )
#         else:
#             return filtering_po_details_pt(
#                 page_no=page_no, 
#                 page_length=page_length, 
#                 company=company, 
#                 refno=refno, 
#                 status=status, 
#                 search=search, 
#                 usr=usr, 
#                 early_del=early_del
#             )
            
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "filtering_po_details API Error")
#         return {
#             "status": "error",
#             "message": "Failed to filter PO details.",
#             "error": str(e),
#             "code": 500
#         }





# @frappe.whitelist(allow_guest=False)
# def filtering_po_details_pt(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del = None):
#     """
#     Main filtering API with pagination and comprehensive search
#     """
#     try:
#         if usr is None:
#             usr = frappe.session.user
#         elif usr != frappe.session.user:
#             return {
#                 "status": "error",
#                 "message": "User mismatch or unauthorized access.",
#                 "code": 404
#             }

#         # Base filters
#         conditions = []
#         values = {}

#         team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
#         if not team:
#             return {
#                 "status": "error",
#                 "message": "No Employee record found for the user.",
#                 "po": []
#             }

#         pur_grp = frappe.get_all("Purchase Group Master", {"team": team}, pluck="purchase_group_code")
       
#         user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
#         if not user_ids:
#             return {
#                 "status": "error",
#                 "message": "No users found in the same team.",
#                 "po": []
#             }

#         conditions.append("po.purchase_group IN %(purchase_group)s")
#         values["purchase_group"] = pur_grp

#         # Add additional filters if provided
#         if company:
#             conditions.append("po.company_code = %(company)s")
#             values["company"] = company
            
      
            
#         if status:
#             conditions.append("po.vendor_status = %(status)s")
#             values["status"] = status

#         # Add search filter with relevance scoring
#         if search:
#             search_condition = """(
#                 po.name LIKE %(search)s OR
           
#                 po.po_no LIKE %(search)s
#             )"""
#             conditions.append(search_condition)
#             values["search"] = f"%{search}%"

#         filter_clause = " AND ".join(conditions)

#         # Total count for pagination
#         total_count = frappe.db.sql(f"""
#             SELECT COUNT(*) AS count
#             FROM `tabPurchase Order` po
#             WHERE {filter_clause}
#         """, values)[0][0]

#         # Pagination
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         offset = (page_no - 1) * page_length
#         values["limit"] = page_length
#         values["offset"] = offset

#         # Order by relevance if search is provided
#         order_clause = "po.creation DESC"
#         if search:
#             # Use parameterized query for security
#             order_clause = """
#                 CASE 
#                     WHEN po.name LIKE %(search_start)s THEN 1
                  
#                     ELSE 4
#                 END,
#                 po.creation DESC
#             """
#             values["search_start"] = f"{search}%"

#         # Final query - Get all required fields
#         po_docs = frappe.db.sql(f"""
#             SELECT 
#                 po.name,
#                 po.po_no,
#                 po.company_code,
#                 po.creation,
#                 po.modified
#             FROM `tabPurchase Order` po
#             WHERE {filter_clause}
#             ORDER BY {order_clause}
#             LIMIT %(limit)s OFFSET %(offset)s
#         """, values, as_dict=True)

#         return {
#             "status": "success",
#             "message": "Paginated and filtered po records fetched successfully.",
#             "total_count": total_count,
#             "page_no": page_no,
#             "page_length": page_length,
#             "total_po": po_docs,
#             "search_term": search
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Total po Details API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch po onboarding data.",
#             "error": str(e),
#             "po": []
#         }
    




# @frappe.whitelist()
# def get_po_against_all_vc(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
#     try:
#         if usr is None:
#             usr = frappe.session.user
#         elif usr != frappe.session.user:
#             return {
#                 "status": "error",
#                 "message": "User mismatch or unauthorized access.",
#                 "code": 404
#             }

#         # Base filters
#         user_doc = frappe.get_doc('User', usr)
#         user_roles = frappe.get_roles(user_doc.name)
#         conditions = []
#         values = {}

#         # Check if user has Vendor role
#         if "Vendor" not in user_roles:
#             return {"status": "error", "message": "User does not have the Vendor role."}

#         # Get vendor codes for the current user
#         try:
#             vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": usr})
#             vendor_code_data = collect_vendor_code_data(vendor_master, method=None)
            
#             if not vendor_code_data:
#                 return {
#                     "status": "success",
#                     "message": "No vendor codes found for the user.",
#                     "total_count": 0,
#                     "page_no": int(page_no) if page_no else 1,
#                     "page_length": int(page_length) if page_length else 5,
#                     "total_po": [],
#                     "search_term": search
#                 }
            
#             # Extract vendor codes
#             vendor_codes = [vc['vendor_code'] for vc in vendor_code_data if vc.get('vendor_code')]
            
#             if not vendor_codes:
#                 return {
#                     "status": "success",
#                     "message": "No valid vendor codes found for the user.",
#                     "total_count": 0,
#                     "page_no": int(page_no) if page_no else 1,
#                     "page_length": int(page_length) if page_length else 5,
#                     "total_po": [],
#                     "search_term": search
#                 }
            
#             # Add vendor code filter
#             conditions.append("po.vendor_code IN %(vendor_codes)s")
#             values["vendor_codes"] = vendor_codes
            
#         except frappe.DoesNotExistError:
#             return {"status": "error", "message": "Vendor Master not found for the user."}

#         # Add additional filters if provided
#         if company:
#             conditions.append("po.company_code = %(company)s")
#             values["company"] = company
            
#         if status:
#             conditions.append("po.vendor_status = %(status)s")
#             values["status"] = status

#         # Add search filter with relevance scoring
#         if search:
#             search_condition = """(
#                 po.name LIKE %(search)s OR
#                 po.po_no LIKE %(search)s
#             )"""
#             conditions.append(search_condition)
#             values["search"] = f"%{search}%"

#         filter_clause = " AND ".join(conditions)

#         # Total count for pagination
#         total_count = frappe.db.sql(f"""
#             SELECT COUNT(*) AS count
#             FROM `tabPurchase Order` po
#             WHERE {filter_clause}
#         """, values)[0][0]

#         # Pagination
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         offset = (page_no - 1) * page_length
#         values["limit"] = page_length
#         values["offset"] = offset

#         # Order by relevance if search is provided
#         order_clause = "po.creation DESC"
#         if search:
#             # Use parameterized query for security
#             order_clause = """
#                 CASE 
#                     WHEN po.name LIKE %(search_start)s THEN 1
#                     ELSE 4
#                 END,
#                 po.creation DESC
#             """
#             values["search_start"] = f"{search}%"

#         # Final query - Get all required fields
#         po_docs = frappe.db.sql(f"""
#             SELECT 
#                 po.name,
#                 po.po_no,
#                 po.company_code,
#                 po.vendor_code,
#                 po.creation,
#                 po.modified
#             FROM `tabPurchase Order` po
#             WHERE {filter_clause}
#             ORDER BY {order_clause}
#             LIMIT %(limit)s OFFSET %(offset)s
#         """, values, as_dict=True)

#         return {
#             "status": "success",
#             "message": "Paginated and filtered po records fetched successfully.",
#             "total_count": total_count,
#             "page_no": page_no,
#             "page_length": page_length,
#             "total_po": po_docs,
#             "search_term": search,
#             "vendor_codes_used": vendor_codes
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Total po Details API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch po onboarding data.",
#             "error": str(e),
#             "po": []
#         }


# def get_all_vc_against_vendor():
#     user = frappe.session.user
#     vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": user})
#     vendor_code = collect_vendor_code_data(vendor_master, method=None)
#     response = {
#         'vendor_codes': vendor_code,
#         'designation': 'Vendor'
#     }
#     return response


# def collect_vendor_code_data(vendor_doc, method=None):
#     """Collect all vendor code data from multiple company data"""
#     all_vendor_data = []
    
#     try:
#         # Check if multiple_company_data exists and has data
#         if not hasattr(vendor_doc, 'multiple_company_data') or not vendor_doc.multiple_company_data:
#             frappe.logger().info("No multiple_company_data found in vendor document")
#             return all_vendor_data
        
#         # Iterate through multiple_company_data table
#         for company_data_row in vendor_doc.multiple_company_data:
#             if hasattr(company_data_row, 'company_vendor_code') and company_data_row.company_vendor_code:
#                 try:
#                     # Fetch Company Vendor Code document
#                     company_vendor_code_doc = frappe.get_doc("Company Vendor Code", company_data_row.company_vendor_code)
                    
#                     # Check if vendor_code table exists and has data
#                     if hasattr(company_vendor_code_doc, 'vendor_code') and company_vendor_code_doc.vendor_code:
#                         # Iterate through vendor_code table in Company Vendor Code doc
#                         for vendor_code_row in company_vendor_code_doc.vendor_code:
#                             vendor_info = {
#                                 'company_name': getattr(company_vendor_code_doc, 'company_name', ''),
#                                 'state': getattr(vendor_code_row, 'state', ''),
#                                 'gst_no': getattr(vendor_code_row, 'gst_no', ''),
#                                 'vendor_code': getattr(vendor_code_row, 'vendor_code', '')
#                             }
#                             all_vendor_data.append(vendor_info)
#                     else:
#                         frappe.logger().info(f"No vendor_code data found in Company Vendor Code {company_data_row.company_vendor_code}")
                        
#                 except Exception as e:
#                     frappe.logger().error(f"Error fetching Company Vendor Code {company_data_row.company_vendor_code}: {str(e)}")
#                     continue
                    
#     except Exception as e:
#         frappe.logger().error(f"Error in collect_vendor_code_data: {str(e)}")
    
#     print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22", all_vendor_data)	
    
#     return all_vendor_data