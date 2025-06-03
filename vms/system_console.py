# To change the docnames



# companies = frappe.get_all("Company Master", fields=["name", "company_code", "company_name"])

# for comp in companies:
#     new_name = f"{comp.company_code}-{comp.company_name}"
#     if comp.name != new_name:
#         frappe.rename_doc("Company Master", comp.name, new_name, force=1, merge=False)
