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
            fields=["name", "purchase_organization_name", "description", "org_type"]
        )

        # Fetch Purchase Groups

        purchase_groups = []
        if emp.show_all_purchase_groups == 1:
            purchase_groups = frappe.get_all(
                "Purchase Group Master",
                filters={"company": company},
                fields=["name", "purchase_group_name", "description"]
            )
        else:
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
def account_group_details(data):
    purchase_organization = data.get("purchase_organization")
    vendor_types = data.get("vendor_types")
    if not purchase_organization:
        return {
            "status": "error",
            "message": "Please provide a purchase organization."
        }


    pur_doc = frappe.get_doc("Purchase Organization Master", purchase_organization)
    org_type = pur_doc.org_type
    
    
    # all_account_group = []
    # all_account_groups = []

    # for vendor_type in vendor_types:
    #     account_groups = frappe.get_all(
    #         "Account Group Master", 
    #         filters={
    #             "purchase_organization": purchase_organization, 
    #             "vendor_type": vendor_type
    #         },
    #         fields=["name", "account_group_name", "account_group_description"]
    #     )
    #     all_account_groups.extend(account_groups)
    all_account_groups = set()

    # Get all Account Group Master records that match the purchase_organization
    account_groups = frappe.get_all(
        "Account Group Master",
        filters={"purchase_organization": purchase_organization},
        fields=["name", "account_group_name", "account_group_description"]
    )

    for group in account_groups:
        # Fetch child table entries for vendor_type (e.g., "Vendor Type Child")
        vendor_type_children = frappe.get_all(
            "Vendor Type for Account",  # replace with actual child table doctype name
            filters={"parent": group.name, "vendor_type_ac": ["in", vendor_types]},
            fields=["vendor_type_ac"]
        )

        if vendor_type_children:
            # Add as tuple to make it hashable for set
            all_account_groups.add((
                group.name,
                group.account_group_name,
                group.account_group_description
            ))

    # Optional: Convert set to list of dicts if needed
    all_account_groups_list = [
        {
            "name": name,
            "account_group_name": agn,
            "account_group_description": agd
        }
        for name, agn, agd in all_account_groups
    ]


   
    # all_account_groups.append(all_account_group)
    # org_data = ["org_type": org_type]
    # all_account_groups.extend(org_type)


    return {"all_account_groups":all_account_groups_list,
            "org_type":org_type}



    
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

