import frappe

from vms.utils.get_employee_for_cur_user import get_employee_name_for_cur_user


def get_approval_employee(role_short, company_list, filters={}, fields=["*"]):
    # Build the base filters for Employee
    base_filters = {
        **filters,
        "user_id": ("is", "set"),
        "is_active": 1,
    }
    
    
    company_tuple = tuple(company_list) if isinstance(company_list, list) else (company_list,)
    
    # Build field list for SQL
    field_str = ", ".join([f"emp.{field}" for field in fields]) if fields != ["*"] else "emp.*"
    
    # SQL query with JOIN to child table
    sql_query = f"""
        SELECT DISTINCT {field_str}
        FROM `tabEmployee` emp
        INNER JOIN `tabCompany Master` comp ON comp.parent = emp.name
        WHERE comp.company_name IN %(companies)s
        AND emp.user_id IS NOT NULL
        AND emp.user_id != ''
        AND emp.status = 'Active
    """
    
    for key, value in base_filters.items():
        if key not in ["'user_id", "is_active"]:
            if isinstance(value, tuple) and value[0] == "in":
                values_str = "', '".join(str(v) for v in value[1])
                sql_query += f" AND emp.{key} IN ('{values_str}')"
            elif isinstance(value, tuple) and value[0] == "is":
                if value[1] == "set":
                    sql_query += f" AND emp.{key} IS NOT NULL AND emp.{key} != ''"
                else:
                    sql_query += f" AND (emp.{key} IS NULL OR emp.{key} = '')"
            else:
                sql_query += f" AND emp.{key} = '{value}'"
    
    sql_query += " LIMIT 1"
    
    result = frappe.db.sql(sql_query, {"companies": company_tuple}, as_dict=True)
    
    return result[0] if result else None

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
