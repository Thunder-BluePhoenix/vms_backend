import frappe

@frappe.whitelist()
def get_full_data_of_import_vendors(refno=None, via_data_import=None, company=None):
    try:
        if not refno and not company:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Missing required parameter: 'refno' or 'company'."
            }

        docname = frappe.db.get_value("Vendor Master", {"name": refno, "via_data_import": via_data_import}, "name")

        if not docname:
            return {
                "status": "error",
                "message": f"No Vendor Master found for refno: {refno}"
            }

        vendor_master = frappe.get_doc("Vendor Master", docname)

        vendor_master_fields = [
            "vendor_title",
            "vendor_name",
            "office_email_primary",
            "search_term",
            "country",
            "mobile_number",
            "office_email_secondary",
            "registered_date",
            "service_provider_type",
            "registered_by",
            "via_data_import"
        ]

        vendor_details = {field: vendor_master.get(field) for field in vendor_master_fields}

        vendor_details["vendor_types"] = [
            row.vendor_type for row in vendor_master.vendor_types
        ] if vendor_master.vendor_types else []

        vendor_details["multiple_company_data"] = [
            row.as_dict() for row in vendor_master.multiple_company_data
        ] if vendor_master.multiple_company_data else []


        #------------------------------------- Payment details tab ------------------------------
        payment_details = {} 

        if vendor_master.bank_details:

            payment_doc = frappe.get_doc("Vendor Bank Details", vendor_master.bank_details)

            payment_fields = [
            "country" ,"company_pan_number", "bank_name", "ifsc_code", "account_number", "name_of_account_holder", "bank_key",
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
                try:
                    if frappe.db.exists("File", {"file_url": payment_doc.bank_proof}):
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
                except Exception as e:
                    frappe.log_error(f"Error fetching bank_proof file: {str(e)}")
                    payment_details["bank_proof"] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }
            else:
                payment_details["bank_proof"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }


            if payment_doc.bank_proof_by_purchase_team:
                try:
                    if frappe.db.exists("File", {"file_url": payment_doc.bank_proof_by_purchase_team}):
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
                except Exception as e:
                    frappe.log_error(f"Error fetching bank_proof_by_purchase_team file: {str(e)}")
                    payment_details["bank_proof_by_purchase_team"] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }
            else:
                payment_details["bank_proof_by_purchase_team"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }

            # international bank details and intermediate bank details
            international_bank_details = []

            for row in payment_doc.international_bank_details:
                bank_row = row.as_dict()
                
                if row.bank_proof_for_beneficiary_bank:
                    try:
                        if frappe.db.exists("File", {"file_url": row.bank_proof_for_beneficiary_bank}):
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
                    except Exception as e:
                        frappe.log_error(f"Error fetching bank_proof_for_beneficiary_bank: {str(e)}")
                        bank_row["bank_proof_for_beneficiary_bank"] = {
                            "url": "",
                            "name": "",
                            "file_name": ""
                        }
                else:
                    bank_row["bank_proof_for_beneficiary_bank"] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }

                if row.international_bank_proof_by_purchase_team:
                    try:
                        if frappe.db.exists("File", {"file_url": row.international_bank_proof_by_purchase_team}):
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
                    except Exception as e:
                        frappe.log_error(f"Error fetching international_bank_proof_by_purchase_team: {str(e)}")
                        bank_row["international_bank_proof_by_purchase_team"] = {
                            "url": "",
                            "name": "",
                            "file_name": ""
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
                    try:
                        if frappe.db.exists("File", {"file_url": row.bank_proof_for_intermediate_bank}):
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
                    except Exception as e:
                        frappe.log_error(f"Error fetching bank_proof_for_intermediate_bank: {str(e)}")
                        bank_row["bank_proof_for_intermediate_bank"] = {
                            "url": "",
                            "name": "",
                            "file_name": ""
                        }
                else:
                    bank_row["bank_proof_for_intermediate_bank"] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }

                if row.intermediate_bank_proof_by_purchase_team:
                    try:
                        if frappe.db.exists("File", {"file_url": row.intermediate_bank_proof_by_purchase_team}):
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
                    except Exception as e:
                        frappe.log_error(f"Error fetching intermediate_bank_proof_by_purchase_team: {str(e)}")
                        bank_row["intermediate_bank_proof_by_purchase_team"] = {
                            "url": "",
                            "name": "",
                            "file_name": ""
                        }
                else:
                    bank_row["intermediate_bank_proof_by_purchase_team"] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }
                
                intermediate_bank_details.append(bank_row)

            payment_details["intermediate_bank_details"] = intermediate_bank_details
        
        # --------------------------- Legal Documents details -------------------------------
        
        document_details = {}

        if vendor_master.document_details:
            legal_doc = frappe.get_doc("Vendor Document Details", vendor_master.document_details)

        legal_fields = [
            "company_pan_number", "name_on_company_pan", "enterprise_registration_number",
            "msme_registered", "msme_enterprise_type", "udyam_number", "name_on_udyam_certificate", "iec", "trc_certificate_no"
        ]

        document_details = {field: legal_doc.get(field) for field in legal_fields}

        # Attach fields
        for field in ["pan_proof", "entity_proof", "msme_proof", "iec_proof", "form_10f_proof", "trc_certificate", "pe_certificate"]:
            file_url = legal_doc.get(field)
            if file_url:
                try:
                    if frappe.db.exists("File", {"file_url": file_url}):
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
                except Exception as e:
                    frappe.log_error(f"Error fetching file for field '{field}': {str(e)}")
                    document_details[field] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
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
                try:
                    if frappe.db.exists("File", {"file_url": row.gst_document}):
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
                except Exception as e:
                    frappe.log_error(f"Error fetching GST document for GSTIN '{row.gstin}': {str(e)}")
                    gst_row["gst_document"] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }
            else:
                gst_row["gst_document"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }

            gst_table.append(gst_row)

        document_details["gst_table"] = gst_table

        # ---------------------------------------------- Manufacturing Details -------------------------------------------
        
        manuf_details = {}
        if vendor_master.manufacturing_details:

            manuf_doc = frappe.get_doc("Vendor Manufacturing Details", vendor_master.manufacturing_details)

            manuf_fields = [
                "details_of_product_manufactured", "total_godown", "storage_capacity", "spare_capacity", "type_of_premises", "working_hours",
                "weekly_holidays", "number_of_manpower", "annual_revenue", "cold_storage", "cold_storage"
            ]

            manuf_details = {field: manuf_doc.get(field) for field in manuf_fields}

            materials_supplied = []

            for row in manuf_doc.materials_supplied:
                row_data = row.as_dict()

                if row.material_images:
                    try:
                        if frappe.db.exists("File", {"file_url": row.material_images}):
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
                    except Exception as e:
                        frappe.log_error(f"Error fetching material_images for materials_supplied: {str(e)}")
                        row_data["material_images"] = {
                            "url": "",
                            "name": "",
                            "file_name": ""
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
                    try:
                        if frappe.db.exists("File", {"file_url": file_url}):
                            file_doc = frappe.get_doc("File", {"file_url": file_url})
                            manuf_details[field] = {
                                "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                                "name": file_doc.name,
                                "file_name": file_doc.file_name
                            }
                        else:
                            manuf_details[field] = {
                                "url": "",
                                "name": "",
                                "file_name": ""
                            }
                    except Exception as e:
                        frappe.log_error(f"Error fetching file for '{field}': {str(e)}")
                        manuf_details[field] = {
                            "url": "",
                            "name": "",
                            "file_name": ""
                        }
                else:
                    manuf_details[field] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }

        #----------------------------------------------- Company Details -----------------------------------

        company_details = {}
        address_details = {}

        if vendor_master.vendor_company_details:
            for row in vendor_master.vendor_company_details:
                if row.meril_company_name == company:

                    docname = row.vendor_company_details

                    if not docname:
                        return {
                            "status": "error",
                            "message": f"Vendor Onboarding Company Details not found for name: {row.vendor_company_details}, company: {company}"
                        }

                    doc = frappe.get_doc("Vendor Onboarding Company Details", docname)

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
  
                    # attach field
                    if doc.address_proofattachment:
                        try:
                            if frappe.db.exists("File", {"file_url": doc.address_proofattachment}):
                                file_doc = frappe.get_doc("File", {"file_url": doc.address_proofattachment})
                                address_details["address_proofattachment"] = {
                                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                                    "name": file_doc.name,
                                    "file_name": file_doc.file_name
                                }
                            else:
                                address_details["address_proofattachment"] = {
                                    "url": "",
                                    "name": "",
                                    "file_name": ""
                                }
                        except Exception as e:
                            frappe.log_error(f"Error fetching address_proofattachment: {str(e)}")
                            address_details["address_proofattachment"] = {
                                "url": "",
                                "name": "",
                                "file_name": ""
                            }
                    else:
                        address_details["address_proofattachment"] = {
                            "url": "",
                            "name": "",
                            "file_name": ""
                        }

        return {
            "status": "success",
            "vendor_details_tab": vendor_details,
            "payment_details_tab": payment_details,
            "document_details_tab": document_details,
            "manufacturing_details_tab": manuf_details,
            "company_details_tab": company_details,
            "address_details_tab": address_details
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_full_data_of_import_vendors")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": "An unexpected error occurred while fetching vendor data.",
            "error": str(e)
        }
