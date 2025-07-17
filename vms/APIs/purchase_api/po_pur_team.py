import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_all_po_for_team():
    try:
        usr = frappe.session.user
        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the logged-in user.",
                "vendor_count": 0
            }

        user_ids = frappe.get_all(
            "Employee",
            filters={"team": team},
            pluck="user_id"
        )


        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_count": 0
            }
        
        

        values = {"user_ids": user_ids}
        

        po_count = frappe.db.count(
            "Purchase Order",
            filters={"email": ["in", user_ids]}
        )


       

        
        return {
            "status": "success",
            "message": "PO DashBoard counts fetched successfully.",
            # "role": user_roles,
            "team": team,
            "po_count": po_count,
            
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO DashBoard Card API Error")
        return {
            "status": "error",
            "message": "Failed to fetch PO DashBoard data.",
            "error": str(e),
            "vendor_count": 0
        }

 
    