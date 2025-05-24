from frappe.utils import today, get_first_day, get_last_day
import frappe
import json

@frappe.whitelist(allow_guest=False)
def get_vendors_details(usr):
    try:
        # usr = frappe.session.user

        # Check if user has role
        roles = frappe.get_roles(usr)
        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        if not any(role in allowed_roles for role in roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
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
        user_ids = [emp.user_id for emp in team_users if emp.user_id]

        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_master": []
            }

        vendor_docs = frappe.get_all(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids]},
            fields=["name"]
        )

        vendor_master_data = []
        vendor_onboarding_data = []

        for doc in vendor_docs:
            vendor_master_doc = frappe.get_doc("Vendor Master", doc.name)
            vendor_master_data.append(vendor_master_doc.as_dict())

            onboarding_docs = frappe.get_all(
                "Vendor Onboarding",
                filters={"ref_no": doc.name},
                fields=["name"]
            )

            for onboarding in onboarding_docs:
                onboarding_doc = frappe.get_doc("Vendor Onboarding", onboarding.name)
                vendor_onboarding_data.append(onboarding_doc.as_dict())


        return {
            "status": "success",
            "message": "Vendor Master records fetched successfully.",
            "role": roles,
            "team": team,
            "vendor_master": vendor_master_data,
            "vendor_onboarding": vendor_onboarding_data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Master Team Filter API Error")
        return {
            "status": "error",
            "message": "Failed to fetch Vendor Master records.",
            "error": str(e),
            "vendor_master": []
        }


@frappe.whitelist(allow_guest=False)
def dashboard_card(usr):
    try:
        # Check if user has "Purchase Team" role
        roles = frappe.get_roles(usr)
        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        if not any(role in allowed_roles for role in roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_master": []
            }

        # Get team of the logged-in user from Employee
        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the logged-in user.",
                "vendor_count": 0
            }

        # Get all users belonging to the same team
        team_users = frappe.get_all(
            "Employee",
            filters={"team": team},
            fields=["user_id"]
        )
        user_ids = [emp.user_id for emp in team_users if emp.user_id]

        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_count": 0
            }

        # Count Vendor Master records created by users from the same team
        total_vendor_count = frappe.db.count(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids]}
        )

        pending_vendor_count = frappe.db.count(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids], "status": "pending"}
        )

        approved_vendor_count = frappe.db.count(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids], "status": "approved"}
        )

        start_date = get_first_day(today())
        end_date = get_last_day(today())

        current_month_vendor = frappe.db.count(
            "Vendor Master",
            filters={
                "registered_by": ["in", user_ids],
                "registered_date": ["between", [start_date, end_date]]
            }
        )

        return {
            "status": "success",
            "message": "Vendor Master record count fetched successfully.",
            "role": roles,
            "team": team,
            "total_vendor_count": total_vendor_count,
            "pending_vendor_count": pending_vendor_count,
            "approved_vendor_count": approved_vendor_count,
            "current_month_vendor": current_month_vendor
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Master Dashboard Card API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor master count.",
            "error": str(e),
            "vendor_count": 0
        }
    

# get vendor onboarding vendor details based on status
import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_vendors_based_on_status(usr):
    try:
        # Validate role
        roles = frappe.get_roles(usr)
        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        if not any(role in allowed_roles for role in roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_master": [],
                "vendor_onboarding": {}
            }

        # Get employee's team
        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the logged-in user.",
                "vendor_master": [],
                "vendor_onboarding": {}
            }

        # Get users in same team
        user_ids = frappe.get_all(
            "Employee",
            filters={"team": team},
            pluck="user_id"
        )
        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_master": [],
                "vendor_onboarding": {}
            }

        # Get vendor master records
        vendor_docs = frappe.get_all(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids]},
            fields=["name"]
        )

        vendor_master_data = []
        vendor_onboarding_data = {
            "approved_vendor_onb": [],
            "pending_vendor_onb": [],
            "rejected_vendor_onb": []
        }

        for vendor in vendor_docs:
            vendor_master_doc = frappe.get_doc("Vendor Master", vendor.name)
            vendor_master_data.append(vendor_master_doc.as_dict())

            onboarding_docs = frappe.get_all(
                "Vendor Onboarding",
                filters={"ref_no": vendor.name},
                fields=["name", "onboarding_form_status"]
            )

            for onboarding in onboarding_docs:
                doc = frappe.get_doc("Vendor Onboarding", onboarding.name)
                status = (doc.onboarding_form_status or "").lower().strip()

                if status == "approved":
                    vendor_onboarding_data["approved_vendor_onb"].append(doc.as_dict())
                elif status == "rejected":
                    vendor_onboarding_data["rejected_vendor_onb"].append(doc.as_dict())
                elif status == "pending":
                    vendor_onboarding_data["pending_vendor_onb"].append(doc.as_dict())
                # elif status == "expired":
                #     vendor_onboarding_data["expired_vendor_onb"].append(doc.as_dict())

        return {
            "status": "success",
            "message": "Vendor Onboarding data grouped by status.",
            "role": roles,
            "team": team,
            "vendor_master": vendor_master_data,
            "vendor_onboarding": vendor_onboarding_data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Master Status Filter API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding data.",
            "error": str(e),
            "vendor_master": [],
            "vendor_onboarding": {}
        }
