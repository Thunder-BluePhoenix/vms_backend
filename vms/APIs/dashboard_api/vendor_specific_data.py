import frappe
import json
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_vendor_comprehensive_data(v_id):
    """
    Comprehensive API to fetch vendor data with all linked records
    
    Parameters:
    - v_id: Vendor Master document name (e.g., "V-25000001")
    
    Returns:
    - Complete vendor data with all linked records and child tables
    """
    
    try:
        if not v_id:
            return {
                "status": "error",
                "message": "Vendor ID (v_id) is required"
            }
        
        # Check if vendor exists
        if not frappe.db.exists("Vendor Master", v_id):
            return {
                "status": "error", 
                "message": f"Vendor with ID '{v_id}' not found"
            }
        
        # Get main vendor master document
        vendor_doc = frappe.get_doc("Vendor Master", v_id)
        
        # Build comprehensive response
        response = {
            "status": "success",
            "message": "Vendor data retrieved successfully",
            "vendor_id": v_id,
            "data": {
                "vendor_master": _build_vendor_master_data(vendor_doc),
                "multiple_company_data": _fetch_multiple_company_data(vendor_doc),
                "vendor_types": _fetch_vendor_types_data(vendor_doc),
                "bank_details": _fetch_bank_details_data(v_id),
                "document_details": _fetch_document_details_data(v_id),
                "manufacturing_details": _fetch_manufacturing_details_data(v_id),
                "onboarding_records": _fetch_onboarding_records_data(vendor_doc),
                "annual_assessment_records": _fetch_annual_assessment_records(vendor_doc)
            }
        }
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_comprehensive_data API: {str(e)}", "Vendor API Error")
        return {
            "status": "error",
            "message": f"Failed to fetch vendor data: {str(e)}"
        }


def _build_vendor_master_data(vendor_doc):
    """Build vendor master basic data with linked field details"""
    
    vendor_data = vendor_doc.as_dict()
    
    # Fetch linked field data
    linked_fields_data = {}
    
    # Vendor Title Link
    if vendor_doc.vendor_title:
        try:
            vendor_title_doc = frappe.get_doc("Vendor Title", vendor_doc.vendor_title)
            linked_fields_data["vendor_title_details"] = vendor_title_doc.as_dict()
        except:
            linked_fields_data["vendor_title_details"] = None
    
    # Country Link
    if vendor_doc.country:
        try:
            country_doc = frappe.get_doc("Country Master", vendor_doc.country)
            linked_fields_data["country_details"] = country_doc.as_dict()
        except:
            linked_fields_data["country_details"] = None
    
    # Service Provider Type Link
    if vendor_doc.service_provider_type:
        try:
            service_type_doc = frappe.get_doc("Service Provider Type Master", vendor_doc.service_provider_type)
            linked_fields_data["service_provider_type_details"] = service_type_doc.as_dict()
        except:
            linked_fields_data["service_provider_type_details"] = None
    
    vendor_data["linked_fields"] = linked_fields_data
    return vendor_data


def _fetch_multiple_company_data(vendor_doc):
    """Fetch multiple company data with all linked field details"""
    
    company_data_list = []
    
    for company_row in vendor_doc.multiple_company_data:
        company_data = company_row.as_dict()
        
        # Fetch linked field details for each company row
        linked_data = {}
        
        # Company Name Link
        if company_row.company_name:
            try:
                company_doc = frappe.get_doc("Company Master", company_row.company_name)
                linked_data["company_details"] = company_doc.as_dict()
            except:
                linked_data["company_details"] = None
        
        # Purchase Organization Link
        if company_row.purchase_organization:
            try:
                po_doc = frappe.get_doc("Purchase Organization Master", company_row.purchase_organization)
                linked_data["purchase_organization_details"] = po_doc.as_dict()
            except:
                linked_data["purchase_organization_details"] = None
        
        # Account Group Link
        if company_row.account_group:
            try:
                ag_doc = frappe.get_doc("Account Group Master", company_row.account_group)
                linked_data["account_group_details"] = ag_doc.as_dict()
            except:
                linked_data["account_group_details"] = None
        
        # Terms of Payment Link
        if company_row.terms_of_payment:
            try:
                top_doc = frappe.get_doc("Terms of Payment Master", company_row.terms_of_payment)
                linked_data["terms_of_payment_details"] = top_doc.as_dict()
            except:
                linked_data["terms_of_payment_details"] = None
        
        # Purchase Group Link
        if company_row.purchase_group:
            try:
                pg_doc = frappe.get_doc("Purchase Group Master", company_row.purchase_group)
                linked_data["purchase_group_details"] = pg_doc.as_dict()
            except:
                linked_data["purchase_group_details"] = None
        
        # Order Currency Link
        if company_row.order_currency:
            try:
                currency_doc = frappe.get_doc("Currency Master", company_row.order_currency)
                linked_data["order_currency_details"] = currency_doc.as_dict()
            except:
                linked_data["order_currency_details"] = None
        
        # Incoterm Link
        if company_row.incoterm:
            try:
                incoterm_doc = frappe.get_doc("Incoterm Master", company_row.incoterm)
                linked_data["incoterm_details"] = incoterm_doc.as_dict()
            except:
                linked_data["incoterm_details"] = None
        
        # Reconciliation Account Link
        if company_row.reconciliation_account:
            try:
                recon_doc = frappe.get_doc("Reconciliation Account", company_row.reconciliation_account)
                linked_data["reconciliation_account_details"] = recon_doc.as_dict()
            except:
                linked_data["reconciliation_account_details"] = None
        
        # Company Vendor Code Link (This contains child table with vendor codes)
        if company_row.company_vendor_code:
            try:
                cvc_doc = frappe.get_doc("Company Vendor Code", company_row.company_vendor_code)
                cvc_data = cvc_doc.as_dict()
                
                # Get vendor codes child table with state details
                vendor_codes_with_details = []
                for vc_row in cvc_doc.vendor_code:
                    vc_data = vc_row.as_dict()
                    
                    # Fetch state details for each vendor code
                    if vc_row.state:
                        try:
                            state_doc = frappe.get_doc("State Master", vc_row.state)
                            vc_data["state_details"] = state_doc.as_dict()
                        except:
                            vc_data["state_details"] = None
                    
                    vendor_codes_with_details.append(vc_data)
                
                cvc_data["vendor_codes_with_details"] = vendor_codes_with_details
                linked_data["company_vendor_code_details"] = cvc_data
            except:
                linked_data["company_vendor_code_details"] = None
        
        company_data["linked_fields"] = linked_data
        company_data_list.append(company_data)
    
    return company_data_list


def _fetch_vendor_types_data(vendor_doc):
    """Fetch vendor types data with linked vendor type master details"""
    
    vendor_types_list = []
    
    for vt_row in vendor_doc.vendor_types:
        vt_data = vt_row.as_dict()
        
        # Fetch vendor type master details
        if vt_row.vendor_type:
            try:
                vtm_doc = frappe.get_doc("Vendor Type Master", vt_row.vendor_type)
                vt_data["vendor_type_details"] = vtm_doc.as_dict()
            except:
                vt_data["vendor_type_details"] = None
        
        vendor_types_list.append(vt_data)
    
    return vendor_types_list


def _fetch_bank_details_data(v_id):
    """Fetch all bank details records linked to vendor"""
    
    bank_details_list = []
    
    # Get all vendor bank details records for this vendor
    bank_records = frappe.get_all(
        "Vendor Bank Details",
        filters={"ref_no": v_id},
        fields=["name"]
    )
    
    for bank_record in bank_records:
        try:
            bank_doc = frappe.get_doc("Vendor Bank Details", bank_record.name)
            bank_data = bank_doc.as_dict()
            
            # Fetch linked field details
            linked_data = {}
            
            # Bank Name Link
            if bank_doc.bank_name:
                try:
                    bank_master_doc = frappe.get_doc("Bank Master", bank_doc.bank_name)
                    linked_data["bank_name_details"] = bank_master_doc.as_dict()
                except:
                    linked_data["bank_name_details"] = None
            
            # Currency Link
            if bank_doc.currency:
                try:
                    currency_doc = frappe.get_doc("Currency Master", bank_doc.currency)
                    linked_data["currency_details"] = currency_doc.as_dict()
                except:
                    linked_data["currency_details"] = None
            
            # Country Link
            if bank_doc.country:
                try:
                    country_doc = frappe.get_doc("Country Master", bank_doc.country)
                    linked_data["country_details"] = country_doc.as_dict()
                except:
                    linked_data["country_details"] = None
            
            bank_data["linked_fields"] = linked_data
            
            # Process child tables with their linked fields
            
            # Banker Details Child Table
            banker_details_with_links = []
            for banker_row in bank_doc.banker_details:
                banker_data = banker_row.as_dict()
                # Add any linked field processing for banker details if needed
                banker_details_with_links.append(banker_data)
            bank_data["banker_details_processed"] = banker_details_with_links
            
            # International Bank Details Child Table  
            intl_bank_details_with_links = []
            for intl_row in bank_doc.international_bank_details:
                intl_data = intl_row.as_dict()
                # Add any linked field processing for international bank details if needed
                intl_bank_details_with_links.append(intl_data)
            bank_data["international_bank_details_processed"] = intl_bank_details_with_links
            
            # Intermediate Bank Details Child Table
            intermediate_bank_details_with_links = []
            for intermediate_row in bank_doc.intermediate_bank_details:
                intermediate_data = intermediate_row.as_dict()
                # Add any linked field processing for intermediate bank details if needed
                intermediate_bank_details_with_links.append(intermediate_data)
            bank_data["intermediate_bank_details_processed"] = intermediate_bank_details_with_links
            
            bank_details_list.append(bank_data)
            
        except Exception as e:
            frappe.log_error(f"Error fetching bank details {bank_record.name}: {str(e)}", "Bank Details Error")
            continue
    
    return bank_details_list


def _fetch_document_details_data(v_id):
    """Fetch all document details records linked to vendor"""
    
    document_details_list = []
    
    # Get all vendor document details records for this vendor
    doc_records = frappe.get_all(
        "Legal Documents",
        filters={"ref_no": v_id},
        fields=["name"]
    )
    
    for doc_record in doc_records:
        try:
            doc_details_doc = frappe.get_doc("Legal Documents", doc_record.name)
            doc_data = doc_details_doc.as_dict()
            
            # Fetch linked field details
            linked_data = {}
            
            # Country Link
            if doc_details_doc.country:
                try:
                    country_doc = frappe.get_doc("Country Master", doc_details_doc.country)
                    linked_data["country_details"] = country_doc.as_dict()
                except:
                    linked_data["country_details"] = None
            
            doc_data["linked_fields"] = linked_data
            
            # Process child tables with their linked fields
            
            # GST Table Child Table with state details
            gst_table_with_links = []
            for gst_row in doc_details_doc.gst_table:
                gst_data = gst_row.as_dict()
                
                # Fetch state details if state link exists
                if gst_row.gst_state:
                    try:
                        state_doc = frappe.get_doc("State Master", gst_row.gst_state)
                        gst_data["gst_state_details"] = state_doc.as_dict()
                    except:
                        gst_data["gst_state_details"] = None
                
                gst_table_with_links.append(gst_data)
            doc_data["gst_table_processed"] = gst_table_with_links
            
            # Company GST Table Child Table with state details
            company_gst_table_with_links = []
            for company_gst_row in doc_details_doc.company_gst_table:
                company_gst_data = company_gst_row.as_dict()
                
                # Fetch state details if state link exists
                if company_gst_row.gst_state:
                    try:
                        state_doc = frappe.get_doc("State Master", company_gst_row.gst_state)
                        company_gst_data["gst_state_details"] = state_doc.as_dict()
                    except:
                        company_gst_data["gst_state_details"] = None
                
                company_gst_table_with_links.append(company_gst_data)
            doc_data["company_gst_table_processed"] = company_gst_table_with_links
            
            document_details_list.append(doc_data)
            
        except Exception as e:
            frappe.log_error(f"Error fetching document details {doc_record.name}: {str(e)}", "Document Details Error")
            continue
    
    return document_details_list


def _fetch_manufacturing_details_data(v_id):
    """Fetch all manufacturing details records linked to vendor"""
    
    manufacturing_details_list = []
    
    # Get all vendor manufacturing details records for this vendor
    mfg_records = frappe.get_all(
        "Vendor Onboarding Manufacturing Details",
        filters={"ref_no": v_id},
        fields=["name"]
    )
    
    for mfg_record in mfg_records:
        try:
            mfg_doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", mfg_record.name)
            mfg_data = mfg_doc.as_dict()
            
            # Fetch linked field details
            linked_data = {}
            
            # Type of Premises Link (if exists)
            if hasattr(mfg_doc, 'type_of_premises') and mfg_doc.type_of_premises:
                try:
                    premises_doc = frappe.get_doc("Type of Premises Master", mfg_doc.type_of_premises)
                    linked_data["type_of_premises_details"] = premises_doc.as_dict()
                except:
                    linked_data["type_of_premises_details"] = None
            
            mfg_data["linked_fields"] = linked_data
            
            # Process child tables if they exist
            
            # Materials Supplied Child Table
            if hasattr(mfg_doc, 'materials_supplied'):
                materials_with_links = []
                for material_row in mfg_doc.materials_supplied:
                    material_data = material_row.as_dict()
                    # Add any linked field processing for materials if needed
                    materials_with_links.append(material_data)
                mfg_data["materials_supplied_processed"] = materials_with_links
            
            # Employee Details Child Table
            if hasattr(mfg_doc, 'number_of_employee'):
                employee_details_with_links = []
                for emp_row in mfg_doc.number_of_employee:
                    emp_data = emp_row.as_dict()
                    # Add any linked field processing for employee details if needed
                    employee_details_with_links.append(emp_data)
                mfg_data["employee_details_processed"] = employee_details_with_links
            
            # Machinery Details Child Table
            if hasattr(mfg_doc, 'machinery_detail'):
                machinery_details_with_links = []
                for machinery_row in mfg_doc.machinery_detail:
                    machinery_data = machinery_row.as_dict()
                    # Add any linked field processing for machinery details if needed
                    machinery_details_with_links.append(machinery_data)
                mfg_data["machinery_details_processed"] = machinery_details_with_links
            
            # Testing Details Child Table
            if hasattr(mfg_doc, 'testing_detail'):
                testing_details_with_links = []
                for testing_row in mfg_doc.testing_detail:
                    testing_data = testing_row.as_dict()
                    # Add any linked field processing for testing details if needed
                    testing_details_with_links.append(testing_data)
                mfg_data["testing_details_processed"] = testing_details_with_links
            
            # Reputed Partners Child Table
            if hasattr(mfg_doc, 'reputed_partners'):
                partners_details_with_links = []
                for partner_row in mfg_doc.reputed_partners:
                    partner_data = partner_row.as_dict()
                    # Add any linked field processing for reputed partners if needed
                    partners_details_with_links.append(partner_data)
                mfg_data["reputed_partners_processed"] = partners_details_with_links
            
            manufacturing_details_list.append(mfg_data)
            
        except Exception as e:
            frappe.log_error(f"Error fetching manufacturing details {mfg_record.name}: {str(e)}", "Manufacturing Details Error")
            continue
    
    return manufacturing_details_list


def _fetch_onboarding_records_data(vendor_doc):
    """Fetch onboarding records with complete details"""
    
    onboarding_records_list = []
    
    for onb_row in vendor_doc.vendor_onb_records:
        onb_data = onb_row.as_dict()
        
        # Fetch complete onboarding document details
        if onb_row.vendor_onboarding_no:
            try:
                onb_doc = frappe.get_doc("Vendor Onboarding", onb_row.vendor_onboarding_no)
                onb_complete_data = onb_doc.as_dict()
                
                # Process child tables in onboarding document
                
                # Contact Details Child Table
                contact_details_with_links = []
                for contact_row in onb_doc.contact_details:
                    contact_data = contact_row.as_dict()
                    # Add any linked field processing if needed
                    contact_details_with_links.append(contact_data)
                onb_complete_data["contact_details_processed"] = contact_details_with_links
                
                # Number of Employee Child Table
                employee_details_with_links = []
                for emp_row in onb_doc.number_of_employee:
                    emp_data = emp_row.as_dict()
                    # Add any linked field processing if needed
                    employee_details_with_links.append(emp_data)
                onb_complete_data["employee_details_processed"] = employee_details_with_links
                
                # Machinery Details Child Table
                machinery_details_with_links = []
                for machinery_row in onb_doc.machinery_detail:
                    machinery_data = machinery_row.as_dict()
                    # Add any linked field processing if needed
                    machinery_details_with_links.append(machinery_data)
                onb_complete_data["machinery_details_processed"] = machinery_details_with_links
                
                # Testing Details Child Table
                testing_details_with_links = []
                for testing_row in onb_doc.testing_detail:
                    testing_data = testing_row.as_dict()
                    # Add any linked field processing if needed
                    testing_details_with_links.append(testing_data)
                onb_complete_data["testing_details_processed"] = testing_details_with_links
                
                # Reputed Partners Child Table
                partners_details_with_links = []
                for partner_row in onb_doc.reputed_partners:
                    partner_data = partner_row.as_dict()
                    # Add any linked field processing if needed
                    partners_details_with_links.append(partner_data)
                onb_complete_data["reputed_partners_processed"] = partners_details_with_links
                
                # Multiple Company Child Table (if multi-company registration)
                if onb_doc.registered_for_multi_companies:
                    multi_company_details_with_links = []
                    for mc_row in onb_doc.multiple_company:
                        mc_data = mc_row.as_dict()
                        
                        # Fetch company details
                        if mc_row.company:
                            try:
                                company_doc = frappe.get_doc("Company Master", mc_row.company)
                                mc_data["company_details"] = company_doc.as_dict()
                            except:
                                mc_data["company_details"] = None
                        
                        multi_company_details_with_links.append(mc_data)
                    onb_complete_data["multi_company_details_processed"] = multi_company_details_with_links
                
                onb_data["onboarding_complete_details"] = onb_complete_data
                
            except Exception as e:
                frappe.log_error(f"Error fetching onboarding details {onb_row.vendor_onboarding_no}: {str(e)}", "Onboarding Details Error")
                onb_data["onboarding_complete_details"] = None
        
        onboarding_records_list.append(onb_data)
    
    return onboarding_records_list


def _fetch_annual_assessment_records(vendor_doc):
    """Fetch annual assessment form records"""
    
    assessment_records_list = []
    
    for assessment_row in vendor_doc.form_records:
        assessment_data = assessment_row.as_dict()
        
        # Fetch complete assessment document details if needed
        if assessment_row.vendor_annual_assessment_form:
            try:
                assessment_doc = frappe.get_doc("Vendor Annual Assessment Form", assessment_row.vendor_annual_assessment_form)
                assessment_complete_data = assessment_doc.as_dict()
                
                # Process any child tables or linked fields in assessment form if they exist
                assessment_data["assessment_complete_details"] = assessment_complete_data
                
            except Exception as e:
                frappe.log_error(f"Error fetching assessment details {assessment_row.vendor_annual_assessment_form}: {str(e)}", "Assessment Details Error")
                assessment_data["assessment_complete_details"] = None
        
        assessment_records_list.append(assessment_data)
    
    return assessment_records_list


def _fetch_document_details_data(v_id):
    """Fetch all document details records linked to vendor"""
    
    document_details_list = []
    
    # Get all vendor document details records for this vendor
    doc_records = frappe.get_all(
        "Legal Documents",
        filters={"ref_no": v_id},
        fields=["name"]
    )
    
    for doc_record in doc_records:
        try:
            doc_details_doc = frappe.get_doc("Legal Documents", doc_record.name)
            doc_data = doc_details_doc.as_dict()
            
            # Fetch linked field details
            linked_data = {}
            
            # Country Link
            if doc_details_doc.country:
                try:
                    country_doc = frappe.get_doc("Country Master", doc_details_doc.country)
                    linked_data["country_details"] = country_doc.as_dict()
                except:
                    linked_data["country_details"] = None
            
            doc_data["linked_fields"] = linked_data
            
            # Process child tables with their linked fields
            
            # GST Table Child Table with state details
            gst_table_with_links = []
            for gst_row in doc_details_doc.gst_table:
                gst_data = gst_row.as_dict()
                
                # Fetch state details for GST
                if gst_row.gst_state:
                    try:
                        state_doc = frappe.get_doc("State Master", gst_row.gst_state)
                        gst_data["gst_state_details"] = state_doc.as_dict()
                    except:
                        gst_data["gst_state_details"] = None
                
                gst_table_with_links.append(gst_data)
            doc_data["gst_table_processed"] = gst_table_with_links
            
            # Company GST Table Child Table with state details
            company_gst_table_with_links = []
            for company_gst_row in doc_details_doc.company_gst_table:
                company_gst_data = company_gst_row.as_dict()
                
                # Fetch state details for Company GST
                if company_gst_row.gst_state:
                    try:
                        state_doc = frappe.get_doc("State Master", company_gst_row.gst_state)
                        company_gst_data["gst_state_details"] = state_doc.as_dict()
                    except:
                        company_gst_data["gst_state_details"] = None
                
                company_gst_table_with_links.append(company_gst_data)
            doc_data["company_gst_table_processed"] = company_gst_table_with_links
            
            document_details_list.append(doc_data)
            
        except Exception as e:
            frappe.log_error(f"Error fetching document details {doc_record.name}: {str(e)}", "Document Details Error")
            continue
    
    return document_details_list


# Additional helper function for payment details if needed
def _fetch_payment_details_data(v_id):
    """Fetch all payment details records linked to vendor"""
    
    payment_details_list = []
    
    # Get all vendor payment details records for this vendor
    payment_records = frappe.get_all(
        "Vendor Onboarding Payment Details",
        filters={"ref_no": v_id},
        fields=["name"]
    )
    
    for payment_record in payment_records:
        try:
            payment_doc = frappe.get_doc("Vendor Onboarding Payment Details", payment_record.name)
            payment_data = payment_doc.as_dict()
            
            # Fetch linked field details
            linked_data = {}
            
            # Bank Name Link
            if payment_doc.bank_name:
                try:
                    bank_master_doc = frappe.get_doc("Bank Master", payment_doc.bank_name)
                    linked_data["bank_name_details"] = bank_master_doc.as_dict()
                except:
                    linked_data["bank_name_details"] = None
            
            # Currency Link
            if payment_doc.currency:
                try:
                    currency_doc = frappe.get_doc("Currency Master", payment_doc.currency)
                    linked_data["currency_details"] = currency_doc.as_dict()
                except:
                    linked_data["currency_details"] = None
            
            # Country Link
            if payment_doc.country:
                try:
                    country_doc = frappe.get_doc("Country Master", payment_doc.country)
                    linked_data["country_details"] = country_doc.as_dict()
                except:
                    linked_data["country_details"] = None
            
            payment_data["linked_fields"] = linked_data
            
            # Process child tables
            
            # Banker Details Child Table
            banker_details_with_links = []
            for banker_row in payment_doc.banker_details:
                banker_data = banker_row.as_dict()
                banker_details_with_links.append(banker_data)
            payment_data["banker_details_processed"] = banker_details_with_links
            
            # International Bank Details Child Table
            intl_bank_details_with_links = []
            for intl_row in payment_doc.international_bank_details:
                intl_data = intl_row.as_dict()
                intl_bank_details_with_links.append(intl_data)
            payment_data["international_bank_details_processed"] = intl_bank_details_with_links
            
            # Intermediate Bank Details Child Table
            intermediate_bank_details_with_links = []
            for intermediate_row in payment_doc.intermediate_bank_details:
                intermediate_data = intermediate_row.as_dict()
                intermediate_bank_details_with_links.append(intermediate_data)
            payment_data["intermediate_bank_details_processed"] = intermediate_bank_details_with_links
            
            payment_details_list.append(payment_data)
            
        except Exception as e:
            frappe.log_error(f"Error fetching payment details {payment_record.name}: {str(e)}", "Payment Details Error")
            continue
    
    return payment_details_list


# Enhanced API with all related documents
@frappe.whitelist(allow_guest=True)
def get_vendor_complete_ecosystem(v_id):
    """
    Ultra-comprehensive API to fetch vendor and ALL related ecosystem data
    
    Parameters:
    - v_id: Vendor Master document name
    
    Returns:
    - Complete vendor ecosystem including all related documents and their linked fields
    """
    
    try:
        if not v_id:
            return {
                "status": "error",
                "message": "Vendor ID (v_id) is required"
            }
        
        # Check if vendor exists
        if not frappe.db.exists("Vendor Master", v_id):
            return {
                "status": "error",
                "message": f"Vendor with ID '{v_id}' not found"
            }
        
        # Get main vendor master document
        vendor_doc = frappe.get_doc("Vendor Master", v_id)
        
        # Build ultra-comprehensive response
        response = {
            "status": "success",
            "message": "Complete vendor ecosystem data retrieved successfully",
            "vendor_id": v_id,
            "timestamp": frappe.utils.now(),
            "data": {
                # Core vendor data
                "vendor_master": _build_vendor_master_data(vendor_doc),
                "multiple_company_data": _fetch_multiple_company_data(vendor_doc),
                "vendor_types": _fetch_vendor_types_data(vendor_doc),
                
                # Financial & Banking data
                "bank_details": _fetch_bank_details_data(v_id),
                "payment_details": _fetch_payment_details_data(v_id),
                
                # Documentation & Compliance
                "document_details": _fetch_document_details_data(v_id),
                "certificates": _fetch_certificates_data(v_id),
                
                # Operational data
                "manufacturing_details": _fetch_manufacturing_details_data(v_id),
                "company_details": _fetch_company_details_data(v_id),
                
                # Registration & Onboarding
                "onboarding_records": _fetch_onboarding_records_data(vendor_doc),
                "annual_assessment_records": _fetch_annual_assessment_records(vendor_doc),
                
                # Additional linked documents
                "purchase_orders": _fetch_purchase_orders_data(v_id),
                "invoices": _fetch_invoices_data(v_id),
                "sap_logs": _fetch_sap_logs_data(v_id)
            },
            "summary": {
                "total_bank_records": len(_fetch_bank_details_data(v_id)),
                "total_document_records": len(_fetch_document_details_data(v_id)),
                "total_onboarding_records": len(vendor_doc.vendor_onb_records),
                "total_companies": len(vendor_doc.multiple_company_data),
                "vendor_status": vendor_doc.status,
                "onboarding_status": vendor_doc.onboarding_form_status
            }
        }
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_complete_ecosystem API: {str(e)}", "Vendor Ecosystem API Error")
        return {
            "status": "error",
            "message": f"Failed to fetch complete vendor ecosystem: {str(e)}"
        }


def _fetch_certificates_data(v_id):
    """Fetch all certificates records linked to vendor"""
    
    certificates_list = []
    
    # Get all vendor certificates records for this vendor
    cert_records = frappe.get_all(
        "Vendor Onboarding Certificates",
        filters={"ref_no": v_id},
        fields=["name"]
    )
    
    for cert_record in cert_records:
        try:
            cert_doc = frappe.get_doc("Vendor Onboarding Certificates", cert_record.name)
            cert_data = cert_doc.as_dict()
            
            # Process child tables if they exist
            
            # Certificate Details Child Table
            if hasattr(cert_doc, 'certificate_details'):
                cert_details_with_links = []
                for cert_detail_row in cert_doc.certificate_details:
                    cert_detail_data = cert_detail_row.as_dict()
                    
                    # Fetch certificate type details if it's a link field
                    if hasattr(cert_detail_row, 'certificate_type') and cert_detail_row.certificate_type:
                        try:
                            cert_type_doc = frappe.get_doc("Certificate Type Master", cert_detail_row.certificate_type)
                            cert_detail_data["certificate_type_details"] = cert_type_doc.as_dict()
                        except:
                            cert_detail_data["certificate_type_details"] = None
                    
                    cert_details_with_links.append(cert_detail_data)
                cert_data["certificate_details_processed"] = cert_details_with_links
            
            certificates_list.append(cert_data)
            
        except Exception as e:
            frappe.log_error(f"Error fetching certificates {cert_record.name}: {str(e)}", "Certificates Error")
            continue
    
    return certificates_list


def _fetch_company_details_data(v_id):
    """Fetch all company details records linked to vendor"""
    
    company_details_list = []
    
    # Get all vendor company details records for this vendor
    company_records = frappe.get_all(
        "Vendor Onboarding Company Details",
        filters={"ref_no": v_id},
        fields=["name"]
    )
    
    for company_record in company_records:
        try:
            company_doc = frappe.get_doc("Vendor Onboarding Company Details", company_record.name)
            company_data = company_doc.as_dict()
            
            # Fetch linked field details
            linked_data = {}
            
            # Company Name Link
            if company_doc.company_name:
                try:
                    company_master_doc = frappe.get_doc("Company Master", company_doc.company_name)
                    linked_data["company_name_details"] = company_master_doc.as_dict()
                except:
                    linked_data["company_name_details"] = None
            
            # Type of Business Link
            if company_doc.type_of_business:
                try:
                    business_type_doc = frappe.get_doc("Type of Business", company_doc.type_of_business)
                    linked_data["type_of_business_details"] = business_type_doc.as_dict()
                except:
                    linked_data["type_of_business_details"] = None
            
            # Nature of Company Link
            if company_doc.nature_of_company:
                try:
                    nature_doc = frappe.get_doc("Company Nature Master", company_doc.nature_of_company)
                    linked_data["nature_of_company_details"] = nature_doc.as_dict()
                except:
                    linked_data["nature_of_company_details"] = None
            
            company_data["linked_fields"] = linked_data
            
            # Process child tables
            
            # Multiple Location Table Child Table
            if hasattr(company_doc, 'multiple_location_table'):
                location_details_with_links = []
                for location_row in company_doc.multiple_location_table:
                    location_data = location_row.as_dict()
                    
                    # Fetch state details for location
                    if hasattr(location_row, 'state') and location_row.state:
                        try:
                            state_doc = frappe.get_doc("State Master", location_row.state)
                            location_data["state_details"] = state_doc.as_dict()
                        except:
                            location_data["state_details"] = None
                    
                    # Fetch country details for location
                    if hasattr(location_row, 'country') and location_row.country:
                        try:
                            country_doc = frappe.get_doc("Country Master", location_row.country)
                            location_data["country_details"] = country_doc.as_dict()
                        except:
                            location_data["country_details"] = None
                    
                    location_details_with_links.append(location_data)
                company_data["multiple_location_table_processed"] = location_details_with_links
            
            company_details_list.append(company_data)
            
        except Exception as e:
            frappe.log_error(f"Error fetching company details {company_record.name}: {str(e)}", "Company Details Error")
            continue
    
    return company_details_list


def _fetch_purchase_orders_data(v_id):
    """Fetch purchase orders related to vendor"""
    
    try:
        # Get vendor codes first
        vendor_doc = frappe.get_doc("Vendor Master", v_id)
        vendor_codes = []
        
        # Collect all vendor codes from multiple company data
        for company_data_row in vendor_doc.multiple_company_data:
            if company_data_row.company_vendor_code:
                try:
                    cvc_doc = frappe.get_doc("Company Vendor Code", company_data_row.company_vendor_code)
                    for vc_row in cvc_doc.vendor_code:
                        if vc_row.vendor_code:
                            vendor_codes.append(vc_row.vendor_code)
                except:
                    continue
        
        # Fetch purchase orders using vendor codes
        purchase_orders = []
        if vendor_codes:
            po_records = frappe.get_all(
                "Purchase Order",
                filters={"vendor_code": ["in", vendor_codes]},
                fields=["name", "vendor_code", "transaction_date", "status", "grand_total", "currency", "company"],
                limit=50  # Limit for performance
            )
            
            for po_record in po_records:
                po_data = po_record
                
                # Fetch company details for each PO
                if po_record.company:
                    try:
                        company_doc = frappe.get_doc("Company Master", po_record.company)
                        po_data["company_details"] = company_doc.as_dict()
                    except:
                        po_data["company_details"] = None
                
                purchase_orders.append(po_data)
        
        return purchase_orders
        
    except Exception as e:
        frappe.log_error(f"Error fetching purchase orders for vendor {v_id}: {str(e)}", "PO Fetch Error")
        return []


def _fetch_invoices_data(v_id):
    """Fetch invoices related to vendor"""
    
    try:
        # Similar logic to purchase orders - fetch by vendor codes
        vendor_doc = frappe.get_doc("Vendor Master", v_id)
        vendor_codes = []
        
        # Collect all vendor codes
        for company_data_row in vendor_doc.multiple_company_data:
            if company_data_row.company_vendor_code:
                try:
                    cvc_doc = frappe.get_doc("Company Vendor Code", company_data_row.company_vendor_code)
                    for vc_row in cvc_doc.vendor_code:
                        if vc_row.vendor_code:
                            vendor_codes.append(vc_row.vendor_code)
                except:
                    continue
        
        # Fetch invoices using vendor codes (if invoice doctype exists)
        invoices = []
        if vendor_codes:
            try:
                invoice_records = frappe.get_all(
                    "Purchase Invoice",  # Assuming this doctype exists
                    filters={"vendor_code": ["in", vendor_codes]},
                    fields=["name", "vendor_code", "posting_date", "status", "grand_total", "currency"],
                    limit=50
                )
                
                for invoice_record in invoice_records:
                    invoices.append(invoice_record)
                    
            except frappe.DoesNotExistError:
                # Invoice doctype might not exist
                pass
        
        return invoices
        
    except Exception as e:
        frappe.log_error(f"Error fetching invoices for vendor {v_id}: {str(e)}", "Invoice Fetch Error")
        return []


def _fetch_sap_logs_data(v_id):
    """Fetch SAP logs related to vendor"""
    
    try:
        # Get SAP logs where vendor is involved
        sap_logs = frappe.get_all(
            "VMS SAP Logs",
            filters={"vendor_ref_no": v_id},
            fields=["name", "creation", "sap_status", "vendor_code_generated", "company_name"],
            order_by="creation desc",
            limit=20  # Recent logs only
        )
        
        sap_logs_with_details = []
        for log_record in sap_logs:
            try:
                log_doc = frappe.get_doc("VMS SAP Logs", log_record.name)
                log_data = log_doc.as_dict()
                sap_logs_with_details.append(log_data)
            except:
                sap_logs_with_details.append(log_record)
        
        return sap_logs_with_details
        
    except Exception as e:
        frappe.log_error(f"Error fetching SAP logs for vendor {v_id}: {str(e)}", "SAP Logs Fetch Error")
        return []


# Utility API for getting vendor basic info only
@frappe.whitelist(allow_guest=True)
def get_vendor_basic_info(v_id):
    """
    Lightweight API to get basic vendor information without child tables
    
    Parameters:
    - v_id: Vendor Master document name
    
    Returns:
    - Basic vendor information with immediate linked fields only
    """
    
    try:
        if not v_id:
            return {
                "status": "error",
                "message": "Vendor ID (v_id) is required"
            }
        
        # Check if vendor exists
        if not frappe.db.exists("Vendor Master", v_id):
            return {
                "status": "error",
                "message": f"Vendor with ID '{v_id}' not found"
            }
        
        # Get vendor master document
        vendor_doc = frappe.get_doc("Vendor Master", v_id)
        
        # Build basic response with only direct linked fields
        response = {
            "status": "success",
            "message": "Basic vendor data retrieved successfully",
            "vendor_id": v_id,
            "data": {
                "basic_info": {
                    "name": vendor_doc.name,
                    "vendor_name": vendor_doc.vendor_name,
                    "office_email_primary": vendor_doc.office_email_primary,
                    "office_email_secondary": vendor_doc.office_email_secondary,
                    "mobile_number": vendor_doc.mobile_number,
                    "country": vendor_doc.country,
                    "status": vendor_doc.status,
                    "onboarding_form_status": vendor_doc.onboarding_form_status,
                    "registered_date": vendor_doc.registered_date,
                    "creation": vendor_doc.creation,
                    "modified": vendor_doc.modified
                },
                "linked_fields": {
                    "vendor_title_details": _get_linked_doc_safe("Vendor Title", vendor_doc.vendor_title),
                    "country_details": _get_linked_doc_safe("Country Master", vendor_doc.country),
                    "service_provider_type_details": _get_linked_doc_safe("Service Provider Type Master", vendor_doc.service_provider_type)
                },
                "counts": {
                    "total_companies": len(vendor_doc.multiple_company_data),
                    "total_vendor_types": len(vendor_doc.vendor_types),
                    "total_onboarding_records": len(vendor_doc.vendor_onb_records),
                    "total_assessment_records": len(vendor_doc.form_records)
                }
            }
        }
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_basic_info API: {str(e)}", "Vendor Basic Info API Error")
        return {
            "status": "error",
            "message": f"Failed to fetch basic vendor info: {str(e)}"
        }


def _get_linked_doc_safe(doctype, name):
    """Safely fetch linked document"""
    
    if not name:
        return None
    
    try:
        return frappe.get_doc(doctype, name).as_dict()
    except:
        return None


# Quick status check API
@frappe.whitelist(allow_guest=True) 
def get_vendor_status_check(v_id):
    """
    Quick API to check vendor status and basic validation
    
    Parameters:
    - v_id: Vendor Master document name
    
    Returns:
    - Vendor status and validation summary
    """
    
    try:
        if not v_id:
            return {
                "status": "error",
                "message": "Vendor ID (v_id) is required"
            }
        
        # Quick existence check
        vendor_data = frappe.db.get_value(
            "Vendor Master", 
            v_id, 
            ["name", "vendor_name", "status", "onboarding_form_status", "office_email_primary"],
            as_dict=True
        )
        
        if not vendor_data:
            return {
                "status": "error",
                "message": f"Vendor with ID '{v_id}' not found"
            }
        
        # Count related records
        bank_count = frappe.db.count("Vendor Bank Details", {"ref_no": v_id})
        doc_count = frappe.db.count("Legal Documents", {"ref_no": v_id})
        onb_count = frappe.db.count("Vendor Onboarding", {"ref_no": v_id})
        
        return {
            "status": "success",
            "message": "Vendor status retrieved successfully",
            "vendor_id": v_id,
            "data": {
                "basic_info": vendor_data,
                "record_counts": {
                    "bank_details_count": bank_count,
                    "document_details_count": doc_count,
                    "onboarding_records_count": onb_count
                },
                "completion_status": {
                    "has_bank_details": bank_count > 0,
                    "has_documents": doc_count > 0,
                    "has_onboarding": onb_count > 0,
                    "is_complete": bank_count > 0 and doc_count > 0 and onb_count > 0
                }
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_status_check API: {str(e)}", "Vendor Status API Error")
        return {
            "status": "error", 
            "message": f"Failed to check vendor status: {str(e)}"
        }