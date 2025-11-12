import frappe
import json

# @frappe.whitelist(allow_guest=True)
# def update_vendor_onboarding_contact_details(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)

#         ref_no = data.get("ref_no")
#         vendor_onboarding = data.get("vendor_onboarding")

#         if not ref_no or not vendor_onboarding:
#             return {
#                 "status": "error",
#                 "message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
#             }

#         doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

#         doc.set("contact_details", [])

#         # Update contact details table
#         if "contact_details" in data or isinstance(data["contact_details"], list):
#             for contact in data["contact_details"]:
#                 # is_duplicate = False

#                 # for row in doc.contact_details:
#                 #     if (
#                 #         (row.email or "").strip().lower() == (contact.get("email") or "").strip().lower() and
#                 #         (row.contact_number or "").strip() == (contact.get("contact_number") or "").strip()
#                 #     ):
#                 #         is_duplicate = True
#                 #         break

#                 # if not is_duplicate:
#                 doc.append("contact_details", {
#                     "first_name": contact.get("first_name"),
#                     "last_name": contact.get("last_name"),
#                     "designation": contact.get("designation"),
#                     "email": contact.get("email"),
#                     "contact_number": contact.get("contact_number"),
#                     "department_name": contact.get("department_name")
#                 })
#         else:
#             return {
#                 "status": "error",
#                 "message": "Missing or invalid 'contact_details' table."
#             }

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Vendor Onboarding Contact Details updated successfully.",
#             "docname": doc.name
#         }

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), "Contact Details Update Error")
#         return {
#             "status": "error",
#             "message": "Failed to update contact details.",
#             "error": str(e)
#         }


@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_contact_details(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		ref_no = data.get("ref_no")
		vendor_onboarding = data.get("vendor_onboarding")

		if not ref_no or not vendor_onboarding:
			frappe.local.response["http_status_code"] = 400
			return {
				"status": "error",
				"message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
			}

		# Get main Vendor Onboarding doc
		main_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

		# Find linked docs if registered_for_multi_companies = 1
		if main_doc.registered_for_multi_companies == 1:
			linked_docs = frappe.get_all(
				"Vendor Onboarding",
				filters={
					"registered_for_multi_companies": 1,
					"unique_multi_comp_id": main_doc.unique_multi_comp_id
				},
				fields=["name"]
			)
		else:
			linked_docs = [{"name": main_doc.name}]

		# Validate contact_details
		if "contact_details" not in data or not isinstance(data["contact_details"], list):
			frappe.local.response["http_status_code"] = 400
			return {
				"status": "error",
				"message": "Missing or invalid 'contact_details' table."
			}

		# Loop over all linked docs and update contact_details table
		for entry in linked_docs:
			doc = frappe.get_doc("Vendor Onboarding", entry["name"])

			# Clear existing table
			doc.set("contact_details", [])

			# Append new contact rows
			for contact in data["contact_details"]:
				doc.append("contact_details", {
					"first_name": contact.get("first_name"),
					"last_name": contact.get("last_name"),
					"designation": contact.get("designation"),
					"email": contact.get("email"),
					"contact_number": contact.get("contact_number"),
					"department_name": contact.get("department_name")
				})

			doc.save(ignore_permissions=True)

		frappe.db.commit()

		frappe.local.response["http_status_code"] = 200
		return {
			"status": "success",
			"message": "Vendor Onboarding Contact Details updated successfully.",
			"docnames": [d["name"] for d in linked_docs]
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.local.response["http_status_code"] = 500
		frappe.log_error(frappe.get_traceback(), "Contact Details Update Error")
		return {
			"status": "error",
			"message": "Failed to update contact details.",
			"error": str(e)
		}
