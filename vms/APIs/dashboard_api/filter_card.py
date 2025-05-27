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

# get vendor onboarding details based on status with limited fields

# approved vendor details
@frappe.whitelist(allow_guest=False)
def approved_vendor_details(usr):
    try:
        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "vendor_onboarding": []
            }

        user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_onboarding": []
            }

        vendor_names = frappe.get_all(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids]},
            pluck="name"
        )
        if not vendor_names:
            return {
                "status": "error",
                "message": "No vendor records found for this team.",
                "vendor_onboarding": []
            }

        onboarding_docs = frappe.get_all(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names]},
            fields=["name", "onboarding_form_status"]
        )

        approved_vendors = []
        for onboarding in onboarding_docs:
            if (onboarding.onboarding_form_status or "").lower().strip() == "approved":
                doc = frappe.get_doc("Vendor Onboarding", onboarding.name)
                approved_vendors.append(doc.as_dict())

        if not approved_vendors:
            return {
                "status": "error",
                "message": "No approved vendor onboarding records found.",
                "vendor_onboarding": []
            }

        return {
            "status": "success",
            "message": "Approved vendor onboarding records fetched successfully.",
            "vendor_onboarding": approved_vendors
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Approved Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch approved vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }


# rejected vendor details

@frappe.whitelist(allow_guest=False)
def rejected_vendor_details(usr):
    try:
        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "vendor_onboarding": []
            }

        user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_onboarding": []
            }

        vendor_names = frappe.get_all(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids]},
            pluck="name"
        )
        if not vendor_names:
            return {
                "status": "error",
                "message": "No vendor records found for this team.",
                "vendor_onboarding": []
            }

        onboarding_docs = frappe.get_all(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names]},
            fields=["name", "onboarding_form_status"]
        )

        rejected_vendors = []
        for onboarding in onboarding_docs:
            if (onboarding.onboarding_form_status or "").lower().strip() == "rejected":
                doc = frappe.get_doc("Vendor Onboarding", onboarding.name)
                rejected_vendors.append(doc.as_dict())

        if not rejected_vendors:
            return {
                "status": "error",
                "message": "No rejected vendor onboarding records found.",
                "vendor_onboarding": []
            }

        return {
            "status": "success",
            "message": "Rejected vendor onboarding records fetched successfully.",
            "vendor_onboarding": rejected_vendors
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Rejected Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch rejected vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }
    

# pending vendor details

@frappe.whitelist(allow_guest=False)
def pending_vendor_details(usr):
    try:
        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "vendor_onboarding": []
            }

        user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_onboarding": []
            }

        vendor_names = frappe.get_all(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids]},
            pluck="name"
        )
        if not vendor_names:
            return {
                "status": "error",
                "message": "No vendor records found for this team.",
                "vendor_onboarding": []
            }

        onboarding_docs = frappe.get_all(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names]},
            fields=["name", "onboarding_form_status"]
        )

        pending_vendors = []
        for onboarding in onboarding_docs:
            if (onboarding.onboarding_form_status or "").lower().strip() == "pending":
                doc = frappe.get_doc("Vendor Onboarding", onboarding.name)
                pending_vendors.append(doc.as_dict())

        if not pending_vendors:
            return {
                "status": "error",
                "message": "No Pending vendor onboarding records found.",
                "vendor_onboarding": []
            }

        return {
            "status": "success",
            "message": "Pending vendor onboarding records fetched successfully.",
            "vendor_onboarding": pending_vendors
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Pending Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch Pending vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }
    

# Expired vendor details

@frappe.whitelist(allow_guest=False)
def expired_vendor_details(usr):
    try:
        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
        if not team:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "vendor_onboarding": []
            }

        user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
        if not user_ids:
            return {
                "status": "error",
                "message": "No users found in the same team.",
                "vendor_onboarding": []
            }

        vendor_names = frappe.get_all(
            "Vendor Master",
            filters={"registered_by": ["in", user_ids]},
            pluck="name"
        )
        if not vendor_names:
            return {
                "status": "error",
                "message": "No vendor records found for this team.",
                "vendor_onboarding": []
            }

        onboarding_docs = frappe.get_all(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names]},
            fields=["name", "onboarding_form_status"]
        )

        expired_vendors = []
        for onboarding in onboarding_docs:
            if (onboarding.onboarding_form_status or "").lower().strip() == "expired":
                doc = frappe.get_doc("Vendor Onboarding", onboarding.name)
                expired_vendors.append(doc.as_dict())

        if not expired_vendors:
            return {
                "status": "error",
                "message": "No Expired vendor onboarding records found.",
                "vendor_onboarding": []
            }

        return {
            "status": "success",
            "message": "Expired vendor onboarding records fetched successfully.",
            "vendor_onboarding": expired_vendors
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Expired Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch Expired vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }