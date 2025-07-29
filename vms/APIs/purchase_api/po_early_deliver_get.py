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
import redis
import json
import hashlib
from datetime import datetime, timedelta

# Redis connection for caching
def get_redis_connection():
    """Get Redis connection for caching"""
    try:
        return frappe.cache()
    except:
        return None

# Advanced caching with TTL
class AdvancedCache:
    def __init__(self, ttl=300):  # 5 minutes default TTL
        self.redis_conn = get_redis_connection()
        self.ttl = ttl
    
    def get_cache_key(self, prefix, *args):
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args if arg is not None)}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def get(self, key):
        """Get cached data"""
        if not self.redis_conn:
            return None
        try:
            data = self.redis_conn.get(key)
            return json.loads(data) if data else None
        except:
            return None
    
    def set(self, key, data):
        """Set cached data with TTL"""
        if not self.redis_conn:
            return
        try:
            self.redis_conn.setex(key, self.ttl, json.dumps(data, default=str))
        except:
            pass

# Global cache instances
user_cache = AdvancedCache(ttl=1800)  # 30 minutes for user data
po_cache = AdvancedCache(ttl=60)      # 1 minute for PO data

@frappe.whitelist(allow_guest=True)
def filtering_po_details_ultra_fast(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None, **kwargs):
    """
    Ultra-fast filtering with aggressive caching and query optimization
    """
    try:
        # Validate user
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {"status": "error", "message": "Unauthorized access.", "code": 404}

        # Check cache first for user role
        cache_key = user_cache.get_cache_key("user_role", usr)
        user_role_data = user_cache.get(cache_key)
        
        if not user_role_data:
            # Single query to get user, roles, and team data
            user_data = frappe.db.sql("""
                SELECT 
                    u.name as user_name,
                    GROUP_CONCAT(DISTINCT r.role) as roles,
                    e.team,
                    GROUP_CONCAT(DISTINCT pgm.purchase_group_code) as purchase_groups
                FROM `tabUser` u
                LEFT JOIN `tabHas Role` r ON r.parent = u.name
                LEFT JOIN `tabEmployee` e ON e.user_id = u.name
                LEFT JOIN `tabPurchase Group Master` pgm ON pgm.team = e.team
                WHERE u.name = %(user)s
                GROUP BY u.name, e.team
            """, {"user": usr}, as_dict=True)
            
            if not user_data:
                return {"status": "error", "message": "User not found.", "code": 404}
            
            user_role_data = {
                "roles": set(user_data[0].roles.split(',')) if user_data[0].roles else set(),
                "team": user_data[0].team,
                "purchase_groups": user_data[0].purchase_groups.split(',') if user_data[0].purchase_groups else []
            }
            user_cache.set(cache_key, user_role_data)

        # Route based on role
        if "Vendor" in user_role_data["roles"]:
            return get_vendor_po_ultra_fast(page_no, page_length, company, refno, status, search, usr)
        else:
            return get_employee_po_ultra_fast(page_no, page_length, company, refno, status, search, usr, user_role_data)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Ultra Fast PO Filter Error")
        return {"status": "error", "message": "System error", "error": str(e), "code": 500}


def get_employee_po_ultra_fast(page_no, page_length, company, refno, status, search, usr, user_role_data):
    """Ultra-fast employee PO filtering"""
    try:
        if not user_role_data["purchase_groups"]:
            return {"status": "error", "message": "No purchase groups found.", "po": []}

        # Generate cache key for this specific query
        cache_key = po_cache.get_cache_key(
            "employee_po", usr, page_no, page_length, company, status, search,
            hash(tuple(user_role_data["purchase_groups"]))
        )
        
        cached_result = po_cache.get(cache_key)
        if cached_result:
            return cached_result

        # Pagination setup
        page_no = int(page_no) if page_no else 1
        page_length = min(int(page_length) if page_length else 10, 100)  # Cap at 100
        offset = (page_no - 1) * page_length

        # Build dynamic WHERE clause
        where_conditions = ["po.purchase_group IN %(purchase_groups)s"]
        params = {"purchase_groups": user_role_data["purchase_groups"]}

        if company:
            where_conditions.append("po.company_code = %(company)s")
            params["company"] = company
        if status:
            where_conditions.append("po.vendor_status = %(status)s")
            params["status"] = status
        if search:
            where_conditions.append("(po.name LIKE %(search)s OR po.po_no LIKE %(search)s)")
            params["search"] = f"%{search}%"

        where_clause = " AND ".join(where_conditions)

        # Ultra-optimized single query with materialized CTE
        query = f"""
        WITH po_filtered AS (
            SELECT 
                po.name,
                po.po_no,
                po.company_code,
                po.creation,
                po.modified,
                ROW_NUMBER() OVER (
                    ORDER BY 
                    {f"CASE WHEN po.name LIKE %(search_start)s THEN 1 WHEN po.po_no LIKE %(search_start)s THEN 2 ELSE 3 END," if search else ""}
                    po.creation DESC
                ) as row_num
            FROM `tabPurchase Order` po
            WHERE {where_clause}
        )
        SELECT 
            *,
            (SELECT COUNT(*) FROM po_filtered) as total_count
        FROM po_filtered
        WHERE row_num BETWEEN %(start_row)s AND %(end_row)s
        """

        params.update({
            "start_row": offset + 1,
            "end_row": offset + page_length
        })

        if search:
            params["search_start"] = f"{search}%"

        results = frappe.db.sql(query, params, as_dict=True)
        
        total_count = results[0].total_count if results else 0
        po_docs = [{k: v for k, v in r.items() if k not in ['total_count', 'row_num']} for r in results]

        response = {
            "status": "success",
            "message": "Ultra-fast PO fetch completed.",
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "total_po": po_docs,
            "search_term": search,
            "cached": False
        }

        # Cache the result
        po_cache.set(cache_key, response)
        return response

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Employee PO Ultra Fast Error")
        return {"status": "error", "message": "Failed to fetch employee POs", "error": str(e)}


def get_vendor_po_ultra_fast(page_no, page_length, company, refno, status, search, usr):
    """Ultra-fast vendor PO filtering with pre-computed vendor codes"""
    try:
        # Check vendor codes cache first
        vendor_cache_key = user_cache.get_cache_key("vendor_codes", usr)
        vendor_codes = user_cache.get(vendor_cache_key)
        
        if not vendor_codes:
            # Single optimized query for vendor codes
            vendor_codes_result = frappe.db.sql("""
                SELECT DISTINCT vc.vendor_code
                FROM `tabVendor Master` vm
                STRAIGHT_JOIN `tabMultiple Company Data` mcd ON mcd.parent = vm.name
                STRAIGHT_JOIN `tabCompany Vendor Code` cvc ON cvc.name = mcd.company_vendor_code  
                STRAIGHT_JOIN `tabVendor Code` vc ON vc.parent = cvc.name
                WHERE vm.office_email_primary = %(user)s
                AND vc.vendor_code IS NOT NULL 
                AND vc.vendor_code != ''
            """, {"user": usr}, as_dict=True)
            
            vendor_codes = [r.vendor_code for r in vendor_codes_result]
            if not vendor_codes:
                return {
                    "status": "success", "message": "No vendor codes found.",
                    "total_count": 0, "page_no": int(page_no) if page_no else 1,
                    "page_length": int(page_length) if page_length else 10,
                    "total_po": [], "search_term": search
                }
            
            user_cache.set(vendor_cache_key, vendor_codes)

        # Generate cache key for this vendor query
        cache_key = po_cache.get_cache_key(
            "vendor_po", usr, page_no, page_length, company, status, search,
            hash(tuple(vendor_codes))
        )
        
        cached_result = po_cache.get(cache_key)
        if cached_result:
            return cached_result

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = min(int(page_length) if page_length else 10, 100)
        offset = (page_no - 1) * page_length

        # Build conditions
        where_conditions = ["po.vendor_code IN %(vendor_codes)s"]
        params = {"vendor_codes": vendor_codes}

        if company:
            where_conditions.append("po.company_code = %(company)s")
            params["company"] = company
        if status:
            where_conditions.append("po.vendor_status = %(status)s")
            params["status"] = status
        if search:
            where_conditions.append("(po.name LIKE %(search)s OR po.po_no LIKE %(search)s)")
            params["search"] = f"%{search}%"

        where_conditions.append("po.sent_to_vendor = True")

        where_clause = " AND ".join(where_conditions)

        # Use covering index query with materialized CTE
        query = f"""
        WITH vendor_po_filtered AS (
            SELECT 
                po.name,
                po.po_no,
                po.company_code,
                po.vendor_code,
                po.creation,
                po.modified,
                ROW_NUMBER() OVER (
                    ORDER BY 
                    {f"CASE WHEN po.name LIKE %(search_start)s THEN 1 WHEN po.po_no LIKE %(search_start)s THEN 2 ELSE 3 END," if search else ""}
                    po.creation DESC
                ) as row_num
            FROM `tabPurchase Order` po
            WHERE {where_clause}
        )
        SELECT 
            *,
            (SELECT COUNT(*) FROM vendor_po_filtered) as total_count
        FROM vendor_po_filtered  
        WHERE row_num BETWEEN %(start_row)s AND %(end_row)s
        """

        params.update({
            "start_row": offset + 1,
            "end_row": offset + page_length
        })

        if search:
            params["search_start"] = f"{search}%"

        results = frappe.db.sql(query, params, as_dict=True)
        
        total_count = results[0].total_count if results else 0
        po_docs = [{k: v for k, v in r.items() if k not in ['total_count', 'row_num']} for r in results]

        response = {
            "status": "success",
            "message": "Ultra-fast vendor PO fetch completed.",
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "total_po": po_docs,
            "search_term": search,
            "vendor_codes_count": len(vendor_codes),
            "cached": False
        }

        po_cache.set(cache_key, response)
        return response

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor PO Ultra Fast Error")
        return {"status": "error", "message": "Failed to fetch vendor POs", "error": str(e)}


# Async background cache warming
@frappe.whitelist()
def warm_po_cache(user_list=None, **kwargs):
    """
    Background job to pre-warm caches for active users
    Run this via scheduler every 5 minutes
    """
    try:
        if not user_list:
            # Get active users from last 30 minutes
            user_list = frappe.db.sql("""
                SELECT DISTINCT user 
                FROM `tabActivity Log` 
                WHERE creation > NOW() - INTERVAL 30 MINUTE
                AND user != 'Guest'
            """, as_dict=True)
            user_list = [u.user for u in user_list]

        for user in user_list[:20]:  # Limit to 20 users per run
            try:
                # Warm user role cache
                cache_key = user_cache.get_cache_key("user_role", user)
                if not user_cache.get(cache_key):
                    filtering_po_details_ultra_fast(page_no=1, page_length=10, usr=user)
            except:
                continue

        return {"status": "success", "warmed_users": len(user_list)}
    except Exception as e:
        frappe.log_error(str(e), "Cache Warming Error")
        return {"status": "error", "error": str(e)}


# Database optimization functions
def create_advanced_indexes():
    """
    Create advanced covering indexes for maximum performance
    Run once during deployment
    """
    advanced_indexes = [
        # Covering indexes for employee queries
        """CREATE INDEX IF NOT EXISTS idx_po_employee_covering 
           ON `tabPurchase Order` (purchase_group, company_code, vendor_status, creation DESC, name, po_no)""",
        
        # Covering indexes for vendor queries  
        """CREATE INDEX IF NOT EXISTS idx_po_vendor_covering
           ON `tabPurchase Order` (vendor_code, company_code, vendor_status, creation DESC, name, po_no)""",
        
        # Full-text search index
        """CREATE FULLTEXT INDEX IF NOT EXISTS idx_po_fulltext
           ON `tabPurchase Order` (name, po_no)""",
        
        # Optimized user-team index
        """CREATE INDEX IF NOT EXISTS idx_employee_user_team_covering
           ON `tabEmployee` (user_id, team)""",
        
        # Purchase group index
        """CREATE INDEX IF NOT EXISTS idx_purchase_group_team
           ON `tabPurchase Group Master` (team, purchase_group_code)""",
        
        # Vendor master email index
        """CREATE INDEX IF NOT EXISTS idx_vendor_master_email_covering
           ON `tabVendor Master` (office_email_primary)""",
        
        # Multi-column vendor code index
        """CREATE INDEX IF NOT EXISTS idx_vendor_code_covering
           ON `tabVendor Code` (parent, vendor_code)""",
        
        # User roles index for faster role checking
        """CREATE INDEX IF NOT EXISTS idx_has_role_covering
           ON `tabHas Role` (parent, role)"""
    ]
    
    for index_sql in advanced_indexes:
        try:
            frappe.db.sql(index_sql)
            frappe.db.commit()
            print(f"✓ Created index: {index_sql[:50]}...")
        except Exception as e:
            print(f"✗ Error creating index: {str(e)}")


def optimize_mysql_config():
    """
    Recommended MySQL configuration optimizations
    Add these to your MySQL config file
    """
    mysql_optimizations = """
    # Add to /etc/mysql/mysql.conf.d/mysqld.cnf or equivalent
    
    [mysqld]
    # Query cache (if MySQL < 8.0)
    query_cache_type = 1
    query_cache_size = 256M
    query_cache_limit = 2M
    
    # Buffer pools
    innodb_buffer_pool_size = 2G  # 70-80% of RAM
    innodb_log_file_size = 512M
    innodb_log_buffer_size = 64M
    
    # Connections
    max_connections = 500
    thread_cache_size = 50
    
    # Performance
    innodb_flush_log_at_trx_commit = 2
    innodb_flush_method = O_DIRECT
    innodb_file_per_table = 1
    
    # Query optimization
    join_buffer_size = 2M
    sort_buffer_size = 2M
    read_buffer_size = 1M
    read_rnd_buffer_size = 1M
    """
    print(mysql_optimizations)


# Performance monitoring
@frappe.whitelist()
def get_performance_stats(**kwargs):
    """Get performance statistics for monitoring"""
    try:
        stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_query_time": 0,
            "active_connections": frappe.db.sql("SHOW STATUS LIKE 'Threads_connected'")[0][1],
            "query_cache_hit_rate": 0
        }
        
        # Get query cache stats (MySQL < 8.0)
        try:
            cache_stats = frappe.db.sql("SHOW STATUS LIKE 'Qcache_%'", as_dict=True)
            cache_dict = {stat.Variable_name: int(stat.Value) for stat in cache_stats}
            if cache_dict.get('Qcache_hits', 0) + cache_dict.get('Qcache_inserts', 0) > 0:
                stats["query_cache_hit_rate"] = (
                    cache_dict.get('Qcache_hits', 0) / 
                    (cache_dict.get('Qcache_hits', 0) + cache_dict.get('Qcache_inserts', 0))
                ) * 100
        except:
            pass
            
        return stats
    except Exception as e:
        return {"error": str(e)}


# Legacy function wrappers for backward compatibility
@frappe.whitelist(allow_guest=True)
def filtering_po_details(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None, **kwargs):
    """Backward compatible wrapper"""
    return filtering_po_details_ultra_fast(page_no, page_length, company, refno, status, search, usr, early_del)

@frappe.whitelist()
def get_po_against_all_vc(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None, **kwargs):
    """Backward compatible wrapper"""
    return get_vendor_po_ultra_fast(page_no, page_length, company, refno, status, search, usr)








# import frappe
# from frappe import _

# # Cache for user roles to avoid repeated database calls
# _user_roles_cache = {}

# def get_cached_user_roles(user):
#     """Cache user roles to avoid repeated database queries"""
#     if user not in _user_roles_cache:
#         _user_roles_cache[user] = set(frappe.get_roles(user))
#     return _user_roles_cache[user]

# @frappe.whitelist(allow_guest=True)
# def filtering_po_details(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
#     """
#     Optimized main filtering API with pagination and comprehensive search
#     """
#     try:
#         # Validate user session
#         if usr is None:
#             usr = frappe.session.user
#         elif usr != frappe.session.user:
#             return {
#                 "status": "error",
#                 "message": "User mismatch or unauthorized access.",
#                 "code": 404
#             }

#         # Use cached roles for better performance
#         user_roles = get_cached_user_roles(usr)
       
#         # Route to appropriate function based on role
#         if "Vendor" in user_roles:
#             return get_po_against_all_vc_optimized(
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
#             return filtering_po_details_pt_optimized(
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
# def filtering_po_details_pt_optimized(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
#     """
#     Optimized version of filtering_po_details_pt with single query approach
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

#         # Get team and purchase groups in a single optimized query
#         team_data = frappe.db.sql("""
#             SELECT 
#                 e.team,
#                 GROUP_CONCAT(DISTINCT pgm.purchase_group_code) as purchase_groups
#             FROM `tabEmployee` e
#             LEFT JOIN `tabPurchase Group Master` pgm ON pgm.team = e.team
#             WHERE e.user_id = %(user)s
#             GROUP BY e.team
#         """, {"user": usr}, as_dict=True)

#         if not team_data:
#             return {
#                 "status": "error",
#                 "message": "No Employee record found for the user.",
#                 "po": []
#             }

#         team = team_data[0].team
#         purchase_groups = team_data[0].purchase_groups.split(',') if team_data[0].purchase_groups else []

#         if not purchase_groups:
#             return {
#                 "status": "error",
#                 "message": "No purchase groups found for the team.",
#                 "po": []
#             }

#         # Build optimized query with single execution
#         conditions = ["po.purchase_group IN %(purchase_groups)s"]
#         values = {"purchase_groups": purchase_groups}

#         # Add filters
#         if company:
#             conditions.append("po.company_code = %(company)s")
#             values["company"] = company
            
#         if status:
#             conditions.append("po.vendor_status = %(status)s")
#             values["status"] = status

#         # Optimized search with full-text indexing consideration
#         if search:
#             conditions.append("(po.name LIKE %(search)s OR po.po_no LIKE %(search)s)")
#             values["search"] = f"%{search}%"

#         filter_clause = " AND ".join(conditions)

#         # Single query to get both count and data
#         if search:
#             # With search relevance ordering
#             query = f"""
#                 SELECT 
#                     po.name,
#                     po.po_no,
#                     po.company_code,
#                     po.creation,
#                     po.modified,
#                     COUNT(*) OVER() as total_count,
#                     CASE 
#                         WHEN po.name LIKE %(search_start)s THEN 1
#                         WHEN po.po_no LIKE %(search_start)s THEN 2
#                         ELSE 3
#                     END as relevance
#                 FROM `tabPurchase Order` po
#                 WHERE {filter_clause}
#                 ORDER BY relevance, po.creation DESC
#                 LIMIT %(limit)s OFFSET %(offset)s
#             """
#             values["search_start"] = f"{search}%"
#         else:
#             query = f"""
#                 SELECT 
#                     po.name,
#                     po.po_no,
#                     po.company_code,
#                     po.creation,
#                     po.modified,
#                     COUNT(*) OVER() as total_count
#                 FROM `tabPurchase Order` po
#                 WHERE {filter_clause}
#                 ORDER BY po.creation DESC
#                 LIMIT %(limit)s OFFSET %(offset)s
#             """

#         # Pagination setup
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         values["limit"] = page_length
#         values["offset"] = (page_no - 1) * page_length

#         # Execute single query
#         results = frappe.db.sql(query, values, as_dict=True)
        
#         total_count = results[0].total_count if results else 0
        
#         # Remove total_count from individual records
#         po_docs = []
#         for result in results:
#             po_doc = {k: v for k, v in result.items() if k != 'total_count' and k != 'relevance'}
#             po_docs.append(po_doc)

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
#         frappe.log_error(frappe.get_traceback(), "filtering_po_details_pt_optimized API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch po data.",
#             "error": str(e),
#             "po": []
#         }


# @frappe.whitelist()
# def get_po_against_all_vc_optimized(page_no=None, page_length=None, company=None, refno=None, status=None, search=None, usr=None, early_del=None):
#     """
#     Heavily optimized vendor PO filtering with single query approach
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

#         # Check vendor role using cached roles
#         user_roles = get_cached_user_roles(usr)
#         if "Vendor" not in user_roles:
#             return {"status": "error", "message": "User does not have the Vendor role."}

#         # Get all vendor codes in a single optimized query
#         vendor_codes_query = """
#             SELECT DISTINCT cvc_child.vendor_code
#             FROM `tabVendor Master` vm
#             JOIN `tabMultiple Company Data` mcd ON mcd.parent = vm.name
#             JOIN `tabCompany Vendor Code` cvc ON cvc.name = mcd.company_vendor_code
#             JOIN `tabVendor Code` cvc_child ON cvc_child.parent = cvc.name
#             WHERE vm.office_email_primary = %(user)s
#             AND cvc_child.vendor_code IS NOT NULL
#             AND cvc_child.vendor_code != ''
#         """
        
#         vendor_codes_result = frappe.db.sql(vendor_codes_query, {"user": usr}, as_dict=True)
#         vendor_codes = [row.vendor_code for row in vendor_codes_result if row.vendor_code]

#         if not vendor_codes:
#             return {
#                 "status": "success",
#                 "message": "No vendor codes found for the user.",
#                 "total_count": 0,
#                 "page_no": int(page_no) if page_no else 1,
#                 "page_length": int(page_length) if page_length else 5,
#                 "total_po": [],
#                 "search_term": search
#             }

#         # Build query conditions
#         conditions = ["po.vendor_code IN %(vendor_codes)s"]
#         values = {"vendor_codes": vendor_codes}

#         if company:
#             conditions.append("po.company_code = %(company)s")
#             values["company"] = company
            
#         if status:
#             conditions.append("po.vendor_status = %(status)s")
#             values["status"] = status

#         if search:
#             conditions.append("(po.name LIKE %(search)s OR po.po_no LIKE %(search)s)")
#             values["search"] = f"%{search}%"

#         filter_clause = " AND ".join(conditions)

#         # Single optimized query with pagination and count
#         if search:
#             query = f"""
#                 SELECT 
#                     po.name,
#                     po.po_no,
#                     po.company_code,
#                     po.vendor_code,
#                     po.creation,
#                     po.modified,
#                     COUNT(*) OVER() as total_count,
#                     CASE 
#                         WHEN po.name LIKE %(search_start)s THEN 1
#                         WHEN po.po_no LIKE %(search_start)s THEN 2
#                         ELSE 3
#                     END as relevance
#                 FROM `tabPurchase Order` po
#                 WHERE {filter_clause}
#                 ORDER BY relevance, po.creation DESC
#                 LIMIT %(limit)s OFFSET %(offset)s
#             """
#             values["search_start"] = f"{search}%"
#         else:
#             query = f"""
#                 SELECT 
#                     po.name,
#                     po.po_no,
#                     po.company_code,
#                     po.vendor_code,
#                     po.creation,
#                     po.modified,
#                     COUNT(*) OVER() as total_count
#                 FROM `tabPurchase Order` po
#                 WHERE {filter_clause}
#                 ORDER BY po.creation DESC
#                 LIMIT %(limit)s OFFSET %(offset)s
#             """

#         # Pagination
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         values["limit"] = page_length
#         values["offset"] = (page_no - 1) * page_length

#         # Execute query
#         results = frappe.db.sql(query, values, as_dict=True)
        
#         total_count = results[0].total_count if results else 0
        
#         # Clean up results
#         po_docs = []
#         for result in results:
#             po_doc = {k: v for k, v in result.items() if k not in ['total_count', 'relevance']}
#             po_docs.append(po_doc)

#         return {
#             "status": "success",
#             "message": "Paginated and filtered po records fetched successfully.",
#             "total_count": total_count,
#             "page_no": page_no,
#             "page_length": page_length,
#             "total_po": po_docs,
#             "search_term": search,
#             "vendor_codes_count": len(vendor_codes)
#         }

#     except frappe.DoesNotExistError:
#         return {"status": "error", "message": "Vendor Master not found for the user."}
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_po_against_all_vc_optimized API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch po data.",
#             "error": str(e),
#             "po": []
#         }


# @frappe.whitelist()
# def get_all_vc_against_vendor_optimized():
#     """
#     Optimized function to get all vendor codes for a vendor user
#     """
#     user = frappe.session.user
    
#     # Single query to get all vendor code data
#     vendor_data_query = """
#         SELECT 
#             cvc.company_name,
#             cvc_child.state,
#             cvc_child.gst_no,
#             cvc_child.vendor_code
#         FROM `tabVendor Master` vm
#         JOIN `tabMultiple Company Data` mcd ON mcd.parent = vm.name
#         JOIN `tabCompany Vendor Code` cvc ON cvc.name = mcd.company_vendor_code
#         JOIN `tabVendor Code` cvc_child ON cvc_child.parent = cvc.name
#         WHERE vm.office_email_primary = %(user)s
#         AND cvc_child.vendor_code IS NOT NULL
#         AND cvc_child.vendor_code != ''
#         ORDER BY cvc.company_name, cvc_child.vendor_code
#     """
    
#     vendor_codes = frappe.db.sql(vendor_data_query, {"user": user}, as_dict=True)
    
#     return {
#         'vendor_codes': vendor_codes,
#         'designation': 'Vendor'
#     }


# def collect_vendor_code_data_optimized(vendor_doc):
#     """
#     Optimized version using single query instead of multiple document fetches
#     """
#     try:
#         # Single query to get all vendor code data for this vendor
#         query = """
#             SELECT 
#                 cvc.company_name,
#                 vc.state,
#                 vc.gst_no,
#                 vc.vendor_code
#             FROM `tabMultiple Company Data` mcd
#             JOIN `tabCompany Vendor Code` cvc ON cvc.name = mcd.company_vendor_code
#             JOIN `tabVendor Code` vc ON vc.parent = cvc.name
#             WHERE mcd.parent = %(vendor_name)s
#             AND vc.vendor_code IS NOT NULL
#             AND vc.vendor_code != ''
#         """
        
#         vendor_data = frappe.db.sql(query, {"vendor_name": vendor_doc.name}, as_dict=True)
        
#         return vendor_data
        
#     except Exception as e:
#         frappe.logger().error(f"Error in collect_vendor_code_data_optimized: {str(e)}")
#         return []


# # Additional performance optimization utility
# def create_database_indexes():
#     """
#     Create database indexes for better query performance
#     Run this once during deployment
#     """
#     indexes = [
#         "CREATE INDEX IF NOT EXISTS idx_po_vendor_code ON `tabPurchase Order` (vendor_code)",
#         "CREATE INDEX IF NOT EXISTS idx_po_company_code ON `tabPurchase Order` (company_code)", 
#         "CREATE INDEX IF NOT EXISTS idx_po_vendor_status ON `tabPurchase Order` (vendor_status)",
#         "CREATE INDEX IF NOT EXISTS idx_po_purchase_group ON `tabPurchase Order` (purchase_group)",
#         "CREATE INDEX IF NOT EXISTS idx_po_creation ON `tabPurchase Order` (creation DESC)",
#         "CREATE INDEX IF NOT EXISTS idx_po_search ON `tabPurchase Order` (name, po_no)",
#         "CREATE INDEX IF NOT EXISTS idx_employee_user_team ON `tabEmployee` (user_id, team)",
#         "CREATE INDEX IF NOT EXISTS idx_vendor_master_email ON `tabVendor Master` (office_email_primary)"
#     ]
    
#     for index_sql in indexes:
#         try:
#             frappe.db.sql(index_sql)
#             frappe.db.commit()
#         except Exception as e:
#             frappe.logger().error(f"Error creating index: {index_sql}, Error: {str(e)}")







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