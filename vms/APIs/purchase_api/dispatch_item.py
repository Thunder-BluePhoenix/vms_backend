import frappe
import json
from frappe.utils.file_manager import save_file
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True)
def update_dispatch_item(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		is_update = "name" in data and data["name"]

		if is_update:
			doc = frappe.get_doc("Dispatch Item", data["name"])
		else:
			doc = frappe.new_doc("Dispatch Item")

		# Top-level fields (excluding attach fields for now)
		top_fields = [
			"naming_series", "courier_number", "courier_name", "docket_number",
			"dispatch_date", "invoice_number", "invoice_date", "status", "invoice_amount",
			"vendor_code"
		]

		for field in top_fields:
			if field in data:
				doc.set(field, data[field])

		# Save or insert the document to generate name (required for attachments)
		if is_update:
			doc.save(ignore_permissions=True)
		else:
			doc.insert(ignore_permissions=True)

		# Attach fields
		file_keys = [
			"packing_list_attachment",
			"invoice_attachment",
			"commercial_attachment",
			"e_way_bill_attachment",
			"test_certificates_attachment"
		]

		for key in file_keys:
			if key in frappe.request.files:
				file = frappe.request.files[key]
				saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
				doc.set(key, saved.file_url)

		# Child Table 1: purchase_number
		if "purchase_number" in data and isinstance(data["purchase_number"], list):
			for row in data["purchase_number"]:
				if not row:
					continue

				child_row = None
				if "name" in row:
					child_row = next((r for r in doc.purchase_number if r.name == row["name"]), None)

				if child_row:
					child_row.set("purchase_number", row.get("purchase_number"))
					child_row.set("date_time", now_datetime())
				else:
					# fallback: append new row if no match found by name
					doc.append("purchase_number", {
						"purchase_number": row.get("purchase_number"),
						"date_time": now_datetime()
					})

		# Child Table 2: items → Dispatch Order Items
		if "items" in data and isinstance(data["items"], list):
			for row in data["items"]:
				if not row:
					continue

				child_row = None
				if "name" in row:
					child_row = next((r for r in doc.items if r.name == row["name"]), None)

				if child_row:
					for key in [
						"po_number", "product_code", "product_name", "description", "quantity",
						"hsnsac", "uom", "rate", "amount", "dispatch_qty", "pending_qty",
						"coa_document", "msds_document"
					]:
						if key in row:
							child_row.set(key, row[key])
				else:
					child_row = doc.append("items", {
						"po_number": row.get("po_number"),
						"product_code": row.get("product_code"),
						"product_name": row.get("product_name"),
						"description": row.get("description"),
						"quantity": row.get("quantity"),
						"hsnsac": row.get("hsnsac"),
						"uom": row.get("uom"),
						"rate": row.get("rate"),
						"amount": row.get("amount"),
						"dispatch_qty": row.get("dispatch_qty"),
						"pending_qty": row.get("pending_qty"),
						"coa_document": row.get("coa_document"),
						"msds_document": row.get("msds_document")
					})

				for attach_field in ["coa_document", "msds_document"]:
					file_key = f"{attach_field}"
					if file_key in frappe.request.files:
						uploaded_file = frappe.request.files[file_key]
						saved = save_file(uploaded_file.filename, uploaded_file.stream.read(), doc.doctype, doc.name, is_private=1)
						child_row.set(attach_field, saved.file_url)

		# Final save to persist attachments and child updates
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Dispatch Item saved successfully.",
			"name": doc.name
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Dispatch Item API Error")
		return {
			"status": "error",
			"message": "Failed to save Dispatch Item.",
			"error": str(e)
		}
	

@frappe.whitelist(allow_guest=True)
def submit_dispatch_item(name):
	try:
		doc = frappe.get_doc("Dispatch Item", name)
		if not doc:
			return {
				"status": "error",
				"message": "Dispatch Item not found."
			}
		if not doc.dispatch_form_submitted:
			doc.dispatch_form_submitted = 1
		else:
			return {
				"status": "error",
				"message": "Dispatch Item already submitted."
			}

		for row in doc.items:
			if row.po_number:
				po = frappe.get_doc("Purchase Order", row.po_number)
				po.append("dispatch_ids", {
					"dispatch_id": name,
					"dispatch_datetime": now_datetime()
				})
				po.save(ignore_permissions=True)
			else:
				return {
					"status": "error",
					"message": "Purchase Order not found for the Dispatch Item."
				}

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Dispatch Item submitted successfully."
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Dispatch Item Submit Error")
		return {
			"status": "error",
			"message": "Failed to submit Dispatch Item.",
			"error": str(e)
		}

# list of purchase order based on vendor code and status
@frappe.whitelist(allow_guest=True)
def list_purchase_order(vendor_code):
	try:
		purchase_orders = frappe.get_all(
			"Purchase Order",
			filters={
				"status": ["in", [None, "", "Partial"]],
				"vendor_code": vendor_code
			},
			fields="*"
		)
		return {
			"status": "success",
			"data": purchase_orders,
			"purchase_orders": [po["name"] for po in purchase_orders]	
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "List Purchase Order Error")
		return {
			"status": "error",
			"message": "Failed to fetch purchase orders.",
			"error": str(e)
		}