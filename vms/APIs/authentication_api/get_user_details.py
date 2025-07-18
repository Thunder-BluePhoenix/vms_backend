import frappe
from frappe import _


@frappe.whitelist()
def get_user_details(email):
    """
    Fetches employee details using the user's email (user_id field).
    """
    try:
        if not email:
            frappe.throw(_("Email is required."))

        print(f"Fetching employee record for email: {email}")

        employee_doc = frappe.get_all(
            "Employee",
            filters={"user_id": email},
            fields=["name", "full_name", "designation", "department", "team"]
        )

        if not employee_doc:
            frappe.throw(_("No Employee found for the provided email."))

        return employee_doc[0]  # Since user_id is unique

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching user details"))
        frappe.throw(_("Something went wrong while fetching user details."))
