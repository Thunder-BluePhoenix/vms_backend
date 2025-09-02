import frappe
from werkzeug.exceptions import UnprocessableEntity
from typing import Optional


def _verify_linked_user(
    user: Optional[str],
    doctype: str,
    linked_field: str,
    cache_prefix: str,
    throw_exception: bool,
    error_message: str,
) -> Optional[str]:
    """
    Internal helper: verify a DocType record linked to a Frappe user, with cache.

    :param user:            Frappe user ID (defaults to frappe.session.user)
    :param doctype:         Name of the DocType to query (e.g. "Distributor Master")
    :param linked_field:    Name of the field in that DocType which holds the user
    :param cache_prefix:    Prefix for the cache key (e.g. "distributor_id")
    :param throw_exception: Whether to raise if no record is found
    :param error_message:   Message for the UnprocessableEntity exception
    :return:                The record name (ID) or None
    :raises:                UnprocessableEntity if not found and throw_exception=True
    """
    user = user or frappe.session.user
    cache_key = f"{cache_prefix}_{user}"

    # Try cache first
    cached = frappe.cache.get_value(cache_key)
    if cached:
        return cached

    # Lookup in database
    record_id = frappe.get_value(doctype, {linked_field: user}, "name")

    if record_id:
        frappe.cache.set_value(cache_key, record_id)

    if throw_exception and not record_id:
        raise UnprocessableEntity(error_message)

    return record_id


def verify_distributor(
    user: Optional[str] = None, throw_exception: bool = True
) -> Optional[str]:
    """
    Verify and return the Distributor Master record linked to a user.

    :param user:            Frappe user ID (defaults to frappe.session.user)
    :param throw_exception: Whether to raise if no distributor is found
    :return:                Distributor ID (str) or None
    :raises:                UnprocessableEntity if not found and throw_exception=True
    """
    return _verify_linked_user(
        user=user,
        doctype="Distributor Master",
        linked_field="linked_user",
        cache_prefix="distributor_id",
        throw_exception=throw_exception,
        error_message="Distributor not found",
    )


def verify_employee(
    user: Optional[str] = None, throw_exception: bool = True
) -> Optional[str]:
    """
    Verify and return the Employee Master record linked to a user.

    :param user:            Frappe user ID (defaults to frappe.session.user)
    :param throw_exception: Whether to raise if no employee is found
    :return:                Employee ID (str) or None
    :raises:                UnprocessableEntity if not found and throw_exception=True
    """
    return _verify_linked_user(
        user=user,
        doctype="Employee Master",
        linked_field="linked_user",
        cache_prefix="employee_id",
        throw_exception=throw_exception,
        error_message="Employee not found",
    )


def verify_sales_executive_person(
    user: Optional[str] = None, throw_exception: bool = True
) -> Optional[str]:
    """
    Verify and return the Sales Executive Profile record linked to a user.

    :param user:            Frappe user ID (defaults to frappe.session.user)
    :param throw_exception: Whether to raise if no sales executive is found
    :return:                Sales Executive Profile ID (str) or None
    :raises:                UnprocessableEntity if not found and throw_exception=True
    """
    return _verify_linked_user(
        user=user,
        doctype="Sales Executive Profile",
        linked_field="linked_user",
        cache_prefix="sales_executive_id",
        throw_exception=throw_exception,
        error_message="Sales Executive not found",
    )


def get_current_user_document(user=None):
    user = user or frappe.session.user  

    # Log user for debugging
    frappe.logger("user_document").error(user)

    # Search in different masters safely
    for doctype, phone_field in [
        ("Employee", "mobile")
    ]:
        result = frappe.get_value(doctype, {"user_id": user}, ["name", phone_field])
        if result:
            user_document, mobile_number = result
            return user_document, mobile_number


    frappe.logger("user_document").warning(f"No linked record found for user: {user}")
    return None, None
