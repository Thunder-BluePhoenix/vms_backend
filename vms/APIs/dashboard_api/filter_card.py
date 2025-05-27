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

# count of vendor onboarding based on status
@frappe.whitelist(allow_guest=False)
def dashboard_card(usr):
    try:

        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_master": []
            }


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

        # Dates for current month
        start_date = get_first_day(today())
        end_date = get_last_day(today())

        # Count Vendor Onboarding records by status
        total_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names]}
        )

        approved_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names], "onboarding_form_status": "Approved"}
        )

        pending_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names], "onboarding_form_status": "Pending"}
        )

        rejected_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names], "onboarding_form_status": "Rejected"}
        )

        expired_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"ref_no": ["in", vendor_names], "onboarding_form_status": "Expired"}
        )

        current_month_vendor = frappe.db.count(
            "Vendor Onboarding",
            filters={
                "ref_no": ["in", vendor_names],
                "creation": ["between", [start_date, end_date]]
            }
        )

        # Count Vendor Master records created by users from the same team
        # total_vendor_count = frappe.db.count(
        #     "Vendor Master",
        #     filters={"registered_by": ["in", user_ids]}
        # )

        # pending_vendor_count = frappe.db.count(
        #     "Vendor Master",
        #     filters={"registered_by": ["in", user_ids], "status": "pending"}
        # )

        # approved_vendor_count = frappe.db.count(
        #     "Vendor Master",
        #     filters={"registered_by": ["in", user_ids], "status": "approved"}
        # )

        # rejected_vendor_count = frappe.db.count(
        #     "Vendor Master",
        #     filters={"registered_by": ["in", user_ids], "status": "rejected"}
        # )

        # expired_vendor_count = frappe.db.count(
        #     "Vendor Master",
        #     filters={"registered_by": ["in", user_ids], "status": "expired"}
        # )

        # start_date = get_first_day(today())
        # end_date = get_last_day(today())

        # current_month_vendor = frappe.db.count(
        #     "Vendor Master",
        #     filters={
        #         "registered_by": ["in", user_ids],
        #         "registered_date": ["between", [start_date, end_date]]
        #     }
        # )

        return {
            "status": "success",
            "message": "Vendor Onboarding dashboard counts fetched successfully.",
            "role": user_roles,
            "team": team,
            "total_vendor_count": total_vendor_count,
            "pending_vendor_count": pending_vendor_count,
            "approved_vendor_count": approved_vendor_count,
            "rejected_vendor_count": rejected_vendor_count,
            "expired_vendor_count": expired_vendor_count,
            "current_month_vendor": current_month_vendor
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Dashboard Card API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding dashboard data.",
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
            filters={
                "ref_no": ["in", vendor_names],
                "onboarding_form_status": "Approved"
            },
            fields=[
                "name", "ref_no", "company_name", "vendor_name", "onboarding_form_status",
                "purchase_t_approval", "accounts_t_approval", "purchase_h_approval",
                "mandatory_data_filled", "purchase_team_undertaking", "accounts_team_undertaking", "purchase_head_undertaking",
                "form_fully_submitted_by_vendor", "sent_registration_email_link", "rejected", "data_sent_to_sap", "expired",
                "payee_in_document", "check_double_invoice", "gr_based_inv_ver", "service_based_inv_ver"
            ]
        )

        return {
            "status": "success",
            "message": "Approved vendor onboarding records fetched successfully.",
            "approved_vendor_onboarding": onboarding_docs
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
            filters={
                "ref_no": ["in", vendor_names],
                "onboarding_form_status": "Rejected"
            },
            fields=[
                "name", "ref_no", "company_name", "vendor_name", "onboarding_form_status",
                "purchase_t_approval", "accounts_t_approval", "purchase_h_approval",
                "mandatory_data_filled", "purchase_team_undertaking", "accounts_team_undertaking", "purchase_head_undertaking",
                "form_fully_submitted_by_vendor", "sent_registration_email_link", "rejected", "data_sent_to_sap", "expired",
                "payee_in_document", "check_double_invoice", "gr_based_inv_ver", "service_based_inv_ver"
            ]
        )
        
        return {
            "status": "success",
            "message": "Rejected vendor onboarding records fetched successfully.",
            "rejected_vendor_onboarding": onboarding_docs
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
            filters={
                "ref_no": ["in", vendor_names],
                "onboarding_form_status": "Pending"
            },
            fields=[
                "name", "ref_no", "company_name", "vendor_name", "onboarding_form_status",
                "purchase_t_approval", "accounts_t_approval", "purchase_h_approval",
                "mandatory_data_filled", "purchase_team_undertaking", "accounts_team_undertaking", "purchase_head_undertaking",
                "form_fully_submitted_by_vendor", "sent_registration_email_link", "rejected", "data_sent_to_sap", "expired",
                "payee_in_document", "check_double_invoice", "gr_based_inv_ver", "service_based_inv_ver"
            ]
        )

        return {
            "status": "success",
            "message": "Pending vendor onboarding records fetched successfully.",
            "pending_vendor_onboarding": onboarding_docs
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Pending Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch pending vendor onboarding data.",
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
            filters={
                "ref_no": ["in", vendor_names],
                "onboarding_form_status": "Expired"
            },
            fields=[
                "name", "ref_no", "company_name", "vendor_name", "onboarding_form_status",
                "purchase_t_approval", "accounts_t_approval", "purchase_h_approval",
                "mandatory_data_filled", "purchase_team_undertaking", "accounts_team_undertaking", "purchase_head_undertaking",
                "form_fully_submitted_by_vendor", "sent_registration_email_link", "rejected", "data_sent_to_sap", "expired",
                "payee_in_document", "check_double_invoice", "gr_based_inv_ver", "service_based_inv_ver"
            ]
        )

        return {
            "status": "success",
            "message": "Expired vendor onboarding records fetched successfully.",
            "expired_vendor_onboarding": onboarding_docs
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Expired Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch expired vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }

# Total vendor details

@frappe.whitelist(allow_guest=False)
def total_vendor_details(usr):
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
            filters={
                "ref_no": ["in", vendor_names]
            },
            fields=[
                "name", "ref_no", "company_name", "vendor_name", "onboarding_form_status",
                "purchase_t_approval", "accounts_t_approval", "purchase_h_approval",
                "mandatory_data_filled", "purchase_team_undertaking", "accounts_team_undertaking", "purchase_head_undertaking",
                "form_fully_submitted_by_vendor", "sent_registration_email_link", "rejected", "data_sent_to_sap", "expired",
                "payee_in_document", "check_double_invoice", "gr_based_inv_ver", "service_based_inv_ver"
            ]
        )

        return {
            "status": "success",
            "message": "Approved vendor onboarding records fetched successfully.",
            "total_vendor_onboarding": onboarding_docs
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Approved Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch approved vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }


# current month vendor details

@frappe.whitelist(allow_guest=False)
def current_month_vendor_details(usr):
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

        # Get start and end of current month
        start_date = get_first_day(today())
        end_date = get_last_day(today())

        # Fetch onboarding records created in current month
        onboarding_docs = frappe.get_all(
            "Vendor Onboarding",
            filters={
                "ref_no": ["in", vendor_names],
                "creation": ["between", [start_date, end_date]]
            },
            fields=[
                "name", "ref_no", "company_name", "vendor_name", "onboarding_form_status",
                "purchase_t_approval", "accounts_t_approval", "purchase_h_approval",
                "mandatory_data_filled", "purchase_team_undertaking", "accounts_team_undertaking", "purchase_head_undertaking",
                "form_fully_submitted_by_vendor", "sent_registration_email_link", "rejected", "data_sent_to_sap", "expired",
                "payee_in_document", "check_double_invoice", "gr_based_inv_ver", "service_based_inv_ver"
            ]
        )

        return {
            "status": "success",
            "message": "Vendor onboarding records for the current month fetched successfully.",
            "vendor_onboarding": onboarding_docs
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Current Month Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }

    
    