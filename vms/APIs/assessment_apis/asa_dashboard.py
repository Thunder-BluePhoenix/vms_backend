import frappe

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
            return {
                "status": "error",
                "message": "User does not have ASA access",
                "data": [],
                "total_count": 0,
                "overall_total_asa": 0
            }
        filters = {}
        if vendor_name and vendor_name.strip():
            filters["vendor_name"] = ["like", f"%{vendor_name.strip()}%"]
        total_count = frappe.db.count(
            "Annual Supplier Assessment Questionnaire",
            filters=filters
        )
        overall_total_asa = frappe.db.count(
            "Annual Supplier Assessment Questionnaire"
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
        frappe.log_error(message=frappe.get_traceback(), title="ASA Dashboard Error")
        return {
            "status": "error",
            "message": "Failed to fetch ASA dashboard data."
        }
    

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
        frappe.log_error(frappe.get_traceback(), "Approved Vendor Count Error")
        return {
            "status": "error",
            "message": str(e)
        }


# no of pending asa
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

        pending_count = 0

        # Loop through vendor masters and check child table
        for vm in vendor_masters:
            child_records = frappe.get_all(
                "Assessment Form Records",
                filters={"parent": vm},
                limit=1
            )
            if not child_records:  # No assessment form records
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


@frappe.whitelist(allow_guest=False)
def pending_asa_vendor_list():
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
                "pending_asa_count": 0,
                "pending_asa_vendors": []
            }

        pending_vendors = []

        # Loop through Vendor Masters with matching ref_no
        vendor_masters = frappe.get_all(
            "Vendor Master",
            filters={"name": ["in", vendor_onboarding]},
            fields=["name", "vendor_name", "office_email_primary", "country", "mobile_number", "registered_date"]
        )

        for vm in vendor_masters:
            # Check if child table has any records
            has_child = frappe.get_all(
                "Assessment Form Records",
                filters={"parent": vm.name},
                limit=1
            )
            if not has_child:
                # Append only those vendors with NO child records
                pending_vendors.append(vm)

        return {
            "status": "success",
            "pending_asa_count": len(pending_vendors),
            "pending_asa_vendors": pending_vendors
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Pending ASA Count Error")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=False)
def send_asa_reminder_email(name):
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
        Dear {vendor_master.vendor_name},

        As your onboarding process has been completed, you are kindly requested to fill the
        Annual Supplier Assessment (ASA) Questionnaire, which is an essential part of the
        vendor onboarding compliance.

        We request you to complete the form at the earliest.

        Regards,  
        Vendor Management Team
        """

        frappe.sendmail(
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
