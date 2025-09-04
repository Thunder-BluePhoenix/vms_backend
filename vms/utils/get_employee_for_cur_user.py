import frappe
from vms.utils.verify_employee import verify_employee


def get_employee_name_for_cur_user():
    user = frappe.session.user
    employee_id = verify_employee()
    employee_info = frappe.get_all(
        "Employee Master", fields=["*"], filters={"name": employee_id}
    )

    if not employee_info:
        frappe.throw("Employee not found for the current user.")

    return employee_info[0].name


def get_employee_info_for_cur_user(fields=["*"]):
    user = frappe.session.user
    employee_id = verify_employee()
    employee_info = frappe.get_all(
        "Employee Master", fields=fields, filters={"name": employee_id}
    )

    if not employee_info:
        frappe.throw("Employee not found for the current user.")

    return employee_info[0]
