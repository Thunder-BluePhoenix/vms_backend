import frappe
import json

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
                fields=["name", "product_name"]
            )
        else:
            result = frappe.get_all(
                "VMS Product Master",
                fields=["name", "product_name"]
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

        main_doc_fields = {
            "doctype": "Cart Details",
            "user": data.get("user"),
            "cart_use": data.get("cart_use"),
            "cart_date": data.get("cart_date"),
            "category_type": data.get("category_type")
        }

        doc = frappe.new_doc("Cart Details")
        doc.update(main_doc_fields)
    
        table_data = data.get("cart_product", [])
        for row in table_data:
            doc.append("cart_product", {
                "assest_code": row.get("assest_code"),
                # "category_type": row.get("category_type"),
                "product_name": row.get("product_name"),
                "product_price": row.get("product_price"),
                "uom": row.get("uom"),
                "lead_time": row.get("lead_time"),
                "product_quantity": row.get("product_quantity"),
                "user_specifications": row.get("user_specifications")
            })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Cart Details created successfully.",
            "name": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Cart Details API Error")
        return {
            "status": "error",
            "message": "Failed to create Cart Details.",
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