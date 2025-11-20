
import frappe
from frappe import _


def validate_string(value, field_name="Value", required=True, allow_empty=False, min_length=None, max_length=None):
    
    if value is None:
        if required:
            frappe.throw(
                _(f"{field_name} is required"), 
                frappe.ValidationError
            )
        return None
    
    if not isinstance(value, str):
        frappe.throw(
            _(f"{field_name} must be a string"), 
            frappe.ValidationError
        )
    
    # Strip whitespace
    value = value.strip()
    
    # Check if empty after stripping
    if not value and not allow_empty:
        if required:
            frappe.throw(
                _(f"{field_name} cannot be empty"), 
                frappe.ValidationError
            )
        return None
    
    # Check length constraints
    if min_length is not None and len(value) < min_length:
        frappe.throw(
            _(f"{field_name} must be at least {min_length} characters long"), 
            frappe.ValidationError
        )
    
    if max_length is not None and len(value) > max_length:
        frappe.throw(
            _(f"{field_name} must be at most {max_length} characters long"), 
            frappe.ValidationError
        )
    
    return value


