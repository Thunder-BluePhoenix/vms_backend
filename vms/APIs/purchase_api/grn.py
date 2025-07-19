import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_grn_for_team_direct(page_no=None, page_length=None):
    try:
        usr = frappe.session.user
        
        # Get employee team
        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the logged-in user.",
                "grn_details": [],
                "total_count": 0,
                "page_no": 1,
                "page_length": 5
            }

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        start = (page_no - 1) * page_length

        # Get GRNs with pagination directly from database
        grn_data = frappe.db.sql("""
            SELECT grn.name, grn.*, 
                   COUNT(*) OVER() as total_count
            FROM `tabGRN` grn
            INNER JOIN `tabGRN Items` git ON git.parent = grn.name
            INNER JOIN `tabPurchase Order` po ON git.po_no = po.name
            INNER JOIN `tabPurchase Group Master` pgm ON po.purchase_group = pgm.name
            WHERE pgm.team = %(team)s
            GROUP BY grn.name
            ORDER BY grn.modified DESC
            LIMIT %(page_length)s OFFSET %(start)s
        """, {
            "team": team,
            "page_length": page_length,
            "start": start
        }, as_dict=True)

        if not grn_data:
            return {
                "status": "success",
                "message": "No GRNs found with matching team Purchase Orders.",
                "grn_details": [],
                "total_count": 0,
                "page_no": page_no,
                "page_length": page_length
            }

        # Get total count from first row
        total_count = grn_data[0].get('total_count', 0) if grn_data else 0

        # Get full GRN documents with child tables
        grn_details = []
        for grn_row in grn_data:
            grn_doc = frappe.get_doc("GRN", grn_row.name)
            grn_details.append(grn_doc.as_dict())

        return {
            "status": "success",
            "message": "GRN details fetched successfully.",
            "grn_details": grn_details,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "team": team
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get GRN for Team Direct API Error")
        return {
            "status": "error",
            "message": "Failed to fetch GRN details.",
            "error": str(e),
            "grn_details": [],
            "total_count": 0,
            "page_no": int(page_no) if page_no else 1,
            "page_length": int(page_length) if page_length else 5
        }