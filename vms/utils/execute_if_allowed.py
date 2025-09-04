import frappe

allowed_sales_organisations = [
    "8100",
    "1211",
    "3100",
    "9100",
    "9200",
    "SA01",
    "7100",
    "SA03",
]


def execute_if_allowed(method, sales_organisation, **kwargs):
    if sales_organisation in allowed_sales_organisations:
        return method(sales_organisation, **kwargs)
    else:
        frappe.logger("sales_organisation").error(sales_organisation)


def get_allowed_companyList():
    company_list = []

    for sales_organisation in allowed_sales_organisations:
        company = frappe.get_value(
            "Sales Organisation Master", sales_organisation, "company"
        )
        company_list.append(company)

    return company_list
