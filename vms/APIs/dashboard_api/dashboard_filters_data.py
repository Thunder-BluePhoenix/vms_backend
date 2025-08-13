import frappe
from frappe.utils import today, get_first_day, get_last_day


@frappe.whitelist(allow_guest=False)
def filtering_total_vendor_details(page_no=None, page_length=None, company=None, refno=None, status=None, usr=None, vendor_name=None):
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access.",
                "code": 404
            }

        allowed_roles = {"Purchase Team", "Accounts Team", "Accounts Head", "Purchase Head", "QA Team", "QA Head"}
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

        if "Accounts Team" in user_roles or "Accounts Head" in user_roles:
            # employee = frappe.get_doc("Employee", {"user_id": usr})
            
            # company_list = [row.company_name for row in employee.company]

            # if not company_list:
            #     return {
            #         "status": "error",
            #         "message": "No company records found in Employee.",
            #         "vendor_onboarding": []
            #     }

            # conditions.append("vo.company_name IN %(company_list)s")
            # values["company_list"] = company_list

            vend_onb = frappe.get_all(
                "Vendor Onboarding",
                filters={"register_by_account_team": 1},
                pluck="name"  
            )

            if not vend_onb:
                return {
                    "status": "error",
                    "message": "No vendor onboarding records found for Accounts Team/Head.",
                    "vendor_onboarding": []
                }

            conditions.append("vo.name IN %(vend_onb)s")
            values["vend_onb"] = vend_onb

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

        # if refno:
        #     conditions.append("vo.ref_no = %(refno)s")
        #     values["refno"] = refno

        if refno:
            conditions.append("vo.ref_no LIKE %(refno)s")
            values["refno"] = f"%{refno}%"

        if vendor_name:
            conditions.append("vo.vendor_name LIKE %(vendor_name)s")
            values["vendor_name"] = f"%{vendor_name}%"

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
                vo.name, vo.ref_no, vo.company_name, vo.vendor_name, vo.onboarding_form_status, vo.awaiting_approval_status, vo.modified,
                vo.purchase_t_approval, vo.accounts_t_approval, vo.purchase_h_approval,
                vo.mandatory_data_filled, vo.purchase_team_undertaking, vo.accounts_team_undertaking, vo.purchase_head_undertaking,
                vo.form_fully_submitted_by_vendor, vo.sent_registration_email_link, vo.rejected, vo.data_sent_to_sap, vo.expired,
                vo.payee_in_document, vo.check_double_invoice, vo.gr_based_inv_ver, vo.service_based_inv_ver, vo.qms_form_filled, vo.sent_qms_form_link,
                vo.registered_by, vo.register_by_account_team, vo.vendor_country, vo.rejected_by, vo.rejected_by_designation, vo.reason_for_rejection
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
def approved_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
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
            usr=usr,
            vendor_name=vendor_name
        )

        if result.get("status") != "success":
            return result

        onboarding_docs = result.get("total_vendor_onboarding", [])

        # Enrich with company vendor codes
        for doc in onboarding_docs:
            ref_no = doc.get("ref_no")
            main_company = doc.get("company_name")

            # Fetch all company vendor codes for this ref_no
            company_vendor = frappe.get_all(
                "Company Vendor Code",
                filters={"vendor_ref_no": ref_no},
                fields=["name", "company_name", "company_code"]
            )

            # Prepare only matching company vendor codes
            filtered_codes = []
            for cvc in company_vendor:
                if cvc.company_name == main_company:
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

            # Assign only the filtered codes for this doc
            doc["company_vendor_codes"] = filtered_codes

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
def rejected_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
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
            usr=usr,
            vendor_name=vendor_name
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
def pending_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
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
            usr=usr,
            vendor_name=vendor_name
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
def expired_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
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
            usr=usr,
            vendor_name=vendor_name
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
def total_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
    try:
        if not usr:
            usr = frappe.session.user

        allowed_roles = {"Purchase Team", "Accounts Team", "Accounts Head", "Purchase Head", "QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        values = {}
        filters = []

        if "Accounts Team" in user_roles or "Accounts Head" in user_roles:
            # employee = frappe.get_doc("Employee", {"user_id": usr})
            # company_list = [row.company_name for row in employee.company]
            # if not company_list:
            #     return {
            #         "status": "error",
            #         "message": "No company records found in Employee.",
            #         "vendor_onboarding": []
            #     }
            # filters.append("company_name IN %(company_list)s")
            # values["company_list"] = company_list
            
            vo_names = frappe.get_all(
                "Vendor Onboarding",
                filters={"register_by_account_team": 1},
                pluck="name"
            )

            if not vo_names:
                return {
                    "status": "error",
                    "message": "No vendor onboarding records found for Accounts Team/Head.",
                    "vendor_onboarding": []
                }

            filters.append("name IN %(vo_names)s")
            values["vo_names"] = vo_names

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
            filters.append("registered_by IN %(user_ids)s")
            values["user_ids"] = user_ids

        # if refno:
        #     filters.append("ref_no = %(refno)s")
        #     values["refno"] = refno

        if refno:
            filters.append("ref_no LIKE %(refno)s")
            values["refno"] = f"%{refno}%"

        if vendor_name:
            filters.append("vendor_name LIKE %(vendor_name)s")
            values["vendor_name"] = f"%{vendor_name}%"

        if company:
            filters.append("company = %(company)s")
            values["company"] = company

        where_clause = " AND ".join(filters)

        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values.update({"limit": page_length, "offset": offset})

        total_count = frappe.db.sql(f"""
            SELECT COUNT(*)
            FROM (
                SELECT ref_no
                FROM `tabVendor Onboarding`
                WHERE {where_clause}
                GROUP BY ref_no
            ) AS temp
        """, values)[0][0]

        onboarding_docs = frappe.db.sql(f"""
            SELECT
                vo.name, vo.ref_no, vo.company_name, vo.company, vo.vendor_name, vo.onboarding_form_status, vo.awaiting_approval_status, 
                vo.purchase_t_approval, vo.accounts_t_approval, vo.purchase_h_approval,
                vo.mandatory_data_filled, vo.purchase_team_undertaking, vo.accounts_team_undertaking, vo.purchase_head_undertaking,
                vo.form_fully_submitted_by_vendor, vo.register_by_account_team, vo.sent_registration_email_link, vo.rejected, vo.data_sent_to_sap, vo.expired,
                vo.payee_in_document, vo.check_double_invoice, vo.gr_based_inv_ver, vo.service_based_inv_ver,
                vo.creation, vo.modified
            FROM `tabVendor Onboarding` vo
            WHERE vo.creation = (
                SELECT MAX(vo2.creation)
                FROM `tabVendor Onboarding` vo2
                WHERE vo2.ref_no = vo.ref_no AND {where_clause}
            )
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
def current_month_vendor_details(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
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
        
        # if refno:
        #     filter_clause += " AND ref_no = %(filter_refno)s"
        #     values["filter_refno"] = refno

        if refno:
            filter_clause += " AND ref_no LIKE %(filter_refno)s"
            values["filter_refno"] = f"%{refno}%"

        if vendor_name:
            filter_clause += " AND vendor_name LIKE %(vendor_name)s"
            values["vendor_name"] = f"%{vendor_name}%"

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







@frappe.whitelist(allow_guest=False)
def filtering_total_vendor_details_for_pending(page_no=None, page_length=None, company=None, refno=None, status=None, usr=None, vendor_name=None):
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
        employee = frappe.get_doc("Employee", {"user_id": usr})
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

        # if refno:
        #     conditions.append("vo.ref_no = %(refno)s")
        #     values["refno"] = refno

        if refno:
            conditions.append("vo.ref_no LIKE %(refno)s")
            values["refno"] = f"%{refno}%"

        if vendor_name:
            conditions.append("vo.vendor_name LIKE %(vendor_name)s")
            values["vendor_name"] = f"%{vendor_name}%"

        if status:
            conditions.append("vo.onboarding_form_status = %(status)s")
            values["status"] = status


        if "Accounts Team" in user_roles:
            conditions.append("vo.onboarding_form_status = 'Pending'")
            conditions.append("vo.purchase_head_undertaking = 1")

        elif "Purchase Head" in user_roles:
            conditions.append("vo.onboarding_form_status = 'Pending'")
            conditions.append("vo.purchase_team_undertaking = 1")

        elif "Purchase Team" in user_roles:
            conditions.append("vo.onboarding_form_status = 'Pending'")

        else:
            conditions.append("vo.onboarding_form_status = 'Pending'")


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
            "pending_vendor_onboarding": onboarding_docs,
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


# Vendor brief details of company, documents and bank

@frappe.whitelist(allow_guest=False)
def vendors_brief_details(page_no=None, page_length=None, company=None, vendor_name=None):
    try:
        usr = frappe.session.user

        if "Purchase Team" not in frappe.get_roles(usr):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

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

        conditions = [
            "vo.registered_by IN %(user_ids)s",
            "vo.onboarding_form_status = 'Approved'"
        ]
        values = {"user_ids": user_ids}

        if company:
            conditions.append("vo.company_name = %(company)s")
            values["company"] = company

        if vendor_name:
            conditions.append("vo.vendor_name LIKE %(vendor_name)s")
            values["vendor_name"] = f"%{vendor_name}%"

        filter_clause = " AND ".join(conditions)

        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values["limit"] = page_length
        values["offset"] = offset

        total_count = frappe.db.sql(f"""
            SELECT COUNT(*) AS count
            FROM `tabVendor Onboarding` vo
            WHERE {filter_clause}
        """, values)[0][0]

        onboarding_docs = frappe.db.sql(f"""
            SELECT
                vo.name, vo.ref_no, vo.company_name, vo.vendor_name, vo.onboarding_form_status, vo.modified,
                vo.qms_form_filled, vo.sent_qms_form_link, vo.registered_by, vo.vendor_country,
                vo.document_details, vo.payment_detail
            FROM `tabVendor Onboarding` vo
            WHERE {filter_clause}
            ORDER BY vo.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        # ✅ Enrich vendor data
        for doc in onboarding_docs:
            vo_id = doc.get("name")
            main_company = doc.get("company_name")
            ref_no = doc.get("ref_no")

            filtered_codes = []
            company_vendor = frappe.get_all(
                "Company Vendor Code",
                filters={"vendor_ref_no": ref_no},
                fields=["name", "company_name", "company_code"]
            )
            for cvc in company_vendor:
                if cvc.company_name == main_company:
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
            doc["company_vendor_codes"] = filtered_codes

            if doc.get("document_details"):
                legal_doc = frappe.get_doc("Legal Documents", doc.get("document_details"))
                doc["legal_documents"] = {
                    "company_pan_number": legal_doc.company_pan_number,
                    "msme_enterprise_type": legal_doc.msme_enterprise_type,
                    "udyam_number": legal_doc.udyam_number,
                    "trc_certificate_no": legal_doc.trc_certificate_no
                }

            company_detail = frappe.get_all(
                "Vendor Onboarding Company Details",
                filters={"vendor_onboarding": vo_id},
                fields=["address_line_1", "city", "district", "state", "country", "pincode"],
                limit=1
            )
            doc["company_details"] = company_detail[0] if company_detail else {}

            if doc.get("payment_detail"):
                payment_detail = frappe.get_doc("Vendor Onboarding Payment Details", doc.get("payment_detail"))
                doc["payment_details"] = {
                    "bank_name": payment_detail.bank_name,
                    "ifsc_code": payment_detail.ifsc_code,
                    "account_number": payment_detail.account_number,
                    "name_of_account_holder": payment_detail.name_of_account_holder,
                    "currency_code": payment_detail.currency_code
                }

            vendor_master = frappe.get_all(
                "Vendor Master",
                filters={"name": ref_no},
                fields=["vendor_name", "mobile_number", "office_email_primary", "service_provider_type"],
                limit=1
            )
            doc["vendor_master"] = vendor_master[0] if vendor_master else {}

        return {
            "status": "success",
            "message": "Filtered records fetched.",
            "total_vendor_onboarding": onboarding_docs,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendors Brief Details API Error")
        return {
            "status": "error",
            "message": "Failed to filter vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }
