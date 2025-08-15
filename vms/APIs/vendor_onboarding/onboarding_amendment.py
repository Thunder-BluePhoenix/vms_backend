# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now, getdate, get_fullname
import json


@frappe.whitelist()
def create_vendor_onboarding_amendment(data):
    """
    Robust API to create vendor onboarding amendment
    
    Args:
        data: JSON string or dict containing:
            - vendor_onboarding: Vendor Onboarding document name (required)
            - remarks: Amendment remarks (required)
            - amended_by: User who is making the amendment (optional, defaults to current user)
    
    Returns:
        dict: Status and details of the amendment creation
    """
    try:
        # Parse data if it's a JSON string
        if isinstance(data, str):
            data = json.loads(data)
        
        # Validate required fields
        vendor_onboarding_name = data.get("vendor_onboarding")
        remarks = data.get("remarks")
        amended_by = data.get("amended_by") or frappe.session.user
        
        if not vendor_onboarding_name:
            return {
                "status": "error",
                "message": "Missing required field: 'vendor_onboarding'"
            }
        
        if not remarks:
            return {
                "status": "error", 
                "message": "Missing required field: 'remarks'"
            }
        
        # Validate vendor onboarding document exists
        if not frappe.db.exists("Vendor Onboarding", vendor_onboarding_name):
            return {
                "status": "error",
                "message": f"Vendor Onboarding '{vendor_onboarding_name}' does not exist"
            }
        
        # Validate amended_by user exists
        if not frappe.db.exists("User", amended_by):
            return {
                "status": "error",
                "message": f"User '{amended_by}' does not exist"
            }
        
        # Get the vendor onboarding document
        vendor_onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding_name)

        prev_rej_reason = vendor_onboarding_doc.reason_for_rejection or None
        
        # Check permissions
        if not vendor_onboarding_doc.has_permission("write"):
            return {
                "status": "error",
                "message": "You don't have permission to amend this vendor onboarding"
            }
        
        # Begin database transaction
        frappe.db.begin()
        
        # Reset rejection fields as required
        vendor_onboarding_doc.rejected = 0
        vendor_onboarding_doc.rejected_by = None
        vendor_onboarding_doc.rejected_by_designation = None
        vendor_onboarding_doc.reason_for_rejection = None
        
        # Add new amendment entry to the amendment_details table
        amendment_row = vendor_onboarding_doc.append("amendment_details", {})
        amendment_row.datetime = now()
        amendment_row.amended_by = amended_by
        amendment_row.remarks = remarks
        amendment_row.previous_rejected_reason = prev_rej_reason
        amendment_row.amended_by_name = frappe.get_value("User", amended_by, "full_name")
        
        # Save the document
        vendor_onboarding_doc.save(ignore_permissions=True)
        
        # Commit the transaction
        frappe.db.commit()
        
        # Get amended by user details for response
        amended_by_details = frappe.get_value("User", amended_by, 
                                            ["full_name", "email"], as_dict=True)
        
        return {
            "status": "success",
            "message": "Vendor onboarding amendment created successfully",
            "data": {
                "vendor_onboarding": vendor_onboarding_name,
                "amendment_id": amendment_row.name,
                "datetime": amendment_row.datetime,
                "amended_by": amended_by,
                "amended_by_name": amended_by_details.get("full_name") if amended_by_details else amended_by,
                "amended_by_email": amended_by_details.get("email") if amended_by_details else None,
                "remarks": remarks,
                "rejected": vendor_onboarding_doc.rejected,
                "rejected_by": vendor_onboarding_doc.rejected_by,
                "rejected_by_designation": vendor_onboarding_doc.rejected_by_designation
            }
        }
        
    except frappe.ValidationError as ve:
        frappe.db.rollback()
        frappe.log_error(f"Validation error in amendment creation: {str(ve)}", 
                         "Vendor Amendment Validation Error")
        return {
            "status": "error",
            "message": f"Validation error: {str(ve)}"
        }
        
    except frappe.PermissionError as pe:
        frappe.db.rollback()
        frappe.log_error(f"Permission error in amendment creation: {str(pe)}", 
                         "Vendor Amendment Permission Error")
        return {
            "status": "error",
            "message": "You don't have sufficient permissions to perform this action"
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error creating vendor onboarding amendment: {str(e)}\n\n{frappe.get_traceback()}", 
                         "Vendor Amendment Creation Error")
        return {
            "status": "error",
            "message": "Failed to create vendor onboarding amendment",
            "error": str(e)
        }






@frappe.whitelist(allow_guest=True)
def send_amendment_email_to_vendor(vendor_onboarding_name, remarks, amended_by):
    """
    Send amendment notification email to vendor
    Similar to send_registration_email_link but for amendments
    
    Args:
        vendor_onboarding_name: Name of the vendor onboarding document
        remarks: Amendment remarks
        amended_by: User who made the amendment
        custom_message: Additional custom message to include (optional)
        
    Returns:
        dict: Email sending result
    """
    try:
        # Get the vendor onboarding document
        onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding_name)
        
        # Get vendor master document
        vendor_master = frappe.get_doc("Vendor Master", onboarding_doc.ref_no)
        
        # Get recipient email
        recipient_email = vendor_master.office_email_primary or vendor_master.office_email_secondary
        
        if not recipient_email:
            return {
                "status": "error",
                "message": "No recipient email found for the vendor."
            }
        
        # Get amended by user details
        amended_by_name = frappe.get_value("User", amended_by, "full_name") or amended_by
        
        # Get company names for multi-company registration
        company_names = []
        if onboarding_doc.registered_for_multi_companies == 1:
            multi_company_data = frappe.get_all(
                "Vendor Onboarding",
                filters={
                    "registered_for_multi_companies": 1,
                    "unique_multi_comp_id": onboarding_doc.unique_multi_comp_id
                },
                fields=["company_name"]
            )
            company_names = [comp.company_name for comp in multi_company_data if comp.company_name]
        else:
            if onboarding_doc.company_name:
                company_names = [onboarding_doc.company_name]
        
        company_names_str = ", ".join(company_names) if company_names else "Meril Group"
        
        # Get frontend server URL from configuration
        conf = frappe.conf
        http_server = conf.get("frontend_http", "")
        
        # Create amendment review link with parameters
        from urllib.parse import urlencode
        query_params = urlencode({
            "vendor_onboarding": onboarding_doc.name,
            "ref_no": onboarding_doc.ref_no,
            "action": "amendment_review"
        })
        
        amendment_review_link = f"{http_server}/vendor-form?{query_params}"
        
        # Create QMS section if QMS is required
        qms_section = ""
        if onboarding_doc.qms_required == "Yes":
            # Get company codes for QMS form
            qms_company_code = []
            
            if onboarding_doc.registered_for_multi_companies == 1:
                qms_mul_company_names = [comp for comp in company_names if comp]
                for name in qms_mul_company_names:
                    if frappe.db.exists("Company Master", name):
                        comp = frappe.db.get_value("Company Master", name, ["company_code"], as_dict=True)
                        if comp:
                            qms_company_code.append(comp.company_code)
            else:
                if onboarding_doc.company_name:
                    comp = frappe.db.get_value("Company Master", onboarding_doc.company_name, ["company_code"], as_dict=True)
                    qms_company_code = [comp.company_code] if comp else []
            
            qms_query_params = urlencode({
                "vendor_onboarding": onboarding_doc.name,
                "ref_no": onboarding_doc.ref_no,
                "company_code": ",".join(qms_company_code)
            })
            
            qms_link = f"{http_server}/qms-form?tabtype=vendor_information&{qms_query_params}"
            
            qms_section = f"""
                <p>As part of your updated registration, please also review and update the QMS Form at the link below:</p>
                <p style="margin: 15px 0px;">
                    <a href="{qms_link}" rel="nofollow" class="btn btn-secondary" style="
                        background-color: #6c757d;
                        color: white;
                        padding: 10px 20px;
                        text-decoration: none;
                        border-radius: 5px;
                        display: inline-block;
                        font-weight: bold;
                    ">Update QMS Form</a>
                </p>
                <p>You may also copy and paste this link into your browser:<br>
                <a href="{qms_link}">{qms_link}</a></p>
            """
        
        # Add custom message if provided
        custom_section = ""
        # if custom_message:
        #     custom_section = f"""
        #         <div style="background-color: #e8f4fd; padding: 15px; border: 1px solid #bee5eb; border-radius: 5px; margin: 20px 0;">
        #             <h4 style="color: #0c5460; margin-top: 0;">Additional Information:</h4>
        #             <p style="margin: 0;">{custom_message}</p>
        #         </div>
        #     """
        
        # Send amendment notification email
        frappe.sendmail(
            recipients=[recipient_email],
            cc=[onboarding_doc.registered_by, amended_by] if amended_by != onboarding_doc.registered_by else [onboarding_doc.registered_by],
            subject=f"Vendor Onboarding Amendment - {vendor_master.vendor_name} - VMS Ref {vendor_master.name}",
            message=f"""
                <p>Dear {vendor_master.vendor_name},</p>
                <p>Greetings for the Day!</p>
                
                <p>Your vendor onboarding registration with <strong>{company_names_str}</strong> has been amended by <strong>{amended_by_name}</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                    <h4 style="color: #007bff; margin-top: 0;">Amendment Details:</h4>
                    <p><strong>Amendment Reason:</strong> {remarks}</p>
                    <p><strong>Amended By:</strong> {amended_by_name}</p>
                    <p><strong>Amendment Date:</strong> {frappe.utils.format_datetime(frappe.utils.now())}</p>
                    <p><strong>Vendor Onboarding ID:</strong> {onboarding_doc.name}</p>
                    <p><strong>Vendor Reference:</strong> {vendor_master.name}</p>
                </div>
                
                <p>The rejection status has been cleared and you can now proceed with updating your information if needed.</p>
                
                <p>Founded in 2006, Meril Life Sciences Pvt. Ltd. is a global medtech company based in India, dedicated to designing and manufacturing innovative, 
                patient-centric medical devices. We focus on advancing healthcare through cutting-edge R&D, quality manufacturing, and clinical excellence 
                to help people live longer, healthier lives. We are a family of 3000+ Vendors/Sub – Vendors across India.</p>
                
                <p>Please click here to review your registration details:</p>
                <p style="margin: 15px 0px;">
                    <a href="{amendment_review_link}" rel="nofollow" class="btn btn-primary" style="
                        background-color: #007bff;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 5px;
                        display: inline-block;
                        font-weight: bold;
                    ">Review Registration</a>
                </p>
                <p>You may also copy and paste this link into your browser:<br>
                <a href="{amendment_review_link}">{amendment_review_link}</a></p>

                {qms_section}

                {custom_section}

                <div style="background-color: #fff3cd; padding: 10px; border: 1px solid #ffeaa7; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Note:</strong> Please ensure all your information is up to date and complete. If you have any questions or need assistance, please contact our VMS team.</p>
                </div>

                <p>Thanking you,<br><strong>VMS Team</strong><br>Meril Life Sciences Pvt. Ltd.</p>
            """,
            delayed=False
        )
        
        return {
            "status": "success",
            "message": "Amendment notification email sent successfully to vendor.",
            "recipient": recipient_email,
            "cc": [onboarding_doc.registered_by, amended_by] if amended_by != onboarding_doc.registered_by else [onboarding_doc.registered_by]
        }
        
    except Exception as e:
        frappe.log_error(f"Error sending amendment email: {str(e)}\n\n{frappe.get_traceback()}", 
                         "Amendment Email Error")
        return {
            "status": "error",
            "message": "Failed to send amendment notification email",
            "error": str(e)
        }