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

        doc = frappe.get_doc("Vendor Onboarding Certificates", doc_name)

        # update child table
        if "certificates" not in data:
            return {
                "status": "error",
                "message": "Missing child table fields: 'certificates'."
            }

        # doc.set("certificates", [])   

        # index = 0
        for row in data["certificates"]:
            certificate_code = str(row.get("certificate_code", "")).strip()
            certificate_name = str(row.get("certificate_name", "")).strip()
            other_certificate_name = str(row.get("other_certificate_name", "")).strip()
            valid_till = str(row.get("valid_till", "")).strip()

        #     new_row = doc.append("certificates", {
        #         "certificate_code": str(row.get("certificate_code", "")).strip(),
        #         "certificate_name": str(row.get("certificate_name", "")).strip(),
        #         "other_certificate_name": str(row.get("other_certificate_name", "")).strip(),
        #         "valid_till": str(row.get("valid_till", "")).strip()
        #     })

            # Check for duplicate
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

                # Upload file if present
                file_key = "certificate_attach"
                if file_key in frappe.request.files:
                    file = frappe.request.files[file_key]
                    saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
                    new_row.certificate_attach = saved.file_url

            # index += 1

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Certificates updated successfully.",
            "docname": doc.name
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
def delete_vendor_onboarding_certificate_row(row_id, ref_no, vendor_onboarding):
    try:
        if not row_id or not ref_no or not vendor_onboarding:
            return {
                "status": "error",
                "message": "Missing required fields: 'row_id', 'ref_no', or 'vendor_onboarding'."
            }

        # Fetch the parent document name
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

        # Fetch parent document
        parent_doc = frappe.get_doc("Vendor Onboarding Certificates", doc_name)

        # Find and remove the matching row
        found = False
        new_rows = []
        for row in parent_doc.certificates:
            if row.name != row_id:
                new_rows.append(row)
            else:
                found = True

        if not found:
            return {
                "status": "error",
                "message": f"No row with ID {row_id} found in certificates table."
            }

        # Update the child table
        parent_doc.set("certificates", new_rows)
        parent_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Row {row_id} deleted successfully from certificates table.",
            "docname": parent_doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Delete Vendor Certificate Row Error")
        return {
            "status": "error",
            "message": "Failed to delete row from Vendor Onboarding Certificates.",
            "error": str(e)
        }