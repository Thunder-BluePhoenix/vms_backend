import frappe
import json

@frappe.whitelist(allow_guest=False)
def get_vendor_master_details(usr):
    try:
        # usr = frappe.session.user

        # Check if user has "Purchase Team" role
        roles = frappe.get_roles(usr)
        if "Purchase Team" not in roles:
            return {
                "status": "error",
                "message": "User does not have the 'Purchase Team' role.",
                "vendor_master": []
            }

        # Get team of the logged-in user from Employee
        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the logged-in user.",
                "vendor_master": []
            }

        # Get all users belonging to the same team
        team_users = frappe.get_all(
            "Employee",
            filters={"team": team},
            fields=["user_id"]
        )
        team_user_ids = [emp.user_id for emp in team_users if emp.user_id]

        if not team_user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_master": []
            }

        # Fetch Vendor Master records registered by users from the same team
        vendor_records = frappe.get_all(
            "Vendor Master",
            filters={"registered_by": ["in", team_user_ids]},
            fields=["*"]
        )

        return {
            "status": "success",
            "message": "Vendor Master records fetched successfully.",
            "team": team,
            "vendor_master": vendor_records
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Master Team Filter API Error")
        return {
            "status": "error",
            "message": "Failed to fetch Vendor Master records.",
            "error": str(e),
            "vendor_master": []
        }
