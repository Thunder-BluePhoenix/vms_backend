import frappe
import datetime
from vms.purchase.report.product_inquiry_details.product_inquiry_details import execute


# Get latest Previous Product Inquiry beased on Cart ID
@frappe.whitelist(allow_guest=True, methods=['GET'])
def get_latest_product_inquiry(cart_id=None):
	try:
		if not cart_id:
			frappe.local.response["http_status_code"] = 404
			return {
				"status": "error",
				"message": "Cart ID not provided"
			}

		try:
			cart_details = frappe.get_doc("Cart Details", cart_id)
		except:
			frappe.local.response["http_status_code"] = 404
			return {
				"status": "error",
				"message": "Cart not found"
			}

		final_data = [] 

		for row in cart_details.cart_product:
			if not row.product_name:
				continue

			latest_product_cart = frappe.db.sql("""
				SELECT parent, creation
				FROM `tabCart Master`
				WHERE product_name = %s
				ORDER BY creation DESC
				LIMIT 2
			""", (row.product_name,), as_dict=True)

			if len(latest_product_cart) < 2:
				continue

			latest_cart_id = latest_product_cart[1].parent

			try:
				latest_cart_details = frappe.get_doc("Cart Details", latest_cart_id)
			except:
				continue

			for latest_row in latest_cart_details.cart_product:
				if latest_row.product_name == row.product_name:

					final_data.append({
						"cart_id": latest_cart_details.name,
						"user": latest_cart_details.user,
						"cart_date": latest_cart_details.cart_date,
						"purchase_requisition_form_created": latest_cart_details.purchase_requisition_form_created,
						"purchase_requisition_form": latest_cart_details.purchase_requisition_form,

						"product_name": latest_row.product_name,
						"price": latest_row.product_price,
						"final_price": latest_row.final_price_by_purchase_team,
						"qty": latest_row.product_quantity
					})

		if not final_data:
			frappe.local.response["http_status_code"] = 404
			return {
				"status": "error",
				"message": "No related Cart Details found"
			}

		frappe.local.response["http_status_code"] = 200
		return {
			"status": "success",
			"data": final_data,
			"total_records": len(final_data)
		}

	except Exception as e:
		frappe.local.response["http_status_code"] = 500
		return {
			"status": "error",
			"message": "Internal Server Error",
			"error": str(e)
		}


# API Call to get the data of Product Inquiry Details Report
@frappe.whitelist(allow_guest=True, methods=['GET'])
def get_product_inquiry_report(cart_id=None, user=None, cart_date=None, product_name=None, page_no=None, page_size=None):

	page = int(page_no) if page_no else 1
	page_size = int(page_size) if page_size else 10

	filters = {}
	if cart_id:
		filters["cart_id"] = cart_id
	if user:
		filters["user"] = user
	if cart_date:
		filters["cart_date"] = cart_date
	if product_name:
		filters["product_name"] = product_name

	columns, data = execute(filters)

	data = sorted(
		data,
		key=lambda x: x.get("cart_date") or datetime.date.min,
		reverse=True
	)

	total_records = len(data)

	start = (page - 1) * page_size
	end = start + page_size
	paginated_data = data[start:end]

	return {
		"data": paginated_data,
		"pagination": {
			"page_no": page,
			"page_size": page_size,
			"total_records": total_records,
			"total_pages": (total_records + page_size - 1) // page_size,
			"has_next": end < total_records,
			"has_previous": start > 0
		}
	}
