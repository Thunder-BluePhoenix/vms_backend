import frappe

@frappe.whitelist(allow_guest=True)
def dispatch_dashboard(page_no=None, page_length=None, status=None):
	try:
		user = frappe.session.user
		roles = frappe.get_roles(user)

		filters = {}
		if status:
			filters["status"] = status

		page_no = int(page_no) if page_no else 1
		page_length = int(page_length) if page_length else 5
		offset = (page_no - 1) * page_length

		dispatches = []
		card_count = 0
		total_count = 0

		if "Purchase Team" in roles:
			employee = frappe.get_doc("Employee", {"user_id": user})
			employee_companies = [row.company_name for row in employee.company]

			all_dispatch_docs = frappe.get_all(
				"Dispatch Item",
				fields=["name", "vendor_code", "invoice_number", "invoice_date", "invoice_amount", "status", "owner"],
				order_by="modified desc"
		 )

			matching_docs = []
			filtered_docs = []

			for doc in all_dispatch_docs:
				vendor_row = frappe.get_all(
					"Vendor Code",
					filters={"vendor_code": doc.vendor_code},
					fields=["parent"],
					limit=1
				)
				if not vendor_row:
					continue

				company_vendor_code_doc = frappe.get_doc("Company Vendor Code", vendor_row[0]["parent"])
				vendor_master = frappe.get_doc("Vendor Master", company_vendor_code_doc.vendor_ref_no)
				vendor_companies = [row.company_name for row in vendor_master.multiple_company_data]

				if set(employee_companies) & set(vendor_companies):
					matching_docs.append(doc)  # for card count
					if not status or doc.status == status:
						filtered_docs.append(doc)

			card_count = len(matching_docs)
			total_count = len(filtered_docs)

			for doc in filtered_docs[offset:offset + page_length]:
				dispatch_doc = frappe.get_doc("Dispatch Item", doc.name)
				purchase_numbers = [r.purchase_number for r in dispatch_doc.purchase_number or []]

				dispatches.append({
					"name": doc.name,
					"invoice_number": doc.invoice_number,
					"invoice_date": doc.invoice_date,
					"invoice_amount": doc.invoice_amount,
					"status": doc.status,
					"owner": doc.owner,
					"purchase_numbers": purchase_numbers
				})

		elif "Vendor" in roles:
			card_count = frappe.db.count("Dispatch Item", filters={"owner": user})

			if status:
				filters["status"] = status
			filters["owner"] = user

			total_count = frappe.db.count("Dispatch Item", filters=filters)

			dispatch_docs = frappe.get_all(
				"Dispatch Item",
				filters=filters,
				fields=["name", "invoice_number", "invoice_date", "invoice_amount", "status", "owner"],
				limit_start=offset,
				limit_page_length=page_length,
				order_by="modified desc"
			)

			for doc in dispatch_docs:
				dispatch_doc = frappe.get_doc("Dispatch Item", doc.name)
				purchase_numbers = [row.purchase_number for row in dispatch_doc.purchase_number or []]

				dispatches.append({
					"name": doc.name,
					"invoice_number": doc.invoice_number,
					"invoice_date": doc.invoice_date,
					"invoice_amount": doc.invoice_amount,
					"status": doc.status,
					"owner": doc.owner,
					"purchase_numbers": purchase_numbers
				})

		else:
			return {
				"status": "error",
				"message": "User does not have access to view this data.",
				"dispatches": []
			}

		return {
			"status": "success",
			"message": "Dispatch data fetched successfully.",
			"dispatches": dispatches,
			"total_count": total_count,
			"card_count": card_count,
			"page_no": page_no,
			"page_length": page_length
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Dispatch Dashboard Error")
		return {
			"status": "error",
			"message": "Failed to fetch dispatch data.",
			"error": str(e)
		}


# @frappe.whitelist(allow_guest=True)
# def dispatch_card_count():
# 	try:
# 		user = frappe.session.user
# 		roles = frappe.get_roles(user)

# 		count = 0

# 		if "Purchase Team" in roles:
# 			employee = frappe.get_doc("Employee", {"user_id": user})
# 			employee_companies = [row.company_name for row in employee.company]

# 			all_dispatch_docs = frappe.get_all(
# 				"Dispatch Item",
# 				fields=["name", "vendor_code"]
# 			)

# 			for doc in all_dispatch_docs:
# 				vendor_row = frappe.get_all(
# 					"Vendor Code",
# 					filters={"vendor_code": doc.vendor_code},
# 					fields=["parent"],
# 					limit=1
# 				)

# 				if not vendor_row:
# 					continue

# 				company_vendor_code_name = vendor_row[0]["parent"]
# 				company_vendor_code_doc = frappe.get_doc("Company Vendor Code", company_vendor_code_name)
# 				vendor_master_name = company_vendor_code_doc.vendor_ref_no

# 				vendor_master = frappe.get_doc("Vendor Master", vendor_master_name)
# 				vendor_companies = [row.company_name for row in vendor_master.multiple_company_data]

# 				if set(employee_companies) & set(vendor_companies):
# 					count += 1

# 		elif "Vendor" in roles:
# 			count = frappe.db.count("Dispatch Item", filters={"owner": user})

# 		else:
# 			return {
# 				"status": "error",
# 				"message": "User does not have access to view this data.",
# 				"total_count": 0
# 			}

# 		return {
# 			"status": "success",
# 			"message": "Dispatch card count fetched successfully.",
# 			"total_count": count
# 		}

# 	except Exception as e:
# 		frappe.log_error(frappe.get_traceback(), "Dispatch Card Count Error")
# 		return {
# 			"status": "error",
# 			"message": "Failed to fetch dispatch card count.",
# 			"error": str(e)
# 		}