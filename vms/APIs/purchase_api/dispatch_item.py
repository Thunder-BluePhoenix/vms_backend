import frappe
import json
from frappe.utils.file_manager import save_file
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True)
def update_dispatch_item(data=None):
	try:
		# Handle FormData - get all form fields
		form_data = {}
		
		# Get all form fields from frappe.form_dict
		for key, value in frappe.form_dict.items():
			if key and value is not None and value != '':
				# Special handling for 'data' field containing JSON
				if key == "data":
					try:
						if isinstance(value, str):
							json_data = json.loads(value)
							form_data.update(json_data)
						else:
							form_data.update(value)
					except:
						form_data[key] = value
				else:
					form_data[key] = value
		
		# If data parameter is passed, merge it
		if data:
			if isinstance(data, str):
				data = json.loads(data)
			form_data.update(data)

		# Check if this is an update or create operation
		is_update = "name" in form_data and form_data["name"]

		if is_update:
			doc = frappe.get_doc("Dispatch Item", form_data["name"])
			name = doc.name
		else:
			doc = frappe.new_doc("Dispatch Item")

		# Get the doctype meta to understand field structure
		meta = frappe.get_meta("Dispatch Item")
		
		# Handle main document fields dynamically
		for fieldname, value in form_data.items():
			if fieldname == "name":
				continue  # Skip name field for updates
				
			# Check if this is a main document field
			if meta.has_field(fieldname):
				field = meta.get_field(fieldname)
				
				# Skip child table fields and attachment fields for now
				if field.fieldtype not in ["Table", "Attach", "Attach Image"]:
					doc.set(fieldname, value)

		# Handle child table data
		child_tables = {}
		
		# Parse child table data from form - handle both array format and bracket notation
		for key, value in form_data.items():
			# Handle direct child table arrays (like your JSON structure)
			if meta.has_field(key):
				field = meta.get_field(key)
				if field.fieldtype == "Table" and isinstance(value, list):
					child_tables[key] = {}
					for idx, row_data in enumerate(value):
						if row_data:
							child_tables[key][str(idx)] = row_data
			
			# Handle child table format like: purchase_number[0][purchase_number]
			elif '[' in key and ']' in key:
				# Extract table name, row index, and field name
				parts = key.split('[')
				if len(parts) >= 3:
					table_name = parts[0]
					row_index = parts[1].replace(']', '')
					field_name = parts[2].replace(']', '')
					
					if table_name not in child_tables:
						child_tables[table_name] = {}
					
					if row_index not in child_tables[table_name]:
						child_tables[table_name][row_index] = {}
					
					child_tables[table_name][row_index][field_name] = value

		# Process child tables
		for table_name, rows in child_tables.items():
			if meta.has_field(table_name):
				field = meta.get_field(table_name)
				if field.fieldtype == "Table":
					
					for row_index, row_data in rows.items():
						if not row_data:
							continue
							
						child_row = None
						
						# For updates, try to find existing row by name
						if is_update and "name" in row_data:
							existing_rows = getattr(doc, table_name, [])
							child_row = next((r for r in existing_rows if r.name == row_data["name"]), None)
						
						if child_row:
							# Update existing child row - only update provided fields
							for field_name, field_value in row_data.items():
								if field_name != "name":  # Don't update name field
									child_row.set(field_name, field_value)
							
							# Special handling for purchase_number table - update date_time
							if table_name == "purchase_number" and "purchase_number" in row_data:
								child_row.set("date_time", now_datetime())
						else:
							# Create new child row - only include provided fields
							new_row_data = {}
							for field_name, field_value in row_data.items():
								new_row_data[field_name] = field_value
							
							# Special handling for purchase_number table - add date_time
							if table_name == "purchase_number" and "purchase_number" in new_row_data:
								new_row_data["date_time"] = now_datetime()
							
							if new_row_data:
								doc.append(table_name, new_row_data)

		# Save or insert the document to generate name (required for attachments)
		if is_update:
			doc.save(ignore_permissions=True)
		else:
			doc.insert(ignore_permissions=True)
			name = doc.name

		# Handle file attachments dynamically
		if frappe.request.files:
			for file_key, uploaded_file in frappe.request.files.items():
				if uploaded_file and uploaded_file.filename:
					
					# Check if this is a main document attachment field
					if meta.has_field(file_key):
						field = meta.get_field(file_key)
						if field.fieldtype in ["Attach", "Attach Image"]:
							saved = save_file(uploaded_file.filename, uploaded_file.stream.read(), doc.doctype, doc.name, is_private=0)
							doc.set(file_key, saved.file_url)
					
					# Handle child table attachments (format: tablename_rowindex_fieldname)
					elif '_' in file_key:
						parts = file_key.split('_')
						if len(parts) >= 3:
							table_name = parts[0]
							row_index = parts[1]
							field_name = '_'.join(parts[2:])  # Join remaining parts for field name
							
							if meta.has_field(table_name):
								table_field = meta.get_field(table_name)
								if table_field.fieldtype == "Table":
									existing_rows = getattr(doc, table_name, [])
									if row_index.isdigit() and int(row_index) < len(existing_rows):
										child_row = existing_rows[int(row_index)]
										saved = save_file(uploaded_file.filename, uploaded_file.stream.read(), doc.doctype, doc.name, is_private=0)
										child_row.set(field_name, saved.file_url)

		# Set dispatch form as submitted
		# doc.dispatch_form_submitted = 1
		doc.save(ignore_permissions=True)

		frappe.db.commit()

		return {
			"status": "success",
			"message": "Dispatch Item submitted successfully.",
			"dis_name": f"{doc.name}"
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Dispatch Item Submit Error")
		return {
			"status": "error",
			"message": "Failed to submit Dispatch Item.",
			"error": str(e)
		}

@frappe.whitelist(allow_guest=True)
def full_data_dispatch_item(name):
	try:
		doc = frappe.get_doc("Dispatch Item", name)
		if not doc:
			return {
				"status": "error",
				"message": "Dispatch Item not found."
			}

		data = doc.as_dict()
		data["purchase_number"] = [row.as_dict() for row in doc.purchase_number]

		# Process item child table with attachment formatting
		data["items"] = []
		for row in doc.items:
			row_data = row.as_dict()

			for field in ["coa_document", "msds_document"]:
				if row.get(field):
					file_doc = frappe.get_doc("File", {"file_url": row.get(field)})
					row_data[field] = {
						"url": frappe.utils.get_url(file_doc.file_url),
						"name": file_doc.name,
						"file_name": file_doc.file_name
					}
				else:
					row_data[field] = {
						"url": "",
						"name": "",
						"file_name": ""
					}

			data["items"].append(row_data)

		# Handle top-level attachments
		for top_field in [
			"packing_list_attachment",
			"invoice_attachment",
			"commercial_attachment",
			"e_way_bill_attachment",
			"test_certificates_attachment"
		]:
			if doc.get(top_field):
				file_doc = frappe.get_doc("File", {"file_url": doc.get(top_field)})
				data[top_field] = {
					"url": frappe.utils.get_url(file_doc.file_url),
					"name": file_doc.name,
					"file_name": file_doc.file_name
				}
			else:
				data[top_field] = {
					"url": "",
					"name": "",
					"file_name": ""
				}

		return {
			"status": "success",
			"data": data
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Full Data Dispatch Item Error")
		return {
			"status": "error",
			"message": "Failed to fetch Dispatch Item data.",
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def submit_dispatch_item(data=None):
	try:
		# Handle FormData - get all form fields
		form_data = {}
		
		# Get all form fields from frappe.form_dict
		for key, value in frappe.form_dict.items():
			if key and value is not None and value != '':
				# Special handling for 'data' field containing JSON
				if key == "data":
					try:
						if isinstance(value, str):
							json_data = json.loads(value)
							form_data.update(json_data)
						else:
							form_data.update(value)
					except:
						form_data[key] = value
				else:
					form_data[key] = value
		
		# If data parameter is passed, merge it
		if data:
			if isinstance(data, str):
				data = json.loads(data)
			form_data.update(data)

		# Check if this is an update or create operation
		is_update = "name" in form_data and form_data["name"]

		if is_update:
			doc = frappe.get_doc("Dispatch Item", form_data["name"])
			name = doc.name
		else:
			doc = frappe.new_doc("Dispatch Item")

		# Get the doctype meta to understand field structure
		meta = frappe.get_meta("Dispatch Item")
		
		# Handle main document fields dynamically
		for fieldname, value in form_data.items():
			if fieldname == "name":
				continue  # Skip name field for updates
				
			# Check if this is a main document field
			if meta.has_field(fieldname):
				field = meta.get_field(fieldname)
				
				# Skip child table fields and attachment fields for now
				if field.fieldtype not in ["Table", "Attach", "Attach Image"]:
					doc.set(fieldname, value)

		# Handle child table data
		child_tables = {}
		
		# Parse child table data from form - handle both array format and bracket notation
		for key, value in form_data.items():
			# Handle direct child table arrays (like your JSON structure)
			if meta.has_field(key):
				field = meta.get_field(key)
				if field.fieldtype == "Table" and isinstance(value, list):
					child_tables[key] = {}
					for idx, row_data in enumerate(value):
						if row_data:
							child_tables[key][str(idx)] = row_data
			
			# Handle child table format like: purchase_number[0][purchase_number]
			elif '[' in key and ']' in key:
				# Extract table name, row index, and field name
				parts = key.split('[')
				if len(parts) >= 3:
					table_name = parts[0]
					row_index = parts[1].replace(']', '')
					field_name = parts[2].replace(']', '')
					
					if table_name not in child_tables:
						child_tables[table_name] = {}
					
					if row_index not in child_tables[table_name]:
						child_tables[table_name][row_index] = {}
					
					child_tables[table_name][row_index][field_name] = value

		# Process child tables
		for table_name, rows in child_tables.items():
			if meta.has_field(table_name):
				field = meta.get_field(table_name)
				if field.fieldtype == "Table":
					
					for row_index, row_data in rows.items():
						if not row_data:
							continue
							
						child_row = None
						
						# For updates, try to find existing row by name
						if is_update and "name" in row_data:
							existing_rows = getattr(doc, table_name, [])
							child_row = next((r for r in existing_rows if r.name == row_data["name"]), None)
						
						if child_row:
							# Update existing child row - only update provided fields
							for field_name, field_value in row_data.items():
								if field_name != "name":  # Don't update name field
									child_row.set(field_name, field_value)
							
							# Special handling for purchase_number table - update date_time
							if table_name == "purchase_number" and "purchase_number" in row_data:
								child_row.set("date_time", now_datetime())
						else:
							# Create new child row - only include provided fields
							new_row_data = {}
							for field_name, field_value in row_data.items():
								new_row_data[field_name] = field_value
							
							# Special handling for purchase_number table - add date_time
							if table_name == "purchase_number" and "purchase_number" in new_row_data:
								new_row_data["date_time"] = now_datetime()
							
							if new_row_data:
								doc.append(table_name, new_row_data)

		# Save or insert the document to generate name (required for attachments)
		if is_update:
			doc.save(ignore_permissions=True)
		else:
			doc.insert(ignore_permissions=True)
			name = doc.name

		# Handle file attachments dynamically
		if frappe.request.files:
			for file_key, uploaded_file in frappe.request.files.items():
				if uploaded_file and uploaded_file.filename:
					
					# Check if this is a main document attachment field
					if meta.has_field(file_key):
						field = meta.get_field(file_key)
						if field.fieldtype in ["Attach", "Attach Image"]:
							saved = save_file(uploaded_file.filename, uploaded_file.stream.read(), doc.doctype, doc.name, is_private=0)
							doc.set(file_key, saved.file_url)
					
					# Handle child table attachments (format: tablename_rowindex_fieldname)
					elif '_' in file_key:
						parts = file_key.split('_')
						if len(parts) >= 3:
							table_name = parts[0]
							row_index = parts[1]
							field_name = '_'.join(parts[2:])  # Join remaining parts for field name
							
							if meta.has_field(table_name):
								table_field = meta.get_field(table_name)
								if table_field.fieldtype == "Table":
									existing_rows = getattr(doc, table_name, [])
									if row_index.isdigit() and int(row_index) < len(existing_rows):
										child_row = existing_rows[int(row_index)]
										saved = save_file(uploaded_file.filename, uploaded_file.stream.read(), doc.doctype, doc.name, is_private=0)
										child_row.set(field_name, saved.file_url)

		# Set dispatch form as submitted
		doc.dispatch_form_submitted = 1
		doc.save(ignore_permissions=True)

		frappe.db.commit()

		return {
			"status": "success",
			"message": "Dispatch Item submitted successfully.",
			"dis_name": f"{doc.name}"
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Dispatch Item Submit Error")
		return {
			"status": "error",
			"message": "Failed to submit Dispatch Item.",
			"error": str(e)
		}
	

@frappe.whitelist(allow_guest=True)
def submit_child_dispatch_item(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		doc = frappe.get_doc("Dispatch Item", data["name"])

		row_name = data.get("row_name")

		child_row = None
		if row_name:
			child_row = next((r for r in doc.items if r.name == row_name), None)

		if child_row:
			# Update existing row
			for key in [
				"po_number", "product_code", "product_name", "description", "quantity",
				"hsnsac", "uom", "rate", "amount", "dispatch_qty", "pending_qty",
				"coa_document", "msds_document"
			]:
				if key in data:
					child_row.set(key, data[key])
		else:
			pass
			# Append new row
			# child_row = doc.append("items", {
			# 	"po_number": data.get("po_number"),
			# 	"product_code": data.get("product_code"),
			# 	"product_name": data.get("product_name"),
			# 	"description": data.get("description"),
			# 	"quantity": data.get("quantity"),
			# 	"hsnsac": data.get("hsnsac"),
			# 	"uom": data.get("uom"),
			# 	"rate": data.get("rate"),
			# 	"amount": data.get("amount"),
			# 	"dispatch_qty": data.get("dispatch_qty"),
			# 	"pending_qty": data.get("pending_qty"),
			# 	"coa_document": data.get("coa_document"),
			# 	"msds_document": data.get("msds_document")
			# })

		# Handle file uploads for this row
		for attach_field in ["coa_document", "msds_document"]:
			if attach_field in frappe.request.files:
				uploaded_file = frappe.request.files[attach_field]
				saved = save_file(
					uploaded_file.filename,
					uploaded_file.stream.read(),
					doc.doctype,
					doc.name,
					is_private=0
				)
				child_row.set(attach_field, saved.file_url)

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Child row processed successfully.",
			"row_name": child_row.name
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Child Dispatch Item Submit Error")
		return {
			"status": "error",
			"message": "Failed to process child dispatch item.",
			"error": str(e)
		}


# submit the dispatch item doc
@frappe.whitelist(allow_guest=True)
def submit_dispatch_item(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		doc = frappe.get_doc("Dispatch Item", data.get("name"))

		if data.get("submit") == 1:
			doc.dispatch_form_submitted = 1

			for row in doc.purchase_number:
				if row.purchase_number:
					pur_team_email = frappe.db.get_value("Purchase Order", row.purchase_number, "email")
					if pur_team_email:
						frappe.sendmail(
							recipients=[pur_team_email],
							subject="Dispatch Item Submitted",
							message="""
								Dear Purchase Team,<br><br>
								A user has submitted a Dispatch Item.<br>
								Please review it and take necessary action.<br><br>
								Regards,<br>
								VMS Team
							""",
							now=True
						)

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "Dispatch item submitted successfully.",
			"name": doc.name
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Dispatch Item Submit Error")
		return {
			"status": "error",
			"message": "Failed to process dispatch item.",
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
	












@frappe.whitelist(allow_guest=True)
def get_poitem_against_po(data):
	try:
		po_names = data.get("po_name")
		if not po_names:
			return {
				"status": "error",
				"message": "po_name is required"
			}
		
		if isinstance(po_names, str):
			po_names = [po_names]
		
		purchase_order_items = frappe.get_all(
			"Purchase Order Item",  
			filters={
				"parent": ["in", po_names]  
			},
			fields="*"  
		)
		
		purchase_orders = frappe.get_all(
			"Purchase Order",
			filters={
				"name": ["in", po_names]
			},
			fields="*"
		)
		
		return {
			"status": "success",
			"data": purchase_order_items,
			"purchase_orders": purchase_orders,
			"po_items_count": len(purchase_order_items)
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get PO Items Error")
		return {
			"status": "error",
			"message": "Failed to fetch purchase order items.",
			"error": str(e)
		}

