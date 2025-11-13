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


# @frappe.whitelist(allow_guest=True)
# def update_vendor_onboarding_payment_details(data):
# 	try:
# 		if isinstance(data, str):
# 			data = json.loads(data)

# 		ref_no = data.get("ref_no")
# 		vendor_onboarding = data.get("vendor_onboarding")

# 		if not ref_no or not vendor_onboarding:
# 			return {
# 				"status": "error",
# 				"message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
# 			}

# 		doc_name = frappe.db.get_value(
# 			"Vendor Onboarding Payment Details",
# 			{"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
# 			"name"
# 		)

# 		if not doc_name:
# 			return {
# 				"status": "error",
# 				"message": "No record found for Vendor Onboarding Payment Details"
# 			}

# 		main_doc = frappe.get_doc("Vendor Onboarding Payment Details", doc_name)

# 		# Upload files once
# 		file_urls = {}
# 		file_keys = [
# 			"bank_proof", "bank_proof_for_beneficiary_bank", "bank_proof_for_intermediate_bank"
# 		]

# 		for key in file_keys:
# 			if key in frappe.request.files:
# 				file = frappe.request.files[key]
# 				saved = save_file(file.filename, file.stream.read(), main_doc.doctype, main_doc.name, is_private=0)
# 				file_urls[key] = saved.file_url

# 		# Handle linked docs if registered_for_multi_companies is 1
# 		if main_doc.registered_for_multi_companies == 1:
# 			linked_docs = frappe.get_all(
# 				"Vendor Onboarding Payment Details",
# 				filters={
# 					"registered_for_multi_companies": 1,
# 					"unique_multi_comp_id": main_doc.unique_multi_comp_id
# 				},
# 				fields=["name"]
# 			)
# 		else:
# 			linked_docs = [{"name": main_doc.name}]

# 		fields_to_update = [
# 			"bank_name", "ifsc_code", "account_number", "name_of_account_holder",
# 			"type_of_account", "currency", "rtgs", "neft", "ift"
# 		]

# 		for entry in linked_docs:
# 			doc = frappe.get_doc("Vendor Onboarding Payment Details", entry["name"])

# 			for field in fields_to_update:
# 				if field in data and data[field] is not None:
# 					doc.set(field, data[field])

# 			for fkey, furl in file_urls.items():
# 				doc.set(fkey, furl)

# 			# International Bank Details
# 			if "international_bank_details" in data and isinstance(data["international_bank_details"], list):
# 				for row in data["international_bank_details"]:
# 					child_row = None
# 					if "name" in row:
# 						child_row = next((r for r in doc.international_bank_details if r.name == row["name"]), None)

# 					if child_row:
# 						# Update existing row
# 						for key in [
# 							"meril_company_name", "beneficiary_name", "beneficiary_swift_code", "beneficiary_iban_no",
# 							"beneficiary_aba_no", "beneficiary_bank_address", "beneficiary_bank_name",
# 							"beneficiary_account_no", "beneficiary_ach_no", "beneficiary_routing_no",
# 							"beneficiary_currency"
# 						]:
# 							if key in row:
# 								child_row.set(key, row[key])
# 					else:
# 						# Append new row
# 						child_row = doc.append("international_bank_details", {
# 							"meril_company_name": row.get("meril_company_name"),
# 							"beneficiary_name": row.get("beneficiary_name"),
# 							"beneficiary_swift_code": row.get("beneficiary_swift_code"),
# 							"beneficiary_iban_no": row.get("beneficiary_iban_no"),
# 							"beneficiary_aba_no": row.get("beneficiary_aba_no"),
# 							"beneficiary_bank_address": row.get("beneficiary_bank_address"),
# 							"beneficiary_bank_name": row.get("beneficiary_bank_name"),
# 							"beneficiary_account_no": row.get("beneficiary_account_no"),
# 							"beneficiary_ach_no": row.get("beneficiary_ach_no"),
# 							"beneficiary_routing_no": row.get("beneficiary_routing_no"),
# 							"beneficiary_currency": row.get("beneficiary_currency")
# 						})

# 					# Attach file if available
# 					if "bank_proof_for_beneficiary_bank" in file_urls:
# 						child_row.bank_proof_for_beneficiary_bank = file_urls["bank_proof_for_beneficiary_bank"]


# 			# Intermediate Bank Details
# 			# Intermediate Bank Details
# 			if "intermediate_bank_details" in data and isinstance(data["intermediate_bank_details"], list):
# 				for row in data["intermediate_bank_details"]:
# 					child_row = None
# 					if "name" in row:
# 						child_row = next((r for r in doc.intermediate_bank_details if r.name == row["name"]), None)

# 					if child_row:
# 						# Update existing row
# 						for key in [
# 							"intermediate_name", "intermediate_bank_name", "intermediate_swift_code", "intermediate_iban_no",
# 							"intermediate_aba_no", "intermediate_bank_address", "intermediate_account_no",
# 							"intermediate_ach_no", "intermediate_routing_no", "intermediate_currency"
# 						]:
# 							if key in row:
# 								child_row.set(key, row[key])
# 					else:
# 						# Append new row
# 						child_row = doc.append("intermediate_bank_details", {
# 							"intermediate_name": row.get("intermediate_name"),
# 							"intermediate_bank_name": row.get("intermediate_bank_name"),
# 							"intermediate_swift_code": row.get("intermediate_swift_code"),
# 							"intermediate_iban_no": row.get("intermediate_iban_no"),
# 							"intermediate_aba_no": row.get("intermediate_aba_no"),
# 							"intermediate_bank_address": row.get("intermediate_bank_address"),
# 							"intermediate_account_no": row.get("intermediate_account_no"),
# 							"intermediate_ach_no": row.get("intermediate_ach_no"),
# 							"intermediate_routing_no": row.get("intermediate_routing_no"),
# 							"intermediate_currency": row.get("intermediate_currency")
# 						})

# 					# Attach file if available
# 					if "bank_proof_for_intermediate_bank" in file_urls:
# 						child_row.bank_proof_for_intermediate_bank = file_urls["bank_proof_for_intermediate_bank"]


# 			doc.save(ignore_permissions=True)

# 		frappe.db.commit()

# 		return {
# 			"status": "success",
# 			"message": "Vendor Onboarding Payment Details updated successfully.",
# 			"docnames": [d["name"] for d in linked_docs],
# 			**file_urls
# 		}

# 	except Exception as e:
# 		frappe.db.rollback()
# 		frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Payment Update Error")
# 		return {
# 			"status": "error",
# 			"message": "Failed to update Vendor Onboarding Payment Details.",
# 			"error": str(e)
# 		}


@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_payment_details(data):
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

        doc_name = frappe.db.get_value(
            "Vendor Onboarding Payment Details",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            frappe.local.response["http_status_code"] = 404
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
                saved = save_file(file.filename, file.stream.read(), main_doc.doctype, main_doc.name, is_private=0)
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
                for row in data["international_bank_details"]:
                    if not row:
                        continue  # Skip null or empty entries

                    child_row = None
                    if "name" in row:
                        child_row = next((r for r in doc.international_bank_details if r.name == row["name"]), None)

                    if child_row:
                        # Update existing row
                        for key in [
                            "meril_company_name", "beneficiary_name", "beneficiary_swift_code", "beneficiary_iban_no",
                            "beneficiary_aba_no", "beneficiary_bank_address", "beneficiary_bank_name",
                            "beneficiary_account_no", "beneficiary_ach_no", "beneficiary_routing_no",
                            "beneficiary_currency"
                        ]:
                            if key in row:
                                child_row.set(key, row[key])
                    else:
                        # Append new row
                        child_row = doc.append("international_bank_details", {
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

                    # Attach file if available
                    if "bank_proof_for_beneficiary_bank" in file_urls:
                        child_row.bank_proof_for_beneficiary_bank = file_urls["bank_proof_for_beneficiary_bank"]

            # Intermediate Bank Details
            if "intermediate_bank_details" in data and isinstance(data["intermediate_bank_details"], list):
                for row in data["intermediate_bank_details"]:
                    if not row:
                        continue  # Skip null or empty entries

                    child_row = None
                    if "name" in row:
                        child_row = next((r for r in doc.intermediate_bank_details if r.name == row["name"]), None)

                    if child_row:
                        # Update existing row
                        for key in [
                            "intermediate_name", "intermediate_bank_name", "intermediate_swift_code", "intermediate_iban_no",
                            "intermediate_aba_no", "intermediate_bank_address", "intermediate_account_no",
                            "intermediate_ach_no", "intermediate_routing_no", "intermediate_currency"
                        ]:
                            if key in row:
                                child_row.set(key, row[key])
                    else:
                        # Append new row
                        child_row = doc.append("intermediate_bank_details", {
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

                    # Attach file if available
                    if "bank_proof_for_intermediate_bank" in file_urls:
                        child_row.bank_proof_for_intermediate_bank = file_urls["bank_proof_for_intermediate_bank"]

            doc.save(ignore_permissions=True)

        frappe.db.commit()

        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": "Vendor Onboarding Payment Details updated successfully.",
            "docnames": [d["name"] for d in linked_docs],
            **file_urls
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Payment Update Error")
        return {
            "status": "error",
            "message": "Failed to update Vendor Onboarding Payment Details.",
            "error": str(e)
        }


# upload bank proof by purchase team

# @frappe.whitelist(allow_guest=True)
# def update_bank_proof_purchase_team(data):
# 	try:
# 		if isinstance(data, str):
# 			data = json.loads(data)

# 		ref_no = data.get("ref_no")
# 		vendor_onboarding = data.get("vendor_onboarding")

# 		if not ref_no or not vendor_onboarding:
# 			return {
# 				"status": "error",
# 				"message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
# 			}

# 		doc_name = frappe.db.get_value(
# 			"Vendor Onboarding Payment Details",
# 			{"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
# 			"name"
# 		)

# 		if not doc_name:
# 			return {
# 				"status": "error",
# 				"message": "No record found for Vendor Onboarding Payment Details"
# 			}

# 		main_doc = frappe.get_doc("Vendor Onboarding Payment Details", doc_name)

# 		file_url = None
# 		if "bank_proof_by_purchase_team" in frappe.request.files:
# 			file = frappe.request.files["bank_proof_by_purchase_team"]

# 			saved = save_file(
# 				file.filename,               
# 				file.stream.read(),          
# 				main_doc.doctype,            
# 				main_doc.name,               
# 				is_private=0                 
# 			)
# 			file_url = saved.file_url

# 		if main_doc.registered_for_multi_companies == 1:
# 			linked_docs = frappe.get_all(
# 				"Vendor Onboarding Payment Details",
# 				filters={
# 					"registered_for_multi_companies": 1,
# 					"unique_multi_comp_id": main_doc.unique_multi_comp_id
# 				},
# 				fields=["name"]
# 			)
# 		else:
# 			linked_docs = [{"name": main_doc.name}]

# 		for entry in linked_docs:
# 			doc = frappe.get_doc("Vendor Onboarding Payment Details", entry["name"])
# 			if file_url:
# 				doc.bank_proof_by_purchase_team = file_url
# 			doc.save(ignore_permissions=True)

# 		frappe.db.commit()

# 		return {
# 			"status": "success",
# 			"message": "Vendor Onboarding Payment Details updated successfully.",
# 			"docnames": [d["name"] for d in linked_docs],
# 			"file_url": file_url
# 		}

# 	except Exception as e:
# 		frappe.db.rollback()
# 		frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Payment Update Error")
# 		return {
# 			"status": "error",
# 			"message": "Failed to update Vendor Onboarding Payment Details.",
# 			"error": str(e)
# 		}


# @frappe.whitelist(allow_guest=True)
# def update_bank_proof_purchase_team(data):
# 	try:
# 		if isinstance(data, str):
# 			data = json.loads(data)

# 		ref_no = data.get("ref_no")
# 		vendor_onboarding = data.get("vendor_onboarding")

# 		if not ref_no or not vendor_onboarding:
# 			return {
# 				"status": "error",
# 				"message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
# 			}

# 		doc_name = frappe.db.get_value(
# 			"Vendor Onboarding Payment Details",
# 			{"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
# 			"name"
# 		)

# 		if not doc_name:
# 			return {
# 				"status": "error",
# 				"message": "No record found for Vendor Onboarding Payment Details"
# 			}

# 		main_doc = frappe.get_doc("Vendor Onboarding Payment Details", doc_name)

# 		# --- Upload files ---
# 		file_urls = {}

# 		# Handle all three file types
# 		for file_key in [
# 			"bank_proof_by_purchase_team",
# 			"international_bank_proof_by_purchase_team",
# 			"intermediate_bank_proof_by_purchase_team"
# 		]:
# 			if file_key in frappe.request.files:
# 				file = frappe.request.files[file_key]
# 				saved = save_file(
# 					file.filename,
# 					file.stream.read(),
# 					main_doc.doctype,
# 					main_doc.name,
# 					is_private=0
# 				)
# 				file_urls[file_key] = saved.file_url

# 		# --- Find linked docs for multi-company ---
# 		if main_doc.registered_for_multi_companies == 1:
# 			linked_docs = frappe.get_all(
# 				"Vendor Onboarding Payment Details",
# 				filters={
# 					"registered_for_multi_companies": 1,
# 					"unique_multi_comp_id": main_doc.unique_multi_comp_id
# 				},
# 				fields=["name"]
# 			)
# 		else:
# 			linked_docs = [{"name": main_doc.name}]

# 		# --- Update parent + child tables ---
# 		for entry in linked_docs:
# 			doc = frappe.get_doc("Vendor Onboarding Payment Details", entry["name"])

# 			# Parent field
# 			if "bank_proof_by_purchase_team" in file_urls:
# 				doc.bank_proof_by_purchase_team = file_urls["bank_proof_by_purchase_team"]

# 			# Child: international bank details
# 			if "international_bank_proof_by_purchase_team" in file_urls:
# 				for row in doc.international_bank_details:
# 					row.international_bank_proof_by_purchase_team = file_urls["international_bank_proof_by_purchase_team"]

# 			# Child: intermediate bank details
# 			if "intermediate_bank_proof_by_purchase_team" in file_urls:
# 				for row in doc.intermediate_bank_details:
# 					row.intermediate_bank_proof_by_purchase_team = file_urls["intermediate_bank_proof_by_purchase_team"]

# 			doc.save(ignore_permissions=True)

# 		frappe.db.commit()

# 		return {
# 			"status": "success",
# 			"message": "Vendor Onboarding Payment Details updated successfully.",
# 			"docnames": [d["name"] for d in linked_docs],
# 			"file_urls": file_urls
# 		}

# 	except Exception as e:
# 		frappe.db.rollback()
# 		frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Payment Update Error")
# 		return {
# 			"status": "error",
# 			"message": "Failed to update Vendor Onboarding Payment Details.",
# 			"error": str(e)
# 		}


@frappe.whitelist(allow_guest=True)
def update_bank_proof_purchase_team(data):
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

        doc_name = frappe.db.get_value(
            "Vendor Onboarding Payment Details",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "No record found for Vendor Onboarding Payment Details"
            }

        main_doc = frappe.get_doc("Vendor Onboarding Payment Details", doc_name)

        # --- Upload files ---
        file_urls = {}

        for file_key in [
            "bank_proofs_by_purchase_team",
            "international_bank_proofs_by_purchase_team",
            "intermediate_bank_proofs_by_purchase_team"
        ]:
            if file_key in frappe.request.files:
                files = frappe.request.files.getlist(file_key)
                file_urls[file_key] = []

                for file in files:
                    saved = save_file(
                        file.filename,
                        file.stream.read(),
                        main_doc.doctype,
                        main_doc.name,
                        is_private=0
                    )
                    file_urls[file_key].append(saved.file_url)

        # --- Find linked docs for multi-company ---
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

        new_rows = {
            "bank_proofs_by_purchase_team": [],
            "international_bank_proofs_by_purchase_team": [],
            "intermediate_bank_proofs_by_purchase_team": []
        }

        for entry in linked_docs:
            doc = frappe.get_doc("Vendor Onboarding Payment Details", entry["name"])

            # Store current row count before adding new rows
            existing_counts = {
                "bank_proofs_by_purchase_team": len(doc.bank_proofs_by_purchase_team),
                "international_bank_proofs_by_purchase_team": len(doc.international_bank_proofs_by_purchase_team),
                "intermediate_bank_proofs_by_purchase_team": len(doc.intermediate_bank_proofs_by_purchase_team)
            }

            if "bank_proofs_by_purchase_team" in file_urls:
                for url in file_urls["bank_proofs_by_purchase_team"]:
                    doc.append("bank_proofs_by_purchase_team", {
                        "name1": frappe.utils.now(),
                        "attachment_name": url
                    })

            if "international_bank_proofs_by_purchase_team" in file_urls:
                for url in file_urls["international_bank_proofs_by_purchase_team"]:
                    doc.append("international_bank_proofs_by_purchase_team", {
                        "name1": frappe.utils.now(),
                        "attachment_name": url
                    })

            if "intermediate_bank_proofs_by_purchase_team" in file_urls:
                for url in file_urls["intermediate_bank_proofs_by_purchase_team"]:
                    doc.append("intermediate_bank_proofs_by_purchase_team", {
                        "name1": frappe.utils.now(),
                        "attachment_name": url
                    })

            # Save to assign row names
            doc.save(ignore_permissions=True)

            # Now collect the newly added row names (only the ones we just added)
            if "bank_proofs_by_purchase_team" in file_urls:
                new_bank_rows = doc.bank_proofs_by_purchase_team[existing_counts["bank_proofs_by_purchase_team"]:]
                for row in new_bank_rows:
                    new_rows["bank_proofs_by_purchase_team"].append({
                        "row_name": row.name,
                        "attachment_name": row.attachment_name
                    })

            if "international_bank_proofs_by_purchase_team" in file_urls:
                new_intl_rows = doc.international_bank_proofs_by_purchase_team[existing_counts["international_bank_proofs_by_purchase_team"]:]
                for row in new_intl_rows:
                    new_rows["international_bank_proofs_by_purchase_team"].append({
                        "row_name": row.name,
                        "attachment_name": row.attachment_name
                    })

            if "intermediate_bank_proofs_by_purchase_team" in file_urls:
                new_intermediate_rows = doc.intermediate_bank_proofs_by_purchase_team[existing_counts["intermediate_bank_proofs_by_purchase_team"]:]
                for row in new_intermediate_rows:
                    new_rows["intermediate_bank_proofs_by_purchase_team"].append({
                        "row_name": row.name,
                        "attachment_name": row.attachment_name
                    })

        frappe.db.commit()

        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": "Vendor Onboarding Payment Details updated successfully.",
            "docnames": [d["name"] for d in linked_docs],
            "file_urls": file_urls,
            "new_rows": new_rows
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Payment Update Error")
        return {
            "status": "error",
            "message": "Failed to update Vendor Onboarding Payment Details.",
            "error": str(e)
        }
@frappe.whitelist(allow_guest=True)
def delete_bank_proof_attachment(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        ref_no = data.get("ref_no")
        vendor_onboarding = data.get("vendor_onboarding")
        attachment_table_name = data.get("attachment_table_name")
        row_name = data.get("attachment_name")

        if not all([ref_no, vendor_onboarding, attachment_table_name, row_name]):
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Missing required fields: 'ref_no', 'vendor_onboarding', 'attachment_table_name', and 'attachment_name'."
            }

        # Validate attachment table name
        valid_tables = [
            "bank_proofs_by_purchase_team",
            "international_bank_proofs_by_purchase_team",
            "intermediate_bank_proofs_by_purchase_team"
        ]

        if attachment_table_name not in valid_tables:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": f"Invalid attachment table name. Must be one of: {', '.join(valid_tables)}"
            }

        doc_name = frappe.db.get_value(
            "Vendor Onboarding Payment Details",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "No record found for Vendor Onboarding Payment Details"
            }

        main_doc = frappe.get_doc("Vendor Onboarding Payment Details", doc_name)

        # --- Find linked docs for multi-company ---
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

        deleted_from_docs = []
        deleted_attachments = []

        for entry in linked_docs:
            doc = frappe.get_doc("Vendor Onboarding Payment Details", entry["name"])

            # Get the child table
            child_table = getattr(doc, attachment_table_name, [])

            # Find and remove matching attachments by row name
            rows_to_remove = []
            for i, row in enumerate(child_table):
                if hasattr(row, 'name') and row.name == row_name:
                    rows_to_remove.append(i)
                    deleted_attachments.append({
                        "doc_name": doc.name,
                        # "attachment_name": getattr(row, 'attachment_name', ''),
                        "row_name": row.name
                    })

            # Remove rows in reverse order to maintain indices
            for i in reversed(rows_to_remove):
                doc.get(attachment_table_name).pop(i)

            if rows_to_remove:
                doc.save(ignore_permissions=True)
                deleted_from_docs.append(doc.name)

        frappe.db.commit()

        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": f"Attachment deleted successfully from {len(deleted_from_docs)} document(s).",
            "deleted_from_docs": deleted_from_docs,
            "deleted_attachments": deleted_attachments
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Attachment Delete Error")
        return {
            "status": "error",
            "message": "Failed to delete attachment.",
            "error": str(e)
        }
