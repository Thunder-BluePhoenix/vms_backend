import frappe

@frappe.whitelist(allow_guest=True)
def asa_dashboard(vendor_name=None, page_no=1, page_length=5):
    try:
        usr = frappe.session.user
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length

        user_emp = frappe.get_value("Employee", {"user_id": usr}, ["name", "team"], as_dict=True)
        if not user_emp or not user_emp.team:
            return {
                "status": "success",
                "message": "No team assigned to this user",
                "data": [],
                "total_count": 0,
                "overall_total_asa": 0
            }

        team_emps = frappe.get_all("Employee", filters={"team": user_emp.team}, pluck="user_id")

        vendor_list = frappe.get_all(
            "Vendor Master",
            filters={"registered_by": ["in", team_emps]},
            pluck="name"
        )

        if not vendor_list:
            return {
                "status": "success",
                "message": "No vendors found for team",
                "data": [],
                "total_count": 0,
                "overall_total_asa": 0
            }

        filters = {"vendor_ref_no": ["in", vendor_list]}
        if vendor_name:
            filters["vendor_name"] = ["like", f"%{vendor_name}%"]

        total_count = frappe.db.count(
            "Annual Supplier Assessment Questionnaire",
            filters=filters
        )

        overall_total_asa = frappe.db.count(
            "Annual Supplier Assessment Questionnaire",
            filters={"vendor_ref_no": ["in", vendor_list]}
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
