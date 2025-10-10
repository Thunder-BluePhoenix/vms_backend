import frappe
import json
from datetime import datetime
from frappe import _
from vms.APIs.material_onboarding.material_master_onboarding_field_map import MATERIAL_FIELDS, MATERIAL_ONBOARDING_FIELDS








@frappe.whitelist()
def send_sap_duplicate_change_email(doc_name, changed_fields):
    try:
        print("*******SAP TEAM DUPLICATE CHANGE EMAIL HIT********", doc_name)
        
        # Fetch required documents
        requestor = frappe.get_doc("Requestor Master", doc_name)
        mo_doc_name = requestor.material_onboarding_ref_no
        mo_details = frappe.get_doc("Material Onboarding", mo_doc_name)
        request_id = requestor.request_id
        
        # Get SAP team email (primary recipient)
        sap_email = frappe.get_value("Employee", {"designation": "SAP Team"}, "company_email")
        if not sap_email:
            frappe.log_error("No SAP team email found", f"Requestor: {doc_name}")
            return {"status": "fail", "message": _("No SAP team email found")}
        
        # Build CC list
        cc_emails = []
        
        # Add requestor email
        if requestor.contact_information_email:
            cc_emails.append(requestor.contact_information_email)
        
        # Add CP team email
        cp_team = mo_details.approved_by
        if cp_team:
            cp_email = frappe.get_value("Employee", {"user_id": cp_team}, "company_email")
            if cp_email:
                cc_emails.append(cp_email)
        
        # Add reporting head email
        if requestor.immediate_reporting_head:
            cc_email2 = frappe.get_value("Employee", {"name": requestor.immediate_reporting_head}, "company_email")
            if cc_email2:
                cc_emails.append(cc_email2)
        
        # Remove duplicates from CC list
        cc_emails = list(set(cc_emails))
        
        # Build changes HTML
        changes_html = "".join(
            f"<li><strong>{prettify_field_name(f)}:</strong> '{o}' ➜ '{n}'</li>"
            for f, o, n in changed_fields
        )
        
        # Email subject and message
        subject = f"🔄 Changes Detected for Existing Material Request - {request_id}"
        
        message = f"""
            <p>Dear SAP Team,</p>
            <p>The request <strong>{request_id}</strong> was already found in SAP.</p>
            <p>However, the following changes were detected in the latest update:</p>
            <ul>{changes_html}</ul>
            <p>Regards,<br/>ERP System</p>
        """
        
        # Send email using frappe.custom_sendmail
        frappe.custom_sendmail(
            recipients=[sap_email],
            cc=cc_emails,
            subject=subject,
            message=message,
            now=True
        )
        
        print("Duplicate change email sent successfully.")
        return {"status": "success", "message": _("Email sent successfully")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "SAP Duplicate Change Email Error")
        return {"status": "fail", "message": _("Failed to send email.")}
    



@frappe.whitelist()
def send_sap_team_email(doc_name):
    try:
        print("*******SAP TEAM EMAIL HIT********", doc_name)
        
        # Fetch required documents
        requestor = frappe.get_doc("Requestor Master", doc_name)
        print("Requestor--->", requestor)
        
        requestor_name = requestor.requested_by
        request_id = requestor.request_id
        
        # Get SAP team email (primary recipient)
        sap_email = frappe.get_value("Employee Master", {"role": "SAP"}, "email")
        if not sap_email:
            frappe.log_error("No SAP team email found", f"Requestor: {doc_name}")
            return {"status": "fail", "message": _("No SAP team email found")}
        
        # Validate material request exists
        if not requestor.material_request:
            frappe.throw("No material items found in the request.")
            print("No Material Request Child table.")
        
        # Get material details
        material_row = requestor.material_request[0]
        company_code = material_row.company_name or "-"
        company_name = frappe.get_value("Company Master", {"name": company_code}, "company_name")
        plant_name = material_row.plant_name or "-"
        material_type = material_row.material_type or "-"
        material_description = material_row.material_name_description or "-"
        
        # Build CC list
        cc_emails = []
        
        # Add requestor email
        if requestor.contact_information_email:
            cc_emails.append(requestor.contact_information_email)
        
        # Add Material Onboarding approved_by email
        mo_doc_name = requestor.material_onboarding_ref_no
        mo_details = frappe.get_doc("Material Onboarding", mo_doc_name)
        cc_team = mo_details.approved_by_name
        print("CP Team--->", cc_team)
        
        if cc_team:
            cc_email = frappe.get_value("Employee Master", {"name": cc_team}, "email")
            print("CP Team Email--->", cc_email)
            if cc_email:
                cc_emails.append(cc_email)
        
        # Get CP name for email body
        cp_name = frappe.get_value("Employee Master", {"name": cc_team}, "full_name") if cc_team else "N/A"
        print("CP Team Full Name--->", cp_name)
        
        # Add reporting head email
        cc_2 = requestor.immediate_reporting_head
        print("Reporting Head--->", cc_2)
        if cc_2:
            cc_email2 = frappe.get_value("Employee Master", {"name": cc_2}, "email")
            if cc_email2:
                cc_emails.append(cc_email2)
        
        # Remove duplicates from CC list
        cc_emails = list(set(cc_emails))
        
        # Email subject and message
        subject = f"Request for Creating New Material Code in {company_code}-{company_name}"
        
        message = f"""
            <p>Dear SAP Team,</p>
            <p>The following request to generate or create a new material code has been submitted by <strong>{cp_name}</strong>, which was initially requested by <strong>{requestor_name}</strong>.</p>
            <ul>
                <li><strong>Request ID:</strong> {request_id}</li>
                <li><strong>Company:</strong> {company_code} - {company_name}</li>
                <li><strong>Plant:</strong> {plant_name}</li>
                <li><strong>Material Type:</strong> {material_type}</li>
                <li><strong>Material Description:</strong> {material_description}</li>
            </ul>
            <p>Regards,<br/>ERP System</p>
        """
        
        # Send email using frappe.custom_sendmail
        frappe.custom_sendmail(
            recipients=[sap_email],
            cc=cc_emails,
            subject=subject,
            message=message,
            now=True
        )
        
        print("Email Sent Successfully")
        return {"status": "success", "message": _("Email sent successfully.")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "SAP Email Send Failed")
        return {"status": "fail", "message": _("Failed to send email.")}

def prettify_field_name(field_name):
    return field_name.replace("_", " ").title()