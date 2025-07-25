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
        purchase_organisation = frappe.db.sql("""SELECT name, purchase_organization_code, purchase_organization_name, description FROM `tabPurchase Organization Master`""", as_dict=True)
        store_location = frappe.db.sql("""SELECT name, store_name, store_location, store_location_name, description FROM `tabStore Location Master`""", as_dict=True)
        valuation_area = frappe.db.sql("""SELECT name, valuation_area_name, valuation_area_code FROM `tabValuation Area Master`""", as_dict=True)
        currency_master = frappe.db.sql("""SELECT name, currency_code, currency_name FROM `tabCurrency Master`""", as_dict=True)
        rfq_type = frappe.db.sql("""SELECT name, vendor_type_name, vendor_type_code FROM `tabVendor Type Master`""", as_dict=True)
        mode_of_shipment = frappe.db.sql("""SELECT name, description FROM `tabMode Of Shipment`""", as_dict=True)
        port_master = frappe.db.sql("""SELECT name, port_code, port_name FROM `tabPort Master`""", as_dict=True)
        country_master = frappe.db.sql("""SELECT name, country_code, country_name  FROM `tabCountry Master`""", as_dict=True)
        # port_master_code = frappe.db.sql("""SELECT name, port_code, port_name FROM `tabPort Master`""", as_dict=True)
        incoterm_master = frappe.db.sql("""SELECT name, incoterm_code, incoterm_name FROM `tabIncoterm Master`""", as_dict=True)
        package_type = frappe.db.sql("""SELECT name, package_code, package_name, description FROM `tabPackage Type Master`""", as_dict=True)
        product_category = frappe.db.sql("""SELECT name, product_category_code, product_category_name, description FROM `tabProduct Category Master`""", as_dict=True)
        shipment_type = frappe.db.sql("""SELECT name, shipment_type_code, shipment_type_name, description FROM `tabShipment Type Master`""", as_dict=True)
        item_code = frappe.db.sql("""SELECT name, product_code, product_name, description FROM `tabProduct Master`""", as_dict=True)
        material_category = frappe.db.sql("""SELECT name, material_category_code, material_category_name, description FROM `tabMaterial Category Master`""", as_dict=True)
        storage_location = frappe.db.sql("""SELECT name, storage_location_name, description FROM `tabStorage Location Master`""", as_dict=True)
        valuation_class = frappe.db.sql("""SELECT name, valuation_class_code, valuation_class_name FROM `tabValuation Class Master`""", as_dict=True)

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
            "account_category": account_category,
            "purchase_organisation": purchase_organisation,
            "store_location": store_location,
            "valuation_area": valuation_area,  
            "currency_master": currency_master,
            "rfq_type": rfq_type,
            "mode_of_shipment": mode_of_shipment,
            "port_master": port_master,
            "country_master": country_master,
            # "port_master_code": port_master_code,
            "incoterm_master": incoterm_master,
            "package_type": package_type,
            "product_category": product_category,
            "shipment_type": shipment_type,
            "item_code": item_code,
            "material_category": material_category,
            "storage_location": storage_location,
            "valuation_class": valuation_class
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Purchase Requisition Masters API Error")
        return {
            "status": "error",
            "message": "Failed to retrieve Purchase Requisition masters.",
            "error": str(e)
        }


# @frappe.whitelist(allow_guest=True)
# def create_purchase_requisition(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)
        
#         main_doc_fields = {
#             "doctype": "Purchase Requisition Webform",
#             "purchase_requisition_type": data.get("purchase_requisition_type"),
#             "plant": data.get("plant"),
#             "company_code_area": data.get("company_code_area"),
#             "company": data.get("company"),
#             "requisitioner": data.get("requisitioner"),
#             "purchase_group": data.get("purchase_group"),
#             "cart_details_id": data.get("cart_details_id")
#         }

#         # Create new document
#         doc = frappe.new_doc("Purchase Requisition Webform")
#         doc.update(main_doc_fields)

#         # Add child table rows
#         table_data = data.get("purchase_requisition_form_table", [])
#         for row in table_data:
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
#                 # "purchase_group": row.get("purchase_group")
#             })

#         doc.insert(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Purchase Requisition Webform created successfully.",
#             "name": doc.name
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Create Purchase Requisition Webform API Error")
#         return {
#             "status": "error",
#             "message": "Failed to create Purchase Requisition Webform.",
#             "error": str(e)
#         }


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
			"purchase_group": data.get("purchase_group"),
			"cart_details_id": data.get("cart_details_id")
		}

		doc = frappe.new_doc("Purchase Requisition Webform")
		doc.update(main_doc_fields)

		# Group head rows by item_number_of_purchase_requisition_head
		head_rows = data.get("purchase_requisition_form_table", [])
		grouped_data = {}

		for row in head_rows:
			item_number = row.get("item_number_of_purchase_requisition_head")
			if item_number:
				grouped_data.setdefault(item_number, []).append(row)

		# Iterate through each item_number group
		for item_number, grouped_rows in grouped_data.items():
			for head_row in grouped_rows:
				subhead_rows = head_row.get("subhead_rows", [])

				for sub in subhead_rows:
					doc.append("purchase_requisition_form_table", {
						# Head fields
						"purchase_requisition_item_head": head_row.get("purchase_requisition_item_head"),
						"item_number_of_purchase_requisition_head": head_row.get("item_number_of_purchase_requisition_head"),
						"purchase_requisition_date_head": head_row.get("purchase_requisition_date_head"),
						"delivery_date_head": head_row.get("delivery_date_head"),
						"store_location_head": head_row.get("store_location_head"),
						"item_category_head": head_row.get("item_category_head"),
						"material_group_head": head_row.get("material_group_head"),
						"uom_head": head_row.get("uom_head"),
						"cost_center_head": head_row.get("cost_center_head"),
						"main_asset_no_head": head_row.get("main_asset_no_head"),
						"asset_subnumber_head": head_row.get("asset_subnumber_head"),
						"profit_ctr_head": head_row.get("profit_ctr_head"),
						"short_text_head": head_row.get("short_text_head"),
						"quantity_head": head_row.get("quantity_head"),
						"price_of_purchase_requisition_head": head_row.get("price_of_purchase_requisition_head"),
						"gl_account_number_head": head_row.get("gl_account_number_head"),
						"material_code_head": head_row.get("material_code_head"),
						"account_assignment_category_head": head_row.get("account_assignment_category_head"),

						# Subhead fields
						"purchase_requisition_item_subhead": sub.get("purchase_requisition_item_subhead"),
						"item_number_of_purchase_requisition_subhead": sub.get("item_number_of_purchase_requisition_subhead"),
						"purchase_requisition_date_subhead": sub.get("purchase_requisition_date_subhead"),
						"delivery_date_subhead": sub.get("delivery_date_subhead"),
						"store_location_subhead": sub.get("store_location_subhead"),
						"item_category_subhead": sub.get("item_category_subhead"),
						"material_group_subhead": sub.get("material_group_subhead"),
						"uom_subhead": sub.get("uom_subhead"),
						"cost_center_subhead": sub.get("cost_center_subhead"),
						"main_asset_no_subhead": sub.get("main_asset_no_subhead"),
						"asset_subnumber_subhead": sub.get("asset_subnumber_subhead"),
						"profit_ctr_subhead": sub.get("profit_ctr_subhead"),
						"short_text_subhead": sub.get("short_text_subhead"),
						"quantity_subhead": sub.get("quantity_subhead"),
						"price_of_purchase_requisition_subhead": sub.get("price_of_purchase_requisition_subhead"),
						"gl_account_number_subhead": sub.get("gl_account_number_subhead"),
						"material_code_subhead": sub.get("material_code_subhead"),
						"account_assignment_category_subhead": sub.get("account_assignment_category_subhead"),
						"purchase_group_subhead": sub.get("purchase_group_subhead")
					})

		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Purchase Requisition Webform created successfully.",
			"name": doc.name
		}

	except Exception as e:
		frappe.db.rollback()
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