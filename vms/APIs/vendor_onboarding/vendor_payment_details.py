import frappe
import json
from frappe.utils.file_manager import save_file

# @frappe.whitelist(allow_guest=True)
# def update_vendor_onboarding_payment_details(data):
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

#         doc_name = frappe.db.get_value(
#             "Vendor Onboarding Payment Details",
#             {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
#             "name"
#         )

#         if not doc_name:
#             return {
#                 "status": "error",
#                 "message": f"No record found for Vendor Onboarding Payment Details"
#             }

#         doc = frappe.get_doc("Vendor Onboarding Payment Details", doc_name)
#         if doc.registered_for_multi_companies == 0:

#         # Update fields
#             fields_to_update = [
#                 "bank_name", "ifsc_code", "account_number", "name_of_account_holder",
#                 "type_of_account", "currency", "rtgs", "neft", "ift"
#             ]

#             for field in fields_to_update:
#                 if field in data and data[field] is not None:
#                     doc.set(field, data[field])

#             # attach field
#             if 'bank_proof' in frappe.request.files:
#                 file = frappe.request.files['bank_proof']
#                 saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
#                 doc.bank_proof = saved.file_url

#             if 'bank_proof_for_beneficiary_bank' in frappe.request.files:
#                 file = frappe.request.files['bank_proof_for_beneficiary_bank']
#                 saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
#                 bank_proof_for_beneficiary_bank = saved.file_url

#             if 'bank_proof_for_intermediate_bank' in frappe.request.files:
#                 file = frappe.request.files['bank_proof_for_intermediate_bank']
#                 saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
#                 bank_proof_for_intermediate_bank = saved.file_url

#             if "international_bank_details" in data or isinstance(data["international_bank_details"], list):
#                 for row in data["international_bank_details"]:
#                     doc.set("international_bank_details", [])
#                     new_row = doc.append("international_bank_details", {
#                         "meril_company_name": row.get("meril_company_name"),
#                         "beneficiary_name": row.get("beneficiary_name"),
#                         "beneficiary_swift_code": row.get("beneficiary_swift_code"),
#                         "beneficiary_iban_no": row.get("beneficiary_iban_no"),
#                         "beneficiary_aba_no": row.get("beneficiary_aba_no"),
#                         "beneficiary_bank_address": row.get("beneficiary_bank_address"),
#                         "beneficiary_bank_name": row.get("beneficiary_bank_name"),
#                         "beneficiary_account_no": row.get("beneficiary_account_no"),
#                         "beneficiary_ach_no": row.get("beneficiary_ach_no"),
#                         "beneficiary_routing_no": row.get("beneficiary_routing_no"),
#                         "beneficiary_currency": row.get("beneficiary_currency")
#                     })
#                     if bank_proof_for_beneficiary_bank:
#                         new_row.bank_proof_for_beneficiary_bank = bank_proof_for_beneficiary_bank

#             if "intermediate_bank_details" in data or isinstance(data["intermediate_bank_details"], list):
#                 for row in data["intermediate_bank_details"]:
#                     doc.set("intermediate_bank_details", [])
#                     new_row = doc.append("intermediate_bank_details", {
#                         "intermediate_bank_name": row.get("intermediate_bank_name"),
#                         "intermediate_swift_code": row.get("intermediate_swift_code"),
#                         "intermediate_iban_no": row.get("intermediate_iban_no"),
#                         "intermediate_aba_no": row.get("intermediate_aba_no"),
#                         "intermediate_bank_address": row.get("intermediate_bank_address"),
#                         "intermediate_account_no": row.get("intermediate_account_no"),
#                         "intermediate_ach_no": row.get("intermediate_ach_no"),
#                         "intermediate_routing_no": row.get("intermediate_routing_no"),
#                         "intermediate_currency": row.get("intermediate_currency")
#                     })
#                     if bank_proof_for_intermediate_bank:
#                         new_row.bank_proof_for_intermediate_bank = bank_proof_for_intermediate_bank

#             doc.save(ignore_permissions=True)
#             frappe.db.commit()

#             return {
#                 "status": "success",
#                 "message": "Vendor Onboarding Payment Details updated successfully.",
#                 "docname": doc.name,
#                 "bank_proof": doc.bank_proof if hasattr(doc, "bank_proof") else None
#             }
#         else:
#             uniq = doc.unique_multi_comp_id
#             linked_docs = frappe.get_all("Vendor Onboarding Payment Details", 
#                 filters={"unique_multi_comp_id": uniq, "registered_for_multi_companies": 1},
#                 fields=["name"]
#             ) 
#             fields_to_update = [
#             "bank_name", "ifsc_code", "account_number", "name_of_account_holder",
#             "type_of_account", "currency", "rtgs", "neft", "ift"
#             ]
#             if 'bank_proof' in frappe.request.files:
#                 file = frappe.request.files['bank_proof']
#                 saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)

#             if 'bank_proof_for_beneficiary_bank' in frappe.request.files:
#                 file = frappe.request.files['bank_proof_for_beneficiary_bank']
#                 saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
#                 bank_proof_for_beneficiary_bank = saved.file_url

#             if 'bank_proof_for_intermediate_bank' in frappe.request.files:
#                 file = frappe.request.files['bank_proof_for_intermediate_bank']
#                 saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
#                 bank_proof_for_intermediate_bank = saved.file_url

#             for pd_doc in linked_docs:
#                 pd = frappe.get_doc("Vendor Onboarding Payment Details", pd_doc["name"])

#                 for field in fields_to_update:
#                     if field in data and data[field] is not None:
#                         pd.set(field, data[field])

#                 # attach field
                
#                 pd.bank_proof = saved.file_url

#                 if "international_bank_details" in data or isinstance(data["international_bank_details"], list):
#                     for row in data["international_bank_details"]:
#                         pd.set("international_bank_details", [])
#                         new_row = pd.append("international_bank_details", {
#                             "meril_company_name": row.get("meril_company_name"),
#                             "beneficiary_name": row.get("beneficiary_name"),
#                             "beneficiary_swift_code": row.get("beneficiary_swift_code"),
#                             "beneficiary_iban_no": row.get("beneficiary_iban_no"),
#                             "beneficiary_aba_no": row.get("beneficiary_aba_no"),
#                             "beneficiary_bank_address": row.get("beneficiary_bank_address"),
#                             "beneficiary_bank_name": row.get("beneficiary_bank_name"),
#                             "beneficiary_account_no": row.get("beneficiary_account_no"),
#                             "beneficiary_ach_no": row.get("beneficiary_ach_no"),
#                             "beneficiary_routing_no": row.get("beneficiary_routing_no"),
#                             "beneficiary_currency": row.get("beneficiary_currency")
#                         })
#                         if bank_proof_for_beneficiary_bank:
#                             new_row.bank_proof_for_beneficiary_bank = bank_proof_for_beneficiary_bank

#                 if "intermediate_bank_details" in data or isinstance(data["intermediate_bank_details"], list):
#                     for row in data["intermediate_bank_details"]:
#                         pd.set("intermediate_bank_details", [])
#                         new_row = pd.append("intermediate_bank_details", {
#                             "intermediate_bank_name": row.get("intermediate_bank_name"),
#                             "intermediate_swift_code": row.get("intermediate_swift_code"),
#                             "intermediate_iban_no": row.get("intermediate_iban_no"),
#                             "intermediate_aba_no": row.get("intermediate_aba_no"),
#                             "intermediate_bank_address": row.get("intermediate_bank_address"),
#                             "intermediate_account_no": row.get("intermediate_account_no"),
#                             "intermediate_ach_no": row.get("intermediate_ach_no"),
#                             "intermediate_routing_no": row.get("intermediate_routing_no"),
#                             "intermediate_currency": row.get("intermediate_currency")
#                         })
#                         if bank_proof_for_intermediate_bank:
#                             new_row.bank_proof_for_intermediate_bank = bank_proof_for_intermediate_bank

#                 pd.save(ignore_permissions=True)
#             frappe.db.commit()

#             return {
#                 "status": "success",
#                 "message": "Vendor Onboarding Payment Details updated successfully.",
#                 "docname": [pd.name for pd in linked_docs],
#                 "bank_proof": doc.bank_proof if hasattr(doc, "bank_proof") else None
#             }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Payment Update Error")
#         return {
#             "status": "error",
#             "message": "Failed to update Vendor Onboarding Payment Details.",
#             "error": str(e)
#         }


@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_payment_details(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		ref_no = data.get("ref_no")
		vendor_onboarding = data.get("vendor_onboarding")

		if not ref_no or not vendor_onboarding:
			return {
				"status": "error",
				"message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
			}

		doc_name = frappe.db.get_value(
			"Vendor Onboarding Payment Details",
			{"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
			"name"
		)

		if not doc_name:
			return {
				"status": "error",
				"message": "No record found for Vendor Onboarding Payment Details"
			}

		main_doc = frappe.get_doc("Vendor Onboarding Payment Details", doc_name)

		# Upload files once
		file_urls = {}
		file_keys = [
			"bank_proof", "bank_proof_for_beneficiary_bank", "bank_proof_for_intermediate_bank"
		]

		for key in file_keys:
			if key in frappe.request.files:
				file = frappe.request.files[key]
				saved = save_file(file.filename, file.stream.read(), main_doc.doctype, main_doc.name, is_private=1)
				file_urls[key] = saved.file_url

		# Handle linked docs if registered_for_multi_companies is 1
		if main_doc.registered_for_multi_companies == 1:
			linked_docs = frappe.get_all(
				"Vendor Onboarding Payment Details",
				filters={
					"registered_for_multi_companies": 1,
					"unique_multi_comp_id": main_doc.unique_multi_comp_id
				},
				fields=["name"]
			)
		else:
			linked_docs = [{"name": main_doc.name}]

		fields_to_update = [
			"bank_name", "ifsc_code", "account_number", "name_of_account_holder",
			"type_of_account", "currency", "rtgs", "neft", "ift"
		]

		for entry in linked_docs:
			doc = frappe.get_doc("Vendor Onboarding Payment Details", entry["name"])

			for field in fields_to_update:
				if field in data and data[field] is not None:
					doc.set(field, data[field])

			for fkey, furl in file_urls.items():
				doc.set(fkey, furl)

			# International Bank Details
			if "international_bank_details" in data and isinstance(data["international_bank_details"], list):
				doc.set("international_bank_details", [])
				for row in data["international_bank_details"]:
					new_row = doc.append("international_bank_details", {
						"meril_company_name": row.get("meril_company_name"),
						"beneficiary_name": row.get("beneficiary_name"),
						"beneficiary_swift_code": row.get("beneficiary_swift_code"),
						"beneficiary_iban_no": row.get("beneficiary_iban_no"),
						"beneficiary_aba_no": row.get("beneficiary_aba_no"),
						"beneficiary_bank_address": row.get("beneficiary_bank_address"),
						"beneficiary_bank_name": row.get("beneficiary_bank_name"),
						"beneficiary_account_no": row.get("beneficiary_account_no"),
						"beneficiary_ach_no": row.get("beneficiary_ach_no"),
						"beneficiary_routing_no": row.get("beneficiary_routing_no"),
						"beneficiary_currency": row.get("beneficiary_currency")
					})
					if "bank_proof_for_beneficiary_bank" in file_urls:
						new_row.bank_proof_for_beneficiary_bank = file_urls["bank_proof_for_beneficiary_bank"]

			# Intermediate Bank Details
			if "intermediate_bank_details" in data and isinstance(data["intermediate_bank_details"], list):
				doc.set("intermediate_bank_details", [])
				for row in data["intermediate_bank_details"]:
					new_row = doc.append("intermediate_bank_details", {
						"intermediate_name": row.get("intermediate_name"),
						"intermediate_bank_name": row.get("intermediate_bank_name"),
						"intermediate_swift_code": row.get("intermediate_swift_code"),
						"intermediate_iban_no": row.get("intermediate_iban_no"),
						"intermediate_aba_no": row.get("intermediate_aba_no"),
						"intermediate_bank_address": row.get("intermediate_bank_address"),
						"intermediate_account_no": row.get("intermediate_account_no"),
						"intermediate_ach_no": row.get("intermediate_ach_no"),
						"intermediate_routing_no": row.get("intermediate_routing_no"),
						"intermediate_currency": row.get("intermediate_currency")
					})
					if "bank_proof_for_intermediate_bank" in file_urls:
						new_row.bank_proof_for_intermediate_bank = file_urls["bank_proof_for_intermediate_bank"]

			doc.save(ignore_permissions=True)

		frappe.db.commit()

		return {
			"status": "success",
			"message": "Vendor Onboarding Payment Details updated successfully.",
			"docnames": [d["name"] for d in linked_docs],
			**file_urls
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Payment Update Error")
		return {
			"status": "error",
			"message": "Failed to update Vendor Onboarding Payment Details.",
			"error": str(e)
		}