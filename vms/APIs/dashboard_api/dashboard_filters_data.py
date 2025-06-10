import frappe
from frappe.utils import today, get_first_day, get_last_day


@frappe.whitelist(allow_guest=False)
def filtering_total_vendor_details(page_no=None, page_length=None, company=None, refno=None, status=None, usr=None):
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access.",
                "code": 404
            }

        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        # Base filters
        conditions = []
        values = {}

        if "Accounts Team" in user_roles:
            employee = frappe.get_doc("Employee", {"user_id": usr})
            company_list = [row.company_name for row in employee.company]

            if not company_list:
                return {
                    "status": "error",
                    "message": "No company records found in Employee.",
                    "vendor_onboarding": []
                }

            conditions.append("vo.company_name IN %(company_list)s")
            values["company_list"] = company_list

        else:
            team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
            if not team:
                return {
                    "status": "error",
                    "message": "No Employee record found for the user.",
                    "vendor_onboarding": []
                }

            user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
            if not user_ids:
                return {
                    "status": "error",
                    "message": "No users found in the same team.",
                    "vendor_onboarding": []
                }

            conditions.append("vo.registered_by IN %(user_ids)s")
            values["user_ids"] = user_ids

        if company:
            conditions.append("vo.company_name = %(company)s")
            values["company"] = company

        if refno:
            conditions.append("vo.ref_no = %(refno)s")
            values["refno"] = refno

        if status:
            conditions.append("vo.onboarding_form_status = %(status)s")
            values["status"] = status

        filter_clause = " AND ".join(conditions)

        # Total count for pagination
        total_count = frappe.db.sql(f"""
            SELECT COUNT(*) AS count
            FROM `tabVendor Onboarding` vo
            WHERE {filter_clause}
        """, values)[0][0]

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values["limit"] = page_length
        values["offset"] = offset

        onboarding_docs = frappe.db.sql(f"""
            SELECT
                vo.name, vo.ref_no, vo.company_name, vo.vendor_name, vo.onboarding_form_status, vo.modified,
                vo.purchase_t_approval, vo.accounts_t_approval, vo.purchase_h_approval,
                vo.mandatory_data_filled, vo.purchase_team_undertaking, vo.accounts_team_undertaking, vo.purchase_head_undertaking,
                vo.form_fully_submitted_by_vendor, vo.sent_registration_email_link, vo.rejected, vo.data_sent_to_sap, vo.expired,
                vo.payee_in_document, vo.check_double_invoice, vo.gr_based_inv_ver, vo.service_based_inv_ver
            FROM `tabVendor Onboarding` vo
            WHERE {filter_clause}
            ORDER BY vo.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        return {
            "status": "success",
            "message": "Filtered records fetched.",
            "total_vendor_onboarding": onboarding_docs,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Filtering Total Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to filter vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }


@frappe.whitelist(allow_guest=True)
def approved_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Approved for this API
        status = "Approved"

        # Call reusable filter function
        result = filtering_total_vendor_details(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr
        )

        if result.get("status") != "success":
            return result

        onboarding_docs = result.get("total_vendor_onboarding", [])

        # Enrich with company vendor codes
        for doc in onboarding_docs:
            ref_no = doc.get("ref_no")
            company_vendor = frappe.get_all(
                "Company Vendor Code",
                filters={"vendor_ref_no": ref_no},
                fields=["name", "company_code"]
            )

            enriched_codes = []
            for cvc in company_vendor:
                vendor_code_children = frappe.get_all(
                    "Vendor Code",
                    filters={"parent": cvc.name},
                    fields=["state", "gst_no", "vendor_code"]
                )
                enriched_codes.append({
                    "company_code": cvc.company_code,
                    "vendor_codes": vendor_code_children
                })

            doc["company_vendor_codes"] = enriched_codes

        return {
            "status": "success",
            "message": "Approved vendor onboarding records fetched successfully.",
            "approved_vendor_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Approved Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch approved vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }


@frappe.whitelist(allow_guest=False)
def rejected_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Rejected for this API
        status = "Rejected"

        # Call reusable filter function
        result = filtering_total_vendor_details(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr
        )

        if result.get("status") != "success":
            return result

        onboarding_docs = result.get("total_vendor_onboarding", [])

        return {
            "status": "success",
            "message": "Rejected vendor onboarding records fetched successfully.",
            "rejected_vendor_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Rejected Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch rejected vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }


@frappe.whitelist(allow_guest=False)
def pending_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Pending for this API
        status = "Pending"

        # Call reusable filter function
        result = filtering_total_vendor_details(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr
        )

        if result.get("status") != "success":
            return result

        onboarding_docs = result.get("total_vendor_onboarding", [])

        return {
            "status": "success",
            "message": "Pending vendor onboarding records fetched successfully.",
            "pending_vendor_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Pending Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch pending vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }


@frappe.whitelist(allow_guest=False)
def expired_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Expired for this API
        status = "Expired"

        # Call reusable filter function
        result = filtering_total_vendor_details(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr
        )

        if result.get("status") != "success":
            return result

        onboarding_docs = result.get("total_vendor_onboarding", [])

        return {
            "status": "success",
            "message": "Expired vendor onboarding records fetched successfully.",
            "expired_vendor_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Expired Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch expired vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }

 
# apply a different query so cannot use the above filteration function
@frappe.whitelist(allow_guest=False)
def total_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None):
    try:
        if not usr:
            usr = frappe.session.user

        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        values = {}
        if "Accounts Team" in user_roles:
            employee = frappe.get_doc("Employee", {"user_id": usr})
            company_list = [row.company_name for row in employee.company]

            if not company_list:
                return {
                    "status": "error",
                    "message": "No company records found in Employee.",
                    "vendor_onboarding": []
                }

            where_clause = "company_name IN %(company_list)s"
            values["company_list"] = company_list

        else:
            team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
            if not team:
                return {
                    "status": "error",
                    "message": "No Employee record found for the user.",
                    "vendor_onboarding": []
                }

            user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
            if not user_ids:
                return {
                    "status": "error",
                    "message": "No users found in the same team.",
                    "vendor_onboarding": []
                }

            where_clause = "registered_by IN %(user_ids)s"
            values["user_ids"] = user_ids

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values["limit"] = page_length
        values["offset"] = offset

        # Count Query
        total_count = frappe.db.sql(f"""
            SELECT COUNT(*)
            FROM (
                SELECT ref_no
                FROM `tabVendor Onboarding`
                WHERE {where_clause}
                GROUP BY ref_no
            ) AS temp
        """, values)[0][0]

        # Main Query
        onboarding_docs = frappe.db.sql(f"""
            SELECT
                vo.name, vo.ref_no, vo.company_name, vo.company, vo.vendor_name, vo.onboarding_form_status,
                vo.purchase_t_approval, vo.accounts_t_approval, vo.purchase_h_approval,
                vo.mandatory_data_filled, vo.purchase_team_undertaking, vo.accounts_team_undertaking, vo.purchase_head_undertaking,
                vo.form_fully_submitted_by_vendor, vo.sent_registration_email_link, vo.rejected, vo.data_sent_to_sap, vo.expired,
                vo.payee_in_document, vo.check_double_invoice, vo.gr_based_inv_ver, vo.service_based_inv_ver,
                vo.creation, vo.modified
            FROM `tabVendor Onboarding` vo
            INNER JOIN (
                SELECT ref_no, MAX(creation) AS max_creation
                FROM `tabVendor Onboarding`
                WHERE {where_clause}
                GROUP BY ref_no
            ) latest ON vo.ref_no = latest.ref_no AND vo.creation = latest.max_creation
            ORDER BY vo.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        return {
            "status": "success",
            "message": "Total vendor onboarding records fetched successfully.",
            "total_vendor_onboarding": onboarding_docs,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Total Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch total vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }


# need some checking for query records are not match 
# apply a different query so cannot use the above filteration function
@frappe.whitelist(allow_guest=False)
def current_month_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None):
    try:
        if not usr:
            usr = frappe.session.user

        allowed_roles = {"Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        start_date = get_first_day(today())
        end_date = get_last_day(today())

        values = {
            "start_date": start_date,
            "end_date": end_date
        }

        # Build filter clause
        filter_clause = "creation BETWEEN %(start_date)s AND %(end_date)s"

        if "Accounts Team" in user_roles:
            employee = frappe.get_doc("Employee", {"user_id": usr})
            company_list = [row.company_name for row in employee.company]
            if not company_list:
                return {
                    "status": "error",
                    "message": "No company records found in Employee.",
                    "vendor_onboarding": []
                }
            filter_clause += " AND company_name IN %(company_list)s"
            values["company_list"] = company_list
        else:
            team = frappe.db.get_value("Employee", {"user_id": usr}, "team")
            if not team:
                return {
                    "status": "error",
                    "message": "No Employee record found for the user.",
                    "vendor_onboarding": []
                }
            user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
            if not user_ids:
                return {
                    "status": "error",
                    "message": "No users found in the same team.",
                    "vendor_onboarding": []
                }
            filter_clause += " AND registered_by IN %(user_ids)s"
            values["user_ids"] = user_ids

        if company:
            filter_clause += " AND company_name = %(filter_company)s"
            values["filter_company"] = company
        if refno:
            filter_clause += " AND ref_no = %(filter_refno)s"
            values["filter_refno"] = refno

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values["limit"] = page_length
        values["offset"] = offset

        # Count query
        total_count = frappe.db.sql(f"""
            SELECT COUNT(*)
            FROM (
                SELECT ref_no
                FROM `tabVendor Onboarding`
                WHERE {filter_clause}
            ) AS temp
        """, values)[0][0]

        # Main query
        # onboarding_docs = frappe.db.sql(f"""
        #     SELECT
        #         vo.name, vo.ref_no, vo.company_name, vo.company, vo.vendor_name, vo.onboarding_form_status,
        #         vo.purchase_t_approval, vo.accounts_t_approval, vo.purchase_h_approval,
        #         vo.mandatory_data_filled, vo.purchase_team_undertaking, vo.accounts_team_undertaking, vo.purchase_head_undertaking,
        #         vo.form_fully_submitted_by_vendor, vo.sent_registration_email_link, vo.rejected, vo.data_sent_to_sap, vo.expired,
        #         vo.payee_in_document, vo.check_double_invoice, vo.gr_based_inv_ver, vo.service_based_inv_ver,
        #         vo.creation, vo.modified
        #     FROM `tabVendor Onboarding` vo
        #     INNER JOIN (
        #         SELECT ref_no, MAX(creation) AS max_creation
        #         FROM `tabVendor Onboarding`
        #         WHERE {filter_clause}
        #         GROUP BY ref_no
        #     ) latest ON vo.ref_no = latest.ref_no AND vo.creation = latest.max_creation
        #     ORDER BY vo.modified DESC
        #     LIMIT %(limit)s OFFSET %(offset)s
        # """, values, as_dict=True)

        onboarding_docs = frappe.db.sql(f"""
            SELECT
                vo.name, vo.ref_no, vo.company_name, vo.company, vo.vendor_name, vo.onboarding_form_status,
                vo.purchase_t_approval, vo.accounts_t_approval, vo.purchase_h_approval,
                vo.mandatory_data_filled, vo.purchase_team_undertaking, vo.accounts_team_undertaking, vo.purchase_head_undertaking,
                vo.form_fully_submitted_by_vendor, vo.sent_registration_email_link, vo.rejected, vo.data_sent_to_sap, vo.expired,
                vo.payee_in_document, vo.check_double_invoice, vo.gr_based_inv_ver, vo.service_based_inv_ver,
                vo.creation, vo.modified
            FROM `tabVendor Onboarding` vo
            WHERE vo.creation = (
                SELECT MAX(vo2.creation)
                FROM `tabVendor Onboarding` vo2
                WHERE vo2.ref_no = vo.ref_no AND {filter_clause}
            )
            ORDER BY vo.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        return {
            "status": "success",
            "message": "Vendor onboarding records for the current month fetched successfully.",
            "vendor_onboarding": onboarding_docs,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Current Month Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }

