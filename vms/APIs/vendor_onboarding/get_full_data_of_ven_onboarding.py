import frappe

@frappe.whitelist(allow_guest=True)
def get_vendor_onboarding_details(vendor_onboarding, ref_no):
    try:
        if not vendor_onboarding or not ref_no:
            return {
                "status": "error",
                "message": "Missing required parameters: 'vendor_onboarding' and 'ref_no'."
            }

        docname = frappe.db.get_value(
            "Vendor Onboarding Company Details",
            {"vendor_onboarding": vendor_onboarding, "ref_no": ref_no},
            "name"
        )

        if not docname:
            return {
                "status": "error",
                "message": "No matching Vendor Onboarding Company Details record found."
            }

        doc = frappe.get_doc("Vendor Onboarding Company Details", docname)

        # --- Company Details Tab ---
        company_fields = [
            "vendor_title", "vendor_name", "company_name", "type_of_business", "size_of_company",
            "website", "registered_office_number", "telephone_number", "whatsapp_number",
            "established_year", "office_email_primary", "office_email_secondary",
            "corporate_identification_number", "cin_date", "nature_of_company", "nature_of_business"
        ]

        company_details = {field: doc.get(field) for field in company_fields}

        # --- Fetch vendor types from Vendor Master ---
        vendor_type_list = []
        if frappe.db.exists("Vendor Master", ref_no):
            vendor_doc = frappe.get_doc("Vendor Master", ref_no)
            for row in vendor_doc.vendor_types:
                vendor_type_list.append(row.vendor_type)

        company_details["vendor_types"] = vendor_type_list

        # --- Company Address Tab ---
        address_fields = [
            "address_line_1", "address_line_2", "city", "district", "state", "country", "pincode",
            "same_as_above", "street_1", "street_2", "manufacturing_city", "manufacturing_district",
            "manufacturing_state", "manufacturing_country", "manufacturing_pincode",
            "multiple_locations"
        ]

        address_details = {field: doc.get(field) for field in address_fields}

        address_details["multiple_location_table"] = [
            row.as_dict() for row in doc.multiple_location_table
        ]
        
        # attach field
        if doc.address_proofattachment:
            file_doc = frappe.get_doc("File", {"file_url": doc.address_proofattachment})
            address_details["address_proofattachment"] = {
                "url": frappe.utils.get_url(file_doc.file_url),
                "name": file_doc.name,
                "file_name": file_doc.file_name

            }
        else:
            address_details["address_proofattachment"] = {
                "url": "",
                "name": ""
            }


        #--- Documents details Tab--------
        legal_docname = frappe.db.get_value(
            "Legal Documents",
            {"vendor_onboarding": vendor_onboarding, "ref_no": ref_no},
            "name"
        )

        if not legal_docname:
            return {
                "status": "error",
                "message": "No matching Legal Documents record found."
            }

        legal_doc = frappe.get_doc("Legal Documents", legal_docname)

        legal_fields = [
            "company_pan_number", "name_on_company_pan", "enterprise_registration_number",
            "msme_registered", "msme_enterprise_type", "udyam_number", "name_on_udyam_certificate"
        ]

        document_details = {field: legal_doc.get(field) for field in legal_fields}

        # Attach fields
        for field in ["pan_proof", "entity_proof", "msme_proof"]:
            file_url = legal_doc.get(field)
            if file_url:
                file_doc = frappe.get_doc("File", {"file_url": file_url})
                document_details[field] = {
                    "url": frappe.utils.get_url(file_doc.file_url),
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                }
            else:
                document_details[field] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }

        # Child Table: GST Table with attachment
        gst_table = []
        for row in legal_doc.gst_table:
            gst_row = row.as_dict()
            if row.gst_document:
                file_doc = frappe.get_doc("File", {"file_url": row.gst_document})
                gst_row["gst_document"] = {
                    "url": frappe.utils.get_url(file_doc.file_url),
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                }
            else:
                gst_row["gst_document"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }
            gst_table.append(gst_row)

        document_details["gst_table"] = gst_table


        #---------------- Payment details Tab-----------------------------

        payment_docname = frappe.db.get_value("Vendor Onboarding Payment Details", {
            "vendor_onboarding": vendor_onboarding,
            "ref_no": ref_no
        }, "name")

        if not payment_docname:
            return {
                "status": "error",
                "message": "No matching Vendor Onboarding Payment Details record found."
            }

        payment_doc = frappe.get_doc("Vendor Onboarding Payment Details", payment_docname)

        payment_fields = [
            "bank_name", "ifsc_code", "account_number", "name_of_account_holder",
            "type_of_account", "currency", "rtgs", "neft"
        ]
        payment_details = {field: payment_doc.get(field) for field in payment_fields}

        if payment_doc.bank_proof:
            file_doc = frappe.get_doc("File", {"file_url": payment_doc.bank_proof})
            payment_details["bank_proof"] = {
                "url": frappe.utils.get_url(file_doc.file_url),
                "name": file_doc.name,
                "file_name": file_doc.file_name
            }
        else:
            payment_details["bank_proof"] = {
                "url": "",
                "name": "",
                "file_name": ""
            }


        #----------contact details tab-----------------

        ven_onb_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        contact_details = [row.as_dict() for row in ven_onb_doc.contact_details]




        return {
            "status": "success",
            "message": "Vendor onboarding company and address details fetched successfully.",
            "company_details_tab": company_details,
            "company_address_tab": address_details,
            "document_details_tab": document_details,
            "payment_details_tab": payment_details,
            "contact_details_tab": contact_details
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Company Details Fetch Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding company details.",
            "error": str(e)
        }
