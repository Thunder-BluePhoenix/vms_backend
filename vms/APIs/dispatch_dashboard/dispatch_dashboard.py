import frappe
from frappe import _
from frappe.utils import cint
import json

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
			emp_team = employee.team

			pur_grps = frappe.get_all(
				"Purchase Group Master", 
				filters={
					"team": emp_team,
					"company": ["in", employee_companies]
				}, 
				pluck="purchase_group_code"
			)

			if not pur_grps:
				return {
					"status": "success",
					"message": "No purchase groups found for your team and companies.",
					"dispatches": [],
					"total_count": 0,
					"card_count": 0,
					"page_no": page_no,
					"page_length": page_length
				}

			employee_companies_set = set(employee_companies)
			pur_grps_set = set(pur_grps)

			valid_dispatch_names = frappe.db.sql("""
				SELECT DISTINCT dpng.parent
				FROM `tabDispatch Purchase No Group` dpng
				INNER JOIN `tabPurchase Order` po ON dpng.purchase_number = po.name
				WHERE po.company_code IN %(companies)s
				AND po.purchase_group IN %(purchase_groups)s
			""", {
				"companies": employee_companies_set,
				"purchase_groups": pur_grps_set
			}, as_dict=False)

			valid_dispatch_names_set = {row[0] for row in valid_dispatch_names}

			if not valid_dispatch_names_set:
				return {
					"status": "success",
					"message": "No dispatch items found matching your criteria.",
					"dispatches": [],
					"total_count": 0,
					"card_count": 0,
					"page_no": page_no,
					"page_length": page_length
				}

			dispatch_filters = {"name": ["in", list(valid_dispatch_names_set)]}
			
			card_count = len(valid_dispatch_names_set)

			if status:
				dispatch_filters["status"] = status

			total_count = frappe.db.count("Dispatch Item", filters=dispatch_filters)

			dispatch_docs = frappe.get_all(
				"Dispatch Item",
				filters=dispatch_filters,
				fields=["name", "invoice_number", "invoice_date", "invoice_amount", "status", "owner"],
				limit_start=offset,
				limit_page_length=page_length,
				order_by="modified desc"
			)

			dispatch_names = [doc.name for doc in dispatch_docs]
			if dispatch_names:
				purchase_numbers_map = {}
				purchase_numbers_data = frappe.db.sql("""
					SELECT parent, purchase_number
					FROM `tabDispatch Purchase No Group`
					WHERE parent IN %(dispatch_names)s
					ORDER BY idx
				""", {"dispatch_names": dispatch_names}, as_dict=True)

				for row in purchase_numbers_data:
					if row.parent not in purchase_numbers_map:
						purchase_numbers_map[row.parent] = []
					purchase_numbers_map[row.parent].append(row.purchase_number)

				for doc in dispatch_docs:
					dispatches.append({
						"name": doc.name,
						"invoice_number": doc.invoice_number,
						"invoice_date": doc.invoice_date,
						"invoice_amount": doc.invoice_amount,
						"status": doc.status,
						"owner": doc.owner,
						"purchase_numbers": purchase_numbers_map.get(doc.name, [])
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

			dispatch_names = [doc.name for doc in dispatch_docs]
			if dispatch_names:
				purchase_numbers_map = {}
				purchase_numbers_data = frappe.db.sql("""
					SELECT parent, purchase_number
					FROM `tabDispatch Purchase No Group`
					WHERE parent IN %(dispatch_names)s
					ORDER BY idx
				""", {"dispatch_names": dispatch_names}, as_dict=True)

				for row in purchase_numbers_data:
					if row.parent not in purchase_numbers_map:
						purchase_numbers_map[row.parent] = []
					purchase_numbers_map[row.parent].append(row.purchase_number)

				for doc in dispatch_docs:
					dispatches.append({
						"name": doc.name,
						"invoice_number": doc.invoice_number,
						"invoice_date": doc.invoice_date,
						"invoice_amount": doc.invoice_amount,
						"status": doc.status,
						"owner": doc.owner,
						"purchase_numbers": purchase_numbers_map.get(doc.name, [])
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