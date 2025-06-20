import frappe
from frappe import _





from frappe.utils import today, get_first_day, get_last_day
import frappe
import json

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

        if "Accounts Team" in user_roles:
            return vendor_data_for_accounts(usr, user_roles)
        else:
            return vendor_data_for_purchase(usr, user_roles)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Dashboard API Error")
        return {
            "status": "error",
            "message": "Unexpected error occurred in dashboard_card.",
            "error": str(e)
        }


def vendor_data_for_accounts(usr, user_roles):  
    try:
        employee = frappe.get_doc("Employee", {"user_id": usr})
        company_list = [row.company_name for row in employee.company]

        if not company_list:
            return {
                "status": "error",
                "message": "No company records found in Employee.",
                "vendor_count": 0
            }

        # vendor_onboarding = frappe.get_all(
        #     "Vendor Onboarding",
        #     filters={"company_name": ["in", company_list]},
        #     pluck="ref_no"
        # )

        values = {"company_list": company_list}
        total_vendor_count = frappe.db.sql("""
            SELECT COUNT(*) FROM (
                SELECT ref_no FROM `tabVendor Onboarding`
                WHERE company_name IN %(company_list)s
                GROUP BY ref_no
            ) AS grouped
        """, values)[0][0]

        start_date = get_first_day(today())
        end_date = get_last_day(today())

        # total_vendor_count = frappe.db.count(
        #     "Vendor Master",
        #     filters={"name": ["in", vendor_onboarding]}
        # )

        approved_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={
                "onboarding_form_status": "Approved",
                "company_name": ["in", company_list]
            }
        )

        pending_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={
                "onboarding_form_status": "Pending",
                "company_name": ["in", company_list]
            }
        )

        rejected_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={
                "onboarding_form_status": "Rejected",
                "company_name": ["in", company_list]
            }
        )

        expired_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={
                "onboarding_form_status": "Expired",
                "company_name": ["in", company_list]
            }
        )

        current_month_vendor = frappe.db.count(
            "Vendor Onboarding",
            filters={
                "creation": ["between", [start_date, end_date]],
                "company_name": ["in", company_list]
            }
        )
        cart_count = frappe.db.count("Cart Details")
        pr_count = frappe.db.count("Purchase Requisition Webform")

        return {
            "status": "success",
            "message": "Vendor Onboarding dashboard counts fetched successfully.",
            "role": user_roles,
            "companies": company_list,
            "total_vendor_count": total_vendor_count,
            "pending_vendor_count": pending_vendor_count,
            "approved_vendor_count": approved_vendor_count,
            "rejected_vendor_count": rejected_vendor_count,
            "expired_vendor_count": expired_vendor_count,
            "current_month_vendor": current_month_vendor,
            "cart_count": cart_count,
            "pr_count":pr_count
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Dashboard Card API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding dashboard data.",
            "error": str(e),
            "vendor_count": 0
        }


def vendor_data_for_purchase(usr, user_roles):
    try:
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
        
        # vendor_names = frappe.get_all(
        #     "Vendor Master",
        #     filters={"registered_by": ["in", user_ids]},
        #     pluck="name"
        # )

        # if not vendor_names:
        #     return {
        #         "status": "error",
        #         "message": "No vendor records found for this team.",
        #         "vendor_onboarding": []
        #     }

        # Dates for current month
        start_date = get_first_day(today())
        end_date = get_last_day(today())

        # Count of Vendor Onboarding records by status
        # total_vendor_count = frappe.db.count(
        #     "Vendor Onboarding",
        #     filters={"ref_no": ["in", vendor_names]}
        # )

        values = {"user_ids": user_ids}
        total_vendor_count = frappe.db.sql("""
            SELECT COUNT(*) FROM (
                SELECT ref_no FROM `tabVendor Onboarding`
                WHERE registered_by IN %(user_ids)s
                GROUP BY ref_no
            ) AS grouped
        """, values)[0][0]

        approved_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"registered_by": ["in", user_ids], "onboarding_form_status": "Approved"}
        )

        pending_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"registered_by": ["in", user_ids], "onboarding_form_status": "Pending"}
        )

        rejected_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"registered_by": ["in", user_ids], "onboarding_form_status": "Rejected"}
        )

        expired_vendor_count = frappe.db.count(
            "Vendor Onboarding",
            filters={"registered_by": ["in", user_ids], "onboarding_form_status": "Expired"}
        )

        current_month_vendor = frappe.db.count(
            "Vendor Onboarding",
            filters={
                "registered_by": ["in", user_ids],
                "creation": ["between", [start_date, end_date]]
            }
        )
        cart_count = frappe.db.count("Cart Details")
        pr_count = frappe.db.count("Purchase Requisition Webform")
        # cart_count = len(all_cart)

        # Count of Vendor Master records created by users from the same team
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
            "current_month_vendor": current_month_vendor,
            "cart_count":cart_count,
            "pr_count":pr_count
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Dashboard Card API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding dashboard data.",
            "error": str(e),
            "vendor_count": 0
        }

 
    
























@frappe.whitelist(allow_guest = True)
def get_pi():
    all_pi = frappe.get_all("Cart Details", fields ="*", order_by = "modified desc")
    return all_pi



@frappe.whitelist(allow_guest = True)
def get_pi_details(pi_name):
    # po_name = data.get("po_name")
    pi = frappe.get_doc("Cart Details", pi_name)
    return pi.as_dict()


@frappe.whitelist(allow_guest = True)
def get_pr_w():
    pr_w = frappe.get_all("Purchase Requisition Webform", fields ="*", order_by = "modified desc")
    return pr_w



@frappe.whitelist(allow_guest = True)
def get_pr_w_details(pr_w_name):
    # po_name = data.get("po_name")
    pr_w = frappe.get_doc("Purchase Requisition Webform", pr_w_name)
    return pr_w.as_dict()