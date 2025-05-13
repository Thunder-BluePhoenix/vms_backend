import frappe

# Purchase Team Details
@frappe.whitelist(allow_guest=True)
def purchase_organisation_details(company_name=None):
    if not company_name:
        frappe.throw("Please provide a company name.")

    company = frappe.get_value("Company Master", {"name": company_name}, "name")
    if not company:
        return []

    purchase_organizations = frappe.get_all(
        "Purchase Organization Master",
        filters={"company": company},
        fields=["name", "purchase_organization_name"]
    )

    return purchase_organizations

# http://127.0.0.1:8003/api/method/vms.APIs.vendor_onboarding.vendor_field_details.purchase_organisation_details?company_name=Meril Healthcare Private Limited

@frappe.whitelist(allow_guest=True)
def account_group_details(purchase_organization=None):
    if not purchase_organization:
        frappe.throw("Please provide a purchase organization name.")

    account_group_master = frappe.get_all(
        "Account Group Master", 
        filters={"purchase_organization": purchase_organization},
        fields=["name", "account_group_name"]
    )

    return account_group_master
    
# http://127.0.0.1:8003/api/method/vms.APIs.vendor_onboarding.vendor_field_details.account_group_details?purchase_organization=Expenses-1213

@frappe.whitelist(allow_guest=True)
def purchase_group_details(company_name=None):
    if not company_name:
        frappe.throw(_("Please provide a company name."))

    company = frappe.get_value("Company Master", {"name": company_name}, "name")
    if not company:
        frappe.throw(_("Company not found."))

    purchase_group_master = frappe.get_all(
        "Purchase Group Master",
        filters={"company": company},
        fields=["name", "purchase_group_name", "description"]
    )

    return purchase_group_master

# http://127.0.0.1:8003/api/method/vms.APIs.vendor_onboarding.vendor_field_details.purchase_group_details?company_name=Meril Endo

@frappe.whitelist(allow_guest=True)
def terms_of_payment_details(company_name=None):
    if not company_name:
        frappe.throw(_("Please provide a company name."))

    # Validate company
    company = frappe.get_value("Company Master", {"name": company_name}, "name")
    if not company:
        frappe.throw(_("Company not found."))

    # Fetch terms of payment records
    terms_of_payment_master = frappe.get_all(
        "Terms of Payment Master",
        filters={"company": company},
        fields=["name", "terms_of_payment_name", "description"]
    )

    return terms_of_payment_master

# http://127.0.0.1:8003/api/method/vms.APIs.vendor_onboarding.vendor_field_details.terms_of_payment_details?company_name=Meril Endo

