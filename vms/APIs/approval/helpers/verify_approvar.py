import frappe

from vms.utils.get_approver_employee import get_approval_employee


def verify_approver(user, stage):
    if stage.approver_type.lower() == "user" and stage.user == user:
        return None
    elif stage.approver_type.lower() == "role" and stage.role in frappe.get_roles(user):
        return None

    frappe.throw("You are not authorized to initiate this approval.")


def verify_approver_by_role_short(user, stage, zone, role_short, company_list):
    if stage.approver_type.lower() == "user" and stage.user == user:
        return None
    elif (
        zone
        and role_short
        and stage.approver_type.lower() == "role"
        and get_approval_employee(zone, role_short, company_list)
    ):
        return None

    frappe.throw("You are not authorized to initiate this approval.")
