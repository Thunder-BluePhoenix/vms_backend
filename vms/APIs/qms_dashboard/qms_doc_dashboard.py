import frappe
@frappe.whitelist(allow_guest=False)
def filtering_total_qms(page_no=None, page_length=None, usr=None,  status=None):
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
                "Supplier QMS": []
            }

        # Base filters
        conditions = []
        values = {}


        try:
            employee = frappe.get_doc("Employee", {"user_id": usr})
        except frappe.DoesNotExistError:
            return {
                "status": "error",
                "message": "No Employee record found for the user.",
                "Supplier QMS": []
            }
        
        company_names_from_employee = [row.company_name for row in employee.company]
        company_list = []
        
        for company_name in company_names_from_employee:
            try:
                company_doc = frappe.get_doc("Company Master", company_name)
                company_list.append(company_doc.name)  
            except frappe.DoesNotExistError:
               
                continue

        if not company_list:
            return {
                "status": "error",
                "message": "No company records found in Employee.",
                "Supplier QMS": []
            }

        conditions.append("qms.company IN %(company_list)s")
        values["company_list"] = company_list

        if status:
            conditions.append("qms.status = %(status)s")
            values["status"] = status


        filter_clause = " AND ".join(conditions)

        # Total count for pagination
        total_count = frappe.db.sql(f"""
            SELECT COUNT(*) AS count
            FROM `tabSupplier QMS Assessment Form` qms
            WHERE {filter_clause}
        """, values)[0][0]

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values["limit"] = page_length
        values["offset"] = offset

        supplier_qms_docs = frappe.db.sql(f"""
            SELECT
                qms.unique_name, qms.organization_name , qms.vendor_onboarding, qms.company,qms.ref_no, qms.vendor_name1,
                qms.status, qms.date1
                
            FROM `tabSupplier QMS Assessment Form` qms
            WHERE {filter_clause}
            ORDER BY qms.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        return {
            "status": "success",
            "message": "Filtered Supplier QMS records fetched.",
            "total_supplier_qms": supplier_qms_docs,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Filtering Total Supplier QMS Doc API Error")
        return {
            "status": "error",
            "message": "Failed to filter Supplier QMS data.",
            "error": str(e),
            "supplier_qms": []
        }


@frappe.whitelist(allow_guest=False)
def draft_qms_details(page_no=None, page_length=None,  usr=None,status=None):
    try:
        if not usr:
            usr = frappe.session.user

        status = "Draft"
       
        result = filtering_total_qms(
            page_no=page_no,
            page_length=page_length,
            usr=usr,
            status=status
        )

        if result.get("status") != "success":
            return result

        supplier_qms_docs = result.get("total_supplier_qms", [])

        return {
            "status": "success",
            "message": "Draft Supplier QMS  records fetched successfully.",
            "draft_supplier_qms": supplier_qms_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Draft Supplier QMS Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch Draft Supplier QMS records data.",
            "error": str(e),
            "supplier_qms": []
        }


@frappe.whitelist(allow_guest=False)
def approved_qms_details(page_no=None, page_length=None,  usr=None,status=None):
    try:
        if not usr:
            usr = frappe.session.user

        status = "Approved"
       
        result = filtering_total_qms(
            page_no=page_no,
            page_length=page_length,
            usr=usr,
            status=status
        )

        if result.get("status") != "success":
            return result

        supplier_qms_docs = result.get("total_supplier_qms", [])

        return {
            "status": "success",
            "message": "Approved Supplier QMS  records fetched successfully.",
            "approved_supplier_qms": supplier_qms_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Approved Supplier QMS Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch Approved Supplier QMS records data.",
            "error": str(e),
            "supplier_qms": []
        }


@frappe.whitelist(allow_guest=False)
def rejected_qms_details(page_no=None, page_length=None,  usr=None,status=None):
    try:
        if not usr:
            usr = frappe.session.user

        status = "Rejected"
       
        result = filtering_total_qms(
            page_no=page_no,
            page_length=page_length,
            usr=usr,
            status=status
        )

        if result.get("status") != "success":
            return result

        supplier_qms_docs = result.get("total_supplier_qms", [])

        return {
            "status": "success",
            "message": "Rejected Supplier QMS  records fetched successfully.",
            "rejected_supplier_qms": supplier_qms_docs,
            "total_count": result.get("total_count"),
            "page_no": result.get("page_no"),
            "page_length": result.get("page_length")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Rejected Supplier QMS Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch Rejected Supplier QMS records data.",
            "error": str(e),
            "supplier_qms": []
        }