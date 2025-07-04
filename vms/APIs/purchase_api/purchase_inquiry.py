import frappe
import json
from frappe.utils import now_datetime


# cart details masters
@frappe.whitelist(allow_guest=True)
def cart_details_masters():
    try:
        category_type = frappe.db.sql("select name, category_name from `tabCategory Master`", as_dict=True)
        uom_master = frappe.db.sql("select name, uom from `tabUOM Master`", as_dict=True)

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
                fields=["name", "product_name", "product_price", "lead_time"]
            )
        else:
            result = frappe.get_all(
                "VMS Product Master",
                fields=["name", "product_name", "product_price", "lead_time"]
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
		top_fields = ["user", "cart_use", "cart_date", "category_type"]

		for field in top_fields:
			if field in data:
				doc.set(field, data[field])

		# Save or insert to ensure doc.name exists before handling child tables
		if is_update:
			doc.save(ignore_permissions=True)
		else:
			doc.insert(ignore_permissions=True)

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
    


@frappe.whitelist(allow_guest=True)
def modified_peq(data):
    try:
        doc = frappe.get_doc("Cart Details", data.get("cart_id"))
        if doc:
            doc.asked_to_modify = 1
            doc.append("modification_info", {
                "fields_to_modify": data.get("fields_to_modify"),
                "asked_to_modify_datetime": frappe.utils.now_datetime()
            })
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
                <strong>Cart Date:</strong> {doc.cart_date}</p>
                {table_html}
                <p>Regards,<br>VMS Team</p>
            """
            
            frappe.sendmail(recipients=[doc.user], cc=[hod_email], subject=subject, message=message, now=True)
            
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
        if doc:
            doc.purchase_team_acknowledgement = 1
            doc.acknowledged_date = data.get("acknowledged_date")
            doc.acknowledged_remarks = data.get("acknowledged_remarks")
            doc.purchase_team_status = "Acknowledged"
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
                <p>Your cart details has been approved by HOD</b>.</p>
                <p><b>Cart ID:</b> {doc.name}</p>
                <p><b>Cart Date:</b> {doc.cart_date}</p>
                <p><b>Acknowledged Remarks:</b> {doc.acknowledged_remarks} </p>
                
                {table_html}
                <p>Thank you!</p>
            """
            frappe.sendmail(recipients=[doc.user], cc=[hod_email], subject=subject, message=message, now=True)

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