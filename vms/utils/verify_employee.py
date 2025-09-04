import warnings
import frappe
from vms.utils.verify_user import verify_employee as user_verify_employee


# vms.utils.verify_employee.verify_employee
def verify_employee(user=None):
    """
    DEPRECATED: This function will be removed in a future release.
    Please use the new implementation at:
        vms.utils.verify_user.verify_employee

    :param user: (optional) User to verify; defaults to frappe.session.user
    :returns:    Employee ID (str) or None
    """
    warnings.warn(
        "verify_employee is deprecated; "
        "use vms.utils.verify_user.verify_employee instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return user_verify_employee(user=user, throw_exception=False)


def get_cached_employee_id(user):
    return frappe.cache.get_value(f"employee_id_{user}")
