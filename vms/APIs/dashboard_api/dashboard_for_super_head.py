import frappe

@frappe.whitelist(allow_guest=True)
def team_filter_options():
    try:
        teams = frappe.db.sql(
            "SELECT name, team_name FROM `tabTeam Master`",
            as_dict=True
        )

        # Add "All" option at the top
        teams.insert(0, {
            "name": "All",
            "team_name": "All"
        })

        return {
            "teams": teams
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(f"Error in team_filter_options: {str(e)}", "Team Filter Options")
        return {
            "error": "An error occurred while fetching team options."
        }


# for accounts team
@frappe.whitelist(allow_guest=False)
def filtering_total_vendor_details_by_accounts(page_no=None, page_length=None, company=None, refno=None, status=None, usr=None, vendor_name=None):
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access.",
                "code": 404
            }

        allowed_roles = {"Super Head"}
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

        vend_onb = frappe.get_all(
            "Vendor Onboarding",
            filters={"register_by_account_team": 1},
            pluck="name"  
        )

        if not vend_onb:
            return {
                "status": "error",
                "message": "No vendor onboarding records found for Accounts Team.",
                "vendor_onboarding": []
            }

        conditions.append("vo.name IN %(vend_onb)s")
        values["vend_onb"] = vend_onb

        if company:
            conditions.append("vo.company_name = %(company)s")
            values["company"] = company

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
                vo.registered_by, vo.register_by_account_team, vo.vendor_country, vo.rejected_by, vo.rejected_by_designation, vo.reason_for_rejection, 
                vo.sap_error_mail_sent,
                
                
                registered_user.full_name as registered_by_full_name,
                purchase_t_user.full_name as purchase_t_approval_full_name,
                accounts_t_user.full_name as accounts_t_approval_full_name,
                purchase_h_user.full_name as purchase_h_approval_full_name,
                rejected_user.full_name as rejected_by_full_name
                
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabUser` registered_user ON vo.registered_by = registered_user.name
            LEFT JOIN `tabUser` purchase_t_user ON vo.purchase_t_approval = purchase_t_user.name
            LEFT JOIN `tabUser` accounts_t_user ON vo.accounts_t_approval = accounts_t_user.name
            LEFT JOIN `tabUser` purchase_h_user ON vo.purchase_h_approval = purchase_h_user.name
            LEFT JOIN `tabUser` rejected_user ON vo.rejected_by = rejected_user.name
            WHERE {filter_clause}
            ORDER BY vo.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        

        # Post-process to handle cases where full_name might be empty
        for doc in onboarding_docs:
            # If full_name is empty, fallback to first_name or email
            if doc.get('registered_by') and not doc.get('registered_by_full_name'):
                user_info = frappe.get_value("User", {"email": doc['registered_by']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['registered_by_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['registered_by']
                else:
                    doc['registered_by_full_name'] = doc['registered_by']
            
            if doc.get('purchase_t_approval') and not doc.get('purchase_t_approval_full_name'):
                user_info = frappe.get_value("User", {"email": doc['purchase_t_approval']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['purchase_t_approval_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['purchase_t_approval']
                else:
                    doc['purchase_t_approval_full_name'] = doc['purchase_t_approval']
            
            if doc.get('accounts_t_approval') and not doc.get('accounts_t_approval_full_name'):
                user_info = frappe.get_value("User", {"email": doc['accounts_t_approval']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['accounts_t_approval_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['accounts_t_approval']
                else:
                    doc['accounts_t_approval_full_name'] = doc['accounts_t_approval']
            
            if doc.get('purchase_h_approval') and not doc.get('purchase_h_approval_full_name'):
                user_info = frappe.get_value("User", {"email": doc['purchase_h_approval']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['purchase_h_approval_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['purchase_h_approval']
                else:
                    doc['purchase_h_approval_full_name'] = doc['purchase_h_approval']
            
            if doc.get('rejected_by') and not doc.get('rejected_by_full_name'):
                user_info = frappe.get_value("User", {"email": doc['rejected_by']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['rejected_by_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['rejected_by']
                else:
                    doc['rejected_by_full_name'] = doc['rejected_by']


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
def approved_vendor_details_by_accounts(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Approved for this API
        status = "Approved"

        # Call reusable filter function
        result = filtering_total_vendor_details_by_accounts(
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
def rejected_vendor_details_by_accounts(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Rejected for this API
        status = "Rejected"

        # Call reusable filter function
        result = filtering_total_vendor_details_by_accounts(
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
def pending_vendor_details_by_accounts(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Pending for this API
        status = "Pending"

        # Call reusable filter function
        result = filtering_total_vendor_details_by_accounts(
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
def expired_vendor_details_by_accounts(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Expired for this API
        status = "Expired"

        # Call reusable filter function
        result = filtering_total_vendor_details_by_accounts(
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
    
@frappe.whitelist(allow_guest=False)
def sap_error_vendor_details_by_accounts(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None):
    try:
        if not usr:
            usr = frappe.session.user

        status = "SAP Error"

        result = filtering_total_vendor_details_by_accounts(
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
            "message": "SAP Error vendor onboarding records fetched successfully.",
            "sap_error_vendor_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "SAP Error Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch SAP Error vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }

# for Purchase Team
@frappe.whitelist(allow_guest=False)
def filtering_total_vendor_details_by_purchase(page_no=None, page_length=None, company=None, refno=None, status=None, usr=None, vendor_name=None, team=None):
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access."
            }

        allowed_roles = {"Super Head"}
        user_roles = frappe.get_roles(usr)

        if not any(role in allowed_roles for role in user_roles):
            return {
                "status": "error",
                "message": "User does not have the required role.",
                "vendor_onboarding": []
            }

        conditions = ["vo.register_by_account_team = 0"]  
        values = {}

        if team:
            user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
            if not user_ids:
                return {
                    "status": "error",
                    "message": "No users found in the given team.",
                    "vendor_onboarding": []
                }
            conditions.append("vo.registered_by IN %(user_ids)s")
            values["user_ids"] = user_ids

        # Optional filters
        if company:
            conditions.append("vo.company_name = %(company)s")
            values["company"] = company

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
                vo.registered_by, vo.register_by_account_team, vo.vendor_country, vo.rejected_by, vo.rejected_by_designation, vo.reason_for_rejection, 
                vo.sap_error_mail_sent,
                
                
                registered_user.full_name as registered_by_full_name,
                purchase_t_user.full_name as purchase_t_approval_full_name,
                accounts_t_user.full_name as accounts_t_approval_full_name,
                purchase_h_user.full_name as purchase_h_approval_full_name,
                rejected_user.full_name as rejected_by_full_name
                
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabUser` registered_user ON vo.registered_by = registered_user.name
            LEFT JOIN `tabUser` purchase_t_user ON vo.purchase_t_approval = purchase_t_user.name
            LEFT JOIN `tabUser` accounts_t_user ON vo.accounts_t_approval = accounts_t_user.name
            LEFT JOIN `tabUser` purchase_h_user ON vo.purchase_h_approval = purchase_h_user.name
            LEFT JOIN `tabUser` rejected_user ON vo.rejected_by = rejected_user.name
            WHERE {filter_clause}
            ORDER BY vo.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        

        # Post-process to handle cases where full_name might be empty
        for doc in onboarding_docs:
            # If full_name is empty, fallback to first_name or email
            if doc.get('registered_by') and not doc.get('registered_by_full_name'):
                user_info = frappe.get_value("User", {"email": doc['registered_by']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['registered_by_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['registered_by']
                else:
                    doc['registered_by_full_name'] = doc['registered_by']
            
            if doc.get('purchase_t_approval') and not doc.get('purchase_t_approval_full_name'):
                user_info = frappe.get_value("User", {"email": doc['purchase_t_approval']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['purchase_t_approval_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['purchase_t_approval']
                else:
                    doc['purchase_t_approval_full_name'] = doc['purchase_t_approval']
            
            if doc.get('accounts_t_approval') and not doc.get('accounts_t_approval_full_name'):
                user_info = frappe.get_value("User", {"email": doc['accounts_t_approval']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['accounts_t_approval_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['accounts_t_approval']
                else:
                    doc['accounts_t_approval_full_name'] = doc['accounts_t_approval']
            
            if doc.get('purchase_h_approval') and not doc.get('purchase_h_approval_full_name'):
                user_info = frappe.get_value("User", {"email": doc['purchase_h_approval']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['purchase_h_approval_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['purchase_h_approval']
                else:
                    doc['purchase_h_approval_full_name'] = doc['purchase_h_approval']
            
            if doc.get('rejected_by') and not doc.get('rejected_by_full_name'):
                user_info = frappe.get_value("User", {"email": doc['rejected_by']}, 
                                           ["first_name", "full_name"], as_dict=True)
                if user_info:
                    doc['rejected_by_full_name'] = user_info.get('full_name') or user_info.get('first_name') or doc['rejected_by']
                else:
                    doc['rejected_by_full_name'] = doc['rejected_by']


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
def approved_vendor_details_by_purchase(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None, team=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Approved for this API
        status = "Approved"

        # Call reusable filter function
        result = filtering_total_vendor_details_by_purchase(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr,
            vendor_name=vendor_name,
            team=team
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
def rejected_vendor_details_by_purchase(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None, team=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Rejected for this API
        status = "Rejected"

        # Call reusable filter function
        result = filtering_total_vendor_details_by_purchase(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr,
            vendor_name=vendor_name,
            team=team
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
def pending_vendor_details_by_purchase(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None, team=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Pending for this API
        status = "Pending"

        # Call reusable filter function
        result = filtering_total_vendor_details_by_purchase(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr,
            vendor_name=vendor_name,
            team=team
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
def expired_vendor_details_by_purchase(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None, team=None):
    try:
        if not usr:
            usr = frappe.session.user

        # Always set status to Expired for this API
        status = "Expired"

        # Call reusable filter function
        result = filtering_total_vendor_details_by_purchase(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr,
            vendor_name=vendor_name,
            team=team
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
    
@frappe.whitelist(allow_guest=False)
def sap_error_vendor_details_by_purchase(page_no=None, page_length=None, company=None, refno=None, usr=None, vendor_name=None, team=None):
    try:
        if not usr:
            usr = frappe.session.user

        status = "SAP Error"

        result = filtering_total_vendor_details_by_purchase(
            page_no=page_no,
            page_length=page_length,
            company=company,
            refno=refno,
            status=status,
            usr=usr,
            vendor_name=vendor_name,
            team=team
        )
        if result.get("status") != "success":
            return result
        
        onboarding_docs = result.get("total_vendor_onboarding", [])
        return {
            "status": "success",
            "message": "SAP Error vendor onboarding records fetched successfully.",
            "sap_error_vendor_onboarding": onboarding_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "SAP Error Vendor Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch SAP Error vendor onboarding data.",
            "error": str(e),
            "vendor_onboarding": []
        }