import frappe
import json
from frappe.utils.file_manager import save_file

# certificate names master
@frappe.whitelist(allow_guest=True)
def vendor_certificate_name_masters():
    try:
        certificate_names = frappe.db.sql("SELECT name, certificate_name, certificate_code  FROM `tabCertificate Master`", as_dict=True)

        return {
            "status": "success",
            "message": "Vendor certificate names fetched successfully.",
            "data": {
                "certificate_names": certificate_names
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor certificate names Fetch Error")
        return {
            "status": "error",
            "message": "Failed to fetch Vendor certificate names values.",
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_certificate_details(data):
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
			"Vendor Onboarding Certificates",
			{"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
			"name"
		)

		if not doc_name:
			return {
				"status": "error",
				"message": "Vendor Onboarding Certificates Record not found."
			}

		main_doc = frappe.get_doc("Vendor Onboarding Certificates", doc_name)

		if not data.get("certificates"):
			return {
				"status": "error",
				"message": "Missing child table fields: 'certificates'."
			}

		# Upload file only once
		uploaded_file_url = ""
		if "certificate_attach" in frappe.request.files:
			file = frappe.request.files["certificate_attach"]
			saved = save_file(file.filename, file.stream.read(), main_doc.doctype, main_doc.name, is_private=1)
			uploaded_file_url = saved.file_url

		# If multi-company, update all related docs
		if main_doc.registered_for_multi_companies == 1:
			unique_multi_comp_id = main_doc.unique_multi_comp_id

			linked_docs = frappe.get_all(
				"Vendor Onboarding Certificates",
				filters={
					"registered_for_multi_companies": 1,
					"unique_multi_comp_id": unique_multi_comp_id
				},
				fields=["name"]
			)

			for entry in linked_docs:
				doc = frappe.get_doc("Vendor Onboarding Certificates", entry.name)

				for row in data["certificates"]:
					certificate_code = (row.get("certificate_code") or "").strip()
					certificate_name = (row.get("certificate_name") or "").strip()
					other_certificate_name = (row.get("other_certificate_name") or "").strip()
					valid_till = (row.get("valid_till") or "").strip()

					is_duplicate = any(
						(c.certificate_code or "").strip() == certificate_code
						for c in doc.certificates
					)

					if not is_duplicate:
						new_row = doc.append("certificates", {
							"certificate_code": certificate_code,
							"certificate_name": certificate_name,
							"other_certificate_name": other_certificate_name,
							"valid_till": valid_till
						})

						# Set file URL explicitly if available
						if uploaded_file_url:
							new_row.certificate_attach = uploaded_file_url

				doc.save(ignore_permissions=True)
				frappe.db.commit()

			return {
				"status": "success",
				"message": "Vendor Onboarding Certificates updated successfully for all linked records.",
				"docnames": [doc.name for doc in linked_docs]
			}

		else:
			# Single doc update
			for row in data["certificates"]:
				certificate_code = (row.get("certificate_code") or "").strip()
				certificate_name = (row.get("certificate_name") or "").strip()
				other_certificate_name = (row.get("other_certificate_name") or "").strip()
				valid_till = (row.get("valid_till") or "").strip()

				is_duplicate = any(
					(c.certificate_code or "").strip() == certificate_code
					for c in main_doc.certificates
				)

				if not is_duplicate:
					new_row = main_doc.append("certificates", {
						"certificate_code": certificate_code,
						"certificate_name": certificate_name,
						"other_certificate_name": other_certificate_name,
						"valid_till": valid_till
					})

					# Set file URL explicitly if available
					if uploaded_file_url:
						new_row.certificate_attach = uploaded_file_url

			main_doc.save(ignore_permissions=True)
			frappe.db.commit()

			return {
				"status": "success",
				"message": "Vendor Onboarding Certificates updated successfully.",
				"docname": main_doc.name
			}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Certificates Update Error")
		return {
			"status": "error",
			"message": "Failed to update Vendor Onboarding Certificates.",
			"error": str(e)
		}





# to delete the row of vendor onboarding certificates


@frappe.whitelist(allow_guest=True)
def delete_vendor_onboarding_certificate_row(certificate_code, ref_no, vendor_onboarding):
    try:
        if not certificate_code or not ref_no or not vendor_onboarding:
            return {
                "status": "error",
                "message": "Missing required fields: 'certificate_code', 'ref_no', or 'vendor_onboarding'."
            }

        doc_name = frappe.db.get_value(
            "Vendor Onboarding Certificates",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            return {
                "status": "error",
                "message": "Vendor Onboarding Certificates record not found."
            }

        main_doc = frappe.get_doc("Vendor Onboarding Certificates", doc_name)
        deleted_from_docs = []

        if main_doc.registered_for_multi_companies == 1:
            unique_multi_comp_id = main_doc.unique_multi_comp_id

            linked_docs = frappe.get_all(
                "Vendor Onboarding Certificates",
                filters={
                    "registered_for_multi_companies": 1,
                    "unique_multi_comp_id": unique_multi_comp_id
                },
                fields=["name"]
            )

            for entry in linked_docs:
                doc = frappe.get_doc("Vendor Onboarding Certificates", entry.name)
                original_len = len(doc.certificates)

                doc.certificates = [
                    row for row in doc.certificates
                    if (row.certificate_code or "").strip() != certificate_code.strip()
                ]

                if len(doc.certificates) != original_len:
                    doc.save(ignore_permissions=True)
                    deleted_from_docs.append(doc.name)

            if not deleted_from_docs:
                return {
                    "status": "error",
                    "message": f"No matching certificate_code '{certificate_code}' found in linked records."
                }

            frappe.db.commit()
            return {
                "status": "success",
                "message": f"Certificate with code '{certificate_code}' deleted from linked records.",
                "docnames": deleted_from_docs
            }

        else:
            original_len = len(main_doc.certificates)

            main_doc.certificates = [
                row for row in main_doc.certificates
                if (row.certificate_code or "").strip() != certificate_code.strip()
            ]

            if len(main_doc.certificates) == original_len:
                return {
                    "status": "error",
                    "message": f"No matching certificate_code '{certificate_code}' found in this document."
                }

            main_doc.save(ignore_permissions=True)
            frappe.db.commit()

            return {
                "status": "success",
                "message": f"Certificate with code '{certificate_code}' deleted successfully.",
                "docname": main_doc.name
            }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Delete Vendor Certificate by Code Error")
        return {
            "status": "error",
            "message": "Failed to delete certificate row.",
            "error": str(e)
        }
	