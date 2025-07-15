import frappe
import json
from frappe.utils.file_manager import save_file

# @frappe.whitelist(allow_guest=True)
# def update_vendor_onboarding_manufacturing_details(data):
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
#             "Vendor Onboarding Manufacturing Details",
#             {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
#             "name"
#         )

#         if not doc_name:
#             return {
#                 "status": "error",
#                 "message": "Vendor Onboarding Manufacturing Record not found."
#             }

#         doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", doc_name)

#         # Updatable fields
#         fields_to_update = [
#             "details_of_product_manufactured", "total_godown", "storage_capacity", "spare_capacity",
#             "type_of_premises", "working_hours", "weekly_holidays", "number_of_manpower",
#             "annual_revenue", "google_address_pin", "cold_storage"
#         ]

#         for field in fields_to_update:
#             if field in data and data[field] is not None:
#                 doc.set(field, data[field])

#         # Update brochure attachment
#         if 'brochure_proof' in frappe.request.files:
#             file = frappe.request.files['brochure_proof']
#             saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
#             doc.brochure_proof = saved.file_url

#         # Update org structure attachment
#         if 'organisation_structure_document' in frappe.request.files:
#             file = frappe.request.files['organisation_structure_document']
#             saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
#             doc.organisation_structure_document = saved.file_url

#         doc.set("materials_supplied", [])

#         # update child table
#         if "materials_supplied" in data:
#             # index = 0
#             for row in data["materials_supplied"]:
#                 new_row = doc.append("materials_supplied", {
#                     "material_description": row.get("material_description"),
#                     "annual_capacity": row.get("annual_capacity"),
#                     "hsnsac_code": row.get("hsnsac_code")
#                 })
                
#                 # is_duplicate = False

#                 # for existing in doc.materials_supplied:
#                 #     if (
#                 #         (existing.material_description or "").strip().lower() == (row.get("material_description") or "").strip().lower() and
#                 #         (existing.hsnsac_code or "").strip().lower() == (row.get("hsnsac_code") or "").strip().lower()
#                 #     ):
#                 #         is_duplicate = True
#                 #         break

#                 # if not is_duplicate:
#                 #     new_row = doc.append("materials_supplied", row)

#                 # Attach file if available
#                 file_key = f"material_images"
#                 if file_key in frappe.request.files:
#                     file = frappe.request.files[file_key]
#                     saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
#                     new_row.material_images = saved.file_url

#                 # index += 1

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Manufacturing details updated successfully.",
#             "docname": doc.name,
#             "brochure_proof": doc.brochure_proof if hasattr(doc, "brochure_proof") else None,
#             "organisation_structure_document": doc.organisation_structure_document if hasattr(doc, "organisation_structure_document") else None
#         }

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), "Manufacturing Details Update Error")
#         return {
#             "status": "error",
#             "message": "Failed to update manufacturing details.",
#             "error": str(e)
#         }



@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_manufacturing_details(data):
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
			"Vendor Onboarding Manufacturing Details",
			{"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
			"name"
		)

		if not doc_name:
			return {
				"status": "error",
				"message": "Vendor Onboarding Manufacturing Record not found."
			}

		main_doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", doc_name)

		# Upload files only once
		brochure_url = ""
		org_structure_url = ""
		material_img_url = ""

		if 'brochure_proof' in frappe.request.files:
			file = frappe.request.files['brochure_proof']
			saved = save_file(file.filename, file.stream.read(), main_doc.doctype, main_doc.name, is_private=0)
			brochure_url = saved.file_url

		if 'organisation_structure_document' in frappe.request.files:
			file = frappe.request.files['organisation_structure_document']
			saved = save_file(file.filename, file.stream.read(), main_doc.doctype, main_doc.name, is_private=0)
			org_structure_url = saved.file_url

		if 'material_images' in frappe.request.files:
			file = frappe.request.files['material_images']
			saved = save_file(file.filename, file.stream.read(), main_doc.doctype, main_doc.name, is_private=0)
			material_img_url = saved.file_url

		# Get all linked docs if multi-company
		linked_docs = []
		if main_doc.registered_for_multi_companies == 1:
			unique_multi_comp_id = main_doc.unique_multi_comp_id
			linked_docs = frappe.get_all(
				"Vendor Onboarding Manufacturing Details",
				filters={
					"registered_for_multi_companies": 1,
					"unique_multi_comp_id": unique_multi_comp_id
				},
				fields=["name"]
			)
		else:
			linked_docs = [main_doc]

		for entry in linked_docs:
			doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", entry.name)

			# Set base fields
			fields_to_update = [
				"details_of_product_manufactured", "total_godown", "storage_capacity", "spare_capacity",
				"type_of_premises", "working_hours", "weekly_holidays", "number_of_manpower",
				"annual_revenue", "google_address_pin", "cold_storage"
			]

			for field in fields_to_update:
				if field in data and data[field] is not None:
					doc.set(field, data[field])

			if brochure_url:
				doc.brochure_proof = brochure_url
			if org_structure_url:
				doc.organisation_structure_document = org_structure_url

			# Clear child table and re-append
			doc.set("materials_supplied", [])

			if "materials_supplied" in data:
				for row in data["materials_supplied"]:
					new_row = doc.append("materials_supplied", {
						"material_description": row.get("material_description"),
						"annual_capacity": row.get("annual_capacity"),
						"hsnsac_code": row.get("hsnsac_code")
					})
					if material_img_url:
						new_row.material_images = material_img_url

			doc.save(ignore_permissions=True)

		frappe.db.commit()

		return {
			"status": "success",
			"message": "Manufacturing details updated successfully.",
			"docname": main_doc.name,
			"brochure_proof": brochure_url,
			"organisation_structure_document": org_structure_url
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Manufacturing Details Update Error")
		return {
			"status": "error",
			"message": "Failed to update manufacturing details.",
			"error": str(e)
		}

