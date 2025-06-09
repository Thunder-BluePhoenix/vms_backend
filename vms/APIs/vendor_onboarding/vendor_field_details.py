import frappe
from frappe import _

# Purchase Team Details
@frappe.whitelist(allow_guest=True)
def get_purchase_team_details(company_name=None):
    try:
        if not company_name:
            return {
                "status": "error",
                "message": "Please provide a company name."
            }
        
        user = frappe.session.user
        emp = frappe.get_doc("Employee", {"user_id": user})

        # Validate Company
        company = frappe.get_value("Company Master", {"name": company_name}, "name")
        if not company:
            return {
                "status": "error",
                "message": "Company not found."
            }

        # Fetch Purchase Organizations
        purchase_organizations = frappe.get_all(
            "Purchase Organization Master",
            filters={"company": company},
            fields=["name", "purchase_organization_name"]
        )

        # Fetch Purchase Groups
        purchase_groups = frappe.get_all(
            "Purchase Group Master",
            filters={"company": company, "team": emp.team},
            fields=["name", "purchase_group_name", "description"]
        )

        # Fetch Terms of Payment
        terms_of_payment = frappe.get_all(
            "Terms of Payment Master",
            filters={"company": company},
            fields=["name", "terms_of_payment_name", "description"]
        )

        return {
            "status": "success",
            "message": "Purchase team details fetched successfully.",
            "data": {
                "purchase_organizations": purchase_organizations,
                "purchase_groups": purchase_groups,
                "terms_of_payment": terms_of_payment
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Purchase Team Details Error")
        return {
            "status": "error",
            "message": "Failed to fetch purchase team details.",
            "error": str(e)
        }


# http://127.0.0.1:8003/api/method/vms.APIs.vendor_onboarding.vendor_field_details.get_purchase_team_details?company_name=Meril Healthcare Private Limited

@frappe.whitelist(allow_guest=True)
def account_group_details(purchase_organization=None):
    if not purchase_organization:
        return {
            "status": "error",
            "message": "Please provide a purchase organization."
        }

    account_group_master = frappe.get_all(
        "Account Group Master", 
        filters={"purchase_organization": purchase_organization},
        fields=["name", "account_group_name", "account_group_description"]
    )

    return account_group_master



    
# http://127.0.0.1:8003/api/method/vms.APIs.vendor_onboarding.vendor_field_details.account_group_details?purchase_organization=Meril Medical Import-2212

# @frappe.whitelist(allow_guest=True)
# def purchase_group_details(company_name=None):
#     if not company_name:
#         frappe.throw(_("Please provide a company name."))

#     company = frappe.get_value("Company Master", {"name": company_name}, "name")
#     if not company:
#         frappe.throw(_("Company not found."))

#     purchase_group_master = frappe.get_all(
#         "Purchase Group Master",
#         filters={"company": company},
#         fields=["name", "purchase_group_name", "description"]
#     )

#     return purchase_group_master

# @frappe.whitelist(allow_guest=True)
# def terms_of_payment_details(company_name=None):
#     if not company_name:
#         frappe.throw(_("Please provide a company name."))

#     # Validate company
#     company = frappe.get_value("Company Master", {"name": company_name}, "name")
#     if not company:
#         frappe.throw(_("Company not found."))

#     # Fetch terms of payment records
#     terms_of_payment_master = frappe.get_all(
#         "Terms of Payment Master",
#         filters={"company": company},
#         fields=["name", "terms_of_payment_name", "description"]
#     )

#     return terms_of_payment_master

