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

		for row in cart_details.cart_product:
			pur_req.append("purchase_requisition_form_table", {
				"main_asset_no_head": row.assest_code,
				"product_name_head": row.product_name,
				"product_price_head": row.product_price,
				"final_price_by_purchase_team_head": row.final_price_by_purchase_team,
				"lead_time_head": row.lead_time
			})

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
