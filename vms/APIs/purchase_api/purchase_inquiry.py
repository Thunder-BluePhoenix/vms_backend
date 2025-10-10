import frappe
import json
from frappe.utils import now_datetime
from frappe import _
from vms.utils.custom_send_mail import custom_sendmail
import json
from datetime import datetime, timedelta


# cart details masters
@frappe.whitelist(allow_guest=True)
def cart_details_masters():
    try:
        category_type = frappe.db.sql("select name, category_name from `tabCategory Master`", as_dict=True)
        uom_master = frappe.db.sql("select name, uom, uom_code, description from `tabUOM Master`", as_dict=True)

        return {
            "category_type": category_type,
            "uom_master": uom_master
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching cart details masters")
        return {"error": str(e)}
    
# filter product name based on category type    
@frappe.whitelist(allow_guest=True)
def filter_product_name(category_type=None):
    try:
        if category_type:
            result = frappe.get_all(
                "VMS Product Master",
                filters={"category_type": category_type},
                fields=["name", "product_name", "product_price", "lead_time","uom"]
            )
        else:
            result = frappe.get_all(
                "VMS Product Master",
                fields=["name", "product_name", "product_price", "lead_time","uom"]
            )

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering product name")
        return {
            "status": "error",
            "message": "Failed to filter product names.",
            "error": str(e)
        }


# filter subhead email
@frappe.whitelist(allow_guest=True)
def filter_subhead_email():
    try:
        result = frappe.get_all(
            "Employee",
            filters={"subhead":1},
            fields=["name", "full_name", "user_id"]
        )
        return {
            "status": "success",
            "data": result
        }

    except Exception as e:      
        frappe.log_error(frappe.get_traceback(), "Error filtering subhead email")
        return {
            "status": "error",
            "message": "Failed to filter subhead emails.",
            "error": str(e)
        }


# filter purchase Group
@frappe.whitelist(allow_guest=True)
def filter_purchase_group(company):
    try:
        if not company:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Company is required"
            }

        pur_grp = frappe.get_all(
            "Purchase Group Master",
            filters={"company": company},
            fields=["name", "purchase_group_code", "purchase_group_name", "description"]
        )

        cost_center = frappe.get_all(
            "Cost Center",
            filters={"company_code": company},
            fields=["name", "cost_center_code", "cost_center_name", "description", "short_text"]
        )

        gl_account = frappe.get_all(
            "GL Account",
            filters={"company": company},
            fields=["name", "gl_account_code", "gl_account_name", "account_group", "description"]
        )

        return {
            "status": "success",
            "pur_grp": pur_grp,
            "cost_center": cost_center,
            "gl_account": gl_account
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 400
        frappe.log_error(frappe.get_traceback(), "Error filtering purchase group")
        return {
            "status": "error",
            "message": "Failed to filter purchase group.",
            "error": str(e)
        }
    
    
# send cart details/ purchase inquiry
@frappe.whitelist(allow_guest=True)
def create_purchase_inquiry(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		is_update = "name" in data and data["name"]

		if is_update:
			doc = frappe.get_doc("Cart Details", data["name"])
			for row in doc.modification_info:
				if row.fields_to_modify and not row.modified1:
					row.modified_datetime = frappe.utils.now_datetime()
					row.modified1 = 1
			doc.asked_to_modify = 0
		else:
			doc = frappe.new_doc("Cart Details")

		# Top-level fields
		top_fields = ["user", "cart_use", "cart_date", "category_type", "company", "plant", "purchase_group", "purchase_type", "cost_center", "gl_account"]

		for field in top_fields:
			if field in data:
				doc.set(field, data[field])

		# Save or insert to ensure doc.name exists before handling child tables
		# if is_update:
		# 	doc.save(ignore_permissions=True)
		# else:
		# 	doc.insert(ignore_permissions=True)

		# Child Table: cart_product
		if "cart_product" in data and isinstance(data["cart_product"], list):
			for row in data["cart_product"]:
				if not row:
					continue

				child_row = None
				if "name" in row:
					child_row = next((r for r in doc.cart_product if r.name == row["name"]), None)

				if child_row:
					for key in [
						"assest_code", "product_name", "product_price", "uom",
						"lead_time", "product_quantity", "user_specifications"
					]:
						if key in row:
							child_row.set(key, row[key])
				else:
					doc.append("cart_product", {
						"assest_code": row.get("assest_code"),
						"product_name": row.get("product_name"),
						"product_price": row.get("product_price"),
						"uom": row.get("uom"),
						"lead_time": row.get("lead_time"),
						"product_quantity": row.get("product_quantity"),
						"user_specifications": row.get("user_specifications")
					})

		# Final save to persist updates
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Cart Details saved successfully.",
			"name": doc.name
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Create/Update Cart Details API Error")
		return {
			"status": "error",
			"message": "Failed to save Cart Details.",
			"error": str(e)
		}


# @frappe.whitelist(allow_guest=True)
# def update_cart_products():
# 	try:
# 		# Get form data from the request
# 		form_data = frappe.local.form_dict
# 		files = frappe.request.files

# 		# Get purchase inquiry ID
# 		purchase_inquiry_id = form_data.get("purchase_inquiry_id")
# 		if not purchase_inquiry_id:
# 			return {
# 				"status": "error",
# 				"message": "Purchase Inquiry ID is required."
# 			}

# 		# Verify the document exists
# 		try:
# 			doc = frappe.get_doc("Cart Details", purchase_inquiry_id)
# 		except frappe.DoesNotExistError:
# 			return {
# 				"status": "error",
# 				"message": f"Purchase Inquiry with ID {purchase_inquiry_id} not found."
# 			}

# 		# Get product data from form fields
# 		product_row = {}
# 		product_fields = [
# 			"assest_code", "product_name", "product_price", "uom",
# 			"lead_time", "product_quantity", "user_specifications"
# 		]

# 		for field in product_fields:
# 			if field in form_data:
# 				value = form_data.get(field)
# 				product_row[field] = value if value else ""

# 		# Handle file attachment
# 		if "attachment" in files:
# 			uploaded_file = files["attachment"]
# 			if uploaded_file and uploaded_file.filename:
# 				try:
# 					# Save the file
# 					file_doc = frappe.get_doc({
# 						"doctype": "File",
# 						"file_name": uploaded_file.filename,
# 						"content": uploaded_file.read(),
# 						"decode": False,
# 						"is_private": 0,
# 						"attached_to_doctype": "Cart Details",
# 						"attached_to_name": purchase_inquiry_id
# 					})
# 					file_doc.insert(ignore_permissions=True)

# 					# Add file URL to the product row
# 					product_row["attachment"] = file_doc.file_url
# 				except Exception as file_error:
# 					frappe.log_error(f"File upload error: {str(file_error)}", "Cart Product File Upload")
# 					return {
# 						"status": "error",
# 						"message": "Failed to upload attachment.",
# 						"error": str(file_error)
# 					}

# 		# Handle numeric field conversion
# 		for field in ["product_price", "lead_time", "product_quantity"]:
# 			if field in product_row:
# 				value = product_row[field]
# 				if value and str(value).strip():
# 					try:
# 						if field == "product_quantity":
# 							product_row[field] = int(float(value))
# 						else:
# 							product_row[field] = float(value)
# 					except (ValueError, TypeError):
# 						product_row[field] = 0
# 				else:
# 					product_row[field] = 0

		
# 		if not any(product_row.get(field) for field in product_fields):
# 			return {
# 				"status": "error",
# 				"message": "No product data provided."
# 			}

# 		row_name = form_data.get("name")

# 		# Prepare row data
# 		row_data = {
# 			"assest_code": product_row.get("assest_code", ""),
# 			"product_name": product_row.get("product_name", ""),
# 			"uom": product_row.get("uom", ""),
# 			"user_specifications": product_row.get("user_specifications", ""),
# 			"attachment": product_row.get("attachment", ""),
# 			"product_price": product_row.get("product_price", 0),
# 			"lead_time": product_row.get("lead_time", 0),
# 			"product_quantity": product_row.get("product_quantity", 0),
# 			"final_price_by_purchase_team": product_row.get("final_price_by_purchase_team", 0),
# 			"need_asset_code": product_row.get("need_asset_code", 0)
# 		}

# 		# Handle numeric fields (ensure they are properly set)
# 		for numeric_field in ["product_price", "lead_time", "product_quantity"]:
# 			value = product_row.get(numeric_field, 0)
# 			row_data[numeric_field] = value

# 		if row_name:
# 			# Update existing row
# 			row_found = False
# 			for row in doc.cart_product:
# 				if row.name == row_name:
# 					for field, value in row_data.items():
# 						setattr(row, field, value)
# 					row_found = True
# 					operation = "updated"
# 					child_row_name = row_name
# 					break

# 			if not row_found:
# 				return {
# 					"status": "error",
# 					"message": f"Cart product with row name {row_name} not found."
# 				}
# 		else:
# 			# Create new row
# 			new_row = doc.append("cart_product", row_data)
# 			operation = "added"

# 		# Save the document
# 		doc.save(ignore_permissions=True)
# 		frappe.db.commit()

# 		if not row_name:
# 			child_row_name = doc.cart_product[-1].name
# 		else:
# 			child_row_name = row_name

# 		return {
# 			"status": "success",
# 			"message": f"Cart product {operation} successfully.",
# 			"purchase_inquiry_id": purchase_inquiry_id,
# 			"product_name": row_data.get("product_name", ""),
# 			"child_row_name": child_row_name,
# 			"operation": operation
# 		}

# 	except Exception as e:
# 		frappe.db.rollback()
# 		frappe.log_error(frappe.get_traceback(), "Update Cart Products API Error")
# 		return {
# 			"status": "error",
# 			"message": "Failed to add cart product.",
# 			"error": str(e)
# 		}


@frappe.whitelist(allow_guest=True)
def update_cart_products():
	try:
		# Get form data from the request
		form_data = frappe.local.form_dict
		files = frappe.request.files

		# Get purchase inquiry ID
		purchase_inquiry_id = form_data.get("purchase_inquiry_id")
		if not purchase_inquiry_id:
			return {
				"status": "error",
				"message": "Purchase Inquiry ID is required."
			}

		# Verify the document exists
		try:
			doc = frappe.get_doc("Cart Details", purchase_inquiry_id)
		except frappe.DoesNotExistError:
			return {
				"status": "error",
				"message": f"Purchase Inquiry with ID {purchase_inquiry_id} not found."
			}

		# Get product data from form fields
		product_row = {}
		product_fields = [
			"assest_code", "product_name", "product_price", "uom",
			"lead_time", "product_quantity", "user_specifications", "need_asset_code"
		]

		for field in product_fields:
			if field in form_data:
				value = form_data.get(field)
				product_row[field] = value if value else ""

		# Handle file attachment
		if "attachment" in files:
			uploaded_file = files["attachment"]
			if uploaded_file and uploaded_file.filename:
				try:
					# Save the file
					file_doc = frappe.get_doc({
						"doctype": "File",
						"file_name": uploaded_file.filename,
						"content": uploaded_file.read(),
						"decode": False,
						"is_private": 0,
						"attached_to_doctype": "Cart Details",
						"attached_to_name": purchase_inquiry_id
					})
					file_doc.insert(ignore_permissions=True)

					# Add file URL to the product row
					product_row["attachment"] = file_doc.file_url
				except Exception as file_error:
					frappe.log_error(f"File upload error: {str(file_error)}", "Cart Product File Upload")
					return {
						"status": "error",
						"message": "Failed to upload attachment.",
						"error": str(file_error)
					}

		# Handle numeric field conversion
		for field in ["product_price", "lead_time", "product_quantity"]:
			if field in product_row:
				value = product_row[field]
				if value and str(value).strip():
					try:
						if field == "product_quantity":
							product_row[field] = int(float(value))
						else:
							product_row[field] = float(value)
					except (ValueError, TypeError):
						product_row[field] = 0
				else:
					product_row[field] = 0

		if not any(product_row.get(field) for field in product_fields):
			return {
				"status": "error",
				"message": "No product data provided."
			}

		row_name = form_data.get("name")

		# Prepare row data
		row_data = {
			"assest_code": product_row.get("assest_code", ""),
			"product_name": product_row.get("product_name", ""),
			"uom": product_row.get("uom", ""),
			"user_specifications": product_row.get("user_specifications", ""),
			"attachment": product_row.get("attachment", ""),
			"product_price": product_row.get("product_price", 0),
			"lead_time": product_row.get("lead_time", 0),
			"product_quantity": product_row.get("product_quantity", 0),
			"final_price_by_purchase_team": product_row.get("final_price_by_purchase_team", 0),
			# "need_asset_code": product_row.get("need_asset_code", 0)
		}

		# Handle numeric fields (ensure they are properly set)
		for numeric_field in ["product_price", "lead_time", "product_quantity"]:
			value = product_row.get(numeric_field, 0)
			row_data[numeric_field] = value

		if row_name:
			# Update existing row
			row_found = False
			for row in doc.cart_product:
				if row.name == row_name:
					# store existing attachment
					existing_attachment = row.attachment  # Get existing attachment
					need_asset_code = row.need_asset_code  # Get existing checkbox

					for field, value in row_data.items():
						if field == "attachment":
							# Handle attachment fallback
							if value in ["undefined", None, ""]:
								setattr(row, "attachment", existing_attachment)
							else:
								setattr(row, "attachment", value)

						elif field == "need_asset_code":
							# Handle checkbox fallback
							if value in ["undefined", None, ""]:
								setattr(row, "need_asset_code", need_asset_code)
							else:
								# Cast to int/bool if needed
								setattr(row, "need_asset_code", int(value) if isinstance(value, (str, bool)) else value)

						else:
							setattr(row, field, value)

					row_found = True
					operation = "updated"
					child_row_name = row_name
					break

			if not row_found:
				return {
					"status": "error",
					"message": f"Cart product with row name {row_name} not found."
				}
		else:
			# Create new row
			new_row = doc.append("cart_product", row_data)
			operation = "added"

		# Save the document
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		if not row_name:
			child_row_name = doc.cart_product[-1].name
		else:
			child_row_name = row_name

		return {
			"status": "success",
			"message": f"Cart product {operation} successfully.",
			"purchase_inquiry_id": purchase_inquiry_id,
			"product_name": row_data.get("product_name", ""),
			"child_row_name": child_row_name,
			"operation": operation
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Update Cart Products API Error")
		return {
			"status": "error",
			"message": "Failed to add cart product.",
			"error": str(e)
		}



@frappe.whitelist(allow_guest=True)
def delete_cart_product(purchase_inquiry_id, row_name):
	try:
		
		
		if not purchase_inquiry_id:
			return {
				"status": "error",
				"message": "Purchase Inquiry ID is required."
			}
		
		if not row_name:
			return {
				"status": "error",
				"message": "Row name is required."
			}
		
		# Verify the document exists
		try:
			doc = frappe.get_doc("Cart Details", purchase_inquiry_id)
		except frappe.DoesNotExistError:
			return {
				"status": "error",
				"message": f"Purchase Inquiry with ID {purchase_inquiry_id} not found."
			}
		
		# Find and remove the specific row from cart_product child table
		row_found = False
		product_name = ""
		
		for i, row in enumerate(doc.cart_product):
			if row.name == row_name:
				product_name = row.product_name or ""
				# Remove the row from the child table
				doc.cart_product.pop(i)
				row_found = True
				break
		
		if not row_found:
			return {
				"status": "error",
				"message": f"Cart product with row name {row_name} not found."
			}
		
		# Save the document
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		
		return {
			"status": "success",
			"message": "Cart product deleted successfully.",
			"purchase_inquiry_id": purchase_inquiry_id,
			"deleted_row_name": row_name,
			"product_name": product_name
		}
	
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Delete Cart Product API Error")
		return {
			"status": "error",
			"message": "Failed to delete cart product.",
			"error": str(e)
		}


# get full data of cart details
@frappe.whitelist(allow_guest=True)
def get_full_data_pur_inquiry(pur_inq):
    try:
        if pur_inq:
            doc = frappe.get_doc("Cart Details", pur_inq)
            if doc:
                data = doc.as_dict()
            
                data["cart_product"] = [
                    row.as_dict() for row in doc.cart_product
                ]
                
                return {
                    "status": "success", 
                    "data": data
                }
            else:
                return {
                    "status": "error",
                    "message": "Cart Details not found."
                }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send Cart Details Data API Error")
        return {
            "status": "error",
            "message": "Failed to retrieve Cart Details data.",
            "error": str(e)
        }
    

# modify cart item and need assest code
@frappe.whitelist(allow_guest=True)
def modified_peq(data):
    try:
        doc = frappe.get_doc("Cart Details", data.get("cart_id"))

        if doc.cart_date:
            try:
                cart_date_formatted = datetime.strptime(doc.cart_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            except Exception:
                cart_date_formatted = doc.cart_date
        else:
            cart_date_formatted = "N/A"
                  
        if doc:
            doc.asked_to_modify = 1
            doc.append("modification_info", {
                "fields_to_modify": data.get("fields_to_modify"),
                "asked_to_modify_datetime": frappe.utils.now_datetime()
            })

            cart_products = data.get("cart_product", [])
            
            for cart_item in cart_products:
                row_id = cart_item.get("row_id")
                need_asset_code = int(cart_item.get("need_asset_code", 0))
                
                for child in doc.cart_product:
                    if child.name == row_id:
                        child.need_asset_code = need_asset_code
                        break 

            doc.purchase_team_approval_status = "Modify"
            doc.purchase_team_status = "Raised Query"
                      
            doc.save()

            employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
            hod = frappe.get_value("Employee", {"user_id": doc.user}, "reports_to")
            hod_email = frappe.get_value("Employee", hod, "user_id")

            table_html = """
                <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                    <tr>
                        <th>Fields to Modify</th>
                        <th>Asked To Modify DateTime</th>
                    </tr>
            """

            for row in doc.modification_info:
                table_html += f"""
                    <tr>
                        <td>{row.fields_to_modify or ''}</td>
                        <td>{frappe.utils.format_datetime(row.asked_to_modify_datetime) if row.asked_to_modify_datetime else ''}</td>
                    </tr>
                """

            table_html += "</table>"

            subject = f"Cart Details Modification Request - {doc.name}"
            message = f"""
                <p>Dear {employee_name},</p>

                <p>A modification request has been submitted for the following <strong>Cart Details</strong>:</p>

                <p><strong>Cart ID:</strong> {doc.name}<br>
                <strong>Cart Date:</strong> {cart_date_formatted}</p>

                {table_html}

                <p>Best regards,<br>
                VMS Team</p>
                """

            
            frappe.custom_sendmail(recipients=[doc.user], cc=[hod_email], subject=subject, message=message, now=True)
            
            return {
                "status": "success",
                "message": "Modification request recorded."
            }
        else:
            return {
                "status": "error",
                "message": "Cart Details not found."
            }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Cart Details Modify API Error")
        return {
            "status": "error",
            "message": "Failed to retrieve Cart Details data.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def acknowledge_purchase_inquiry(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        doc = frappe.get_doc("Cart Details", data.get("cart_id"))

        # format cart date
        if doc.cart_date:
            try:
                cart_date_formatted = datetime.strptime(doc.cart_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            except Exception:
                cart_date_formatted = doc.cart_date
        else:
            cart_date_formatted = "N/A"

        # format acknowledge date
        if doc.acknowledged_date:
            try:
                acknowledged_date_formatted = datetime.strptime(doc.acknowledged_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            except Exception:
                acknowledged_date_formatted = doc.acknowledged_date
        else:
            acknowledged_date_formatted = "N/A"
                  
        if doc:
            doc.purchase_team_acknowledgement = 1
            doc.acknowledged_date = data.get("acknowledged_date")
            doc.acknowledged_remarks = data.get("acknowledged_remarks")
            doc.purchase_team_status = "Acknowledged"
            doc.purchase_team_approval_status = "Acknowledged"
            doc.save(ignore_permissions=True)

            employee_name = frappe.get_value("Employee", {"user_id": doc.user}, "full_name")
            hod = frappe.get_value("Employee", {"user_id": doc.user}, "reports_to")
            if hod:
                hod_email = frappe.get_value("Employee", hod, "user_id")

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
                    </tr>
                """

            table_html += "</table>"

            subject = f"Acknowledgement for the Cart Details Submitted by {employee_name}"
            message = f"""
                <p>Dear {employee_name},</p>		

                <p>Your cart details have been <b>acknowledged</b>.</p>

                <p><b>Cart ID:</b> {doc.name}</p>
                <p><b>Cart Date:</b> {cart_date_formatted}</p>
                <p><b>Acknowledged Date:</b> {acknowledged_date_formatted}</p>
                <p><b>Acknowledged Remarks:</b> {doc.acknowledged_remarks}</p>

                {table_html}

                <p>Thank you.<br>
                Best regards,<br>
                VMS Team</p>
                """

            frappe.custom_sendmail(recipients=[doc.user], cc=[hod_email], subject=subject, message=message, now=True)

            return {
                "status": "success",
                "message": "Cart Details acknowledged."
            }
        else:
            return {
                "status": "error",
                "message": "Cart Details not found."
            }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Cart Details Acknowledge API Error")
        return {
            "status": "error",
            "message": "Failed to acknowledge Cart Details.",
        }




# @frappe.whitelist(allow_guest = True)
# def get_company_for_pe(usr):
#     emp = frappe.get_doc("Employee",{"user_id":usr})
#     comps = []
#     for com in emp.company:
#         comps.append(com.company_name)
#     comps_data = []

#     for comp in comps:
#         cd = frappe.get_doc("Company Master", comp)
#         comps_data.append(cd.as_dict())

#     return comps_data

@frappe.whitelist(allow_guest=True)
def get_company_for_pe_detailed(usr):
    """
    Get company data for a given user with detailed error responses
    
    Args:
        usr (str): User ID to fetch employee and company data for
        
    Returns:
        dict: Response with success status, data, and error details
    """
    response = {
        "success": False,
        "data": [],
        "errors": [],
        "warnings": []
    }
    
    try:
        # Validate input
        if not usr:
            response["errors"].append("User ID is required")
            return response
        
        # Check user exists
        if not frappe.db.exists("User", usr):
            response["errors"].append(f"User '{usr}' not found")
            return response
        
        # Get employee
        try:
            emp = frappe.get_doc("Employee", {"user_id": usr})
        except frappe.DoesNotExistError:
            response["errors"].append(f"Employee record not found for user '{usr}'")
            return response
        except Exception as e:
            frappe.log_error(f"Error fetching employee: {str(e)}")
            response["errors"].append("Error fetching employee data")
            return response
        
        # Check company data
        if not hasattr(emp, 'company') or not emp.company:
            response["errors"].append("No company data found for employee")
            return response
        
        # Process companies
        comps = []
        for com in emp.company:
            if hasattr(com, 'company_name') and com.company_name:
                comps.append(com.company_name)
        
        if not comps:
            response["errors"].append("No valid companies found for employee")
            return response
        
        # Get company details
        comps_data = []
        for comp in comps:
            try:
                if not frappe.db.exists("Company Master", comp):
                    response["warnings"].append(f"Company '{comp}' not found in Company Master")
                    continue
                
                cd = frappe.get_doc("Company Master", comp)
                comps_data.append(cd.as_dict())
                
            except frappe.PermissionError:
                response["warnings"].append(f"Permission denied for company '{comp}'")
                continue
            except Exception as e:
                frappe.log_error(f"Error fetching company {comp}: {str(e)}")
                response["warnings"].append(f"Error fetching company '{comp}'")
                continue
        
        if comps_data:
            response["success"] = True
            response["data"] = comps_data
        else:
            response["errors"].append("No company data could be retrieved")
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Unexpected error in get_company_for_pe_detailed: {str(e)}")
        response["errors"].append("An unexpected error occurred")
        return response
    



@frappe.whitelist(allow_guest=True)
def get_plants_and_purchase_group(comp):
    """
    Get plant and purchase group data for a given company
    
    Args:
        comp (str): Company name to filter records
        
    Returns:
        dict: Dictionary containing plant and purchase group data
    """
    try:
        # Validate input parameter
        if not comp:
            frappe.throw(_("Company is required"), frappe.ValidationError)
        
        # Check if company exists
        if not frappe.db.exists("Company", comp) and not frappe.db.exists("Company Master", comp):
            frappe.throw(_("Company '{0}' not found").format(comp), frappe.DoesNotExistError)
        
        response = {
            "success": True,
            "company": comp,
            "plants": [],
            "purchase_groups": [],
            "cost_centers": [],
            "gl_accounts": [],
            "errors": []
        }
        
        # Get Plant Master data
        try:
            plants = frappe.get_all(
                "Plant Master",
                filters={"company": comp},
                fields=["name", "plant_name", "description"]
            )
            response["plants"] = plants

            
        except frappe.PermissionError:
            frappe.log_error(f"Permission denied for Plant Master - Company: {comp}")
            response["errors"].append("Permission denied for Plant Master")
        except Exception as e:
            frappe.log_error(f"Error fetching Plant Master for company {comp}: {str(e)}")
            response["errors"].append("Error fetching Plant Master data")

        try:
            cost_centers = frappe.get_all(
                "Cost Center",
                filters={"company_code": comp},
                fields=["name", "cost_center_name", "cost_center_code", "description"]
            )
            response["cost_centers"] = cost_centers

           

            
        except frappe.PermissionError:
            frappe.log_error(f"Permission denied for Cost Centers - Company: {comp}")
            response["errors"].append("Permission denied for Cost Centers")
        except Exception as e:
            frappe.log_error(f"Error fetching Cost Centers for company {comp}: {str(e)}")
            response["errors"].append("Error fetching Cost centers data")
        
        try:
            gl_accounts = frappe.get_all(
                "GL Account",
                filters={"company": comp},
                fields=["name", "gl_account_name", "description"]
            )
            response["gl_accounts"] = gl_accounts

            
        except frappe.PermissionError:
            frappe.log_error(f"Permission denied for GL Accounts- Company: {comp}")
            response["errors"].append("Permission denied for GL Accounts")
        except Exception as e:
            frappe.log_error(f"Error fetching GL Accounts for company {comp}: {str(e)}")
            response["errors"].append("Error fetching GL Accounts data")
        
        # Get Purchase Group Master data
        try:
            purchase_groups = frappe.get_all(
                "Purchase Group Master",
                filters={"company": comp},
                fields=["name", "purchase_group_code", "team", "purchase_group_name", "description"]
            )
            response["purchase_groups"] = purchase_groups
            
        except frappe.PermissionError:
            frappe.log_error(f"Permission denied for Purchase Group Master - Company: {comp}")
            response["errors"].append("Permission denied for Purchase Group Master")
        except Exception as e:
            frappe.log_error(f"Error fetching Purchase Group Master for company {comp}: {str(e)}")
            response["errors"].append("Error fetching Purchase Group Master data")
        
        # Check if any data was retrieved
        if not response["plants"] and not response["purchase_groups"] and not response["errors"] and not response["cost_centers"] and not response["gl_accounts"]:
            response["errors"].append("No plant or purchase group data found for the specified company")
        
        return response
        
    except frappe.ValidationError:
        # Re-raise validation errors as they contain user-friendly messages
        raise
    except frappe.DoesNotExistError:
        # Re-raise DoesNotExist errors as they contain user-friendly messages
        raise
    except frappe.PermissionError:
        frappe.throw(_("Insufficient permissions to access the requested data"), frappe.PermissionError)
    except Exception as e:
        # Log unexpected errors and return generic message
        frappe.log_error(f"Unexpected error in get_plants_and_purchase_group: {str(e)}")
        frappe.throw(_("An unexpected error occurred. Please try again later."), frappe.ValidationError)


    

# @frappe.whitelist(allow_guest=True)
# def get_purchase_type():
#      pt = frappe.get_all(
#                 "Purchase Requisition Type",
#                 # filters={"company": comp},
#                 fields=["name", "purchase_requisition_type_name", "description"]
#             )

@frappe.whitelist(allow_guest=True)
def get_purchase_type():
    """
    Get all purchase requisition types
    
    Returns:
        dict: Dictionary containing purchase requisition type data
    """
    try:
        # Get Purchase Requisition Type data
        purchase_types = frappe.get_all(
            "Purchase Requisition Type",
            fields=["name", "purchase_requisition_type_name", "description"]
        )
        
        return {
            "success": True,
            "data": purchase_types,
            "count": len(purchase_types),
            "message": "Purchase requisition types retrieved successfully"
        }
        
    except frappe.PermissionError:
        frappe.log_error("Permission denied for Purchase Requisition Type")
        frappe.throw(_("Insufficient permissions to access Purchase Requisition Type data"), frappe.PermissionError)
    except frappe.DoesNotExistError:
        frappe.log_error("Purchase Requisition Type doctype not found")
        frappe.throw(_("Purchase Requisition Type not found in the system"), frappe.DoesNotExistError)
    except Exception as e:
        frappe.log_error(f"Error in get_purchase_type: {str(e)}")
        frappe.throw(_("An unexpected error occurred while fetching purchase requisition types"), frappe.ValidationError)



@frappe.whitelist(allow_guest=True)
def submit_purchase_inquiry(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        purchase_inquiry_id = data.get("purchase_inquiry_id") or data.get("name")
        
        if not purchase_inquiry_id:
            return {
                "status": "error",
                "message": "'purchase_inquiry_id' or 'name' is required in the data."
            }

        # Get the document
        doc = frappe.get_doc("Cart Details", purchase_inquiry_id)
        
        # Update top-level fields
        top_fields = ["user", "cart_use", "cart_date", "category_type", "company", "plant", "purchase_group", "purchase_type", "cost_center", "gl_account"]
        
        for field in top_fields:
            if field in data:
                doc.set(field, data[field])
        
        # Handle modification_info child table updates
        for row in doc.modification_info:
            if row.fields_to_modify and not row.modified1:
                row.modified_datetime = frappe.utils.now_datetime()
                row.modified1 = 1
        doc.asked_to_modify = 0
        
        
        if "cart_product" in data and isinstance(data["cart_product"], list):
            for row in data["cart_product"]:
                if not row:
                    continue
                
                child_row = None
                if "name" in row:
                    child_row = next((r for r in doc.cart_product if r.name == row["name"]), None)
                
                if child_row:
                    # Update existing child row
                    for key in [
                        "assest_code", "product_name", "product_price", "uom",
                        "lead_time", "product_quantity", "user_specifications"
                    ]:
                        if key in row:
                            child_row.set(key, row[key])
                else:
                    # Add new child row
                    doc.append("cart_product", {
                        "assest_code": row.get("assest_code"),
                        "product_name": row.get("product_name"),
                        "product_price": row.get("product_price"),
                        "uom": row.get("uom"),
                        "lead_time": row.get("lead_time"),
                        "product_quantity": row.get("product_quantity"),
                        "user_specifications": row.get("user_specifications")
                    })
        
        # Save the document with updates first
        doc.save(ignore_permissions=True)
        
        # Now submit the document
        doc.is_submited = 1
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": f"Cart Details '{purchase_inquiry_id}' updated and submitted successfully.",
            "name": doc.name
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Submit Cart Details API Error")
        return {
            "status": "error",
            "message": "Failed to update and submit Cart Details.",
            "error": str(e)
        }
