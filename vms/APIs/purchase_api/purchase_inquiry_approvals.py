import frappe
import json
from frappe import _

@frappe.whitelist(allow_guest=True)
def hod_approval_check(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        cart_details = data.get("cart_id")
        user = data.get("user")
        is_approved = int(data.get("approve"))
        is_rejected = int(data.get("reject"))
        rejection_reason = data.get("rejected_reason")
        comments = data.get("comments")

        if is_approved and is_rejected:
            frappe.throw(_("Cannot approve and reject at the same time."))

        # Fetch cart details document
        cart_details_doc = frappe.get_doc("Cart Details", cart_details)
        
        if is_approved:
            cart_details_doc.hod_approved = 1
            cart_details_doc.hod_approval_status = "Approved"
            cart_details_doc.hod_approval_remarks = comments
        elif is_rejected:
            cart_details_doc.rejected = 1
            cart_details_doc.rejected_by = user
            cart_details_doc.hod_approval_status = "Rejected"
            cart_details_doc.reason_for_rejection = rejection_reason
        else:
            frappe.throw(_("Invalid request: either approve or reject must be set."))

        cart_details_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Cart details updated successfully.",
            "cart_details": cart_details,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error updating cart details")
        return {
            "status": "error",
            "message": "Failed to update cart details.",
            "error": str(e),
        }


@frappe.whitelist(allow_guest=True)
def purchase_approval_check(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		cart_id = data.get("cart_id")
		user = data.get("user")
		is_approved = int(data.get("approve"))
		is_rejected = int(data.get("reject"))
		rejection_reason = data.get("rejected_reason")
		comments = data.get("comments")

		if is_approved and is_rejected:
			frappe.throw(_("Cannot approve and reject at the same time."))

		# Fetch Cart Details document
		cart_details_doc = frappe.get_doc("Cart Details", cart_id)

		if is_approved:
			cart_details_doc.purchase_team_approved = 1
			cart_details_doc.purchase_team_approval_status = "Approved"
			cart_details_doc.purchase_team_approval_remarks = comments

			for key, value in data.items():
				if isinstance(value, dict) and "product_price" in value:
					child_row = next((row for row in cart_details_doc.cart_product if row.name == key), None)
					if child_row:
						child_row.product_price = value["product_price"]

		elif is_rejected:
			cart_details_doc.rejected = 1
			cart_details_doc.rejected_by = user
			cart_details_doc.purchase_team_approval_status = "Rejected"
			cart_details_doc.reason_for_rejection = rejection_reason

		else:
			frappe.throw(_("Invalid request: either approve or reject must be set."))

		cart_details_doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Cart details updated successfully.",
			"cart_details": cart_id,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error updating cart details")
		return {
			"status": "error",
			"message": "Failed to update cart details.",
			"error": str(e),
		}