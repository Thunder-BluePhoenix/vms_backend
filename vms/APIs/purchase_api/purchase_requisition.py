import frappe

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
			head_no = str(row.item_number_of_purchase_requisition_head)

			if not head_no:
				continue

			if head_no not in grouped_data:
				grouped_data[head_no] = {
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

			grouped_data[head_no]["subhead_fields"].append({
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
			"data": final_result
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Purchase Requisition Table Data Error")
		return {
			"status": "error",
			"message": "Failed to retrieve Purchase Requisition Webform data.",
			"error": str(e)
		}