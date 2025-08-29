import frappe


def validate_action(action: str):
    valid_actions = ["Approved", "Rejected"]

    if action not in valid_actions:
        frappe.throw(
            f"Invalid action: {action}. Action must be 'Approved' or 'Rejected'."
        )
