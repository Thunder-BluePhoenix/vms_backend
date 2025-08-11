import frappe

@frappe.whitelist(allow_guest=True)
def asa_dashboard(vendor_name=None, page_no=1, page_length=10):
    try:
        usr = frappe.session.user

        user_emp = frappe.get_value("Employee", {"user_id": usr}, ["name", "team"], as_dict=True)
        if not user_emp or not user_emp.team:
            return []

        team_emps = frappe.get_all("Employee", filters={"team": user_emp.team}, pluck="user_id")

        vendor_list = frappe.get_all("Vendor Master",
            filters={"registered_by": ["in", team_emps]},
            pluck="name"
        )

        if not vendor_list:
            return []

        filters = {"vendor_ref_no": ["in", vendor_list]}
        if vendor_name:
            filters["vendor_name"] = ["like", f"%{vendor_name}%"]

        start = (page_no - 1) * page_length
        asa_list = frappe.get_all(
            "Annual Supplier Assessment Questionnaire",
            filters=filters,
            fields=["name", "vendor_name", "vendor_ref_no", "creation"],
            order_by="creation desc",
            start=start,
            page_length=page_length
        )

        return asa_list

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="ASA Dashboard Error")
        return []
