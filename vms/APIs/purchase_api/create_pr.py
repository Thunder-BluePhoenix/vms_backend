import frappe
import json

@frappe.whitelist(allow_guest=True)
def purchase_requsition_masters():
    try:
        purchase_requisition_type = frappe.db.sql("""SELECT name, purchase_requisition_type_code, purchase_requisition_type_name, description FROM `tabPurchase Requisition Type`""",  as_dict=True)
        plant = frappe.db.sql("""SELECT name, plant_code, plant_name, description FROM `tabPlant Master`""", as_dict=True)
        company_code_area = frappe.db.sql("""SELECT name, company_area_code, company_area_name, description FROM `tabCompany Code Area`""", as_dict=True)
        company = frappe.db.sql("""SELECT name, company_code, company_name, description FROM `tabCompany Master`""", as_dict=True)
        item_category_master = frappe.db.sql("""SELECT name, item_code, item_name, description FROM `tabItem Category Master`""", as_dict=True)
        material_group_master = frappe.db.sql("""SELECT name, material_group_name, material_group_description FROM `tabMaterial Group Master`""", as_dict=True)
        uom_master = frappe.db.sql("""SELECT name, uom_code, uom, description FROM `tabUOM Master`""", as_dict=True)
        cost_center  = frappe.db.sql("""SELECT name, cost_center_code, cost_center_name, description FROM `tabCost Center`""", as_dict=True)
        profit_center = frappe.db.sql("""SELECT name, profit_center_code, profit_center_name, description FROM `tabProfit Center`""", as_dict=True)
        gl_account_number = frappe.db.sql("""SELECT name, gl_account_code, gl_account_name, description FROM `tabGL Account`""", as_dict=True)
        material_code = frappe.db.sql("""SELECT name, material_code, material_name, description FROM `tabMaterial Master`""", as_dict=True)
        account_assignment_category = frappe.db.sql("""SELECT name, account_assignment_category_code, account_assignment_category_name, description FROM `tabAccount Assignment Category`""", as_dict=True)
        purchase_group = frappe.db.sql("""SELECT name, purchase_group_code, purchase_group_name, description FROM `tabPurchase Group Master`""", as_dict=True)
        account_category = frappe.db.sql("""SELECT name, account_category_code, account_category_name, description FROM `tabAccount Category Master`""", as_dict=True)

        return {
            "purchase_requisition_type": purchase_requisition_type,
            "plant": plant,
            "company_code_area": company_code_area,
            "company": company,
            "item_category_master": item_category_master,
            "material_group_master": material_group_master,
            "uom_master": uom_master,
            "cost_center": cost_center,
            "profit_center": profit_center,
            "gl_account_number": gl_account_number,
            "material_code": material_code,
            "account_assignment_category": account_assignment_category,
            "purchase_group": purchase_group,
            "account_category": account_category
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Purchase Requisition Masters API Error")
        return {
            "status": "error",
            "message": "Failed to retrieve Purchase Requisition masters.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def create_purchase_requisition(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        main_doc_fields = {
            "doctype": "Purchase Requisition Webform",
            "purchase_requisition_type": data.get("purchase_requisition_type"),
            "plant": data.get("plant"),
            "company_code_area": data.get("company_code_area"),
            "company": data.get("company"),
            "requisitioner": data.get("requisitioner"),
            "purchase_group": data.get("purchase_group")
        }

        # Create new document
        doc = frappe.new_doc("Purchase Requisition Webform")
        doc.update(main_doc_fields)

        # Add child table rows
        table_data = data.get("purchase_requisition_form_table", [])
        for row in table_data:
            doc.append("purchase_requisition_form_table", {
                "item_number_of_purchase_requisition": row.get("item_number_of_purchase_requisition"),
                "purchase_requisition_date": row.get("purchase_requisition_date"),
                "delivery_date": row.get("delivery_date"),
                "store_location": row.get("store_location"),
                "item_category": row.get("item_category"),
                "material_group": row.get("material_group"),
                "uom": row.get("uom"),
                "cost_center": row.get("cost_center"),
                "main_asset_no": row.get("main_asset_no"),
                "asset_subnumber": row.get("asset_subnumber"),
                "profit_ctr": row.get("profit_ctr"),
                "short_text": row.get("short_text"),
                "quantity": row.get("quantity"),
                "price_of_purchase_requisition": row.get("price_of_purchase_requisition"),
                "gl_account_number": row.get("gl_account_number"),
                "material_code": row.get("material_code"),
                "account_assignment_category": row.get("account_assignment_category"),
                # "purchase_group": row.get("purchase_group")
            })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Purchase Requisition Webform created successfully.",
            "name": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Purchase Requisition Webform API Error")
        return {
            "status": "error",
            "message": "Failed to create Purchase Requisition Webform.",
            "error": str(e)
        }
    
# apps/vms/vms/APIs/purchase_api/create_pr.py

@frappe.whitelist(allow_guest=True)
def send_purchase_requisition_data(pur_req):
    try:
        if pur_req:
            doc = frappe.get_doc("Purchase Requisition Webform", pur_req)
            if doc:
                # Convert the document to a dictionary
                data = doc.as_dict()
            
                data["purchase_requisition_form_table"] = [
                    row.as_dict() for row in doc.purchase_requisition_form_table
                ]
                
                return {
                    "status": "success", 
                    "data": data
                }
            else:
                return {
                    "status": "error",
                    "message": "Purchase Requisition Webform not found."
                }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send Purchase Requisition Data API Error")
        return {
            "status": "error",
            "message": "Failed to retrieve Purchase Requisition Webform data.",
            "error": str(e)
        }

# update purchase requisition webform doctype
@frappe.whitelist(allow_guest=True)
def update_pur_req_doc(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        doc_name = data.get("name")
        if not doc_name:
            return {
                "status": "error",
                "message": "Document name (Purchase Requisition Webform) is required."
            }

        doc = frappe.get_doc("Purchase Requisition Webform", doc_name)
        if not doc:
            return {
                "status": "error",
                "message": "Purchase Requisition Webform not found."
            }

        # Update only provided fields
        for field in ["purchase_requisition_type", "plant", "company_code_area", "company", "requisitioner"]:
            if field in data:
                doc.set(field, data.get(field))

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Purchase Requisition Webform updated successfully.",
            "name": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Purchase Requisition Webform API Error")
        return {
            "status": "error",
            "message": "Failed to update Purchase Requisition Webform.",
            "error": str(e)
        }


#update purchase requisition webform table
@frappe.whitelist(allow_guest=True)
def update_pur_req_table(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        doc = frappe.get_doc("Purchase Requisition Webform", data.get("name"))
        if not doc:
            return {
                "status": "error",
                "message": "Purchase Requisition Webform not found."
            }

        row_id = data.get("row_id")
        if not row_id:
            return {
                "status": "error",
                "message": "row_id is required to update a specific child row."
            }

        found = False
        for row in doc.purchase_requisition_form_table:
            if row.name == row_id:
                row.update({
                    "item_number_of_purchase_requisition": data.get("item_number_of_purchase_requisition"),
                    "purchase_requisition_date": data.get("purchase_requisition_date"),
                    "delivery_date": data.get("delivery_date"),
                    "store_location": data.get("store_location"),
                    "item_category": data.get("item_category"),
                    "material_group": data.get("material_group"),
                    "uom": data.get("uom"),
                    "cost_center": data.get("cost_center"),
                    "main_asset_no": data.get("main_asset_no"),
                    "asset_subnumber": data.get("asset_subnumber"),
                    "profit_ctr": data.get("profit_ctr"),
                    "short_text": data.get("short_text"),
                    "quantity": data.get("quantity"),
                    "price_of_purchase_requisition": data.get("price_of_purchase_requisition"),
                    "gl_account_number": data.get("gl_account_number"),
                    "material_code": data.get("material_code"),
                    "account_assignment_category": data.get("account_assignment_category"),
                    # "purchase_group": data.get("purchase_group")
                })
                found = True
                break

        if not found:
            return {
                "status": "error",
                "message": f"Row with row_id {row_id} not found in child table."
            }

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Child table row updated successfully.",
            "name": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Purchase Requisition Webform Table API Error")
        return {
            "status": "error",
            "message": "Failed to update Purchase Requisition Webform table.",
            "error": str(e)
        }

# update whole purchase requisition webform data
@frappe.whitelist(allow_guest=True)
def update_purchase_requisition_data(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        doc_name = data.get("name")
        if not doc_name:
            return {
                "status": "error",
                "message": "Document name (Purchase Requisition Webform) is required."
            }

        doc = frappe.get_doc("Purchase Requisition Webform", doc_name)
        if not doc:
            return {
                "status": "error",
                "message": "Purchase Requisition Webform not found."
            }

        # Update only the fields provided in the data
        main_fields = [
            "purchase_requisition_type", "plant", "company_code_area", "company", "requisitioner"
        ]
        for field in main_fields:
            if field in data:
                doc.set(field, data.get(field))

        # Update only the provided child table row (if row_id is present)
        
        # rows_data = data.get("child_rows")  # List of dicts with 'row_id' and fields
        # if rows_data:
        #     for row_data in rows_data:
        #         row_id = row_data.get("row_id")
        #         if not row_id:
        #             continue
        #         for row in doc.purchase_requisition_form_table:
        #             if row.name == row_id:
        #                 for key in row.meta.get("fields"):
        #                     fieldname = key.fieldname
        #                     if fieldname and fieldname in row_data:
        #                         row.set(fieldname, row_data[fieldname])
        #                 break
        
        # Aletrnative way to update the fields in child table

        rows_data = data.get("child_rows")  # List of dicts with 'row_id' and fields
        if rows_data:
            for row_data in rows_data:
                row_id = row_data.get("row_id")
                if not row_id:
                    continue
                for row in doc.purchase_requisition_form_table:
                    if row.name == row_id:
                        for key, value in row_data.items():
                            if key != "row_id":
                                row.set(key, value)
                        break

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Purchase Requisition Webform updated successfully.",
            "name": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Purchase Requisition Webform Data API Error")
        return {
            "status": "error",
            "message": "Failed to update Purchase Requisition Webform.",
            "error": str(e)
        }