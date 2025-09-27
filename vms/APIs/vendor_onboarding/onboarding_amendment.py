# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now, getdate, get_fullname
import json
from vms.utils.custom_send_mail import custom_sendmail


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

        existing_approvals = {
            "purchase_t_approval": vendor_onboarding_doc.purchase_t_approval,
            "purchase_h_approval": vendor_onboarding_doc.purchase_h_approval,
            "accounts_t_approval": vendor_onboarding_doc.accounts_t_approval,
            "accounts_head_approval": vendor_onboarding_doc.accounts_head_approval
        }
        
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
        # vendor_onboarding_doc.rejected_by = None
        # vendor_onboarding_doc.rejected_by_designation = None
        # vendor_onboarding_doc.reason_for_rejection = None
        vendor_onboarding_doc.rejected_mail_sent = 0
        vendor_onboarding_doc.is_amendment = 1

        # Reset all approvals
        vendor_onboarding_doc.purchase_team_undertaking = 0
        vendor_onboarding_doc.purchase_head_undertaking = 0
        vendor_onboarding_doc.accounts_team_undertaking = 0
        vendor_onboarding_doc.accounts_head_undertaking = 0

        vendor_onboarding_doc.mail_sent_to_purchase_team = 0
        vendor_onboarding_doc.mail_sent_to_purchase_head = 0
        vendor_onboarding_doc.mail_sent_to_account_team = 0
        vendor_onboarding_doc.mail_sent_to_account_head = 0

        vendor_onboarding_doc.purchase_team_approval_remarks = None
        vendor_onboarding_doc.purchase_head_approval_remarks = None
        vendor_onboarding_doc.accounts_team_approval_remarks = None
        vendor_onboarding_doc.accounts_head_approval_remarks = None

        vendor_onboarding_doc.purchase_t_approval = None
        vendor_onboarding_doc.purchase_h_approval = None
        vendor_onboarding_doc.accounts_t_approval = None
        vendor_onboarding_doc.accounts_head_approval = None
        
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

        email_result = send_amendment_email_to_vendor(vendor_onboarding_name, remarks, amended_by, existing_approvals)
        
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
                "rejected_by_designation": vendor_onboarding_doc.rejected_by_designation,
                "email_notification": email_result
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
def send_amendment_email_to_vendor(vendor_onboarding_name, remarks, amended_by, existing_approvals=None):
    """
    Send amendment notification email based on user designation:
    - Purchase Team -> Vendor only
    - Purchase Head -> Purchase Team
    - Accounts Team -> Purchase Head (and CC: Purchase Team)
    - Accounts Head -> Accounts Team
    
    
    """
    try:
        # Get the vendor onboarding document
        onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding_name)
        
        # Get vendor master document
        vendor_master = frappe.get_doc("Vendor Master", onboarding_doc.ref_no)
        
        # Get recipient email
        vendor_email = vendor_master.office_email_primary or vendor_master.office_email_secondary
        
        if not vendor_email:
            return {
                "status": "error",
                "message": "No recipient email found for the vendor."
            }
        
        # Get amended by user details
        amended_by_name = frappe.get_value("User", amended_by, "full_name") or amended_by
        
      
        employee = frappe.get_value("Employee", {"user_id": amended_by}, "designation")
        
        
        if not employee:
            return {
                "status": "error",
                "message": f"Employee record not found for user {amended_by_name}."
            }
        
        def get_user_role_from_designation(designation):
         
            if not designation:
                return None
                
            designation_lower = designation.lower()
            
          
            if any(term in designation_lower for term in ["purchase team"]):
                return "purchase_team"
            elif any(term in designation_lower for term in ["purchase head"]):
                return "purchase_head"
            elif any(term in designation_lower for term in ["accounts team"]):
                return "accounts_team"
            elif any(term in designation_lower for term in ["accounts head"]):
                return "accounts_head"
            else:
                return None
        
        user_role = get_user_role_from_designation(employee)
        
        
        if not user_role:
            return {
                "status": "error",
                "message": f"User {amended_by_name} with designation '{employee}' is not authorized to send amendment notifications."
            }
        
        # Helper function to get user email
        def get_user_email(user):
            if user and frappe.db.exists("User", user):
                return frappe.get_value("User", user, "email")
            return None
        
        # Use existing_approvals if provided, otherwise get from document
        if existing_approvals:
            purchase_team_user = existing_approvals.get("purchase_t_approval")
            purchase_head_user = existing_approvals.get("purchase_h_approval")
            accounts_team_user = existing_approvals.get("accounts_t_approval")
            accounts_head_user = existing_approvals.get("accounts_head_approval")
            
        else:
            # Fallback to document values (for direct function calls)
            purchase_team_user = onboarding_doc.get("purchase_t_approval")
            purchase_head_user = onboarding_doc.get("purchase_h_approval")
            accounts_team_user = onboarding_doc.get("accounts_t_approval")
            accounts_head_user = onboarding_doc.get("accounts_head_approval")
           
        
        # Get recipients based on user role and existing approval hierarchy
        recipients = []
        cc_list = []
        
        if user_role == "purchase_team":
            # Purchase Team -> Vendor only
            recipients = [vendor_email]
            
        elif user_role == "purchase_head":
            # Purchase Head -> Purchase Team
            
            if not purchase_team_user:
                return {
                    "status": "error", 
                    "message": "Purchase Team approval not found. Cannot determine Purchase Team member."
                }
            
            purchase_team_email = get_user_email(purchase_team_user)
            if not purchase_team_email:
                return {
                    "status": "error",
                    "message": "Purchase Team email not found."
                }
            recipients = [purchase_team_email]
            
        elif user_role == "accounts_team":
            # Accounts Team -> Purchase Head (and CC: Purchase Team)
            if not purchase_head_user:
                return {
                    "status": "error",
                    "message": "Purchase Head approval not found. Cannot determine Purchase Head member."
                }
            
            purchase_head_email = get_user_email(purchase_head_user)
            if not purchase_head_email:
                return {
                    "status": "error",
                    "message": "Purchase Head email not found."
                }
            recipients = [purchase_head_email]
            
            # Add Purchase Team to CC
            if purchase_team_user:
                purchase_team_email = get_user_email(purchase_team_user)
                if purchase_team_email:
                    cc_list.append(purchase_team_email)
                    
        elif user_role == "accounts_head":
            # Accounts Head -> Accounts Team
            if not accounts_team_user:
                return {
                    "status": "error",
                    "message": "Accounts Team approval not found. Cannot determine Accounts Team member."
                }
            
            accounts_team_email = get_user_email(accounts_team_user)
            if not accounts_team_email:
                return {
                    "status": "error",
                    "message": "Accounts Team email not found."
                }
            recipients = [accounts_team_email]
        
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
            "tabtype": "Company Detail",
            "refno": onboarding_doc.ref_no,
            "vendor_onboarding": onboarding_doc.name,
            "action": "amendment_review"
        })

        amendment_review_link = f"{http_server}/vendor-details-form?{query_params}"
        
        # Create QMS section if QMS is required (only for vendor recipients)
        qms_section = ""
        is_vendor_recipient = vendor_email in recipients
        
        if is_vendor_recipient and onboarding_doc.qms_required == "Yes":
           
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
                # "mobile_number": vendor_master.mobile_number,
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
        
      
        if is_vendor_recipient:
            greeting = f"Dear {vendor_master.vendor_name},"
            message_context = f"Your vendor onboarding registration with <strong>{company_names_str}</strong> has been amended by <strong>{amended_by_name}</strong>."
            action_text = "Please click here to review your registration details:"
            rejection_status_text = "The rejection status has been cleared and you can now proceed with updating your information if needed."
            note_text = "Please ensure all your information is up to date and complete. If you have any questions or need assistance, please contact our VMS team."
        else:
            greeting = "Dear Team,"
            message_context = f"Vendor onboarding registration for <strong>{vendor_master.vendor_name}</strong> with <strong>{company_names_str}</strong> has been amended by <strong>{amended_by_name}</strong>."
            action_text = "Please click here to review the vendor registration details:"
            rejection_status_text = "The rejection status has been cleared and the vendor can now proceed with updating their information if needed."
            note_text = "Please review the vendor information and take appropriate action as needed. Contact the VMS team if you have any questions."
        
        # Send amendment notification email
        frappe.custom_sendmail(
            recipients=recipients,
            cc=cc_list if cc_list else None,
            subject=f"Vendor Onboarding Amendment - {vendor_master.vendor_name} - VMS Ref {vendor_master.name}",
            message=f"""
                <p>{greeting}</p>
                <p>Greetings for the Day!</p>
                
                <p>{message_context}</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                    <h4 style="color: #007bff; margin-top: 0;">Amendment Details:</h4>
                    <p><strong>Vendor Name:</strong> {vendor_master.vendor_name}</p>
                    <p><strong>Amendment Reason:</strong> {remarks}</p>
                    <p><strong>Amended By:</strong> {amended_by_name} ({employee})</p>
                    <p><strong>Amendment Date:</strong> {frappe.utils.format_datetime(frappe.utils.now())}</p>
                    <p><strong>Vendor Onboarding ID:</strong> {onboarding_doc.name}</p>
                    <p><strong>Vendor Reference:</strong> {vendor_master.name}</p>
                </div>
                
                <p>{rejection_status_text}</p>
                
                <p>Founded in 2006, Meril Life Sciences Pvt. Ltd. is a global medtech company based in India, dedicated to designing and manufacturing innovative, 
                patient-centric medical devices. We focus on advancing healthcare through cutting-edge R&D, quality manufacturing, and clinical excellence 
                to help people live longer, healthier lives. We are a family of 3000+ Vendors/Sub – Vendors across India.</p>
                
                <p>{action_text}</p>
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

                <div style="background-color: #fff3cd; padding: 10px; border: 1px solid #ffeaa7; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Note:</strong> {note_text}</p>
                </div>

                <p>Thanking you,<br><strong>VMS Team</strong><br>Meril Life Sciences Pvt. Ltd.</p>
            """,
            now=True
        )
        
        return {
            "status": "success",
            "message": "Amendment notification email sent successfully.",
            "recipients": recipients,
            "cc": cc_list,
            "user_role": user_role,
            "user_designation": employee
        }
        
    except Exception as e:
        frappe.log_error(f"Error sending amendment email: {str(e)}\n\n{frappe.get_traceback()}", 
                         "Amendment Email Error")
        return {
            "status": "error",
            "message": "Failed to send amendment notification email",
            "error": str(e)
        }