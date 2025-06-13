import frappe
from frappe import _

# get vendor details for dashboard based on user log in
# Not in Use ------------------------------------------
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


# return the po data based on vendor code if present else return all po data based on session user

# @frappe.whitelist(allow_guest=False)
# def get_po_from_vendor_code(vendor_code=None):
#     try:
#         if vendor_code:
#             all_po = frappe.get_all(
#                 "Purchase Order",
#                 filters={"vendor_code": vendor_code},
#                 fields="*",
#                 order_by="modified desc"
#             )
#             return all_po

#         # If vendor_code not passed, get from logged-in user
#         user = frappe.session.user
#         user_doc = frappe.get_doc("User", user)
#         user_roles = frappe.get_roles(user_doc.name)

#         if "Vendor" not in user_roles:
#             return {
#                 "status": "error",
#                 "message": _("User does not have the Vendor role.")
#             }

#         vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": user_doc.name})

#         if not vendor_master or not vendor_master.multiple_company_data:
#             return {
#                 "status": "success",
#                 "message": _("No multiple_company_data found in vendor document."),
#                 "vendor_purchase_orders": []
#             }

#         all_vendor_codes = []
#         for row in vendor_master.multiple_company_data:
#             if row.company_vendor_code:
#                 company_vendor_code_doc = frappe.get_doc("Company Vendor Code", row.company_vendor_code)
#                 if company_vendor_code_doc.vendor_code:
#                     all_vendor_codes.extend(vc.vendor_code for vc in company_vendor_code_doc.vendor_code if vc.vendor_code)

#         if not all_vendor_codes:
#             return {
#                 "status": "success",
#                 "message": _("No vendor codes found for this vendor."),
#                 "vendor_purchase_orders": []
#             }

#         po_list = frappe.get_all(
#             "Purchase Order",
#             filters={"vendor_code": ["in", all_vendor_codes]},
#             fields="*",
#             order_by="modified desc"
#         )

#         # vendor_po_map = {}
#         # for po in po_list:
#         #     vendor_po_map.setdefault(po.vendor_code, []).append(po)

#         # vendor_po_list = [{"vendor_code": code, "purchase_orders": orders} for code, orders in vendor_po_map.items()]

#         return po_list

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_po_from_vendor_code API Error")
#         return {
#             "status": "error",
#             "message": _("An error occurred while fetching purchase orders."),
#             "error": str(e)
#         }



# Alternative code return data for above function name - get_vendor_details_for_dashboard
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


# count the number of purchase orders based on vendor code if present else return all count of po data based on session user
@frappe.whitelist(allow_guest=False)
def get_po_count_from_vendor_code(vendor_code=None):
    try:
        if vendor_code:
            po_count = frappe.db.count(
                "Purchase Order",
                filters={"vendor_code": vendor_code}
            )
            return {
                "status": "success",
                "message": f"{po_count} Purchase Orders found for vendor code {vendor_code}.",
                "vendor_code": vendor_code,
                "purchase_order_count": po_count
            }

        # Fallback to session user
        user = frappe.session.user
        user_doc = frappe.get_doc("User", user)
        user_roles = frappe.get_roles(user_doc.name)

        if "Vendor" not in user_roles:
            return {
                "status": "error",
                "message": _("User does not have the Vendor role.")
            }

        vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": user_doc.name})

        if not vendor_master or not vendor_master.multiple_company_data:
            return {
                "status": "success",
                "message": _("No multiple_company_data found in vendor document."),
                "purchase_order_count": 0
            }

        all_vendor_codes = []
        for row in vendor_master.multiple_company_data:
            if row.company_vendor_code:
                company_vendor_code_doc = frappe.get_doc("Company Vendor Code", row.company_vendor_code)
                if company_vendor_code_doc.vendor_code:
                    all_vendor_codes.extend(vc.vendor_code for vc in company_vendor_code_doc.vendor_code if vc.vendor_code)

        if not all_vendor_codes:
            return {
                "status": "success",
                "message": _("No vendor codes found for this vendor."),
                "purchase_order_count": 0
            }

        po_count = frappe.db.count(
            "Purchase Order",
            filters={"vendor_code": ["in", all_vendor_codes]}
        )

        return {
            "status": "success",
            "message": _("Total Purchase Orders found for session vendor codes."),
            "vendor_codes": all_vendor_codes,
            "purchase_order_count": po_count
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_po_from_vendor_code API Error")
        return {
            "status": "error",
            "message": _("An error occurred while fetching purchase order count."),
            "error": str(e)
        }  
    

# filter the data of po based on paraemeters
@frappe.whitelist(allow_guest=False)
def get_po_from_vendor_code(vendor_code=None, page_no=None, page_length=None, company=None, po_no=None, status=None, user=None):
    try:
        page_no = int(page_no or 1)
        page_length = int(page_length or 5)

        result = filter_po_data(
            vendor_code=vendor_code,
            page_no=page_no,
            page_length=page_length,
            company=company,
            po_no=po_no,
            status=status,
            user=user or frappe.session.user
        )

        if result.get("status") != "success":
            return result

        return {
            "status": "success",
            "message": "Purchase Orders fetched successfully.",
            "purchase_orders": result.get("data"),
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_po_from_vendor_code API Error")
        return {
            "status": "error",
            "message": "An error occurred while fetching purchase orders.",
            "error": str(e)
        }
    

@frappe.whitelist(allow_guest=False)
def filter_po_data(vendor_code=None, page_no=None, page_length=None, company=None, po_no=None, status=None, user=None):
    try:
        filters = {}
        if po_no:
            filters["name"] = po_no
        if status:
            filters["status"] = status
        if company:
            filters["company_code"] = company

        if vendor_code:
            filters["vendor_code"] = vendor_code
        else:
            user_doc = frappe.get_doc("User", user)
            if "Vendor" not in frappe.get_roles(user_doc.name):
                return {"status": "error", "message": "User does not have the Vendor role."}

            vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": user_doc.name})
            if not vendor_master or not vendor_master.multiple_company_data:
                return {
                    "status": "success",
                    "message": "No multiple_company_data found in vendor document.",
                    "data": [],
                    "total_count": 0,
                    "page_no": page_no,
                    "page_length": page_length
                }

            all_vendor_codes = []
            for row in vendor_master.multiple_company_data:
                if row.company_vendor_code:
                    company_vendor_code_doc = frappe.get_doc("Company Vendor Code", row.company_vendor_code)
                    all_vendor_codes += [
                        vc.vendor_code for vc in company_vendor_code_doc.vendor_code if vc.vendor_code
                    ]

            if not all_vendor_codes:
                return {
                    "status": "success",
                    "message": "No vendor codes found for this vendor.",
                    "data": [],
                    "total_count": 0,
                    "page_no": page_no,
                    "page_length": page_length
                }

            filters["vendor_code"] = ["in", all_vendor_codes]

        total_count = frappe.db.count("Purchase Order", filters=filters)
        offset = (page_no - 1) * page_length

        po_data = frappe.get_all(
            "Purchase Order",
            filters=filters,
            fields="*",
            order_by="modified desc",
            start=offset,
            page_length=page_length
        )

        return {
            "status": "success",
            "data": po_data,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "filter_po_data Error")
        return {
            "status": "error",
            "message": "An error occurred during filtering.",
            "error": str(e)
        }