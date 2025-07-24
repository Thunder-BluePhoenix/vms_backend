import frappe
from frappe import _
import json


# filter purchase Group
@frappe.whitelist(allow_guest=True)
def filter_purchase_group(company):
    try:
        if not company:
            return {
                "status": "error",
                "message": "Company is required"
            }

        pur_grp = frappe.get_all(
            "Purchase Group Master",
            filters={"company": company},
            fields=["name", "purchase_group_code", "purchase_group_name", "description"]
        )

        return {
            "status": "success",
            "pur_grp": pur_grp
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering purchase group")
        return {
            "status": "error",
            "message": "Failed to filter purchase group.",
            "error": str(e)
        }
	

# company wise storage location
@frappe.whitelist(allow_guest=True)
def filter_store_location(company):
    try:
        if not company:
            return {
                "status": "error",
                "message": "Company is required"
            }

        storage = frappe.get_all(
            "Storage Location Master",
            filters={"company": company},
            fields=["name", "storage_name", "storage_location_name", "description"]
        )

        return {
            "status": "success",
            "storage": storage
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error filtering storage location")
        return {
            "status": "error",
            "message": "Failed to filter storage location.",
            "error": str(e)
        }


# Get Cart Details based on cart id
@frappe.whitelist(allow_guest=True)
def get_cart_details(cart_id):
	try:
		if not cart_id:
			return {
				"status": "error",
				"message": "cart_id is required"
			}

		doc = frappe.get_doc("Cart Details", cart_id)

		return {
			"status": "success",
			"data": {
				"requisitioner": doc.user,
				"company": doc.company,
				"plant": doc.plant,
				"purchase_group": doc.purchase_group,
				"purchase_requisition_type": doc.purchase_type
			}
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Cart Details Error")
		return {
			"status": "error",
			"message": "Failed to fetch cart details",
			"error": str(e)
		}
	

# create purchase requisition webform doc based on cart id and append the table

@frappe.whitelist(allow_guest=True)
def create_purchase_requisition(cart_id):
	try:
		if not cart_id:
			return {"status": "error", "message": "Cart ID is required."}

		cart_details = frappe.get_doc("Cart Details", cart_id)

		# Create one purchase requisition document for all items
		pur_req = frappe.new_doc("Purchase Requisition Webform")
		pur_req.cart_details_id = cart_id  
		pur_req.requisitioner = cart_details.user
		pur_req.company = cart_details.company  
		pur_req.purchase_group = cart_details.purchase_group  
		pur_req.purchase_requisition_type = cart_details.purchase_type  

		item_number = 10
		for row in cart_details.cart_product:
			pur_req.append("purchase_requisition_form_table", {
				"item_number_of_purchase_requisition_head": str(item_number),
				"main_asset_no_head": row.assest_code,
				"product_name_head": row.product_name,
				"product_price_head": row.product_price,
				"final_price_by_purchase_team_head": row.final_price_by_purchase_team,
				"lead_time_head": row.lead_time,
				"purchase_requisition_type": cart_details.purchase_type,
				"plant_head": cart_details.plant,
				"requisitioner_name_head": cart_details.user,
				"company_code_area_head": cart_details.company
			})
			item_number += 10

		pur_req.save(ignore_permissions=True)

		return {
			"status": "success",   
			"message": "Purchase Requisition created.",
			"name": pur_req.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create Purchase Requisition Error")
		return {
			"status": "error", 
			"message": "An error occurred.", 
			"error": str(e)
		}


# get full data of purchase requisition webform

@frappe.whitelist(allow_guest=True)
def get_full_data_pur_req(name):
	try:
		if name:
			doc = frappe.get_doc("Purchase Requisition Webform", name)
			if doc:
				data = doc.as_dict()

				data["purchase_requisition_form_table"] = [
					row.as_dict() for row in doc.purchase_requisition_form_table
					if not row.get("is_deleted")
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
		else:
			return {
				"status": "error",
				"message": "Name is required."
			}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Send Purchase Requisition Data API Error")
		return {
			"status": "error",
			"message": "Failed to retrieve Purchase Requisition Webform data.",
			"error": str(e)
		}


# get pr table data in format
@frappe.whitelist(allow_guest=True)
def get_pur_req_table_data(name):
	try:
		if not name:
			return {
				"status": "error",
				"message": "Purchase Requisition Webform name is required."
			}

		doc = frappe.get_doc("Purchase Requisition Webform", name)
		grouped_data = {}

		for row in sorted(doc.purchase_requisition_form_table, key=lambda x: x.idx):
			head_id = row.head_unique_id
			if not head_id:
				continue

			# Add head if not present
			if head_id not in grouped_data:
				grouped_data[head_id] = {
					"row_name": row.name,
					"head_unique_id": row.head_unique_id,
					"status_head": row.status_head,
					"purchase_requisition_item_head": row.purchase_requisition_item_head,
					"item_number_of_purchase_requisition_head": row.item_number_of_purchase_requisition_head,
					"purchase_requisition_date_head": row.purchase_requisition_date_head,
					"purchase_requisition_type": row.purchase_requisition_type,
					"delivery_date_head": row.delivery_date_head,
					"store_location_head": row.store_location_head,
					"item_category_head": row.item_category_head,
					"material_group_head": row.material_group_head,
					"uom_head": row.uom_head,
					"cost_center_head": row.cost_center_head,
					"main_asset_no_head": row.main_asset_no_head,
					"asset_subnumber_head": row.asset_subnumber_head,
					"profit_ctr_head": row.profit_ctr_head,
					"short_text_head": row.short_text_head,
					"line_item_number_head": row.line_item_number_head,
					"company_code_area_head": row.company_code_area_head,
					"c_delivery_date_head": row.c_delivery_date_head,
					"quantity_head": row.quantity_head,
					"price_of_purchase_requisition_head": row.price_of_purchase_requisition_head,
					"gl_account_number_head": row.gl_account_number_head,
					"material_code_head": row.material_code_head,
					"account_assignment_category_head": row.account_assignment_category_head,
					"purchase_group_head": row.purchase_group_head,
					"product_name_head": row.product_name_head,
					"product_price_head": row.product_price_head,
					"final_price_by_purchase_team_head": row.final_price_by_purchase_team_head,
					"lead_time_head": row.lead_time_head,
					"plant_head": row.plant_head,
					"requisitioner_name_head": row.requisitioner_name_head,
					"tracking_id_head": row.tracking_id_head,
					"desired_vendor_head": row.desired_vendor_head,
					"valuation_area_head": row.valuation_area_head,
					"fixed_value_head": row.fixed_value_head,
					"spit_head": row.spit_head,
					"purchase_organisation_head": row.purchase_organisation_head,
					"agreement_head": row.agreement_head,
					"item_of_head": row.item_of_head,
					"mpn_number_head": row.mpn_number_head,
					"subhead_fields": []
				}

			# Add subhead if created, not deleted, and not same row as head
			if row.is_created and not row.is_deleted:
				subhead_data = {
					"row_name": row.name,
					"sub_head_unique_id": row.sub_head_unique_id,
					"purchase_requisition_item_subhead": row.purchase_requisition_item_subhead,
					"item_number_of_purchase_requisition_subhead": row.item_number_of_purchase_requisition_subhead,
					"purchase_requisition_date_subhead": row.purchase_requisition_date_subhead,
					"delivery_date_subhead": row.delivery_date_subhead,
					"store_location_subhead": row.store_location_subhead,
					"item_category_subhead": row.item_category_subhead,
					"material_group_subhead": row.material_group_subhead,
					"uom_subhead": row.uom_subhead,
					"cost_center_subhead": row.cost_center_subhead,
					"main_asset_no_subhead": row.main_asset_no_subhead,
					"asset_subnumber_subhead": row.asset_subnumber_subhead,
					"profit_ctr_subhead": row.profit_ctr_subhead,
					"short_text_subhead": row.short_text_subhead,
					"quantity_subhead": row.quantity_subhead,
					"price_of_purchase_requisition_subhead": row.price_of_purchase_requisition_subhead,
					"gl_account_number_subhead": row.gl_account_number_subhead,
					"material_code_subhead": row.material_code_subhead,
					"account_assignment_category_subhead": row.account_assignment_category_subhead,
					"purchase_group_subhead": row.purchase_group_subhead,
					"line_item_number_subhead": row.line_item_number_subhead,
					"service_number_subhead": row.service_number_subhead,
					"gross_price_subhead": row.gross_price_subhead,
					"currency_subhead": row.currency_subhead,
					"service_type_subhead": row.service_type_subhead,
					"net_value_subhead": row.net_value_subhead
				}
				grouped_data[head_id]["subhead_fields"].append(subhead_data)

		return {
			"status": "success",
			"docname": doc.name,
			"Requisitioner": doc.requisitioner,
			"purchase_requisition_type": doc.purchase_requisition_type,
			"Company": frappe.db.sql(
				"""
				SELECT name, company_name, description 
				FROM `tabCompany Master` 
				WHERE name = %s
				""", (doc.company,), as_dict=True
			),
			"Purchase Group": doc.purchase_group,
			"Cart ID": doc.cart_details_id,
			"Form Status": doc.form_status,
			"data": list(grouped_data.values())
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Purchase Requisition Table Data Error")
		return {
			"status": "error",
			"message": "Failed to retrieve Purchase Requisition Webform data.",
			"error": str(e)
		}


# create or update pr table head form
@frappe.whitelist(allow_guest=True)
def create_update_pr_table_head_form(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		docname = data.get("name")
		rows = data.get("rows")

		if not docname or not rows or not isinstance(rows, list):
			return {
				"status": "error",
				"message": "'name' and 'rows' (as a list) are required."
			}

		doc = frappe.get_doc("Purchase Requisition Webform", docname)

		updated_rows = []
		created_rows = []

		for update_row in rows:
			row_name = update_row.get("row_name")
			target_row = None

			if row_name:
				target_row = next((r for r in doc.purchase_requisition_form_table if r.name == row_name), None)

			if target_row:
				# Update existing row
				for field, value in update_row.items():
					if hasattr(target_row, field):
						setattr(target_row, field, value)
				updated_rows.append(row_name)
			else:
				# Append new row
				new_row = doc.append("purchase_requisition_form_table", {
					"purchase_requisition_item_head": update_row.get("purchase_requisition_item_head"),
					"item_number_of_purchase_requisition_head": update_row.get("item_number_of_purchase_requisition_head"),
					"purchase_requisition_date_head": update_row.get("purchase_requisition_date_head"),
					"purchase_requisition_type": update_row.get("purchase_requisition_type"),
					"delivery_date_head": update_row.get("delivery_date_head"),
					"store_location_head": update_row.get("store_location_head"),
					"item_category_head": update_row.get("item_category_head"),
					"material_group_head": update_row.get("material_group_head"),
					"uom_head": update_row.get("uom_head"),
					"cost_center_head": update_row.get("cost_center_head"),
					"main_asset_no_head": update_row.get("main_asset_no_head"),
					"asset_subnumber_head": update_row.get("asset_subnumber_head"),
					"profit_ctr_head": update_row.get("profit_ctr_head"),
					"short_text_head": update_row.get("short_text_head"),
					"line_item_number_head": update_row.get("line_item_number_head"),
					"company_code_area_head": update_row.get("company_code_area_head"),
					"c_delivery_date_head": update_row.get("c_delivery_date_head"),
					"quantity_head": update_row.get("quantity_head"),
					"price_of_purchase_requisition_head": update_row.get("price_of_purchase_requisition_head"),
					"gl_account_number_head": update_row.get("gl_account_number_head"),
					"material_code_head": update_row.get("material_code_head"),
					"account_assignment_category_head": update_row.get("account_assignment_category_head"),
					"purchase_group_head": update_row.get("purchase_group_head"),
					"product_name_head": update_row.get("product_name_head"),
					"product_price_head": update_row.get("product_price_head"),
					"final_price_by_purchase_team_head": update_row.get("final_price_by_purchase_team_head"),
					"lead_time_head": update_row.get("lead_time_head"),
					"plant_head": update_row.get("plant_head"),
					"requisitioner_name_head": update_row.get("requisitioner_name_head"),
					"tracking_id_head": update_row.get("tracking_id_head"),
					"desired_vendor_head": update_row.get("desired_vendor_head"),
					"valuation_area_head": update_row.get("valuation_area_head"),
					"fixed_value_head": update_row.get("fixed_value_head"),
					"spit_head": update_row.get("spit_head"),
					"purchase_organisation_head": update_row.get("purchase_organisation_head"),
					"agreement_head": update_row.get("agreement_head"),
					"item_of_head": update_row.get("item_of_head"),
					"mpn_number_head": update_row.get("mpn_number_head")
				})
				created_rows.append(new_row.name)

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": f"{len(updated_rows)} row(s) updated, {len(created_rows)} row(s) created.",
			"updated_rows": updated_rows,
			"created_rows": created_rows
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Update PR Head Form Error")
		return {
			"status": "error",
			"message": "Failed to update or create head rows.",
			"error": str(e)
		}



# Update only head part fields
@frappe.whitelist(allow_guest=True)
def update_pr_table_head_form(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		docname = data.get("name")
		row_name = data.get("row_name")

		if not docname or not row_name:
			return {
				"status": "error",
				"message": "'name' and 'row_name' are required."
			}

		doc = frappe.get_doc("Purchase Requisition Webform", docname)
		updated = False

		for row in doc.purchase_requisition_form_table:
			if row.name == row_name:
				for field, value in data.items():
					if field not in ["name", "row_name"] and hasattr(row, field):
						setattr(row, field, value if value is not None else "")
				updated = True
				break

		if not updated:
			return {
				"status": "error",
				"message": f"No row found with name: {row_name}"
			}

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": f"Row '{row_name}' updated successfully."
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Update PR Head Form Error")
		return {
			"status": "error",
			"message": "Failed to update head row data.",
			"error": str(e)
		}


# create pr table subhead form

# @frappe.whitelist(allow_guest=True)
# def create_pr_table_subhead_form(data):
# 	try:
# 		if isinstance(data, str):
# 			data = json.loads(data)

# 		docname = data.get("name")
# 		rows = data.get("data")

# 		if not docname or not rows or not isinstance(rows, list):
# 			return {
# 				"status": "error",
# 				"message": "'name' and 'data' (as a list) are required."
# 			}

# 		doc = frappe.get_doc("Purchase Requisition Webform", docname)
# 		created_rows = []
# 		updated_rows = []

# 		for head in rows:
# 			row_name = head.get("row_name")
# 			head_row = None

# 			if row_name:
# 				head_row = next((r for r in doc.purchase_requisition_form_table if r.name == row_name), None)

# 			if not head_row:
# 				continue

# 			subheads = head.get("subhead_fields", [])

# 			for idx, subhead in enumerate(subheads):
# 				if idx == 0 and head_row and not head_row.is_created:
# 					# Update existing head row with first subhead
# 					for field, value in subhead.items():
# 						if hasattr(head_row, field):
# 							setattr(head_row, field, value)
# 					head_row.is_created = 1
# 					updated_rows.append(head_row.name)
# 				else:
# 					# Create new row for remaining subheads
# 					new_row = doc.append("purchase_requisition_form_table", {
# 						"row_name": head_row.name,
# 						"head_unique_id": head_row.head_unique_id,
# 						"purchase_requisition_item_head": head_row.purchase_requisition_item_head,
# 						"item_number_of_purchase_requisition_head": head_row.item_number_of_purchase_requisition_head,
# 						"purchase_requisition_date_head": head_row.purchase_requisition_date_head,
# 						"purchase_requisition_type": head_row.purchase_requisition_type,
# 						"delivery_date_head": head_row.delivery_date_head,
# 						"store_location_head": head_row.store_location_head,
# 						"item_category_head": head_row.item_category_head,
# 						"material_group_head": head_row.material_group_head,
# 						"uom_head": head_row.uom_head,
# 						"cost_center_head": head_row.cost_center_head,
# 						"main_asset_no_head": head_row.main_asset_no_head,
# 						"asset_subnumber_head": head_row.asset_subnumber_head,
# 						"profit_ctr_head": head_row.profit_ctr_head,
# 						"short_text_head": head_row.short_text_head,
# 						"quantity_head": head_row.quantity_head,
# 						"price_of_purchase_requisition_head": head_row.price_of_purchase_requisition_head,
# 						"gl_account_number_head": head_row.gl_account_number_head,
# 						"material_code_head": head_row.material_code_head,
# 						"account_assignment_category_head": head_row.account_assignment_category_head,
# 						"purchase_group_head": head_row.purchase_group_head,
# 						"product_name_head": head_row.product_name_head,
# 						"product_price_head": head_row.product_price_head,
# 						"final_price_by_purchase_team_head": head_row.final_price_by_purchase_team_head,
# 						"lead_time_head": head_row.lead_time_head,
# 						"plant": head_row.plant,

# 						# subhead fields
# 						"sub_head_unique_id": subhead.get("sub_head_unique_id"),
# 						"purchase_requisition_item_subhead": subhead.get("purchase_requisition_item_subhead"),
# 						"item_number_of_purchase_requisition_subhead": subhead.get("item_number_of_purchase_requisition_subhead"),
# 						"purchase_requisition_date_subhead": subhead.get("purchase_requisition_date_subhead"),
# 						"delivery_date_subhead": subhead.get("delivery_date_subhead"),
# 						"store_location_subhead": subhead.get("store_location_subhead"),
# 						"item_category_subhead": subhead.get("item_category_subhead"),
# 						"material_group_subhead": subhead.get("material_group_subhead"),
# 						"uom_subhead": subhead.get("uom_subhead"),
# 						"cost_center_subhead": subhead.get("cost_center_subhead"),
# 						"main_asset_no_subhead": subhead.get("main_asset_no_subhead"),
# 						"asset_subnumber_subhead": subhead.get("asset_subnumber_subhead"),
# 						"profit_ctr_subhead": subhead.get("profit_ctr_subhead"),
# 						"short_text_subhead": subhead.get("short_text_subhead"),
# 						"quantity_subhead": subhead.get("quantity_subhead"),
# 						"price_of_purchase_requisition_subhead": subhead.get("price_of_purchase_requisition_subhead"),
# 						"gl_account_number_subhead": subhead.get("gl_account_number_subhead"),
# 						"material_code_subhead": subhead.get("material_code_subhead"),
# 						"account_assignment_category_subhead": subhead.get("account_assignment_category_subhead"),
# 						"purchase_group_subhead": subhead.get("purchase_group_subhead"),
# 						"is_created": 1,
# 						"is_deleted": 0
# 					})
# 					created_rows.append(new_row.name)

# 		doc.save(ignore_permissions=True)
# 		frappe.db.commit()

# 		return {
# 			"status": "success",
# 			"message": f"{len(updated_rows)} subhead(s) updated, {len(created_rows)} created.",
# 			"updated_rows": updated_rows,
# 			"created_rows": created_rows
# 		}

# 	except Exception as e:
# 		frappe.db.rollback()
# 		frappe.log_error(frappe.get_traceback(), "Create PR Subhead Form Error")
# 		return {
# 			"status": "error",
# 			"message": "Failed to create/update subhead rows.",
# 			"error": str(e)
# 		}


# create pr table subhead form one by one

@frappe.whitelist(allow_guest=True)
def create_pr_table_subhead_form(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		docname = data.get("name")
		row_name = data.get("row_name")

		if not docname or not row_name:
			return {
				"status": "error",
				"message": "'name' and 'row_name' are required."
			}

		doc = frappe.get_doc("Purchase Requisition Webform", docname)
		head_row = next((r for r in doc.purchase_requisition_form_table if r.name == row_name), None)

		if not head_row:
			return {
				"status": "error",
				"message": f"Row '{row_name}' not found in document '{docname}'."
			}

		subhead_fields = [
			"sub_head_unique_id",
			"purchase_requisition_item_subhead",
			"item_number_of_purchase_requisition_subhead",
			"purchase_requisition_date_subhead",
			"delivery_date_subhead",
			"store_location_subhead",
			"item_category_subhead",
			"material_group_subhead",
			"uom_subhead",
			"cost_center_subhead",
			"main_asset_no_subhead",
			"asset_subnumber_subhead",
			"profit_ctr_subhead",
			"short_text_subhead",
			"quantity_subhead",
			"price_of_purchase_requisition_subhead",
			"gl_account_number_subhead",
			"material_code_subhead",
			"account_assignment_category_subhead",
			"purchase_group_subhead",
			"line_item_number_subhead",
			"service_number_subhead",
			"gross_price_subhead",
			"currency_subhead",
			"service_type_subhead",
			"net_value_subhead"
		]

		head_fields = [
			"head_unique_id",
			"purchase_requisition_item_head",
			"item_number_of_purchase_requisition_head",
			"purchase_requisition_date_head",
			"purchase_requisition_type",
			"delivery_date_head",
			"store_location_head",
			"item_category_head",
			"material_group_head",
			"uom_head",
			"cost_center_head",
			"main_asset_no_head",
			"asset_subnumber_head",
			"profit_ctr_head",
			"short_text_head",
			"line_item_number_head",
			"company_code_area_head",
			"c_delivery_date_head",
			"quantity_head",
			"price_of_purchase_requisition_head",
			"gl_account_number_head",
			"material_code_head",
			"account_assignment_category_head",
			"purchase_group_head",
			"product_name_head",
			"product_price_head",
			"final_price_by_purchase_team_head",
			"lead_time_head",
			"plant_head",
			"requisitioner_name_head",
			"tracking_id_head",
			"desired_vendor_head",
			"valuation_area_head",
			"fixed_value_head",
			"spit_head",
			"purchase_organisation_head",
			"agreement_head",
			"item_of_head",
			"mpn_number_head"
		]

		if not head_row.is_created:
			for field in subhead_fields:
				value = data.get(field)
				if value not in [None, ""]:
					setattr(head_row, field, value)
			head_row.is_created = 1
			updated_row = head_row.name
			created_row = None
		else:
			new_row = doc.append("purchase_requisition_form_table", {})
			for field in head_fields:
				new_row.set(field, head_row.get(field))
			for field in subhead_fields:
				value = data.get(field)
				if value not in [None, ""]:
					new_row.set(field, value)
			new_row.is_created = 1
			new_row.is_deleted = 0
			created_row = new_row.name
			updated_row = None

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Subhead row processed successfully.",
			"updated_row": updated_row,
			"created_row": created_row
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Create PR Subhead Form Error")
		return {
			"status": "error",
			"message": "Failed to create/update subhead row.",
			"error": str(e)
		}


#update pr table subhead table form
@frappe.whitelist(allow_guest=True)
def update_pr_table_subhead_form(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		docname = data.get("name")
		row_name = data.get("row_name")

		if not docname or not row_name:
			return {
				"status": "error",
				"message": "'name' and 'row_name' are required."
			}

		doc = frappe.get_doc("Purchase Requisition Webform", docname)
		subhead_fields = [
			"purchase_requisition_item_subhead",
			"item_number_of_purchase_requisition_subhead",
			"purchase_requisition_date_subhead",
			"delivery_date_subhead",
			"store_location_subhead",
			"item_category_subhead",
			"material_group_subhead",
			"uom_subhead",
			"cost_center_subhead",
			"main_asset_no_subhead",
			"asset_subnumber_subhead",
			"profit_ctr_subhead",
			"short_text_subhead",
			"quantity_subhead",
			"price_of_purchase_requisition_subhead",
			"gl_account_number_subhead",
			"material_code_subhead",
			"account_assignment_category_subhead",
			"purchase_group_subhead",
			"line_item_number_subhead",
			"service_number_subhead",
			"gross_price_subhead",
			"currency_subhead",
			"service_type_subhead",
			"net_value_subhead"
		]

		row_found = False
		for row in doc.purchase_requisition_form_table:
			if row.name == row_name:
				for field in subhead_fields:
					value = data.get(field)
					if value not in [None, ""]:
						setattr(row, field, value)
				row_found = True
				break

		if not row_found:
			return {
				"status": "error",
				"message": f"No matching subhead row found with name '{row_name}'."
			}

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": f"Subhead row '{row_name}' updated successfully.",
			"updated_row": row_name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Update PR Subhead Form Error")
		return {
			"status": "error",
			"message": "Failed to update subhead row.",
			"error": str(e)
		}

# delete pr table row
@frappe.whitelist(allow_guest=True)
def delete_pr_table_row(name, row_id):
	try:
		if not name or not row_id:
			return {
				"status": "error",
				"message": "'name' and 'row_id' are required."
			}

		doc = frappe.get_doc("Purchase Requisition Webform", name)
		found = False

		for row in doc.purchase_requisition_form_table:
			if row.name == row_id:
				row.is_deleted = 1
				found = True
				break

		if not found:
			return {
				"status": "error",
				"message": f"Row with ID '{row_id}' not found in document '{name}'."
			}

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": f"Row '{row_id}' marked as deleted successfully."
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Delete PR Table Row Error")
		return {
			"status": "error",
			"message": "Failed to mark row as deleted.",
			"error": str(e)
		}

# submit the pr form
@frappe.whitelist(allow_guest=True)
def submit_pr_form(name):
	try:
		if not name:
			return {
				"status": "error",
				"message": "'name' is required."
			}
		
		doc = frappe.get_doc("Purchase Requisition Webform", name)
		doc.form_is_submitted = 1
		doc.form_status = "Submitted"

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": f"Purchase Requisition Webform '{name}' submitted successfully."
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Submit PR Form Error")
		return {
			"status": "error",
			"message": "Failed to submit the Purchase Requisition Webform.",
			"error": str(e)
		}