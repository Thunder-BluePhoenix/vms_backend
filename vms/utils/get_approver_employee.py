import frappe

from vms.utils.get_employee_for_cur_user import get_employee_name_for_cur_user


def get_approval_employee(role_short, company_list, filters={}, fields=["*"]):
    # Handle single company or list of companies
    if isinstance(company_list, str):
        company_list = [company_list]
    
    # Get employees who have any of the required companies
    employees_with_companies = frappe.get_all(
        "Company Master",
        filters={"name": ("in", company_list)},
        fields=["parent"]
    )
    
    if not employees_with_companies:
        return None
    
    # Extract employee names
    employee_names = [emp.parent for emp in employees_with_companies]
    
    # Build final filters
    final_filters = {
        **filters,
        "name": ("in", employee_names),
        "user_id": ("is", "set"),
        "status": "Active",  
    }
    
    employee_list = frappe.get_all(
        "Employee", 
        filters=final_filters, 
        fields=fields, 
        limit=1
    )

    return employee_list[0] if employee_list else None
def get_approval_employee_by_state_for_rdm(
    state, role_short, company_list, filters={}, fields=["*"]
):
    emp_parent_dict = frappe.get_all(
        "Employee Select State",
        {"parenttype": "Employee", "state": state},
        "parent",
    )
    emp_parent = [item["parent"] for item in emp_parent_dict]
    filters = {
        **filters,
        "name": ("in", emp_parent),
        "is_active": 1,
    }
    employee_list = frappe.get_all(
        "Employee", filters=filters, fields=fields, limit=1
    )

    return employee_list[0] if employee_list else None


def get_user_for_role_short(name, role_short, depth=0, check_cur_user=False):
    frappe.logger("get_user_for_role_short").error([name, role_short, depth])
    # Check if maximum depth reached or employee not found
    if depth > 5 or not name:
        return None

    employee = frappe.get_doc("Employee", name)

    if (check_cur_user or depth > 0) and employee.get("role_short") == role_short:
        return employee

    return get_user_for_role_short(
        employee.get("reporting_head", None), role_short, depth + 1
    )


def get_fd_for_cur_user():
    return get_user_for_role_short(get_employee_name_for_cur_user(), "FD")
