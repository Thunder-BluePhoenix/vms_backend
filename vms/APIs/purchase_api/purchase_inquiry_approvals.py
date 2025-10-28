import frappe
import json
from frappe import _
from vms.utils.custom_send_mail import custom_sendmail
from datetime import datetime, timedelta


# @frappe.whitelist(allow_guest=True)
# def hod_approval_check(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)

#         cart_details = data.get("cart_id")
#         user = data.get("user")
#         is_approved = int(data.get("approve"))
#         is_rejected = int(data.get("reject"))
#         rejection_reason = data.get("rejected_reason")
#         comments = data.get("comments")

#         if is_approved and is_rejected:
#             frappe.throw(_("Cannot approve and reject at the same time."))

#         # Fetch cart details document
#         cart_details_doc = frappe.get_doc("Cart Details", cart_details)
        
#         if is_approved:
#             cart_details_doc.hod_approved = 1
#             cart_details_doc.hod_approval_status = "Approved"
#             cart_details_doc.hod_approval_remarks = comments
#         elif is_rejected:
#             cart_details_doc.rejected = 1
#             cart_details_doc.rejected_by = user
#             cart_details_doc.hod_approval_status = "Rejected"
#             cart_details_doc.reason_for_rejection = rejection_reason
#         else:
#             frappe.throw(_("Invalid request: either approve or reject must be set."))

#         cart_details_doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Cart details updated successfully.",
#             "cart_details": cart_details,
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Error updating cart details")
#         return {
#             "status": "error",
#             "message": "Failed to update cart details.",
#             "error": str(e),
#         }


@frappe.whitelist(allow_guest=True)
def purchase_approval_check(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		session_user = frappe.session.user
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
			cart_details_doc.purchase_team_approval = session_user
			cart_details_doc.purchase_team_approval_remarks = comments

			# Clear old child rows
			# cart_details_doc.set("cart_product", [])

			for row in data.get("cart_product", []):
				if not row:
					continue
				row_id = row.get("name")
				final_price = row.get("final_price_by_purchase_team")
				for child in cart_details_doc.cart_product:
					if child.name == row_id:
						child.final_price_by_purchase_team = final_price
						break
			


				# cart_details_doc.append("cart_product", {
				# 	"assest_code": row.get("assest_code"),
				# 	"product_name": row.get("product_name"),
				# 	"product_quantity": row.get("product_quantity"),
				# 	"user_specifications": row.get("user_specifications"),
				# 	"product_price": row.get("product_price"),
				# 	"uom": row.get("uom"),
				# 	"lead_time": row.get("lead_time"),
				# 	"final_price_by_purchase_team": row.get("final_price_by_purchase_team")
				# })
					
		elif is_rejected:
			cart_details_doc.rejected = 1
			cart_details_doc.rejected_by = session_user
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

# Email for Second Stage Approval 
@frappe.whitelist(allow_guest=False)
def send_purchase_enquiry_approval_mail(email_id, purchase_enquiry_id, method=None):
    try:
        http_server = frappe.conf.get("backend_http")

        # Get purchase enquiry document
        doc = frappe.get_doc("Cart Details", purchase_enquiry_id)

        if doc.cart_date:
            try:
                cart_date_formatted = doc.cart_date.strftime("%d-%m-%Y")
            except Exception:
                cart_date_formatted = str(doc.cart_date)
        else:
            cart_date_formatted = "N/A"

        # Get requestor details
        requestor_name = frappe.session.user
        if email_id:
            employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")

            second_stage_user = frappe.get_value("User", {"email": email_id}, "name")
            second_stage_name = frappe.get_value("User", second_stage_user, "full_name")

            hod_approval = frappe.get_value("User", doc.hod_approval, "full_name")
            purchase_team_approval = frappe.get_value("User", doc.purchase_team_approval, "full_name")

        if email_id:
            # Create approval and reject URLs
            approve_url = f"{http_server}/api/method/vms.APIs.purchase_api.purchase_inquiry_approvals.second_stage_approval_check?cart_id={doc.name}&email={email_id}&action=approve"
            reject_url = f"{http_server}/api/method/vms.APIs.purchase_api.purchase_inquiry_approvals.second_stage_approval_check?cart_id={doc.name}&email={email_id}&action=reject"

            table_html = """
                <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                    <tr>
                        <th>Asset Code</th>
                        <th>Product Name</th>
                        <th>Product Quantity</th>
                        <th>UOM</th>
                        <th>Product Price</th>
                        <th>Lead Time</th>
                        <th>User Specifications</th>
                        <th>Final Price</th>
                    </tr>
            """

            for row in doc.cart_product:
                table_html += f"""
                    <tr>
                        <td>{row.assest_code or ''}</td>
                        <td>{frappe.db.get_value("VMS Product Master", row.product_name, "product_name") or ''}</td>
                        <td>{row.product_quantity or ''}</td>
                        <td>{row.uom or ''}</td>
                        <td>{row.product_price or ''}</td>
                        <td>{row.lead_time or ''}</td> 
                        <td>{row.user_specifications or ''}</td>
                        <td>{row.final_price_by_purchase_team or ''}</td>
                    </tr>
                """

            table_html += "</table>"

            subject = f"Additional Approval of Cart Details Submitted by {employee_name if employee_name else 'user'} - {doc.name}"

            # Message for HOD with buttons Additional Approver
            hod_message = f"""
                <p>Dear {second_stage_name if second_stage_name else 'user'},</p>		
                <p>A new cart details submission has been made by <b>{employee_name if employee_name else 'user'}</b> which is approved by {purchase_team_approval if purchase_team_approval else 'user'}(Purchase Team) and also by {hod_approval if hod_approval else 'user'}(HOD)</p>
                <p>and it is sent to you Second stage for further approval.</p>
                <p>Please review the details and take necessary actions.</p>
                <p><b>Cart ID:</b> {doc.name}</p>
                <p><b>Cart Date:</b> {cart_date_formatted}</p>
                <p><b>Cart Products:</b></p>
                {table_html}
                <br>
                <div style="margin: 20px 0px; text-align: center;">
                    <a href="{approve_url}" style="display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px;">
                        Approve
                    </a>
                    <a href="{reject_url}" style="display: inline-block; padding: 10px 20px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 4px;">
                        Reject
                    </a>
                </div>
                <p>Thank you!</p>
            """

            # Message for user (without buttons)
            user_message = f"""
                <p>Dear {employee_name if employee_name else 'user'},</p>
                <p>Your cart has been approved by Purchase Team and sent to your Second stage <b>{second_stage_name if second_stage_name else 'user'}</b> for further approval.</p>
                <p><b>Cart ID:</b> {doc.name}</p>
                <p><b>Cart Date:</b> {cart_date_formatted}</p>
                <p><b>Cart Products:</b></p>
                {table_html}
                <p>Thank you!</p>
            """

            # Send to HOD
            frappe.custom_sendmail(
                recipients=[email_id],
                subject=subject,
                message=hod_message,
                now=True
            )

            # Send to User separately (without buttons)
            frappe.custom_sendmail(
                recipients=[doc.user],
                subject=subject,
                message=user_message,
                now=True
            )

            frappe.set_value("Cart Details", doc.name, "mail_sent_to_second_stage_approval", 1)
            frappe.set_value("Cart Details", doc.name, "is_requested_second_stage_approval", 1)
            frappe.db.commit()

            return {
                "status": "success",
                "message": "Email sent to Second stage user successfully."
            }
        else:
            return {
                "status": "error",
                "message": "Second Stage Approver email or user email not found.",
                "error": "No email address associated with the HOD."
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error sending purchase enquiry approval email")
        return {
            "status": "error",
            "message": "Failed to send email to approver.",
            "error": str(e)
        }



@frappe.whitelist(allow_guest=True)
def second_stage_approval_check():
    try:
        session_user = frappe.session.user
        cart_id = frappe.form_dict.get("cart_id")
        user = frappe.form_dict.get("email")
        action = frappe.form_dict.get("action")
        comments = frappe.form_dict.get("comments") or ""
        reason_for_rejection = frappe.form_dict.get("rejection_reason") or ""

        if not cart_id or not user or not action:
            return {
                "status": "error",
                "message": "Missing required parameters."
            }

        cart_details_doc = frappe.get_doc("Cart Details", cart_id)

        if action == "approve":
            cart_details_doc.second_stage_approved = 1
            cart_details_doc.second_stage_approval_status = "Approved"
            cart_details_doc.second_stage_approval_remark = "Approved by " + user
            cart_details_doc.second_stage_approval_by = session_user
        elif action == "reject":
            cart_details_doc.rejected = 1
            cart_details_doc.rejected_by = session_user
            cart_details_doc.hod_approval_status = "Rejected"
            cart_details_doc.reason_for_rejection = reason_for_rejection
        else:
            frappe.throw(_("Invalid request: either approve or reject must be set."))

        cart_details_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Your response has been recorded for Cart ID: {cart_id}",
            "status_value": cart_details_doc.hod_approval_status,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error updating cart details")
        return {
            "status": "error",
            "message": "Failed to update cart details.",
            "error": str(e),
        }
