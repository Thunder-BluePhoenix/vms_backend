
import frappe
from vms.utils.custom_send_mail import custom_sendmail
import datetime

# @frappe.whitelist(allow_guest=True)
# def asa_dashboard(vendor_name=None, page_no=1, page_length=5):
#     try:
#         usr = frappe.session.user
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         offset = (page_no - 1) * page_length

#         user_emp = frappe.get_value("Employee", {"user_id": usr}, ["name", "team"], as_dict=True)
#         if not user_emp or not user_emp.team:
#             return {
#                 "status": "success",
#                 "message": "No team assigned to this user",
#                 "data": [],
#                 "total_count": 0,
#                 "overall_total_asa": 0
#             }

#         team_emps = frappe.get_all("Employee", filters={"team": user_emp.team}, pluck="user_id")

#         vendor_list = frappe.get_all(
#             "Vendor Master",
#             filters={"registered_by": ["in", team_emps]},
#             pluck="name"
#         )

#         if not vendor_list:
#             return {
#                 "status": "success",
#                 "message": "No vendors found for team",
#                 "data": [],
#                 "total_count": 0,
#                 "overall_total_asa": 0
#             }

#         filters = {"vendor_ref_no": ["in", vendor_list]}
#         if vendor_name:
#             filters["vendor_name"] = ["like", f"%{vendor_name}%"]

#         total_count = frappe.db.count(
#             "Annual Supplier Assessment Questionnaire",
#             filters=filters
#         )

#         overall_total_asa = frappe.db.count(
#             "Annual Supplier Assessment Questionnaire",
#             filters={"vendor_ref_no": ["in", vendor_list]}
#         )

#         asa_list = frappe.get_all(
#             "Annual Supplier Assessment Questionnaire",
#             filters=filters,
#             fields=["name", "vendor_name", "vendor_ref_no", "creation"],
#             order_by="creation desc",
#             start=offset,
#             page_length=page_length
#         )

#         return {
#             "status": "success",
#             "message": f"{len(asa_list)} ASA record(s) found",
#             "data": asa_list,
#             "total_count": total_count or 0,
#             "overall_total_asa": overall_total_asa or 0,
#             "page_no": page_no,
#             "page_length": page_length
#         }

#     except Exception:
#         frappe.log_error(message=frappe.get_traceback(), title="ASA Dashboard Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch ASA dashboard data."
#         }


@frappe.whitelist(allow_guest=True)
def asa_dashboard(vendor_name=None, page_no=1, page_length=5):
    try:
        usr = frappe.session.user

        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length

        user_designation = frappe.get_value("Employee", {"user_id": usr}, "designation")

        if not user_designation or user_designation.strip().lower() != "asa":
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "User does not have ASA access",
                "data": [],
                "total_count": 0,
                "overall_total_asa": 0
            }
        
        filters = {}

        filters["form_is_submitted"] = 1

        if vendor_name and vendor_name.strip():
            filters["vendor_name"] = ["like", f"%{vendor_name.strip()}%"]

        total_count = frappe.db.count(
            "Annual Supplier Assessment Questionnaire",
            filters=filters
        )

        overall_total_asa = frappe.db.count(
            "Annual Supplier Assessment Questionnaire", filters={"form_is_submitted": 1}
        )

        asa_list = frappe.get_all(
            "Annual Supplier Assessment Questionnaire",
            filters=filters,
            fields=["name", "vendor_name", "vendor_ref_no", "creation"],
            order_by="creation desc",
            start=offset,
            page_length=page_length
        )

        return {
            "status": "success",
            "message": f"{len(asa_list)} ASA record(s) found",
            "data": asa_list,
            "total_count": total_count or 0,
            "overall_total_asa": overall_total_asa or 0,
            "page_no": page_no,
            "page_length": page_length
        }
    
    except Exception:
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(message=frappe.get_traceback(), title="ASA Dashboard Error")
        return {
            "status": "error",
            "message": "Failed to fetch ASA dashboard data."
        }
    
# Not in Used
# Approved Vendors count
@frappe.whitelist(allow_guest=False)
def approved_vendor_count():
    try:
        # Get all Vendor Onboarding docs with status = Approved
        vendor_master = frappe.get_all(
            "Vendor Onboarding",
            filters={"onboarding_form_status": "Approved"},
            pluck="ref_no"   # fetch only ref_no values
        )

        # Count matching records in Vendor Master
        approved_vendor = frappe.db.count(
            "Vendor Master",
            {"name": ["in", vendor_master]}
        )

        return {
            "status": "success",
            "approved_vendor_count": approved_vendor
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Approved Vendor Count Error")
        return {
            "status": "error",
            "message": str(e)
        }

# Not in Used
# no of pending asa who doesnt fill the asa this academic year
@frappe.whitelist(allow_guest=False)
def pending_asa_count():
    try:
        # Get all Approved Vendor Onboarding ref_nos
        vendor_onboarding = frappe.get_all(
            "Vendor Onboarding",
            filters={"onboarding_form_status": "Approved"},
            pluck="ref_no"
        )

        if not vendor_onboarding:
            return {
                "status": "success",
                "pending_asa_count": 0
            }

        # Get all Vendor Master docs with matching ref_nos
        vendor_masters = frappe.get_all(
            "Vendor Master",
            filters={"name": ["in", vendor_onboarding]},
            pluck="name"
        )

        if not vendor_masters:
            return {
                "status": "success",
                "pending_asa_count": 0
            }

        current_year = frappe.utils.now_datetime().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"

        pending_count = 0

        for vm in vendor_masters:
            # check if there is an assessment record in the current year
            has_child_this_year = frappe.db.exists(
                "Assessment Form Records",
                {
                    "parent": vm,
                    "date_time": ["between", [start_date, end_date]]
                }
            )
            if not has_child_this_year:
                pending_count += 1

        return {
            "status": "success",
            "pending_asa_count": pending_count
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Pending ASA Count Error")
        return {
            "status": "error",
            "message": str(e)
        }


# Data of pending ASA for vendors who have not filled the ASA form this academic year, where ‘ASA Form Filled’ is unchecked and 
# ‘ASA Required’ is checked.

# @frappe.whitelist(allow_guest=False)
# def pending_asa_vendor_list(page_no=None, page_length=None, name=None, vendor_name=None):
#     try:
#         vendor_onboarding = frappe.get_all(
#             "Vendor Onboarding",
#             filters={"onboarding_form_status": "Approved"},
#             pluck="ref_no"
#         )

#         if not vendor_onboarding:
#             return {
#                 "status": "success",
#                 "pending_asa_count": 0,
#                 "pending_asa_vendors": []
#             }

#         conditions = ["vm.name IN %(ref_nos)s"]
#         values = {"ref_nos": vendor_onboarding}

#         if name:
#             conditions.append("vm.name LIKE %(name)s")
#             values["name"] = f"%{name}%"

#         if vendor_name:
#             conditions.append("vm.vendor_name LIKE %(vendor_name)s")
#             values["vendor_name"] = f"%{vendor_name}%"

#         filter_clause = " AND ".join(conditions)

#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         offset = (page_no - 1) * page_length
#         values.update({"limit": page_length, "offset": offset})

#         total_count = frappe.db.sql(f"""
#             SELECT COUNT(*) 
#             FROM `tabVendor Master` vm
#             WHERE {filter_clause}
#         """, values)[0][0]

#         if total_count == 0:
#             return {
#                 "status": "success",
#                 "pending_asa_count": 0,
#                 "pending_asa_vendors": []
#             }

#         vendor_masters = frappe.db.sql(f"""
#             SELECT vm.name, vm.vendor_name, vm.office_email_primary,
#                    vm.country, vm.mobile_number, vm.registered_date
#             FROM `tabVendor Master` vm
#             WHERE {filter_clause}
#             ORDER BY vm.modified DESC
#             LIMIT %(limit)s OFFSET %(offset)s
#         """, values, as_dict=True)

#         pending_vendors = []
#         current_year = frappe.utils.now_datetime().year
#         start_date = f"{current_year}-01-01"
#         end_date = f"{current_year}-12-31"

#         for vm in vendor_masters:
#             # check if there is an assessment record in the current year
#             has_child_this_year = frappe.db.exists(
#                 "Assessment Form Records",
#                 {
#                     "parent": vm["name"],
#                     "date_time": ["between", [start_date, end_date]]
#                 }
#             )

#             # if no record in current year → pending
#             if not has_child_this_year:
#                 pending_vendors.append(vm)

#         # Attach company vendor codes to each vendor
#         for vm in vendor_masters:
#             company_vendor = frappe.get_all(
#                 "Company Vendor Code",
#                 filters={"vendor_ref_no": vm["name"]},
#                 fields=["name", "company_name", "company_code"]
#             )

#             filtered_codes = []
#             for cvc in company_vendor:
#                 vendor_code_children = frappe.get_all(
#                     "Vendor Code",
#                     filters={"parent": cvc.name},
#                     fields=["state", "gst_no", "vendor_code"]
#                 )

#                 filtered_codes.append({
#                     "company_name": cvc.company_name,
#                     "company_code": cvc.company_code,
#                     "vendor_codes": vendor_code_children
#                 })

#             vm["company_vendor_codes"] = filtered_codes

#         return {
#             "status": "success",
#             "pending_asa_count": len(pending_vendors),
#             "page_no": page_no,
#             "page_length": page_length,
#             "pending_asa_vendors": pending_vendors
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Pending ASA Count Error")
#         return {
#             "status": "error",
#             "message": str(e)
#         }


@frappe.whitelist(allow_guest=False, methods=['GET'])
def pending_asa_vendor_list(page_no=None, page_length=None, name=None, vendor_name=None):
    try:
        vendor_master_docs = frappe.get_all(
            "Vendor Master",
            filters={"asa_required": 1},
            pluck="name"
        )

        pending_vendors = []

        current_year = frappe.utils.now_datetime().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"

        for vm_name in vendor_master_docs:
            doc = frappe.get_doc("Vendor Master", vm_name)

            if not doc.form_records or len(doc.form_records) == 0:
                pending_vendors.append(vm_name)
                continue

            record_found_but_not_submitted = False

            for row in doc.form_records:
                row_date = row.date_time.date()

                if row_date and start_date <= str(row_date) <= end_date:
                    if int(row.form_is_submitted) == 0:
                        record_found_but_not_submitted = True

            if record_found_but_not_submitted:
                pending_vendors.append(vm_name)

        if not pending_vendors:
            frappe.local.response["http_status_code"] = 200
            return {
                "status": "success",
                "overall_count": 0,
                "pending_vendor_count": 0,
                "pending_vendors": []
            }

        conditions = ["vm.name IN %(vendor_list)s"]
        values = {"vendor_list": pending_vendors}

        if name:
            conditions.append("vm.name LIKE %(name)s")
            values["name"] = f"%{name}%"

        if vendor_name:
            conditions.append("vm.vendor_name LIKE %(vendor_name)s")
            values["vendor_name"] = f"%{vendor_name}%"

        filter_clause = " AND ".join(conditions)

        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length

        values.update({"limit": page_length, "offset": offset})

        total_count = frappe.db.sql(f"""
            SELECT COUNT(*)
            FROM `tabVendor Master` vm
            WHERE {filter_clause}
        """, values)[0][0]

        vendor_masters = frappe.db.sql(f"""
            SELECT 
                vm.name,
                vm.vendor_name,
                vm.office_email_primary,
                vm.country,
                vm.mobile_number,
                vm.registered_date, vm.registered_by
            FROM `tabVendor Master` vm
            WHERE {filter_clause}
            ORDER BY vm.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        for vm in vendor_masters:
            vm["register_by_emp"] = frappe.db.get_value("Employee", {"user_id": vm.get("registered_by")}, "full_name") or ""

        return {
            "status": "success",
            "overall_count": len(pending_vendors),
            "pending_vendor_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "pending_vendors": vendor_masters
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Pending ASA Count Error")
        return {
            "status": "error",
            "message": str(e)
        }
    

# Data of the approved vendor list where the vendor code is available and ‘ASA Required’ is checked.

# @frappe.whitelist(allow_guest=False)
# def approved_vendor_list(page_no=None, page_length=None, name=None, vendor_name=None):
#     try:
#         vendor_onboarding = frappe.get_all(
#             "Vendor Onboarding",
#             filters={"onboarding_form_status": "Approved"},
#             pluck="ref_no"
#         )

#         if not vendor_onboarding:
#             return {
#                 "status": "success",
#                 "approved_vendor_count": 0,
#                 "approved_vendors": []
#             }

#         conditions = ["vm.name IN %(ref_nos)s"]
#         values = {"ref_nos": vendor_onboarding}

#         if name:
#             conditions.append("vm.name LIKE %(name)s")
#             values["name"] = f"%{name}%"

#         if vendor_name:
#             conditions.append("vm.vendor_name LIKE %(vendor_name)s")
#             values["vendor_name"] = f"%{vendor_name}%"

#         filter_clause = " AND ".join(conditions)

#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         offset = (page_no - 1) * page_length
#         values.update({"limit": page_length, "offset": offset})

#         # Count vendors
#         total_count = frappe.db.sql(f"""
#             SELECT COUNT(*) 
#             FROM `tabVendor Master` vm
#             WHERE {filter_clause}
#         """, values)[0][0]

#         if total_count == 0:
#             return {
#                 "status": "success",
#                 "approved_vendor_count": 0,
#                 "approved_vendors": []
#             }

#         vendor_masters = frappe.db.sql(f"""
#             SELECT vm.name, vm.vendor_name, vm.office_email_primary,
#                    vm.country, vm.mobile_number, vm.registered_date
#             FROM `tabVendor Master` vm
#             WHERE {filter_clause}
#             ORDER BY vm.modified DESC
#             LIMIT %(limit)s OFFSET %(offset)s
#         """, values, as_dict=True)

#         # Attach company vendor codes to each vendor
#         for vm in vendor_masters:
#             company_vendor = frappe.get_all(
#                 "Company Vendor Code",
#                 filters={"vendor_ref_no": vm["name"]},
#                 fields=["name", "company_name", "company_code"]
#             )

#             filtered_codes = []
#             for cvc in company_vendor:
#                 vendor_code_children = frappe.get_all(
#                     "Vendor Code",
#                     filters={"parent": cvc.name},
#                     fields=["state", "gst_no", "vendor_code"]
#                 )

#                 filtered_codes.append({
#                     "company_name": cvc.company_name,
#                     "company_code": cvc.company_code,
#                     "vendor_codes": vendor_code_children
#                 })

#             vm["company_vendor_codes"] = filtered_codes

#         return {
#             "status": "success",
#             "approved_vendor_count": int(total_count),
#             "page_no": page_no,
#             "page_length": page_length,
#             "approved_vendors": vendor_masters
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Approved Vendor List Error")
#         return {
#             "status": "error",
#             "message": str(e)
#         }


@frappe.whitelist(allow_guest=False, methods=['GET'])
def approved_vendor_list(page_no=None, page_length=None, name=None, vendor_name=None):
    try:
        vendor_list = []

        vendor_master_docs = frappe.get_all(
            "Vendor Master",
            filters={"asa_required": 1},
            pluck="name"
        )

        for vm_name in vendor_master_docs:
            doc = frappe.get_doc("Vendor Master", vm_name)

            has_vendor_code = any(row.company_vendor_code for row in doc.multiple_company_data)

            if has_vendor_code:
                vendor_list.append(vm_name)

        if not vendor_list:
            frappe.local.response["http_status_code"] = 200
            return {
                "status": "success",
                "overall_count": 0,
                "approved_vendor_count": 0,
                "approved_vendors": []
            }

        conditions = ["vm.name IN %(vendor_list)s"]
        values = {"vendor_list": vendor_list}

        if name:
            conditions.append("vm.name LIKE %(name)s")
            values["name"] = f"%{name}%"

        if vendor_name:
            conditions.append("vm.vendor_name LIKE %(vendor_name)s")
            values["vendor_name"] = f"%{vendor_name}%"

        filter_clause = " AND ".join(conditions)

        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length

        values.update({"limit": page_length, "offset": offset})

        total_count = frappe.db.sql(f"""
            SELECT COUNT(*)
            FROM `tabVendor Master` vm
            WHERE {filter_clause}
        """, values)[0][0]

        overall_count = len(vendor_list)

        vendor_masters = frappe.db.sql(f"""
            SELECT 
                vm.name, 
                vm.vendor_name, 
                vm.office_email_primary,
                vm.country, 
                vm.mobile_number, 
                vm.registered_date, vm.registered_by
            FROM `tabVendor Master` vm
            WHERE {filter_clause}
            ORDER BY vm.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        for vm in vendor_masters:
            vm["register_by_emp"] = frappe.db.get_value("Employee", {"user_id": vm.get("registered_by")}, "full_name") or ""
        # for vm in vendor_masters:
            vm_name = vm["name"]
            print("VM NAMe--->",vm_name)

            # fetch DOC
            doc = frappe.get_doc("Vendor Master", vm_name)

            # Build vendor code list
            ref_no = vm_name
            print("REF NO --->", ref_no)

            # main_company = doc.get("company")

            company_vendor = frappe.get_all(
                "Company Vendor Code",
                filters={"vendor_ref_no": ref_no},
                fields=["name", "company_name", "company_code"]
            )

            filtered_codes = []
            for cvc in company_vendor:
                # print("MAIN COMPANY --->", repr(main_company))
                print("CVC COMPANY  --->", repr(cvc.company_name))
                # print("MATCH? ---->", cvc.company_name == main_company)
                if cvc.company_name:
                    vendor_code_children = frappe.get_all(
                        "Vendor Code",
                        filters={"parent": cvc.name},
                        fields=["state", "gst_no", "vendor_code"]
                    )
                    

                    filtered_codes.append({
                        "company_name": cvc.company_name,
                        "company_code": cvc.company_code,
                        "vendor_codes": vendor_code_children
                    })

            # Attach directly to API output dict
            vm["company_vendor_codes"] = filtered_codes


        return {
            "status": "success",
            "overall_count": overall_count,
            "approved_vendor_count": int(total_count),
            "page_no": page_no,
            "page_length": page_length,
            "approved_vendors": vendor_masters
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Approved Vendor List Error")
        return {
            "status": "error",
            "message": str(e)
        }


# send asa reminder mail who doesnt fill the asa this year
@frappe.whitelist(allow_guest=False)
def send_asa_reminder_email(name, remarks=None):
    try:
        if not name:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "Email not found"
            }

        vendor_master = frappe.get_doc("Vendor Master", name)
        recipient = vendor_master.office_email_primary or vendor_master.office_email_secondary

        if not recipient:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "No recipient email found"
            }
        
        subject = "Reminder: Please Fill the Annual Supplier Assessment (ASA) Questionnaire"
        message = f"""
        Dear {vendor_master.vendor_name},<br><br>

        As your onboarding process has been completed, you are kindly requested to fill out the
        Annual Supplier Assessment (ASA) Questionnaire, which is an essential part of the
        vendor onboarding compliance.<br><br>

        Below are the remarks:<br>
        {remarks}<br><br>

        We request you to complete the form at the earliest.<br><br>

        Best regards,<br>  
        Vendor Management Team
        """


        frappe.custom_sendmail(
            recipients=[recipient],
            subject=subject,
            message=message,
            now=True
        )

        return {
            "status": "success",
            "message": f"Reminder email sent successfully to {recipient}"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "ASA Reminder Email Error")
        return {
            "status": "error",
            "message": str(e)
        }
