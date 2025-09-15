import frappe

from vms.utils.get_employee_for_cur_user import get_employee_name_for_cur_user


def get_approval_employee(role_short, company_list, doc=None, filters={}, fields=["*"]):
    if isinstance(company_list, str):
        company_list = [company_list]

    
    users_with_role = frappe.get_all(
        "Has Role",
        filters={"role": role_short},
        fields=["parent"]
    )
    
    if not users_with_role:
        return None
    
    user_ids_with_role = [user.parent for user in users_with_role]
    
    # Get doctype from doc object
    doctype = doc.get("doctype") if doc else None
    
    # Special handling for Vendor Onboarding doctype
    if doctype == "Vendor Onboarding":
        # Get employees with the required role and active status
        employees_with_role = frappe.get_all(
            "Employee",
            filters={
                "user_id": ("in", user_ids_with_role),
                "status": "Active",
                **filters
            },
            fields=["name", "user_id", "check_team_checkbox"]
        )
        
        if not employees_with_role:
            return None
        
        # Check each employee's checkbox status
        for employee in employees_with_role:
            # If checkbox is checked, apply company filter
            if employee.get("check_team_checkbox"):
                # Check if this employee belongs to the specified companies
                employee_companies = frappe.get_all(
                    "Multiple Company Name",
                    filters={
                        "parent": employee.name,
                        "company_name": ("in", company_list)
                    },
                    fields=["parent"]
                )
                
                # If employee belongs to the company, return this employee
                if employee_companies:
                    # Get the complete employee record with requested fields
                    final_employee = frappe.get_all(
                        "Employee",
                        filters={
                            "name": employee.name,
                            "user_id": ("in", user_ids_with_role),
                            "status": "Active",
                            "check_team_checkbox": 1,
                            **filters
                        },
                        fields=fields,
                        limit=1
                    )
                    return final_employee[0] if final_employee else None
            
            else:
                # If checkbox is not checked, return employee without company filter
                final_employee = frappe.get_all(
                    "Employee",
                    filters={
                        "name": employee.name,
                        "user_id": ("in", user_ids_with_role),
                        "status": "Active",
                        **filters
                    },
                    fields=fields,
                    limit=1
                )
                return final_employee[0] if final_employee else None
        
        return None
    
    else:
        # Original logic for all other doctypes
        # Get employees with companies
        employees_with_companies = frappe.get_all(
            "Multiple Company Name",  
            filters={"company_name": ("in", company_list)},  
            fields=["parent"],
            distinct=True
        )
        
        if not employees_with_companies:
            return None
        
        # Extract employee names
        employee_names = [emp.parent for emp in employees_with_companies]
        
        # Build final filters - combine both conditions
        final_filters = {
            **filters,
            "name": ("in", employee_names),
            "user_id": ("in", user_ids_with_role),  # Users who have the role
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
