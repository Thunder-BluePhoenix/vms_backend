import frappe
import json

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
                "purchase_group": row.get("purchase_group")
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
# @frappe.whitelist(allow_guest=True)
# def update_pur_req_doc(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)
        
#         doc = frappe.get_doc("Purchase Requisition Webform", data.get("name"))
#         if not doc:
#             return {
#                 "status": "error",
#                 "message": "Purchase Requisition Webform not found."
#             }

#         # Update main document fields
#         doc.update({
#             "purchase_requisition_type": data.get("purchase_requisition_type"),
#             "plant": data.get("plant"),
#             "company_code_area": data.get("company_code_area"),
#             "company": data.get("company"),
#             "requisitioner": data.get("requisitioner"),
#         })
      
#         return {
#             "status": "success",
#             "message": "Purchase Requisition Webform updated successfully.",
#             "name": doc.name
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Update Purchase Requisition Webform API Error")
#         return {
#             "status": "error",
#             "message": "Failed to update Purchase Requisition Webform.",
#             "error": str(e)
#         }


# #update purchase requisition webform table
# @frappe.whitelist(allow_guest=True)
# def update_pur_req_table(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)
        
#         doc = frappe.get_doc("Purchase Requisition Webform", data.get("name"))
#         if not doc:
#             return {
#                 "status": "error",
#                 "message": "Purchase Requisition Webform not found."
#             }
#         if data.get(row_id):

#         for row in doc.purchase_requisition_form_table:
#             if row.get("row_id") == data.get("row_id"):
#                 row.update({
#                     "item_number_of_purchase_requisition": data.get("item_number_of_purchase_requisition"),
#                     "purchase_requisition_date": data.get("purchase_requisition_date"),
#                     "delivery_date": data.get("delivery_date"),
#                     "store_location": data.get("store_location"),
#                     "item_category": data.get("item_category"),
#                     "material_group": data.get("material_group"),
#                     "uom": data.get("uom"),
#                     "cost_center": data.get("cost_center"),
#                     "main_asset_no": data.get("main_asset_no"),
#                     "asset_subnumber": data.get("asset_subnumber"),
#                     "profit_ctr": data.get("profit_ctr"),
#                     "short_text": data.get("short_text"),
#                     "quantity": data.get("quantity"),
#                     "price_of_purchase_requisition": data.get("price_of_purchase_requisition"),
#                     "gl_account_number": data.get("gl_account_number"),
#                     "material_code": data.get("material_code"),
#                     "account_assignment_category": data.get("account_assignment_category"),
#                     "purchase_group": data.get("purchase_group")
#                 })
#                 break
#             # If no matching row found, append a new row
#             doc.append("purchase_requisition_form_table", {
#                 "item_number_of_purchase_requisition": row.get("item_number_of_purchase_requisition"),
#                 "purchase_requisition_date": row.get("purchase_requisition_date"),
#                 "delivery_date": row.get("delivery_date"),
#                 "store_location": row.get("store_location"),
#                 "item_category": row.get("item_category"),
#                 "material_group": row.get("material_group"),
#                 "uom": row.get("uom"),
#                 "cost_center": row.get("cost_center"),
#                 "main_asset_no": row.get("main_asset_no"),
#                 "asset_subnumber": row.get("asset_subnumber"),
#                 "profit_ctr": row.get("profit_ctr"),
#                 "short_text": row.get("short_text"),
#                 "quantity": row.get("quantity"),
#                 "price_of_purchase_requisition": row.get("price_of_purchase_requisition"),
#                 "gl_account_number": row.get("gl_account_number"),
#                 "material_code": row.get("material_code"),
#                 "account_assignment_category": row.get("account_assignment_category"),
#                 "purchase_group": row.get("purchase_group")
#             })

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Purchase Requisition Webform updated successfully.",
#             "name": doc.name
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Update Purchase Requisition Webform Table API Error")
#         return {
#             "status": "error",
#             "message": "Failed to update Purchase Requisition Webform table.",
#             "error": str(e)
#         }