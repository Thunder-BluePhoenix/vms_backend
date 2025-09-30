import frappe
@frappe.whitelist(allow_guest=False)
def filtering_total_qms_onboarding(page_no=None, page_length=None, usr=None,  qms_status_filter=None):
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access.",
                "code": 404
            }

        allowed_roles = {"QA Team", "QA Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role. Only QA Team and QA Head are allowed.",
                "qms_onboarding": []
            }

        # Base filters
        conditions = []
        values = {}

        # QMS Required filter - only show records where qms_required = 'Yes'
        conditions.append("vo.qms_required = 'Yes'")

        # Filter based on QA Team/QA Head company
        try:
            employee = frappe.get_doc("Employee", {"user_id": usr})
        except frappe.DoesNotExistError:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "qms_onboarding": []
            }
        
        company_list = [row.company_name for row in employee.company]

        if not company_list:
            return {
                "status": "error",
                "message": "No company records found in Employee.",
                "qms_onboarding": []
            }

        conditions.append("vo.company_name IN %(company_list)s")
        values["company_list"] = company_list

        # Apply QMS status-specific filters
        if qms_status_filter == "pending":
            conditions.append("vo.sent_qms_form_link = 1")
            conditions.append("vo.qms_form_filled = 0")
        elif qms_status_filter == "completed":
            conditions.append("vo.qms_form_filled = 1")
        #


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
                vo.payee_in_document, vo.check_double_invoice, vo.gr_based_inv_ver, vo.service_based_inv_ver, vo.qms_form_filled, vo.sent_qms_form_link,
                vo.registered_by, vo.register_by_account_team, vo.vendor_country, vo.rejected_by, vo.rejected_by_designation, vo.reason_for_rejection, 
                vo.sap_error_mail_sent, vo.qms_required
            FROM `tabVendor Onboarding` vo
            WHERE {filter_clause}
            ORDER BY vo.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        return {
            "status": "success",
            "message": "Filtered QMS onboarding records fetched.",
            "total_qms_onboarding": onboarding_docs,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Filtering Total QMS Onboarding API Error")
        return {
            "status": "error",
            "message": "Failed to filter QMS onboarding data.",
            "error": str(e),
            "qms_onboarding": []
        }


@frappe.whitelist(allow_guest=False)
def total_qms_onboarding_details(page_no=None, page_length=None,  usr=None,):
    try:
        if not usr:
            usr = frappe.session.user

       
        result = filtering_total_qms_onboarding(
            page_no=page_no,
            page_length=page_length,
            usr=usr,
            qms_status_filter=None  
        )

        if result.get("status") != "success":
            return result

        onboarding_docs = result.get("total_qms_onboarding", [])

        return {
            "status": "success",
            "message": "Total QMS onboarding records fetched successfully.",
            "total_qms_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Total QMS Onboarding Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch total QMS onboarding data.",
            "error": str(e),
            "qms_onboarding": []
        }


@frappe.whitelist(allow_guest=False)
def pending_qms_onboarding_details(page_no=None, page_length=None, usr=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Call reusable filter function for pending QMS records
        result = filtering_total_qms_onboarding(
            page_no=page_no,
            page_length=page_length,
            usr=usr,
            qms_status_filter="pending"  
        )

        if result.get("status") != "success":
            return result

        onboarding_docs = result.get("total_qms_onboarding", [])

        return {
            "status": "success",
            "message": "Pending QMS onboarding records fetched successfully.",
            "pending_qms_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Pending QMS Onboarding Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch pending QMS onboarding data.",
            "error": str(e),
            "qms_onboarding": []
        }


@frappe.whitelist(allow_guest=False)
def completed_qms_onboarding_details(page_no=None, page_length=None, usr=None):
    try:
        if not usr:
            usr = frappe.session.user

        
        result = filtering_total_qms_onboarding(
            page_no=page_no,
            page_length=page_length,
            usr=usr,
            qms_status_filter="completed"  
        )

        if result.get("status") != "success":
            return result

        onboarding_docs = result.get("total_qms_onboarding", [])

        return {
            "status": "success",
            "message": "Completed QMS onboarding records fetched successfully.",
            "completed_qms_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Completed QMS Onboarding Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch completed QMS onboarding data.",
            "error": str(e),
            "qms_onboarding": []
        }