import frappe
from frappe import _

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
        
        #---------------Company Master Details----------------
        company_name_description = {}
        if doc.company_name:
            company_name_description = frappe.get_value( "Company Master", doc.company_name, "description")

        company_details["company_name_description"] = company_name_description

        # --- Fetch vendor types from Vendor Master ---
        vendor_type_list_from_master = []
        if frappe.db.exists("Vendor Master", ref_no):
            vendor_doc = frappe.get_doc("Vendor Master", ref_no)
            for row in vendor_doc.vendor_types:
                vendor_type_list_from_master.append(row.vendor_type)

        company_details["vendor_type_list_from_master"] = vendor_type_list_from_master
        # vendor_type_list = []
        # # if frappe.db.exists("Vendor Master", ref_no):
        # vendor_onb_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        # for row in vendor_onb_doc.vendor_types:
        #     vendor_type_list.append(row.vendor_type)

        # company_details["vendor_types"] = vendor_type_list

        # --- Company Address Tab ---

        address_fields = [

            "same_as_above", 
            "multiple_locations"
        ]

        address_details = {field: doc.get(field) for field in address_fields}

        # Fetch and add related city, district, state, and country records with limited fields

        # Billing Address
        billing_address = {}

        billing_address_field = ["address_line_1", "address_line_2", "pincode", "city", "district", "state", "country", "international_city", 
                                "international_state", "international_country", "international_zipcode"
                            ]

        billing_address = {field: doc.get(field) for field in billing_address_field}

        billing_address["city_details"] = (
            frappe.db.get_value("City Master", doc.city, ["name", "city_code", "city_name"], as_dict=True)
            if doc.city and frappe.db.exists("City Master", doc.city) else {}
        )

        billing_address["district_details"] = (
            frappe.db.get_value("District Master", doc.district, ["name", "district_code", "district_name"], as_dict=True)
            if doc.district and frappe.db.exists("District Master", doc.district) else {}
        )

        billing_address["state_details"] = (
            frappe.db.get_value("State Master", doc.state, ["name", "state_code", "state_name"], as_dict=True)
            if doc.state and frappe.db.exists("State Master", doc.state) else {}
        )

        billing_address["country_details"] = (
            frappe.db.get_value("Country Master", doc.country, ["name", "country_code", "country_name"], as_dict=True)
            if doc.country and frappe.db.exists("Country Master", doc.country) else {}
        )

        address_details["billing_address"] = billing_address


        # Shipping Address
        shipping_address = {}

        shipping_address_field = ["street_1", "street_2", "manufacturing_pincode", "manufacturing_city", "manufacturing_district",
            "manufacturing_state", "manufacturing_country", "inter_manufacture_city", "inter_manufacture_state", "inter_manufacture_country",
            "inter_manufacture_zipcode"]

        shipping_address = {field: doc.get(field) for field in shipping_address_field}
        
        shipping_address["city_details"] = (
            frappe.db.get_value("City Master", doc.manufacturing_city, ["name", "city_code", "city_name"], as_dict=True)
            if doc.city and frappe.db.exists("City Master", doc.city) else {}
        )

        shipping_address["district_details"] = (
            frappe.db.get_value("District Master", doc.manufacturing_district, ["name", "district_code", "district_name"], as_dict=True)
            if doc.district and frappe.db.exists("District Master", doc.district) else {}
        )

        shipping_address["state_details"] = (
            frappe.db.get_value("State Master", doc.manufacturing_state, ["name", "state_code", "state_name"], as_dict=True)
            if doc.state and frappe.db.exists("State Master", doc.state) else {}
        )

        shipping_address["country_details"] = (
            frappe.db.get_value("Country Master", doc.manufacturing_country, ["name", "country_code", "country_name"], as_dict=True)
            if doc.country and frappe.db.exists("Country Master", doc.country) else {}
        )

        address_details["shipping_address"] = shipping_address

        # Multiple Location Table with master details
        multiple_location_data = []

        for row in doc.multiple_location_table:
            location = row.as_dict()

            location["city_details"] = (
                frappe.db.get_value("City Master", row.ma_city, ["name", "city_code", "city_name"], as_dict=True)
                if row.ma_city and frappe.db.exists("City Master", row.ma_city) else {}
            )

            location["district_details"] = (
                frappe.db.get_value("District Master", row.ma_district, ["name", "district_code", "district_name"], as_dict=True)
                if row.ma_district and frappe.db.exists("District Master", row.ma_district) else {}
            )

            location["state_details"] = (
                frappe.db.get_value("State Master", row.ma_state, ["name", "state_code", "state_name"], as_dict=True)
                if row.ma_state and frappe.db.exists("State Master", row.ma_state) else {}
            )

            location["country_details"] = (
                frappe.db.get_value("Country Master", row.ma_country, ["name", "country_code", "country_name"], as_dict=True)
                if row.ma_country and frappe.db.exists("Country Master", row.ma_country) else {}
            )

            multiple_location_data.append(location)

        # Set to address_details
        address_details["multiple_location_table"] = multiple_location_data

        # child table data   
        # address_details["multiple_location_table"] = [
        #     row.as_dict() for row in doc.multiple_location_table
        # ]
        
        # attach field
        if doc.address_proofattachment:
            file_doc = frappe.get_doc("File", {"file_url": doc.address_proofattachment})
            address_details["address_proofattachment"] = {
                "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
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
            "msme_registered", "msme_enterprise_type", "udyam_number", "name_on_udyam_certificate", "iec", "trc_certificate_no"
        ]

        document_details = {field: legal_doc.get(field) for field in legal_fields}

        # Attach fields
        for field in ["pan_proof", "entity_proof", "msme_proof", "iec_proof", "form_10f_proof", "trc_certificate", "pe_certificate"]:
            file_url = legal_doc.get(field)
            if file_url:
                file_doc = frappe.get_doc("File", {"file_url": file_url})
                document_details[field] = {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
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
        company_gst_table = []
        for row in legal_doc.gst_table:
            gst_row = row.as_dict()
            gst_row["state_details"] = (
                frappe.db.get_value("State Master", row.gst_state, ["name", "state_code", "state_name"], as_dict=True)
                if row.gst_state and frappe.db.exists("State Master", row.gst_state) else {}
            )
            if row.gst_document:
                file_doc = frappe.get_doc("File", {"file_url": row.gst_document})
                gst_row["gst_document"] = {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
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
        ven_onb_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        if ven_onb_doc.vendor_company_details:
            vendor_company_detail = ven_onb_doc.vendor_company_details[0]
            
            if vendor_company_detail.vendor_company_details:
                company_detail_doc = frappe.get_doc("Vendor Onboarding Company Details", vendor_company_detail.vendor_company_details)
                target_company = company_detail_doc.company_name
                
                for gst_row in gst_table:
                    if hasattr(legal_doc, 'gst_table'):
                        for original_gst_row in legal_doc.gst_table:
                            if (hasattr(original_gst_row, 'company') and 
                                original_gst_row.company == target_company and 
                                original_gst_row.name == gst_row.get('name')):
                                company_gst_table.append(gst_row)
                                break

        document_details["company_gst_table"] = company_gst_table




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
            "type_of_account", "currency", "rtgs", "neft", "ift"
        ]
        payment_details = {field: payment_doc.get(field) for field in payment_fields}

        payment_details["bank_name_details"] = (
                frappe.db.get_value(
                    "Bank Master",
                    payment_doc.bank_name,
                    ["name", "bank_code", "country", "description"],
                    as_dict=True
                ) if payment_doc.bank_name and frappe.db.exists("Bank Master", payment_doc.bank_name) else {}
            )

        # bank proof and bank proof by purchase team
        if payment_doc.bank_proof:
            file_doc = frappe.get_doc("File", {"file_url": payment_doc.bank_proof})
            payment_details["bank_proof"] = {
                "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                "name": file_doc.name,
                "file_name": file_doc.file_name
            }
        else:
            payment_details["bank_proof"] = {
                "url": "",
                "name": "",
                "file_name": ""
            }

        if payment_doc.bank_proof_by_purchase_team:
            file_doc = frappe.get_doc("File", {"file_url": payment_doc.bank_proof_by_purchase_team})
            payment_details["bank_proof_by_purchase_team"] = {
                "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                "name": file_doc.name,
                "file_name": file_doc.file_name
            }
        else:
            payment_details["bank_proof_by_purchase_team"] = {
                "url": "",
                "name": "",
                "file_name": ""
            }

        if payment_doc.country:
            payment_details["address"] = {
                "country": payment_doc.country
            }
        else:
            payment_details["address"] = {
                "country": ""
            }

        # international bank details and intermediate bank details
        international_bank_details = []

        for row in payment_doc.international_bank_details:
            bank_row = row.as_dict()
            
            if row.bank_proof_for_beneficiary_bank:
                file_doc = frappe.get_doc("File", {"file_url": row.bank_proof_for_beneficiary_bank})
                bank_row["bank_proof_for_beneficiary_bank"] = {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                }
            else:
                bank_row["bank_proof_for_beneficiary_bank"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }

            if row.international_bank_proof_by_purchase_team:
                file_doc = frappe.get_doc("File", {"file_url": row.international_bank_proof_by_purchase_team})
                bank_row["international_bank_proof_by_purchase_team"] = {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                }
            else:
                bank_row["international_bank_proof_by_purchase_team"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }
            
            international_bank_details.append(bank_row)

        payment_details["international_bank_details"] = international_bank_details

        # Intermediate Bank details
        intermediate_bank_details = []

        for row in payment_doc.intermediate_bank_details:
            bank_row = row.as_dict()
            
            if row.bank_proof_for_intermediate_bank:
                file_doc = frappe.get_doc("File", {"file_url": row.bank_proof_for_intermediate_bank})
                bank_row["bank_proof_for_intermediate_bank"] = {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                }
            else:
                bank_row["bank_proof_for_intermediate_bank"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }

            if row.intermediate_bank_proof_by_purchase_team:
                file_doc = frappe.get_doc("File", {"file_url": row.intermediate_bank_proof_by_purchase_team})
                bank_row["intermediate_bank_proof_by_purchase_team"] = {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                }
            else:
                bank_row["intermediate_bank_proof_by_purchase_team"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }
            
            intermediate_bank_details.append(bank_row)

        payment_details["intermediate_bank_details"] = intermediate_bank_details

        # Multiple Attachments for Bank proofs by Purchase Team
        bank_proofs_by_purchase_team = []
        for row in payment_doc.bank_proofs_by_purchase_team:
            if row.attachment_name:
                file_doc = frappe.get_doc("File", {"file_url": row.attachment_name})
                bank_proofs_by_purchase_team.append({
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                })
            else:
                bank_proofs_by_purchase_team.append({
                    "url": "",
                    "name": "",
                    "file_name": ""
                })
        payment_details["bank_proofs_by_purchase_team"] = bank_proofs_by_purchase_team

        # International Bank Proofs by Purchase Team
        international_bank_proofs_by_purchase_team = []
        for row in payment_doc.international_bank_proofs_by_purchase_team:
            if row.attachment_name:
                file_doc = frappe.get_doc("File", {"file_url": row.attachment_name})
                international_bank_proofs_by_purchase_team.append({
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                })
            else:
                international_bank_proofs_by_purchase_team.append({
                    "url": "",
                    "name": "",
                    "file_name": ""
                })
        payment_details["international_bank_proofs_by_purchase_team"] = international_bank_proofs_by_purchase_team

        # Intermediate Bank Proofs by Purchase Team
        intermediate_bank_proofs_by_purchase_team = []
        for row in payment_doc.intermediate_bank_proofs_by_purchase_team:
            if row.attachment_name:
                file_doc = frappe.get_doc("File", {"file_url": row.attachment_name})
                intermediate_bank_proofs_by_purchase_team.append({
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                })
            else:
                intermediate_bank_proofs_by_purchase_team.append({
                    "url": "",
                    "name": "",
                    "file_name": ""
                })
        payment_details["intermediate_bank_proofs_by_purchase_team"] = intermediate_bank_proofs_by_purchase_team


        if ven_onb_doc.form_fully_submitted_by_vendor==1 and ven_onb_doc.onboarding_form_status == "Pending" and ven_onb_doc.purchase_team_undertaking == 0:
            payment_details["bank_proof_upload_status"] = 1

        elif ven_onb_doc.form_fully_submitted_by_vendor==1 and ven_onb_doc.register_by_account_team==1 and ven_onb_doc.onboarding_form_status == "Pending" and ven_onb_doc.accounts_team_undertaking == 0:
            payment_details["bank_proof_upload_status"] = 1

        else:
            payment_details["bank_proof_upload_status"] = 0

        #----------contact details tab-----------------

        ven_onb_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        contact_details = [row.as_dict() for row in ven_onb_doc.contact_details]
        vendor_type_list = []
        
        for row in ven_onb_doc.vendor_types:
            vendor_type_list.append(row.vendor_type)

        company_details["vendor_types"] = vendor_type_list


        multi_company_name = []
        
        registered_for_multi_companies =  ven_onb_doc.registered_for_multi_companies
        if ven_onb_doc.registered_for_multi_companies == 1:

            multi_company = [row.as_dict() for row in ven_onb_doc.multiple_company]
            multi_company_name.extend(multi_company)


        #------------Manufacturing details tab------------------

        manuf_docname = frappe.db.get_value("Vendor Onboarding Manufacturing Details", {
            "vendor_onboarding": vendor_onboarding, "ref_no": ref_no
        }, "name")

        if not manuf_docname:
            return {
                "status": "error", 
                "message": "No matching Manufacturing Details record found."
            }

        manuf_doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", manuf_docname)

        manuf_fields = [
            "total_godown", "storage_capacity", "spare_capacity", "type_of_premises", "working_hours",
            "weekly_holidays", "number_of_manpower", "annual_revenue", "cold_storage"
        ]

        manuf_details = {field: manuf_doc.get(field) for field in manuf_fields}

        materials_supplied = []
        for row in manuf_doc.materials_supplied:
            row_data = row.as_dict()
            if row.material_images:
                file_doc = frappe.get_doc("File", {"file_url": row.material_images})
                row_data["material_images"] = {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                }
            else:
                row_data["material_images"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }
            materials_supplied.append(row_data)

        manuf_details["materials_supplied"] = materials_supplied


        for field in ["brochure_proof", "organisation_structure_document"]:
            file_url = manuf_doc.get(field)
            if file_url:
                file_doc = frappe.get_doc("File", {"file_url": file_url})
                manuf_details[field] = {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name
                }
            else:
                manuf_details[field] = {"url": "", "name": "", "file_name": ""}


        #----------------------Employee Detail Tab--------------------

        number_of_employee = [row.as_dict() for row in ven_onb_doc.number_of_employee]

        #---------------------Machinery Detail--------------------------

        machinery_detail = [row.as_dict() for row in ven_onb_doc.machinery_detail]

        #-------------------testing_detail----------------------------------
        
        testing_detail = [row.as_dict() for row in ven_onb_doc.testing_detail]

        #------------------Reputed partners details--------------------

        reputed_partners = [row.as_dict() for row in ven_onb_doc.reputed_partners]
        
        #----------------Certificate Details ------------------------------

        certificate_docname = frappe.db.get_value("Vendor Onboarding Certificates", {
            "vendor_onboarding": vendor_onboarding, "ref_no": ref_no
        }, "name")

        certificate_details = []

        if certificate_docname:
            certificate_doc = frappe.get_doc("Vendor Onboarding Certificates", certificate_docname)

            for row in certificate_doc.certificates:
                row_data = {
                    "name": row.name,
                    "idx": row.idx,
                    "certificate_code": row.certificate_code,
                    "valid_till": row.valid_till
                }

                if row.certificate_attach:
                    file_doc = frappe.get_doc("File", {"file_url": row.certificate_attach})
                    row_data["certificate_attach"] = {
                        "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                        "name": file_doc.name,
                        "file_name": file_doc.file_name
                    }
                else:
                    row_data["certificate_attach"] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }

                certificate_details.append(row_data)
        else:
            certificate_details = []

        #------------------purchasing Details ------------------------------
        
        # purchasing_details = []

        # if vendor_onboarding:
        #     vonb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        #     pur_data = {
        #     "company_name" : vonb.company_name or None,
        #     "purchase_organization" : vonb.purchase_organization or None,
        #     "order_currency" : vonb.order_currency or None,
        #     "terms_of_payment": vonb.terms_of_payment or None,
        #     "purchase_group" : vonb.purchase_group or None,
        #     "account_group" : vonb.account_group or None,
        #     "reconciliation_account" : vonb.reconciliation_account or None,
        #     "qa_team_remarks" : vonb.qa_team_remarks or None,
        #     "purchase_team_remarks" : vonb.purchase_team_approval_remarks or None,
        #     "purchase_head_remarks" : vonb.purchase_head_approval_remarks or None,
        #     "account_team_remarks": vonb.accounts_team_approval_remarks or None,
        #     "incoterms" : vonb.incoterms or None,
        #     }
        # else :
        #      pur_data = {
        #     "company_name" : "",
        #     "purchase_organization" : "",
        #     "order_currency" : "",
        #     "terms_of_payment": "",
        #     "purchase_group" : "",
        #     "account_group" : "",
        #     "reconciliation_account" : "",
        #     "qa_team_remarks" : "",
        #     "purchase_team_remarks" : "",
        #     "purchase_head_remarks" : "",
        #     "incoterms" : "",
        #     }
        # purchasing_details.append(pur_data)

        purchasing_details = []

        if vendor_onboarding:
            vonb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

            pur_data = {
                "company_name": vonb.company_name or None,
                "purchase_organization": vonb.purchase_organization or None,
                "order_currency": vonb.order_currency or None,
                "terms_of_payment": vonb.terms_of_payment or None,
                "purchase_group": vonb.purchase_group or None,
                "account_group": vonb.account_group or None,
                "reconciliation_account": vonb.reconciliation_account or None,
                "qa_team_remarks": vonb.qa_team_remarks or None,
                "purchase_team_remarks": vonb.purchase_team_approval_remarks or None,
                "purchase_head_remarks": vonb.purchase_head_approval_remarks or None,
                "account_team_remarks": vonb.accounts_team_approval_remarks or None,
                "account_head_remarks": vonb.accounts_head_approval_remarks or None,
                "incoterms": vonb.incoterms or None,
            }

            pur_data["company_details"] = (
                frappe.db.get_value(
                    "Company Master",
                    vonb.company_name,
                    ["name", "company_code", "company_name", "description"],
                    as_dict=True
                ) if vonb.company_name and frappe.db.exists("Company Master", vonb.company_name) else {}
            )

            pur_data["pur_org_details"] = (
                frappe.db.get_value(
                    "Purchase Organization Master",
                    vonb.purchase_organization,
                    ["name", "purchase_organization_code", "purchase_organization_name", "description"],
                    as_dict=True
                ) if vonb.purchase_organization and frappe.db.exists("Purchase Organization Master", vonb.purchase_organization) else {}
            )

            pur_data["currency_details"] = (
                frappe.db.get_value(
                    "Currency Master",
                    vonb.order_currency,
                    ["name", "currency_code", "currency_name", "country"],
                    as_dict=True
                ) if vonb.order_currency and frappe.db.exists("Currency Master", vonb.order_currency) else {}
            )

            pur_data["term_payment_details"] = (
                frappe.db.get_value(
                    "Terms of Payment Master",
                    vonb.terms_of_payment,
                    ["name", "terms_of_payment_code", "terms_of_payment_name", "description"],
                    as_dict=True
                ) if vonb.terms_of_payment and frappe.db.exists("Terms of Payment Master", vonb.terms_of_payment) else {}
            )

            pur_data["pur_group_details"] = (
                frappe.db.get_value(
                    "Purchase Group Master",
                    vonb.purchase_group,
                    ["name", "purchase_group_code", "purchase_group_name", "description"],
                    as_dict=True
                ) if vonb.purchase_group and frappe.db.exists("Purchase Group Master", vonb.purchase_group) else {}
            )

            pur_data["account_group_details"] = (
                frappe.db.get_value(
                    "Account Group Master",
                    vonb.account_group,
                    ["name", "account_group_code", "account_group_name", "account_group_description"],
                    as_dict=True
                ) if vonb.account_group and frappe.db.exists("Account Group Master", vonb.account_group) else {}
            )

            pur_data["reconciliation_details"] = (
                frappe.db.get_value(
                    "Reconciliation Account",
                    vonb.reconciliation_account,
                    ["name", "reconcil_account_code", "reconcil_account", "reconcil_description"],
                    as_dict=True
                ) if vonb.reconciliation_account and frappe.db.exists("Reconciliation Account", vonb.reconciliation_account) else {}
            )

        else:
            pur_data = {
                "company_name": "",
                "purchase_organization": "",
                "order_currency": "",
                "terms_of_payment": "",
                "purchase_group": "",
                "account_group": "",
                "reconciliation_account": "",
                "qa_team_remarks": "",
                "purchase_team_remarks": "",
                "purchase_head_remarks": "",
                "account_team_remarks": "",
                "incoterms": "",
                "company_details": {},
                "pur_org_details": {},
                "term_payment_details": {},
                "pur_group_details": {},
                "account_group_details": {},
                "reconciliation_details": {}
            }

        purchasing_details.append(pur_data)


        # Return the check box from vendor onboarding doctype 
        validation_check = {}
    
        # check_box_fields = ["mandatory_data_filled", "register_by_account_team", "form_fully_submitted_by_vendor", "purchase_team_undertaking",
        #         "purchase_head_undertaking", "accounts_team_undertaking", "accounts_head_undertaking"]

        check_box_fields = ["mandatory_data_filled", "register_by_account_team", "form_fully_submitted_by_vendor", "purchase_team_undertaking",
                            "purchase_head_undertaking", "accounts_team_undertaking", "accounts_head_undertaking", "is_amendment"]

        validation_check = {field: vonb.get(field) for field in check_box_fields}

        if vonb.register_by_account_team == 0:
            if vonb.mail_sent_to_purchase_team:
                validation_check.update({
                    "is_purchase_approve": 1,
                    "is_purchase_head_approve": 0,
                    "is_accounts_team_approve": 0,
                    "is_accounts_head_approve": 0
                })

            if vonb.mail_sent_to_purchase_head and vonb.mail_sent_to_purchase_team:
                validation_check.update({
                    "is_purchase_approve": 0,
                    "is_purchase_head_approve": 1,
                    "is_accounts_team_approve": 0,
                    "is_accounts_head_approve": 0
                })

            if vonb.mail_sent_to_account_team and vonb.mail_sent_to_purchase_head and vonb.mail_sent_to_purchase_team:
                validation_check.update({
                    "is_purchase_approve": 0,
                    "is_purchase_head_approve": 0,
                    "is_accounts_team_approve": 1,
                    "is_accounts_head_approve": 0
                })
            if vonb.accounts_team_undertaking and vonb.mail_sent_to_account_team and vonb.mail_sent_to_purchase_head and vonb.mail_sent_to_purchase_team:
                validation_check.update({
                    "is_purchase_approve": 0,
                    "is_purchase_head_approve": 0,
                    "is_accounts_team_approve": 0,
                    "is_accounts_head_approve": 0
                })
            else:
                pass
        
        elif vonb.register_by_account_team == 1:
            if vonb.mail_sent_to_account_team:
                validation_check.update({
                    "is_purchase_approve": 0,
                    "is_purchase_head_approve": 0,
                    "is_accounts_team_approve": 1,
                    "is_accounts_head_approve": 0
                })

            if vonb.mail_sent_to_account_head and vonb.mail_sent_to_account_team:
                validation_check.update({
                    "is_purchase_approve": 0,
                    "is_purchase_head_approve": 0,
                    "is_accounts_team_approve": 0,
                    "is_accounts_head_approve": 1
                })
            
            if vonb.accounts_head_undertaking and vonb.mail_sent_to_account_head and vonb.mail_sent_to_account_team:
                validation_check.update({
                    "is_purchase_approve": 0,
                    "is_purchase_head_approve": 0,
                    "is_accounts_team_approve": 0,
                    "is_accounts_head_approve": 0
                })
            
            else:
                pass

        else:
            pass

        return {
            "status": "success",
            "message": "Vendor onboarding company and address details fetched successfully.",
            "onboarding_form_status": vonb.onboarding_form_status,
            "company_details_tab": company_details,
            "company_address_tab": address_details,
            "document_details_tab": document_details,
            "payment_details_tab": payment_details,
            "contact_details_tab": contact_details,
            "manufacturing_details_tab": manuf_details,
            "employee_details_tab": number_of_employee,
            "machinery_details_tab": machinery_detail,
            "testing_details_tab": testing_detail,
            "reputed_partners_details_tab": reputed_partners,
            "certificate_details_tab": certificate_details,
            "purchasing_details": purchasing_details,
            "validation_check": validation_check,
            "is_multi_company":registered_for_multi_companies,
            "multi_company_data": multi_company_name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Company Details Fetch Error")
        return {
            "status": "error",
            "message": "Failed to fetch vendor onboarding company details.",
            "error": str(e)
        }
