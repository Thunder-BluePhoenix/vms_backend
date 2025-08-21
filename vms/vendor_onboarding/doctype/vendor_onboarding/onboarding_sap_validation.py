# Backend API Functions
# Add these to a new file: vms/vendor_onboarding/api/sap_validation_api.py

import frappe
import json
from frappe import _
# from vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding import validate_mandatory_data


@frappe.whitelist()
def get_sap_validation_display_data(onb_ref):
    """
    Get validation data for JavaScript rendering
    No database field updates needed - purely data API
    """
    try:
       
        
        # Get validation result
        result = validate_mandatory_data(onb_ref)
        
        # Prepare data for frontend rendering
        display_data = {
            "validation_passed": result["success"],
            "vendor_type": result.get("vendor_type", "Unknown"),
            "companies_count": len(result.get("data", [])),
            "message": result.get("message", ""),
            "timestamp": frappe.utils.now(),
            "missing_fields_summary": [],
            "total_missing_count": 0
        }
        
        if not result["success"]:
            # Parse missing fields from the message
            missing_fields_text = result.get("message", "")
            if "Missing Mandatory Fields:" in missing_fields_text:
                missing_fields_list = missing_fields_text.replace("Missing Mandatory Fields:\n", "").split("\n")
                clean_fields = [f.strip() for f in missing_fields_list if f.strip()]
                
                display_data["missing_fields_summary"] = clean_fields
                display_data["total_missing_count"] = len(clean_fields)
        
        return {
            "success": True,
            "display_data": display_data,
            "message": "Validation data retrieved successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting validation display data: {str(e)}", "Validation Display Data API")
        return {
            "success": False,
            "message": f"Error retrieving validation data: {str(e)}",
            "display_data": {
                "validation_passed": False,
                "vendor_type": "Unknown",
                "companies_count": 0,
                "message": f"Error: {str(e)}",
                "timestamp": frappe.utils.now(),
                "missing_fields_summary": [],
                "total_missing_count": 0
            }
        }


@frappe.whitelist()
def get_validation_summary_widget(onb_ref):
    """
    Get compact validation summary for dashboard/widget use
    """
    try:
        
        
        result = validate_mandatory_data(onb_ref)
        
        summary = {
            "validation_passed": result["success"],
            "vendor_type": result.get("vendor_type", "Unknown"),
            "companies_count": len(result.get("data", [])),
            "status_text": "Ready for SAP" if result["success"] else "Validation Failed",
            "error_count": 0,
            "timestamp": frappe.utils.now()
        }
        
        if not result["success"]:
            missing_fields_text = result.get("message", "")
            if "Missing Mandatory Fields:" in missing_fields_text:
                missing_fields_list = missing_fields_text.replace("Missing Mandatory Fields:\n", "").split("\n")
                summary["error_count"] = len([f for f in missing_fields_list if f.strip()])
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting validation summary: {str(e)}", "Validation Summary API")
        return {
            "success": False,
            "message": str(e),
            "summary": {
                "validation_passed": False,
                "vendor_type": "Unknown",
                "companies_count": 0,
                "status_text": "Error",
                "error_count": 0,
                "timestamp": frappe.utils.now()
            }
        }


@frappe.whitelist()
def trigger_manual_validation(onb_ref):
    """
    Manually trigger validation and return updated status
    This can be called from a button to force re-validation
    """
    try:
    
        
        # Run validation
        result = validate_mandatory_data(onb_ref)
        
        # Update the mandatory_data_filled field
        onb_doc = frappe.get_doc("Vendor Onboarding", onb_ref)
        onb_doc.mandatory_data_filled = 1 if result["success"] else 0
        onb_doc.save(ignore_permissions=True)
        
        # Return the result for JavaScript to process
        return {
            "success": True,
            "validation_passed": result["success"],
            "message": "Validation completed successfully",
            "validation_result": result
        }
        
    except Exception as e:
        frappe.log_error(f"Error in manual validation trigger: {str(e)}", "Manual Validation Trigger")
        return {
            "success": False,
            "message": f"Error during validation: {str(e)}"
        }


# Optional: Field mapping helper for detailed error display
@frappe.whitelist()
def get_field_doctype_mapping():
    """
    Return field to doctype mapping for better error display
    """
    try:
        field_mapping = {
            # Company and Organization Fields
            "Company Code": "Company Master",
            "Purchase Organization": "Purchase Organization Master", 
            "Account Group": "Account Group Master",
            
            # Vendor Master Fields
            "Vendor Name": "Vendor Master",
            "Mobile Number": "Vendor Master",
            "Primary Email": "Vendor Master",
            
            # Address Fields
            "Address Line 1": "Vendor Onboarding Company Details",
            "Pin Code": "Vendor Onboarding Company Details",
            "City": "Vendor Onboarding Company Details",
            "State": "Vendor Onboarding Company Details",
            "Country": "Vendor Onboarding Company Details",
            
            # Tax and Legal Fields
            "GST Number": "Vendor Onboarding Company Details",
            "PAN Number": "Vendor Onboarding Company Details",
            "Vendor Type": "Vendor Type Master",
            
            # Financial and Payment Fields
            "Reconciliation Account": "Reconciliation Account",
            "Currency": "Vendor Onboarding Payment Details",
            "Payment Terms": "Terms of Payment Master",
            
            # Purchase Fields
            "Purchase Group": "Purchase Group Master",
            "Incoterm Code": "Incoterm Master",
            "Incoterm Description": "Incoterm Master",
            
            # Banking Fields
            "Bank Code": "Bank Master",
            "Bank Name": "Bank Master",
            "Account Number": "Vendor Onboarding Payment Details",
            "IFSC Code": "Vendor Onboarding Payment Details",
            "Account Holder Name": "Vendor Onboarding Payment Details",
            
            # International Banking Fields
            "Beneficiary Name": "International Bank Details",
            "Beneficiary Bank Name": "International Bank Details",
            "Beneficiary Account Number": "International Bank Details",
            "Beneficiary IBAN": "International Bank Details",
            "SWIFT Code": "International Bank Details"
        }
        
        return {
            "success": True,
            "field_mapping": field_mapping
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "field_mapping": {}
        }



def safe_get_contact_detail(onb_doc, field_name):
    """
    Safely get contact detail field from the first contact record
    Similar to safe_get function used in SAP.py
    """
    try:
        if hasattr(onb_doc, 'contact_details') and onb_doc.contact_details and len(onb_doc.contact_details) > 0:
            first_contact = onb_doc.contact_details[0]
            return getattr(first_contact, field_name, "") or ""
        return ""
    except:
        return ""



def validate_mandatory_data(onb_ref):
    """
    Enhanced validation function with proper international/intermediate bank validation
    based on vendor country (India = domestic, others = international)
    """
    try:
        # Get main documents
        onb = frappe.get_doc("Vendor Onboarding", onb_ref)
        onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
        onb_pmd = frappe.get_doc("Vendor Onboarding Payment Details", onb.payment_detail)
        pur_org = frappe.get_doc("Purchase Organization Master", onb.purchase_organization)
        pur_grp = frappe.get_doc("Purchase Group Master", onb.purchase_group)
        acc_grp = frappe.get_doc("Account Group Master", onb.account_group)
        onb_reco = frappe.get_doc("Reconciliation Account", onb.reconciliation_account)
        onb_pm_term = frappe.get_doc("Terms of Payment Master", onb.terms_of_payment)
        onb_inco = frappe.get_doc("Incoterm Master", onb.incoterms)
        
        # Boolean field mappings
        payee = 'X' if onb.payee_in_document == 1 else ''
        gr_based_inv_ver = 'X' if onb.gr_based_inv_ver == 1 else ''
        service_based_inv_ver = 'X' if onb.service_based_inv_ver == 1 else ''
        check_double_invoice = 'X' if onb.check_double_invoice == 1 else ''

        # Get vendor type names
        vendor_type_names = []
        for row in onb.vendor_types:
            if row.vendor_type:
                # vendor_type_doc = frappe.get_doc("Vendor Type Master", row.vendor_type)
                vendor_type_names.append(row.vendor_type)
        vendor_type_names_str = ", ".join(vendor_type_names)

        validation_errors = []
        data_list = []

        # Check vendor country to determine if domestic or international
        vendor_country = getattr(onb_vm, 'country', '') or getattr(onb_pmd, 'country', '')
        is_domestic_vendor = vendor_country.lower() == 'india'

        # Validate banking details based on vendor country
        banking_validation_errors = validate_banking_details(onb_pmd, is_domestic_vendor)
        if banking_validation_errors:
            validation_errors.extend(banking_validation_errors)

        # Process each company in vendor_company_details
        for company in onb.vendor_company_details:
            vcd = frappe.get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
            com_vcd = frappe.get_doc("Company Master", vcd.company_name)

            # Get bank details (same for all companies but validated above)
            if is_domestic_vendor:
                # For domestic vendors, use bank_name from payment details
                onb_bank = frappe.get_doc("Bank Master", onb_pmd.bank_name) if onb_pmd.bank_name else None
                bank_code = onb_bank.bank_code if onb_bank else ""
                bank_name = onb_bank.bank_name if onb_bank else ""
            else:
                # For international vendors, we'll use international bank details
                bank_code = ""  # Not applicable for international
                bank_name = ""  # Will be filled from international bank details

            # Build complete data dictionary following SAP structure with ALL missing fields
            data = {
                "Bukrs": com_vcd.company_code,
                "Ekorg": pur_org.purchase_organization_code,
                "Ktokk": acc_grp.account_group_code,
                "Title": "",
                "Name1": onb_vm.vendor_name,
                "Name2": "",
                "Sort1": onb_vm.search_term if hasattr(onb_vm, 'search_term') else "",
                "Street": vcd.address_line_1,
                "StrSuppl1": vcd.address_line_2 if hasattr(vcd, 'address_line_2') else "",
                "StrSuppl2": vcd.address_line_3 if hasattr(vcd, 'address_line_3') else "",
                "StrSuppl3": "",
                "PostCode1": vcd.pincode,
                "City1": vcd.city,
                "Country": vcd.country,
                "J1kftind": "",
                "Region": vcd.state,
                "TelNumber": vcd.telephone_number if hasattr(vcd, 'telephone_number') else "",
                "MobNumber": onb_vm.mobile_number,
                "SmtpAddr": onb_vm.office_email_primary,
                "SmtpAddr1": onb_vm.office_email_secondary if hasattr(onb_vm, 'office_email_secondary') else "",
                "Zuawa": "",
                "Akont": onb_reco.reconcil_account_code,
                "Waers": onb_pmd.currency_code if hasattr(onb_pmd, 'currency_code') else "",
                "Zterm": onb_pm_term.terms_of_payment_code,
                "Inco1": onb_inco.incoterm_code,
                "Inco2": onb_inco.incoterm_name,
                "Kalsk": "",
                "Ekgrp": pur_grp.purchase_group_code,
                "Xzemp": payee,
                "Reprf": check_double_invoice,
                "Webre": gr_based_inv_ver,
                "Lebre": service_based_inv_ver,
                "Stcd3": vcd.gst,
                "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
                "J1ipanno": vcd.company_pan_number if hasattr(vcd, 'company_pan_number') else "",
                "J1ipanref": onb_vm.vendor_name,
                "Namev": safe_get_contact_detail(onb, "first_name"),
                "Name11": safe_get_contact_detail(onb, "last_name"),
                "Bankl": bank_code,
                "Bankn": onb_pmd.account_number if is_domestic_vendor else "",
                "Bkref": onb_pmd.ifsc_code if is_domestic_vendor else "",
                "Banka": bank_name,
                "Koinh": onb_pmd.name_of_account_holder if is_domestic_vendor else "",
                "Xezer": "",
                "Bkont": "",  # Additional SAP field
                "Zort1": "",  # Additional SAP field  
                "Zdunn": "",  # Additional SAP field
                "Zzpurgroup": pur_grp.purchase_group_code if pur_grp else "",  # Additional SAP field
                "Vedno": "",  # Additional SAP field
                "Zmsg": "",   # Additional SAP field
                "Refno": onb_ref
            }

            # Add international bank details if not domestic
            if not is_domestic_vendor and onb_pmd.international_bank_details:
                for idx, intl_bank in enumerate(onb_pmd.international_bank_details):
                    if idx == 0:  # Use first international bank record for main fields
                        data.update({
                            "ZZBENF_NAME": intl_bank.beneficiary_name if hasattr(intl_bank, 'beneficiary_name') else "",
                            "ZZBEN_BANK_NM": intl_bank.beneficiary_bank_name if hasattr(intl_bank, 'beneficiary_bank_name') else "",
                            "ZZBEN_ACCT_NO": intl_bank.beneficiary_account_no if hasattr(intl_bank, 'beneficiary_account_no') else "",
                            "ZZBENF_IBAN": intl_bank.beneficiary_iban_no if hasattr(intl_bank, 'beneficiary_iban_no') else "",
                            "ZZBENF_BANKADDR": intl_bank.beneficiary_bank_address if hasattr(intl_bank, 'beneficiary_bank_address') else "",
                            "ZZBENF_SHFTADDR": intl_bank.beneficiary_swift_code if hasattr(intl_bank, 'beneficiary_swift_code') else "",
                            "ZZBENF_ACH_NO": intl_bank.beneficiary_ach_no if hasattr(intl_bank, 'beneficiary_ach_no') else "",
                            "ZZBENF_ABA_NO": intl_bank.beneficiary_aba_no if hasattr(intl_bank, 'beneficiary_aba_no') else "",
                            "ZZBENF_ROUTING": intl_bank.beneficiary_routing_no if hasattr(intl_bank, 'beneficiary_routing_no') else "",
                        })

            # Add intermediate bank details if available and not domestic
            if not is_domestic_vendor and onb_pmd.intermediate_bank_details:
                for idx, inter_bank in enumerate(onb_pmd.intermediate_bank_details):
                    if idx == 0:  # Use first intermediate bank record
                        data.update({
                            "ZZINTR_ACCT_NO": inter_bank.intermediate_account_no if hasattr(inter_bank, 'intermediate_account_no') else "",
                            "ZZINTR_IBAN": inter_bank.intermediate_iban_no if hasattr(inter_bank, 'intermediate_iban_no') else "",
                            "ZZINTR_BANK_NM": inter_bank.intermediate_bank_name if hasattr(inter_bank, 'intermediate_bank_name') else "",
                            "ZZINTR_BANKADDR": inter_bank.intermediate_bank_address if hasattr(inter_bank, 'intermediate_bank_address') else "",
                            "ZZINTR_SHFTADDR": inter_bank.intermediate_swift_code if hasattr(inter_bank, 'intermediate_swift_code') else "",
                            "ZZINTR_ACH_NO": inter_bank.intermediate_ach_no if hasattr(inter_bank, 'intermediate_ach_no') else "",
                            "ZZINTR_ABA_NO": inter_bank.intermediate_aba_no if hasattr(inter_bank, 'intermediate_aba_no') else "",
                            "ZZINTR_ROUTING": inter_bank.intermediate_routing_no if hasattr(inter_bank, 'intermediate_routing_no') else "",
                        })

            # Fields allowed to be empty (based on SAP requirements)
            allowed_empty_fields = {
                "Title", "Name2", "StrSuppl2", "StrSuppl3", "J1kftind", "Zuawa", 
                "Kalsk", "TelNumber", "SmtpAddr1", "Namev", "Name11", "Sort1",
                "Xezer", "Bkont", "Zort1", "Zdunn", "Vedno", "Zmsg"
            }
            
            # Add international/intermediate bank fields to allowed empty for domestic vendors
            if is_domestic_vendor:
                allowed_empty_fields.update({
                    "ZZBENF_NAME", "ZZBEN_BANK_NM", "ZZBEN_ACCT_NO", "ZZBENF_IBAN",
                    "ZZBENF_BANKADDR", "ZZBENF_SHFTADDR", "ZZBENF_ACH_NO", "ZZBENF_ABA_NO",
                    "ZZBENF_ROUTING", "ZZINTR_ACCT_NO", "ZZINTR_IBAN", "ZZINTR_BANK_NM",
                    "ZZINTR_BANKADDR", "ZZINTR_SHFTADDR", "ZZINTR_ACH_NO", "ZZINTR_ABA_NO",
                    "ZZINTR_ROUTING"
                })

            # Field descriptions for better error messages
            field_descriptions = {
                "Bukrs": "Company Code (Company Master)",
                "Ekorg": "Purchase Organization Code (Purchase Organization Master)",
                "Ktokk": "Account Group Code (Account Group Master)",
                "Name1": "Vendor Name (Vendor Master)",
                "Street": "Address Line 1 (Vendor Onboarding Company Details)",
                "StrSuppl1": "Address Line 2 (Vendor Onboarding Company Details)",
                "PostCode1": "Pincode (Vendor Onboarding Company Details)",
                "City1": "City (Vendor Onboarding Company Details)",
                "Country": "Country (Vendor Onboarding Company Details)",
                "Region": "State (Vendor Onboarding Company Details)",
                "MobNumber": "Mobile Number (Vendor Master)",
                "SmtpAddr": "Primary Email (Vendor Master)",
                "Akont": "Reconciliation Account Code (Reconciliation Account)",
                "Waers": "Currency Code (Vendor Onboarding Payment Details)",
                "Zterm": "Terms of Payment Code (Terms of Payment Master)",
                "Inco1": "Incoterm Code (Incoterm Master)",
                "Inco2": "Incoterm Name (Incoterm Master)",
                "Ekgrp": "Purchase Group Code (Purchase Group Master)",
                "Xzemp": "Payee in Document (Vendor Onboarding)",
                "Reprf": "Check Double Invoice (Vendor Onboarding)",
                "Webre": "GR Based Invoice Verification (Vendor Onboarding)",
                "Lebre": "Service Based Invoice Verification (Vendor Onboarding)",
                "Stcd3": "GST Number (Vendor Onboarding Company Details)",
                "J1ivtyp": "Vendor Type (Vendor Type Master)",
                "J1ipanno": "Company PAN Number (Vendor Onboarding Company Details)",
                "J1ipanref": "PAN Reference Name (Vendor Master)",
                "Bankl": "Bank Code (Bank Master)",
                "Bankn": "Account Number (Vendor Onboarding Payment Details)",
                "Bkref": "IFSC Code (Vendor Onboarding Payment Details)",
                "Banka": "Bank Name (Bank Master)",
                "Koinh": "Name of Account Holder (Vendor Onboarding Payment Details)",
                "Xezer": "Alternative Payee (SAP Field)",
                "Bkont": "Bank Control Key (SAP Field)",
                "Zort1": "Sort Field 1 (SAP Field)",
                "Zdunn": "Dunning Procedure (SAP Field)",
                "Zzpurgroup": "Purchase Group Code (Purchase Group Master)",
                "Vedno": "Vendor Number (SAP Field)",
                "Zmsg": "Message (SAP Field)",
                # International bank field descriptions
                "ZZBENF_NAME": "Beneficiary Name (International Bank Details)",
                "ZZBEN_BANK_NM": "Beneficiary Bank Name (International Bank Details)",
                "ZZBEN_ACCT_NO": "Beneficiary Account Number (International Bank Details)",
                "ZZBENF_IBAN": "Beneficiary IBAN Number (International Bank Details)",
                "ZZBENF_BANKADDR": "Beneficiary Bank Address (International Bank Details)",
                "ZZBENF_SHFTADDR": "Beneficiary SWIFT Code (International Bank Details)",
                "ZZBENF_ACH_NO": "Beneficiary ACH Number (International Bank Details)",
                "ZZBENF_ABA_NO": "Beneficiary ABA Number (International Bank Details)",
                "ZZBENF_ROUTING": "Beneficiary Routing Number (International Bank Details)",
                # Intermediate bank field descriptions
                "ZZINTR_ACCT_NO": "Intermediate Account Number (Intermediate Bank Details)",
                "ZZINTR_IBAN": "Intermediate IBAN Number (Intermediate Bank Details)",
                "ZZINTR_BANK_NM": "Intermediate Bank Name (Intermediate Bank Details)",
                "ZZINTR_BANKADDR": "Intermediate Bank Address (Intermediate Bank Details)",
                "ZZINTR_SHFTADDR": "Intermediate SWIFT Code (Intermediate Bank Details)",
                "ZZINTR_ACH_NO": "Intermediate ACH Number (Intermediate Bank Details)",
                "ZZINTR_ABA_NO": "Intermediate ABA Number (Intermediate Bank Details)",
                "ZZINTR_ROUTING": "Intermediate Routing Number (Intermediate Bank Details)",
                "Refno": "Reference Number (Vendor Onboarding)"
            }

            # Check for missing mandatory data
            missing_fields = []
            for field_key, field_value in data.items():
                # Skip fields that are intentionally allowed to be empty
                if field_key in allowed_empty_fields:
                    continue
                    
                # Check if field is None, empty string, or whitespace only
                if field_value is None or field_value == "" or (isinstance(field_value, str) and field_value.strip() == ""):
                    field_description = field_descriptions.get(field_key, field_key)
                    missing_fields.append(f"{field_description}")

            if missing_fields:
                company_name = com_vcd.company_code if hasattr(com_vcd, 'company_code') else 'Unknown Company'
                validation_errors.append(f"Company {company_name}: Missing mandatory fields - {', '.join(missing_fields)}")
            
            data_list.append(data)
				
        # Return results based on validation
        if validation_errors:
            error_message = "Missing Mandatory Fields:\n" + "\n".join(validation_errors)
            frappe.log_error(error_message, "Mandatory Data Validation Failed")
            return {
                "success": False,
                "message": error_message,
                "data": data_list,  # Return data even if validation fails for debugging
                "vendor_type": "International" if not is_domestic_vendor else "Domestic"
            }
        else:
            return {
                "success": True,
                "message": f"✅ Validation passed for {len(data_list)} company records. Vendor Type: {'Domestic (India)' if is_domestic_vendor else 'International'}",
                "data": data_list,
                "vendor_type": "International" if not is_domestic_vendor else "Domestic"
            }
			
    except Exception as e:
        error_message = f"Error during validation: {str(e)}"
        frappe.log_error(error_message, "Mandatory Data Validation Error")
        return {
            "success": False,
            "message": error_message,
            "data": [],
            "vendor_type": "Unknown"
        }


def validate_banking_details(payment_details, is_domestic_vendor):
    """
    Validate banking details based on vendor country
    India = domestic bank validation
    Other countries = international + intermediate bank validation
    """
    validation_errors = []
    
    if is_domestic_vendor:
        # Validate domestic banking details for Indian vendors
        if not payment_details.bank_name:
            validation_errors.append("Bank Name is required for domestic vendors")
        if not payment_details.ifsc_code:
            validation_errors.append("IFSC Code is required for domestic vendors")
        if not payment_details.account_number:
            validation_errors.append("Account Number is required for domestic vendors")
        if not payment_details.name_of_account_holder:
            validation_errors.append("Name of Account Holder is required for domestic vendors")
    else:
        # Validate international banking details for foreign vendors
        if not payment_details.international_bank_details or len(payment_details.international_bank_details) == 0:
            validation_errors.append("International Bank Details table is empty (required for international vendors)")
        else:
            # Validate first international bank record (primary bank)
            intl_bank = payment_details.international_bank_details[0]
            required_intl_fields = {
                'beneficiary_name': 'Beneficiary Name',
                'beneficiary_bank_name': 'Beneficiary Bank Name',
                'beneficiary_account_no': 'Beneficiary Account Number',
                'beneficiary_swift_code': 'Beneficiary SWIFT Code'
            }
            
            for field, label in required_intl_fields.items():
                if not hasattr(intl_bank, field) or not getattr(intl_bank, field):
                    validation_errors.append(f"{label} is required in International Bank Details")
        
        # Check if intermediate bank details are provided and validate them
        if hasattr(payment_details, 'add_intermediate_bank_details') and payment_details.add_intermediate_bank_details:
            if not payment_details.intermediate_bank_details or len(payment_details.intermediate_bank_details) == 0:
                validation_errors.append("Intermediate Bank Details table is empty but 'Add Intermediate Bank Details' is checked")
            else:
                # Validate first intermediate bank record
                inter_bank = payment_details.intermediate_bank_details[0]
                required_inter_fields = {
                    'intermediate_bank_name': 'Intermediate Bank Name',
                    'intermediate_swift_code': 'Intermediate SWIFT Code'
                }
                
                for field, label in required_inter_fields.items():
                    if not hasattr(inter_bank, field) or not getattr(inter_bank, field):
                        validation_errors.append(f"{label} is required in Intermediate Bank Details")
    
    return validation_errors














@frappe.whitelist()
def get_validation_summary(onb_ref):
    """
    API endpoint to get validation summary without HTML
    Useful for dashboard widgets or quick checks
    """
    try:
        
        
        result = validate_mandatory_data(onb_ref)
        
        # Extract summary information
        summary = {
            "validation_passed": result["success"],
            "vendor_type": result.get("vendor_type", "Unknown"),
            "companies_count": len(result.get("data", [])),
            "error_count": 0,
            "missing_fields": []
        }
        
        if not result["success"]:
            missing_fields_list = result.get("message", "").replace("Missing Mandatory Fields:\n", "").split("\n")
            summary["error_count"] = len([f for f in missing_fields_list if f.strip()])
            summary["missing_fields"] = [f.strip() for f in missing_fields_list if f.strip()][:5]  # First 5 only
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting validation summary: {str(e)}", "Validation Summary API")
        return {
            "success": False,
            "message": str(e)
        }