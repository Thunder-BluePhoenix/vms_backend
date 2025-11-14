# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe

def get_context(context):
	"""
	Context handler for HOD rejection form page
	This ensures proper CSRF token is available for guest users
	"""
	# Allow guest access to this page
	frappe.flags.ignore_permissions = True

	# Get parameters from URL
	cart_id = frappe.form_dict.get('cart_id')
	user = frappe.form_dict.get('user')

	# Validate required parameters
	if not cart_id or not user:
		context.error_message = "Invalid URL parameters. Cart ID and User are required."
		context.cart_id = None
		context.user = None
		return context

	# Verify cart exists
	try:
		cart_exists = frappe.db.exists("Cart Details", cart_id)
		if not cart_exists:
			context.error_message = f"Cart with ID '{cart_id}' does not exist."
			context.cart_id = cart_id
			context.user = user
			return context
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error checking cart existence")
		context.error_message = "An error occurred while validating the cart."
		context.cart_id = cart_id
		context.user = user
		return context

	# Set context variables
	context.cart_id = cart_id
	context.user = user
	context.error_message = None

	# Ensure CSRF token is available
	context.csrf_token = frappe.sessions.get_csrf_token()

	return context
