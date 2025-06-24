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
                "item_category" : "Compulsory must D",
                "short_text": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "material_group": "Non Compulsory",
                "uom": "Non Compulsory",
                "gl_account_number": "Compulsory",
                "cost_center": "Compulsory",
                "requisitioner": "Compulsory"
            } 
        elif company == "900" and pur_type == "NB" and acct_cate == "A":
            return {
                # "status": "success",
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "main_asset_no": "Compulsory",
                "purchase_group": "Non Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "800" and pur_type == "SB" and acct_cate == "K":
            return {
                # "status": "success",
                "item_category" : "Compulsory must D",
                "short_text": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "material_group": "Non Compulsory",
                "uom": "Non Compulsory",
                "gl_account_number": "Compulsory",
                "cost_center": "Compulsory",
                "requisitioner": "Compulsory"
            } 
        elif company == "800" and pur_type == "NB" and acct_cate == "A":
            return {
                # "status": "success",
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "main_asset_no": "Compulsory",
                "purchase_group": "Non Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "700" and pur_type == "SB" and (acct_cate == "K" or acct_cate == "A"):
            return {
                # "status": "success",
                "item_category" : "Compulsory must D",
                "short_text": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "material_group": "Non Compulsory",
                "uom": "Non Compulsory",
                "gl_account_number": "Compulsory",
                "cost_center": "Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "700" and pur_type == "NB":
            return {
                # "status": "success",
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "purchase_group": "Non Compulsory",
                "requisitioner": "Compulsory",
            }
        elif company == "700" and pur_type == "NB" and acct_cate == "A":
            return {
                # "status": "success",
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "main_asset_no": "Compulsory",
                "purchase_group": "Non Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "300" and pur_type == "NB":
            return{
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "300" and pur_type == "NB" and acct_cate == "A":
            return{
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "main_asset_no": "Compulsory",
                "purchase_group": "Non Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "300" and pur_type == "SB" and acct_cate == "K":
            return{
                "item_category" : "Compulsory must D",
                "short_text": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "material_group": "Non Compulsory",
                "uom": "Non Compulsory",
                "gl_account_number": "Compulsory",
                "cost_center": "Compulsory",
                "requisitioner": "Compulsory"
        }
        elif company == "200" and pur_type == "NB":    
            return{
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "requisitioner": "Compulsory",
                "purchase_group": "Non Compulsory"
            }
        elif company == "200" and pur_type == "NB" and acct_cate == "A":
            return{
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "main_asset_no": "Compulsory",
                "purchase_group": "Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "200" and pur_type == "SB" and (acct_cate == "K" or acct_cate == "A"):
            return {
                "item_category" : "Compulsory must D",
                "short_text": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "material_group": "Non Compulsory",
                "uom": "Non Compulsory",
                "gl_account_number": "Compulsory",
                "cost_center": "Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "100" and pur_type == "NB" and acct_cate == "A":
            return{
                "material_code": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "main_asset_no": "Compulsory",
                "purchase_group": "Compulsory",
                "requisitioner": "Compulsory"
            }
        elif company == "100" and pur_type == "SB" and (acct_cate == "K" or acct_cate == "A"):
            return {
                "item_category" : "Compulsory must D",
                "short_text": "Compulsory",
                "plant": "Compulsory",
                "quantity": "Compulsory",
                "material_group": "Non Compulsory",
                "uom": "Non Compulsory",
                "gl_account_number": "Compulsory",
                "cost_center": "Compulsory",
                "requisitioner": "Compulsory"
            }
        else:
            return {
                "status": "error",
                "message": "Invalid combination of company, purchase type, and account category."
            }  

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Filter Request Fields API Error")
        return {
            "status": "error",
            "message": "Failed to retrieve filter request fields.",
            "error": str(e)
        }          


