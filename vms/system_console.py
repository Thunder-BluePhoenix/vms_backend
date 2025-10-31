# To change the docnames



# companies = frappe.get_all("Company Master", fields=["name", "company_code", "company_name"])

# for comp in companies:
#     new_name = f"{comp.company_code}-{comp.company_name}"
#     if comp.name != new_name:
#         frappe.rename_doc("Company Master", comp.name, new_name, force=1, merge=False)




# duplicates = frappe.db.sql("""
#     SELECT gl_account_code, COUNT(*) as count
#     FROM `tabGL Account`
#     WHERE gl_account_code IS NOT NULL AND gl_account_code != ''
#     GROUP BY gl_account_code
#     HAVING COUNT(*) > 1
# """, as_dict=True)

# if not duplicates:
#     print("✅ No duplicate employee numbers found.")
# else:
#     print("⚠️ Duplicate Employee Numbers:")
#     for d in duplicates:
#         print(f"{d.gl_account_code} → {d.count} records")

#     # (Optional) To list the specific employees for each duplicate
#     print("\nDetailed list of duplicates:")
#     for d in duplicates:
#         employees = frappe.db.get_all(
#             "GL Account",
#             filters={"gl_account_code": d.gl_account_code},
#             fields=["name", "employee_name", "gl_account_code"]
#         )
#         print(f"\nEmployee Number: {d.gl_account_code}")
#         for e in employees:
#             print(f" - {e.name} | {e.employee_name}")