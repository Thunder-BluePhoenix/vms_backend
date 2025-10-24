from urllib.parse import urlencode
import frappe
from frappe import _
from frappe.model.document import Document


@frappe.whitelist(allow_guest=True)
def send_registration_email_link_v2(vendor_onboarding="ONB-2025-10-01237", refno="V-25001216"):
    """
    Send registration email to vendor with company details and QMS form links.
    
    Args:
        vendor_onboarding: Name of the Vendor Onboarding document
        refno: Reference number of the Vendor Master
        
    Returns:
        dict: Status response with success/error message
    """
    try:
        # Validate input parameters
        if not vendor_onboarding:
            return _error_response("Missing 'vendor_onboarding' parameter.")
        
        if not refno:
            return _error_response("Missing 'refno' parameter.")

        # Fetch documents
        onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        
        # Validate that refno matches
        if onboarding_doc.ref_no != refno:
            return _error_response(
                f"Reference number mismatch. Expected: {onboarding_doc.ref_no}, Got: {refno}"
            )
        
        vendor_master = frappe.get_doc("Vendor Master", refno)

        # Check if email already sent
        if onboarding_doc.sent_registration_email_link:
            return {
                "status": "info",
                "message": "Registration email has already been sent."
            }

        # Get company information
        company_info = _get_company_information(onboarding_doc)
        
        # Build registration link
        registration_link = _build_registration_link(refno, vendor_onboarding)
        
        # Build QMS section (if required)
        qms_section = _build_qms_section(onboarding_doc, company_info['qms_company_codes'])
        
        # Get recipient email
        recipient_email = vendor_master.office_email_primary or vendor_master.office_email_secondary
        if not recipient_email:
            return _error_response("No recipient email found for the vendor.")

        # Send email
        _send_registration_email(
            recipient_email=recipient_email,
            cc_email=onboarding_doc.registered_by,
            vendor_name=vendor_master.vendor_name,
            vendor_ref=vendor_master.name,
            registered_by_name=frappe.db.get_value("User", onboarding_doc.registered_by, "full_name"),
            company_names=company_info['company_names'],
            registration_link=registration_link,
            qms_section=qms_section
        )

        # Update onboarding documents
        _update_onboarding_documents(onboarding_doc, vendor_master)

        return {
            "status": "success",
            "message": "Registration email sent successfully."
        }

    except frappe.DoesNotExistError as e:
        frappe.log_error(frappe.get_traceback(), "Onboarding Registration Email - Document Not Found")
        return _error_response(f"Document not found: {str(e)}")
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Onboarding Registration Email Error")
        return _error_response("Failed to send registration email.", str(e))


def _get_company_information(onboarding_doc):
    """
    Extract company names and codes based on single or multi-company registration.
    
    Returns:
        dict: Contains company_names (str), company_codes (list), qms_company_codes (list)
    """
    company_codes = []
    qms_company_codes = []
    
    if onboarding_doc.registered_for_multi_companies == 1:
        # Multi-company registration
        mul_docs = frappe.get_all(
            "Vendor Onboarding",
            filters={
                "unique_multi_comp_id": onboarding_doc.unique_multi_comp_id,
                "registered_for_multi_companies": 1
            },
            fields=["company_name", "qms_required"]
        )
        
        company_names_list = []
        
        for doc in mul_docs:
            company_name = doc.get("company_name")
            if not company_name or not frappe.db.exists("Company Master", company_name):
                continue
            
            comp = frappe.db.get_value(
                "Company Master", 
                company_name, 
                ["company_name", "company_code"], 
                as_dict=True
            )
            
            if comp:
                company_names_list.append(comp.company_name)
                company_codes.append(comp.company_code)
                
                # Collect QMS company codes
                if doc.get("qms_required") == "Yes":
                    qms_company_codes.append(comp.company_code)
        
        company_names = ", ".join(company_names_list)
    
    else:
        # Single company registration
        comp = frappe.db.get_value(
            "Company Master", 
            onboarding_doc.company_name, 
            ["company_name", "company_code"], 
            as_dict=True
        )
        
        company_names = comp.company_name if comp else ""
        company_codes = [comp.company_code] if comp else []
        
        # Check QMS requirement for single company
        if onboarding_doc.qms_required == "Yes" and comp:
            qms_company_codes = [comp.company_code]
    
    return {
        "company_names": company_names,
        "company_codes": company_codes,
        "qms_company_codes": qms_company_codes
    }


def _build_registration_link(refno, vendor_onboarding):
    """Build the vendor registration form link."""
    http_server = frappe.conf.get("frontend_http")
    return (
        f"{http_server}/vendor-details-form"
        f"?tabtype=Company%20Detail"
        f"&refno={refno}"
        f"&vendor_onboarding={vendor_onboarding}"
    )


def _build_qms_section(onboarding_doc, qms_company_codes):
    """
    Build QMS form section HTML if QMS is required.
    
    Returns:
        str: HTML section for QMS form or empty string
    """
    if not qms_company_codes:
        return ""
    
    http_server = frappe.conf.get("frontend_http")
    
    query_params = urlencode({
        "vendor_onboarding": onboarding_doc.name,
        "ref_no": onboarding_doc.ref_no,
        "company_code": ",".join(qms_company_codes)
    })
    
    webform_link = f"{http_server}/qms-form?tabtype=vendor_information&{query_params}"
    
    return f"""
        <p>As part of your registration, please also complete the QMS Form at the link below:</p>
        <p style="margin: 15px 0px;">
            <a href="{webform_link}" 
                rel="nofollow" 
                style="display: inline-block; 
                        padding: 8px 16px; 
                        background-color: #6c757d; 
                        color: white; 
                        text-decoration: none; 
                        border-radius: 4px; 
                        border: none; 
                        cursor: pointer;">
                Fill QMS Form
            </a>
        </p>
        <p>You may also copy and paste this link into your browser:<br>
        <a href="{webform_link}">{webform_link}</a></p>
    """


def _send_registration_email(recipient_email, cc_email, vendor_name, vendor_ref, 
                             registered_by_name, company_names, registration_link, qms_section):
    """Send the registration email to vendor."""
    frappe.custom_sendmail(
        recipients=[recipient_email], 
        cc=[cc_email],
        subject=f"New Vendor Appointment for Meril Group - {vendor_name} - VMS Ref {vendor_ref}",
        message=f"""
            <p>Dear Vendor,</p>
            <p>Greetings for the Day!</p>
            <p>You have been added by <strong>{registered_by_name}</strong> to Onboard as a Vendor/Supplier for <strong>{company_names}.</strong></p>
            <p>Founded in 2006, Meril Group of Companies is a global MEDTECH company based in India, dedicated to designing and manufacturing innovative, 
            patient-centric medical devices. We focus on advancing healthcare through cutting-edge R&D, quality manufacturing, and clinical excellence 
            to help people live longer, healthier lives. We are a family of 3000+ Vendors/Sub – Vendors across India.</p>
            <p>Please click here to fill details!</p>
            <p style="margin: 15px 0px;">
                <a href="{registration_link}" 
                style="display: inline-block; 
                        padding: 10px 20px; 
                        background-color: #007bff; 
                        color: white; 
                        text-decoration: none; 
                        border-radius: 4px; 
                        font-weight: bold;
                        border: 1px solid #007bff;"
                rel="nofollow">Complete Registration</a>
            </p>
            <p>You may also copy and paste this link into your browser:<br>
            <a href="{registration_link}">{registration_link}</a></p>

            {qms_section}

            <p>Thanking you,<br>VMS Team</p>
        """,
        now=True
    )


def _update_onboarding_documents(onboarding_doc, vendor_master):
    """
    Update all related onboarding documents with email sent status.
    Also updates vendor master with onboarding reference if multi-company.
    
    Logic:
    - For linked documents (excluding current onboarding_doc): Use save() to trigger hooks
    - For current onboarding_doc and vendor_master: Use db_set() for direct updates
    """
    # Get all linked documents (excluding the current onboarding_doc)
    if onboarding_doc.registered_for_multi_companies == 1:
        linked_docs = frappe.get_all(
            "Vendor Onboarding",
            filters={
                "registered_for_multi_companies": 1,
                "unique_multi_comp_id": onboarding_doc.unique_multi_comp_id,
                "name": ["!=", onboarding_doc.name]  # Exclude current document
            },
            fields=["name", "qms_required"]
        )
    else:
        # For single company, no linked docs to update (only current onboarding_doc)
        linked_docs = []

    # Update each LINKED document using save() to trigger document hooks
    for entry in linked_docs:
        doc = frappe.get_doc("Vendor Onboarding", entry["name"])
        
        # Modify in memory
        doc.sent_registration_email_link = 1
        
        if entry.get("qms_required") == "Yes":
            doc.sent_qms_form_link = 1
        
        # Save to trigger hooks/validations
        doc.save(ignore_permissions=True)

    # Update CURRENT onboarding_doc using db_set() for direct updates
    onboarding_doc.db_set('sent_registration_email_link', 1, update_modified=False)
    
    if onboarding_doc.qms_required == "Yes":
        onboarding_doc.db_set('sent_qms_form_link', 1, update_modified=False)

    # Update head target and vendor master for multi-company using db_set()
    if onboarding_doc.registered_for_multi_companies == 1:
        onboarding_doc.db_set('head_target', 1, update_modified=False)
        vendor_master.db_set('onboarding_ref_no', onboarding_doc.name, update_modified=False)

    frappe.db.commit()


def _error_response(message, error=None):
    """Helper function to return error response."""
    response = {
        "status": "error",
        "message": message
    }
    if error:
        response["error"] = error
    return response