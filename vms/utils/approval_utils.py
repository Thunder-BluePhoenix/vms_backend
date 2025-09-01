import frappe
from vms.utils.utils import to_bool, safe_get
from vms.utils.verify_user import verify_employee
from frappe.utils.caching import redis_cache


def get_approval_next_role(stage) -> str:
    """
    Return the next approver role if the stage requires it, else ''.
    """
    role = safe_get(stage, "role", "")

    if not role:
        return ""

    from_hierarchy = to_bool(safe_get(stage, "from_hierarchy", False))
    is_optional = to_bool(safe_get(stage, "is_optional", False))
    approver_type = safe_get(stage, "approver_type", "").strip().lower()

    if not from_hierarchy and not is_optional and approver_type == "role":
        return role
    return ""


@redis_cache(ttl=60 * 5)  # cache for 5 minutes
def get_approval_users_by_role(doctype: str, docname: str) -> list[str]:
    """
    For the given document, return a de-duplicated list of user IDs
    that are eligible for the next approval step based on role-mapping.
    """
    if not frappe.db.exists(doctype, docname):
        return []

    doc = frappe.get_cached_doc(doctype, docname)
    users = set()

    if doctype == "Purchase Order":
        plant = doc.get("plant_wise")
        if plant:
            # `linked_users` is a child table on Plant Master. Pull the doc and iterate rows.
            plant_doc = frappe.get_cached_doc("Plant Master", plant)
            for row in getattr(plant_doc, "linked_users", []) or []:
                # Support both Doc-like rows and dicts
                user = getattr(row, "user_id", None)
                if user is None and isinstance(row, dict):
                    user = row.get("user_id")
                if user:
                    users.add(user)

    return sorted(users)


def get_user_in_next_approval_role(doctype: str, docname: str) -> str:
    """
    Return the current employee's linked user if (and only if)
    they are part of the next-approval user list for the given doc.
    Empty string if not applicable.
    """
    next_approvers = set(get_approval_users_by_role(doctype, docname))
    if not next_approvers:
        return ""

    employee_id = verify_employee(throw_exception=False)
    if not employee_id:
        return ""

    role_short, linked_user = frappe.get_cached_value(
        "Employee Master", employee_id, ["role_short", "linked_user"]
    ) or (None, None)

    if not linked_user:
        return ""

    # Optional role gate: keep only if you must restrict to certain roles.
    # Example: only allow OPT.
    if (role_short or "").strip().lower() not in {"opt"}:
        return ""

    return linked_user if linked_user in next_approvers else ""
