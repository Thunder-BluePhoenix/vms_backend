import frappe

# get vendor details for dashboard

@frappe.whitelist(allow_guest=False)
def get_vendor_details_for_dashboard(user):
    try:
        user_doc = frappe.get_doc('User', user)
        user_roles = frappe.get_roles(user_doc.name)

        if "Vendor" not in user_roles:
            return {"status": "error", "message": "User does not have the Vendor role."}

        vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": user_doc.name})
        if not vendor_master or not getattr(vendor_master, 'multiple_company_data', None):
            return {
                "status": "success",
                "message": "No multiple_company_data found in vendor document.",
                "vendor_purchase_orders": []
            }

        all_vendor_codes = []

        for company_data_row in vendor_master.multiple_company_data:
            if company_data_row.company_vendor_code:
                company_vendor_code_doc = frappe.get_doc("Company Vendor Code", company_data_row.company_vendor_code)
                if getattr(company_vendor_code_doc, 'vendor_code', None):
                    for vendor_code_row in company_vendor_code_doc.vendor_code:
                        if vendor_code_row.vendor_code:
                            all_vendor_codes.append(vendor_code_row.vendor_code)

        vendor_po_map = {}

        if all_vendor_codes:
            pos = frappe.get_all(
                "Purchase Order",
                filters={"vendor_code": ["in", all_vendor_codes]},
                fields="*"
            )

            for po in pos:
                vendor_po_map.setdefault(po.vendor_code, []).append(po)

        vendor_po_list = [{"vendor_code": vcode, "purchase_orders": po_list} for vcode, po_list in vendor_po_map.items()]

        return {
            "status": "success",
            "message": "Purchase Orders grouped by vendor code.",
            "vendor_purchase_orders": vendor_po_list
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Vendor Details for Dashboard Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor dashboard data.",
            "error": str(e)
        }


# @frappe.whitelist(allow_guest=False)
# def get_vendor_details_for_dashboard(user):
#     try:
#         user_doc = frappe.get_doc('User', user)
#         user_roles = frappe.get_roles(user_doc.name)

#         if "Vendor" not in user_roles:
#             return {"status": "error", "message": "User does not have the Vendor role."}

#         vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": user_doc.name})
#         if not vendor_master or not getattr(vendor_master, 'multiple_company_data', []):
#             return {
#                 "status": "success",
#                 "message": "No vendor code records found.",
#                 "data": {}
#             }

#         all_vendor_codes = []

#         for company_data_row in vendor_master.multiple_company_data:
#             if company_data_row.company_vendor_code:
#                 company_vendor_code_doc = frappe.get_doc("Company Vendor Code", company_data_row.company_vendor_code)

#                 if hasattr(company_vendor_code_doc, 'vendor_code') and company_vendor_code_doc.vendor_code:
#                     for vendor_code_row in company_vendor_code_doc.vendor_code:
#                         vendor_code = vendor_code_row.vendor_code
#                         if vendor_code:
#                             all_vendor_codes.append(vendor_code)

#         # Fetch Purchase Orders by vendor code
#         po_data_by_vendor = {}
#         if all_vendor_codes:
#             purchase_orders = frappe.get_all(
#                 "Purchase Order",
#                 filters={"vendor_code": ["in", all_vendor_codes]},
#                 fields=["name", "vendor_code", "transaction_date", "status", "grand_total", "currency", "company"]
#             )

#             for po in purchase_orders:
#                 vendor_code = po.vendor_code
#                 if vendor_code not in po_data_by_vendor:
#                     po_data_by_vendor[vendor_code] = []
#                 po_data_by_vendor[vendor_code].append(po)

#         return {
#             "status": "success",
#             "message": "Purchase Orders grouped by Vendor Code.",
#             "data": po_data_by_vendor
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Get Vendor Details Dashboard API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch vendor dashboard data.",
#             "error": str(e)
#         }
