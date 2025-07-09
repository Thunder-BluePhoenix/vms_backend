import frappe
import json

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
				"purchase_type": doc.purchase_type
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
				"lead_time_head": row.lead_time
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
			if row.get("is_deleted") == 1:
				continue 

			head_no = str(row.item_number_of_purchase_requisition_head or "")

			if not head_no:
				continue

			if head_no not in grouped_data:
				grouped_data[head_no] = {
						"row_name": row.name,
						"head_unique_id": row.head_unique_id,
						"purchase_requisition_item_head": row.purchase_requisition_item_head,
						"item_number_of_purchase_requisition_head": row.item_number_of_purchase_requisition_head,
						"purchase_requisition_date_head": row.purchase_requisition_date_head,
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
						"plant": row.plant,
						"subhead_fields": []
				}

			if row.get("is_created"):
				grouped_data[head_no]["subhead_fields"].append({
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
					"purchase_group_subhead": row.purchase_group_subhead
				})

		final_result = list(grouped_data.values())

		return {
			"status": "success",
			"docname": doc.name,
			"Form Status": doc.form_status,	
			"data": final_result
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Purchase Requisition Table Data Error")
		return {
			"status": "error",
			"message": "Failed to retrieve Purchase Requisition Webform data.",
			"error": str(e)
		}
	

# Update only head part fields
@frappe.whitelist(allow_guest=True)
def update_pr_table_head_form(data):
	import json

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

		for update_row in rows:
			row_name = update_row.get("row_name")
			if not row_name:
				continue

			for row in doc.purchase_requisition_form_table:
				if row.name == row_name:
					if "purchase_requisition_item_head" in update_row:
						row.purchase_requisition_item_head = update_row["purchase_requisition_item_head"]
					if "item_number_of_purchase_requisition_head" in update_row:
						row.item_number_of_purchase_requisition_head = update_row["item_number_of_purchase_requisition_head"]
					if "purchase_requisition_date_head" in update_row:
						row.purchase_requisition_date_head = update_row["purchase_requisition_date_head"]
					if "delivery_date_head" in update_row:
						row.delivery_date_head = update_row["delivery_date_head"]
					if "store_location_head" in update_row:
						row.store_location_head = update_row["store_location_head"]
					if "item_category_head" in update_row:
						row.item_category_head = update_row["item_category_head"]
					if "material_group_head" in update_row:
						row.material_group_head = update_row["material_group_head"]
					if "uom_head" in update_row:
						row.uom_head = update_row["uom_head"]
					if "cost_center_head" in update_row:
						row.cost_center_head = update_row["cost_center_head"]
					if "main_asset_no_head" in update_row:
						row.main_asset_no_head = update_row["main_asset_no_head"]
					if "asset_subnumber_head" in update_row:
						row.asset_subnumber_head = update_row["asset_subnumber_head"]
					if "profit_ctr_head" in update_row:
						row.profit_ctr_head = update_row["profit_ctr_head"]
					if "short_text_head" in update_row:
						row.short_text_head = update_row["short_text_head"]
					if "quantity_head" in update_row:
						row.quantity_head = update_row["quantity_head"]
					if "price_of_purchase_requisition_head" in update_row:
						row.price_of_purchase_requisition_head = update_row["price_of_purchase_requisition_head"]
					if "gl_account_number_head" in update_row:
						row.gl_account_number_head = update_row["gl_account_number_head"]
					if "material_code_head" in update_row:
						row.material_code_head = update_row["material_code_head"]
					if "account_assignment_category_head" in update_row:
						row.account_assignment_category_head = update_row["account_assignment_category_head"]
					if "purchase_group_head" in update_row:
						row.purchase_group_head = update_row["purchase_group_head"]
					if "product_name_head" in update_row:
						row.product_name_head = update_row["product_name_head"]
					if "product_price_head" in update_row:
						row.product_price_head = update_row["product_price_head"]
					if "final_price_by_purchase_team_head" in update_row:
						row.final_price_by_purchase_team_head = update_row["final_price_by_purchase_team_head"]
					if "lead_time_head" in update_row:
						row.lead_time_head = update_row["lead_time_head"]
					if "plant" in update_row:
						row.plant = update_row["plant"]

					updated_rows.append(row_name)
					break

		if not updated_rows:
			return {
				"status": "error",
				"message": "No matching rows found to update."
			}

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": f"{len(updated_rows)} row(s) updated successfully.",
			"updated_rows": updated_rows
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Update PR Head Form Error")
		return {
			"status": "error",
			"message": "Failed to update head row data.",
			"error": str(e)
		}


#update pr table subhead table form
@frappe.whitelist(allow_guest=True)
def update_pr_table_subhead_form(data):
	import json

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

		for update_row in rows:
			row_name = update_row.get("row_name")
			if not row_name:
				continue

			for row in doc.purchase_requisition_form_table:
				if row.name == row_name:
					if "purchase_requisition_item_subhead" in update_row:
						row.purchase_requisition_item_subhead = update_row["purchase_requisition_item_subhead"]
					if "item_number_of_purchase_requisition_subhead" in update_row:
						row.item_number_of_purchase_requisition_subhead = update_row["item_number_of_purchase_requisition_subhead"]
					if "purchase_requisition_date_subhead" in update_row:
						row.purchase_requisition_date_subhead = update_row["purchase_requisition_date_subhead"]
					if "delivery_date_subhead" in update_row:
						row.delivery_date_subhead = update_row["delivery_date_subhead"]
					if "store_location_subhead" in update_row:
						row.store_location_subhead = update_row["store_location_subhead"]
					if "item_category_subhead" in update_row:
						row.item_category_subhead = update_row["item_category_subhead"]
					if "material_group_subhead" in update_row:
						row.material_group_subhead = update_row["material_group_subhead"]
					if "uom_subhead" in update_row:
						row.uom_subhead = update_row["uom_subhead"]
					if "cost_center_subhead" in update_row:
						row.cost_center_subhead = update_row["cost_center_subhead"]
					if "main_asset_no_subhead" in update_row:
						row.main_asset_no_subhead = update_row["main_asset_no_subhead"]
					if "asset_subnumber_subhead" in update_row:
						row.asset_subnumber_subhead = update_row["asset_subnumber_subhead"]
					if "profit_ctr_subhead" in update_row:
						row.profit_ctr_subhead = update_row["profit_ctr_subhead"]
					if "short_text_subhead" in update_row:
						row.short_text_subhead = update_row["short_text_subhead"]
					if "quantity_subhead" in update_row:
						row.quantity_subhead = update_row["quantity_subhead"]
					if "price_of_purchase_requisition_subhead" in update_row:
						row.price_of_purchase_requisition_subhead = update_row["price_of_purchase_requisition_subhead"]
					if "gl_account_number_subhead" in update_row:
						row.gl_account_number_subhead = update_row["gl_account_number_subhead"]
					if "material_code_subhead" in update_row:
						row.material_code_subhead = update_row["material_code_subhead"]
					if "account_assignment_category_subhead" in update_row:
						row.account_assignment_category_subhead = update_row["account_assignment_category_subhead"]
					if "purchase_group_subhead" in update_row:
						row.purchase_group_subhead = update_row["purchase_group_subhead"]

					updated_rows.append(row_name)
					break

		if not updated_rows:
			return {
				"status": "error",
				"message": "No matching subhead rows found to update."
			}

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": f"{len(updated_rows)} subhead row(s) updated successfully.",
			"updated_rows": updated_rows
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Update PR Subhead Form Error")
		return {
			"status": "error",
			"message": "Failed to update subhead row data.",
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