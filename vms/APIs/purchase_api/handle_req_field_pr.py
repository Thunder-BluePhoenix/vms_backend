import frappe

@frappe.whitelist(allow_guest=True)
def filter_master_field(company=None):
    try:
        plant = frappe.get_all("Plant Master", filters={"company": company}, fields=["name", "plant_name", "plant_code"])
        material_code = frappe.get_all("Material Master", filters={"company": company}, fields=["name", "material_name", "material_code"])
        material_group = frappe.get_all("Material Group Master", filters={"material_group_company": company}, fields=["name", "material_group_name", "material_group_description", "material_group_long_description"])

        return {
            "status": "success",
            "message": "Filter Master Fields",
            "plant": plant,
            "material_code": material_code,
            "material_group": material_group
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Filter Master Fields API Error")
        return {
            "status": "error",
            "message": "Failed to retrieve filter master fields.",
            "error": str(e)
        }
    
@frappe.whitelist(allow_guest=True)
def filter_req_fields(company, pur_type, acct_cate):
    try:
        company = frappe.get_value("Company Master", {"name": company}, "sap_client_code")
        if company == "900" and pur_type == "SB" and (acct_cate == "K" or acct_cate == "A"):
            return {
                # "status": "success",
                "item_category_head" : "Compulsory must D",
                "short_text_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "material_group_head": "Non Compulsory",
                "uom_head": "Non Compulsory",
                "gl_account_number_head": "Compulsory",
                "cost_center_head": "Compulsory",
                # "main_asset_no_head": "Compulsory",
                # "requisitioner": "Compulsory"
            } 
        elif company == "900" and pur_type == "NB" and acct_cate == "A":
            return {
                # "status": "success",
                "material_code_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "main_asset_no_head": "Compulsory",
                # "purchase_group": "Non Compulsory",
                # "requisitioner": "Compulsory"
            }
        elif company == "800" and pur_type == "SB" and acct_cate == "K":
            return {
                # "status": "success",
                "item_category_head" : "Compulsory must D",
                "short_text_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "material_group_head": "Non Compulsory",
                "uom_head": "Non Compulsory",
                "gl_account_number_head": "Compulsory",
                "cost_center_head": "Compulsory",
                # "requisitioner": "Compulsory"
            } 
        elif company == "800" and pur_type == "NB" and acct_cate == "A":
            return {
                # "status": "success",
                "material_code_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "main_asset_no_head": "Compulsory",
                # "purchase_group": "Non Compulsory",
                # "requisitioner": "Compulsory"
            }
        elif company == "700" and pur_type == "SB" and (acct_cate == "K" or acct_cate == "A"):
            return {
                # "status": "success",
                "item_category_head" : "Compulsory must D",
                "short_text_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "material_group_head": "Non Compulsory",
                "uom_head": "Non Compulsory",
                "gl_account_number_head": "Compulsory",
                "cost_center_head": "Compulsory",
                # "main_asset_no_head": "Compulsory",
                # "requisitioner": "Compulsory"
            }
        # elif company == "700" and pur_type == "NB":
        #     return {
        #         # "status": "success",
        #         "material_code_head": "Compulsory",
        #         # "plant": "Compulsory",
        #         "quantity_head": "Compulsory",
        #         # "purchase_group": "Non Compulsory",
        #         # "requisitioner": "Compulsory",
        #     }
        elif company == "700" and pur_type == "NB" and acct_cate == "A":
            return {
                # "status": "success",
                "material_code_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "main_asset_no_head": "Compulsory",
                # "purchase_group": "Non Compulsory",
                # "requisitioner": "Compulsory"
            }
        # elif company == "300" and pur_type == "NB":
        #     return{
        #         "material_code_head": "Compulsory",
        #         # "plant": "Compulsory",
        #         "quantity_head": "Compulsory",
        #         # "requisitioner": "Compulsory"
        #     }
        elif company == "300" and pur_type == "NB" and acct_cate == "A":
            return{
                "material_code_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "main_asset_no_head": "Compulsory",
                # "purchase_group": "Non Compulsory",
                # "requisitioner": "Compulsory"
            }
        elif company == "300" and pur_type == "SB" and acct_cate == "K":
            return{
                "item_category_head" : "Compulsory must D",
                "short_text_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "material_group_head": "Non Compulsory",
                "uom_head": "Non Compulsory",
                "gl_account_number_head": "Compulsory",
                "cost_center_head": "Compulsory",
                # "requisitioner": "Compulsory"
        }
        # elif company == "200" and pur_type == "NB":    
        #     return{
        #         "material_code_head": "Compulsory",
        #         # "plant": "Compulsory",
        #         "quantity_head": "Compulsory",
        #         # "requisitioner": "Compulsory",
        #         # "purchase_group": "Non Compulsory"
        #     }
        elif company == "200" and pur_type == "NB" and acct_cate == "A":
            return{
                "material_code_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "main_asset_no_head": "Compulsory",
                # "purchase_group": "Compulsory",
                # "requisitioner": "Compulsory"
            }
        elif company == "200" and pur_type == "SB" and (acct_cate == "K" or acct_cate == "A"):
            return {
                "item_category_head" : "Compulsory must D",
                "short_text_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "material_group_head": "Non Compulsory",
                "uom_head": "Non Compulsory",
                "gl_account_number_head": "Compulsory",
                "cost_center_head": "Compulsory",
                # "main_asset_no_head": "Compulsory",
                # "requisitioner": "Compulsory"
            }
        elif company == "100" and pur_type == "NB" and acct_cate == "A":
            return{
                "material_code_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "main_asset_no_head": "Compulsory",
                # "purchase_group": "Compulsory",
                # "requisitioner": "Compulsory"
            }
        elif company == "100" and pur_type == "SB" and (acct_cate == "K" or acct_cate == "A"):
            return {
                "item_category_head" : "Compulsory must D",
                "short_text_head": "Compulsory",
                # "plant": "Compulsory",
                "quantity_head": "Compulsory",
                "material_group_head": "Non Compulsory",
                "uom_head": "Non Compulsory",
                "gl_account_number_head": "Compulsory",
                "cost_center_head": "Compulsory",
                # "main_asset_no_head": "Compulsory",
                # "requisitioner": "Compulsory"
            }
        else:
            frappe.local.response["http_status_code"] = 500
            return {
                "status": "error",
                "message": "Invalid combination of company, purchase type, and account category."
            }  

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Filter Request Fields API Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": "Failed to retrieve filter request fields.",
            "error": str(e)
        }          


# Return Account Assignment category acc to Pur Req Type and company
@frappe.whitelist(allow_guest=True)
def return_acc_ass_category_list(pur_req_type, company):
    try:
        if not pur_req_type or not company:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Both 'pur_req_type' and 'company' are required."
            }

        purchase_requisition_type = frappe.get_doc("Purchase Requisition Type", pur_req_type)

        if purchase_requisition_type.required_fields:
            for row in purchase_requisition_type.required_fields:
                if row.company == company:

                    # Process account_assignment_category
                    account_assignment_category_head = []
                    if row.account_assignment_category:
                        categories = [cat.strip() for cat in row.account_assignment_category.split(",")]
                        for cat in categories:
                            try:
                                category_doc = frappe.get_doc("Account Assignment Category", cat)
                                account_assignment_category_head.append({
                                    "name": category_doc.name,
                                    "account_assignment_category_code": getattr(category_doc, "account_assignment_category_code", ""),
                                    "account_assignment_category_name": getattr(category_doc, "account_assignment_category_name", ""),
                                    "description": getattr(category_doc, "description", "")
                                })

                            except frappe.DoesNotExistError:
                                frappe.log_error(f"Account Assignment Category '{cat}' not found", "Return Acc Ass Category List")

                    # Process item_category
                    item_category_head = []
                    if row.item_category:
                        try:
                            item_cat_doc = frappe.get_doc("Item Category Master", row.item_category)
                            item_category_head.append({
                                "name": item_cat_doc.name,
                                "item_code": getattr(item_cat_doc, "item_code", ""),
                                "item_name": getattr(item_cat_doc, "item_name", ""),
                                "description": getattr(item_cat_doc, "description", "")
                            })

                        except frappe.DoesNotExistError:
                            frappe.log_error(f"Item Category Master '{row.item_category}' not found", "Return Acc Ass Category List")

                    frappe.local.response["http_status_code"] = 200
                    return {
                        "account_assignment_category_head": account_assignment_category_head,
                        "item_category_head": item_category_head
                    }

        frappe.local.response["http_status_code"] = 404
        return {
            "status": "error",
            "message": f"No matching required fields found for company '{company}'."
        }

    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        return {
            "status": "error",
            "message": f"Purchase Requisition Type '{pur_req_type}' does not exist."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Filter Request Fields API Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": "Failed to retrieve filter request fields.",
            "error": str(e)
        }