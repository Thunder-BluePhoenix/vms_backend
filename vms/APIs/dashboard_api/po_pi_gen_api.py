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
            return normal_data_for_employee(usr)



            # return {
            #     "status": "error",
            #     "message": "User does not have the required role.",
            #     "vendor_master": []
            # }

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



def normal_data_for_employee(usr):
    cart_count = frappe.db.count("Cart Details")
    pr_count = frappe.db.count("Purchase Requisition Webform")

    user_cart_count = frappe.db.count("Cart Details",
                                filters= {"user":usr })
    
    user_pr_count = frappe.db.count("Purchase Requisition Webform",
                                filters= {"requisitioner":usr })
    
    return {
            "status": "success",
            "message": "dashboard counts fetched successfully.",
            
            "cart_count":user_cart_count,
            "pr_count":user_pr_count,
            "all_carts":cart_count,
            "all_pr_count":pr_count
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
                "company_name": ["in", company_list],
                "purchase_head_undertaking": 1
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
        cart_count = frappe.db.count("Cart Details",
                                    filters= {"user":usr })
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



        pending_vendor_count = []
        if "Purchase Head" in user_roles:
            
            pending_vendor_count = frappe.db.count(
                "Vendor Onboarding",
                filters={"registered_by": ["in", user_ids], "onboarding_form_status": "Pending", "purchase_team_undertaking": 1}
            )
        else:
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
        # cart_count = frappe.db.count("Cart Details")
        cart_query = """
            SELECT COUNT(*)
            FROM `tabCart Details` cd
            JOIN `tabCategory Master` cc ON cd.category_type = cc.name
            WHERE cc.purchase_team_user = %s
        """

        cart_count = frappe.db.sql(cart_query, (usr,))[0][0]
        pr_count = frappe.db.count("Purchase Requisition Webform")

        user_cart_count = frappe.db.count("Cart Details",
                                    filters= {"user":usr })
        
        user_pr_count = frappe.db.count("Purchase Requisition Webform",
                                    filters= {"requisitioner":usr })
        # cart_count = len(all_cart)

        # Count of Vendor Master records created by users from the same team.requisitioner
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
            "pr_count":pr_count,
            "all_carts":user_cart_count,
            "all_pr_count":user_pr_count
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Dashboard Card API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding dashboard data.",
            "error": str(e),
            "vendor_count": 0
        }

 
    














@frappe.whitelist(allow_guest=True)
def get_pi_for_pt(purchase_team_user=None):
   
    
    
    purchase_team_user = frappe.session.user
    cart_categories = frappe.get_all("Category Master",
                                     filters={"purchase_team_user": purchase_team_user},
                                     fields=["name"])
    cart_category_names = [c.name for c in cart_categories]
    
    if not cart_category_names:
        return []
    
    all_pi = frappe.get_all("Cart Details",
                           filters={"category_type": ("in", cart_category_names)},
                           order_by="modified desc",
                           fields="*")
    
    return all_pi








@frappe.whitelist(allow_guest = True)
def get_pi():
    try:
        usr = frappe.session.user
        if not usr:
            return {"error": _("User not logged in.")}

        allowed_roles = {"Purchase Team"}
        user_roles = set(frappe.get_roles(usr))

        if allowed_roles.intersection(user_roles):
            return get_pi_for_pt(purchase_team_user=usr)
        else:
            all_pi = frappe.get_all("Cart Details",
                                    filters={"user": usr},
                                    fields="*",
                                    order_by="modified desc")
            return all_pi

    except Exception as e:
        # Log the error and return a message
        frappe.log_error(message=str(e), title="Error in get_pi API")
        return {"error": _("Something went wrong. Please try again later.")}




@frappe.whitelist(allow_guest=True)
def get_pi_details(pi_name):
    try:
        # Fetch the PI (Cart Details) document
        pi = frappe.get_doc("Cart Details", pi_name)
        user = frappe.session.user

        # Get employee linked to the current user
        employee = frappe.get_doc("Employee", {"user_id": user})

        # Get cart owner employee
        cart_owner_emp = frappe.get_doc("Employee", {"user_id": pi.user})
        hod = 0
        if cart_owner_emp.reports_to == employee.name:
            hod = 1

        # Get category type and purchase team user
        cat_type = frappe.get_doc("Category Master", pi.category_type)
        purchase_team = 0
        if cat_type.purchase_team_user:
            try:
                cart_team_emp = frappe.get_doc("Employee", {"user_id": cat_type.purchase_team_user})
                if cart_team_emp.name == employee.name:
                    purchase_team = 1
            except frappe.DoesNotExistError:
                pass  # Skip if purchase team user does not map to Employee

        # Return all necessary info
        pi_dict = pi.as_dict()
        pi_dict.update({
            "hod": hod,
            "purchase_team": purchase_team
        })

        return pi_dict

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_pi_details Error")
        frappe.throw(_("An unexpected error occurred while fetching PI details."))



@frappe.whitelist(allow_guest = True)
def get_pr_w():
    pr_w = frappe.get_all("Purchase Requisition Webform", fields ="*", order_by = "modified desc")
    return pr_w




@frappe.whitelist(allow_guest=True)
def get_pr_w_details(pr_w_name):
    try:
        pr_w = frappe.get_doc("Purchase Requisition Webform", pr_w_name)
        user = frappe.session.user

        employee = frappe.get_doc("Employee", {"user_id": user})
        pr_owner_emp = frappe.get_doc("Employee", {"user_id": pr_w.requisitioner})

        # Check if current employee is HOD of requisitioner
        hod = 1 if pr_owner_emp.reports_to == employee.name else 0

        # Check if current employee is purchase head of the purchase group
        pr_grp = frappe.get_doc("Purchase Group Master", pr_w.purchase_group)
        purchase_head = 0
        if employee.team == pr_grp.team and employee.designation == "Purchase Head":
            purchase_head = 1

        # Prepare response
        prw_dict = pr_w.as_dict()
        prw_dict.update({
            "hod": hod,
            "purchase_head": purchase_head
        })

        return prw_dict

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_pr_w_details Error")
        frappe.throw(_("An unexpected error occurred while fetching Purchase Requisition details."))
