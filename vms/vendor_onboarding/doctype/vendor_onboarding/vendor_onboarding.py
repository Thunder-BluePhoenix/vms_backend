# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
import json
from vms.utils.custom_send_mail import custom_sendmail
# from vms.vendor_onboarding.doctype.vendor_onboarding.onboarding_sap_validation import generate_sap_validation_html



class VendorOnboarding(Document):
    def after_save(self):
        sync_maintain(self, method= None)

    
     

    
    def after_insert(self):
        exp_doc = frappe.get_doc("Vendor Onboarding Settings") or None

        if exp_doc != None:
            exp_t_sec = float(exp_doc.vendor_onboarding_form_validity)
            
        else:
            exp_t_sec = 604800
            
        # Enqueue a background job to handle vendor onboarding expiration
        exp_d_sec = exp_t_sec + 800
        frappe.enqueue(
            method=self.handle_expiration,
            queue='default',
            timeout=exp_d_sec,
            now=False,
            job_name=f'vendor_onboarding_time_expiration_{self.name}',
            # enqueue_after_commit = False
        )
        
        sent_asa_form_link(self, method=None)


    def handle_expiration(self):
        exp_doc = frappe.get_doc("Vendor Onboarding Settings") or None

        if exp_doc != None:
            exp_t_sec = float(exp_doc.vendor_onboarding_form_validity)
            
        else:
            exp_t_sec = 604800
        time.sleep(exp_t_sec)
        if self.form_fully_submitted_by_vendor == 0:
            self.db_set('expired', 1, update_modified=False)
            self.db_set('onboarding_form_status', "Expired", update_modified=False)

        else:
            pass

        # exp_d_sec = exp_t_sec + 300
        frappe.db.commit()


    


    def on_update(self):
            
            vendor_company_update(self,method=None)
            check_vnonb_send_mails(self, method=None)
            on_update_check_fields(self,method=None)
            update_ven_onb_record_table(self, method=None)
            update_van_core_docs(self, method=None)
            set_qms_required_value(self, method=None)
        #   set_vendor_onboarding_status(self,method=None)
        #   check_vnonb_send_mails(self, method=None)
	


@frappe.whitelist(allow_guest=True)
def set_vendor_onboarding_status(doc, method=None):
    try:
        if doc.register_by_account_team == 0:
            if doc.purchase_team_undertaking and doc.accounts_team_undertaking and doc.purchase_head_undertaking and doc.data_sent_to_sap:
                doc.onboarding_form_status = "Approved"
                doc.rejected = False
            elif doc.purchase_team_undertaking and doc.accounts_team_undertaking and doc.purchase_head_undertaking and doc.data_sent_to_sap != 1:
                doc.onboarding_form_status = "SAP Error"
                doc.rejected = False
            
            elif doc.rejected:
                doc.onboarding_form_status = "Rejected"
            else:
                doc.onboarding_form_status = "Pending"

        elif doc.register_by_account_team == 1:
            if doc.accounts_team_undertaking and doc.accounts_head_undertaking and doc.data_sent_to_sap:
                doc.onboarding_form_status = "Approved"
                doc.rejected = False
            elif doc.accounts_team_undertaking and doc.accounts_head_undertaking and doc.data_sent_to_sap != 1:
                doc.onboarding_form_status = "SAP Error"
                doc.rejected = False
            
            elif doc.rejected:
                doc.onboarding_form_status = "Rejected"
            else:
                doc.onboarding_form_status = "Pending"


        # doc.save(ignore_permissions=True)
        # frappe.db.commit()

        return {
            "status": "success",
            "message": f"Status updated to '{doc.onboarding_form_status}' successfully.",
            # "doc_status": doc.onboarding_form_status
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Set Status Onboarding Error")
        return {
            "status": "error",
            "message": "An error occurred while updating status.",
            "error": str(e)
        }
         




@frappe.whitelist(allow_guest=True)
def vendor_company_update(doc, method=None):
    vm = frappe.get_doc("Vendor Master", doc.ref_no)
    
    company_found = False

    for com in vm.multiple_company_data:
        if com.company_name == doc.company_name:
            # Update existing entry
            com.purchase_organization = doc.purchase_organization
            com.account_group = doc.account_group
            com.purchase_group = doc.purchase_group
            com.terms_of_payment = doc.terms_of_payment
            com.order_currency = doc.order_currency
            com.incoterm = doc.incoterms
            com.reconciliation_account = doc.reconciliation_account
            company_found = True
            break

    if not company_found:
        # Append new entry to the child table
        vm.append("multiple_company_data", {
            "company_name": doc.company_name,
            "purchase_organization": doc.purchase_organization,
            "account_group": doc.account_group,
            "purchase_group": doc.purchase_group,
            "terms_of_payment": doc.terms_of_payment,
            "order_currency": doc.order_currency,
            "incoterm": doc.incoterms,
            "reconciliation_account": doc.reconciliation_account
        })

    vm.save()
    frappe.db.commit()





@frappe.whitelist()
def check_vnonb_send_mails(doc, method=None):
    if doc.register_by_account_team == 0:
        if doc.form_fully_submitted_by_vendor == 1 and doc.rejected == 0:   #doc.mandatory_data_filled == 1 and 
            if doc.purchase_team_undertaking == 0 and doc.mail_sent_to_purchase_team == 0 :
                send_mail_purchase_team(doc, method=None)
                # print("@@@@@@@@@@@@@@@@@@@@@@@@@@send_mail_purchase_team")
            elif doc.purchase_team_undertaking == 1 and doc.purchase_head_undertaking == 0 and doc.mail_sent_to_purchase_head == 0:
                send_mail_purchase_head(doc, method=None)
                # print("@@@@@@@@@@@@@@@@@@@@@@@@@@send_mail_purchase_head")
            elif doc.purchase_head_undertaking == 1 and doc.accounts_team_undertaking == 0 and doc.mail_sent_to_account_team == 0:
                send_mail_account_team(doc, method=None)
                # print("@@@@@@@@@@@@@@@@@@@@@@@@@@send_mail_account_team")

            else:
                pass
            
        elif doc.form_fully_submitted_by_vendor == 1 and doc.rejected == 1 and doc.rejected_mail_sent == 0 :
            send_rejection_email(doc, method=None)

        else:
            pass

    elif doc.register_by_account_team == 1:
        if doc.form_fully_submitted_by_vendor == 1 and doc.rejected == 0:
            if doc.accounts_team_undertaking == 0 and doc.mail_sent_to_account_team == 0 :
                send_approval_mail_accounts_team(doc, method=None)
                # print("@@@@@@@@@@@@@@@@@@@@@@@@@@send_approval_mail_accounts_team")
            elif doc.accounts_team_undertaking == 1 and doc.accounts_head_undertaking == 0 and doc.mail_sent_to_account_head == 0:
                send_approval_mail_accounts_head(doc, method=None)
                # print("@@@@@@@@@@@@@@@@@@@@@@@@@@send_approval_mail_accounts_head")
            else:
                pass
            
        elif doc.form_fully_submitted_by_vendor == 1 and doc.rejected == 1 and doc.rejected_mail_sent == 0:
            send_rejection_email(doc, method=None)

        else:
            pass
    else:
        pass







@frappe.whitelist(allow_guest=True)
def send_mail_purchase_team(doc, method=None):
    try:
        if doc:
            vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)

            purchase_team_id = doc.registered_by

            conf = frappe.conf
            http_server = conf.get("frontend_http")
            
            frappe.custom_sendmail(
                recipients=[purchase_team_id],
                subject=f"Vendor {vendor_master.vendor_name} has completed its Onboarding Form.",
                message=f"""
                    <p>Dear Purchase Team,</p>
                    <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed its Onboarding form.</p>
                    <p>Please Log-in into Portal, Review the details and take necessary actions.</p>
                    
                    <p>
                        <a href="{http_server}" style="
                            background-color: #28a745;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            display: inline-block;
                            font-weight: bold;
                        ">
                            Log-in into Portal
                        </a>
                    </p>
                    
                    <p style="margin-top: 15px">Thanks,<br>VMS Team</p>
                """,
                now=True,
            )

            # doc.mail_sent_to_purchase_team = 1
            # frappe.db.commit()
            frappe.db.set_value("Vendor Onboarding", doc.name, "mail_sent_to_purchase_team", 1)

            return {
                "status": "success",
                "message": "email sent successfully."
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Error")
        return {
            "status": "error",
            "message": "Failed to send email.",
            "error": str(e)
        }
        

@frappe.whitelist(allow_guest=True)
def send_mail_purchase_head(doc, method=None):
    try:
        if doc:
            vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)

            # Get team of the registered_by employee
            team = frappe.db.get_value("Employee", {"user_id": doc.registered_by}, "team")

            if not team:
                return {
                    "status": "error",
                    "message": "Team not found for the registered_by user."
                }

            # Get user_ids of employees with designation 'Purchase Head' in the same team
            purchase_heads = frappe.get_all(
                "Employee",
                filters={"team": team, "designation": "Purchase Head"},
                fields=["user_id"]
            )

            recipient_emails = [emp.user_id for emp in purchase_heads if emp.user_id]

            if not recipient_emails:
                return {
                    "status": "error",
                    "message": "No Purchase Head found in the same team."
                }
            conf = frappe.conf
            http_server = conf.get("frontend_http")
            full_name = frappe.db.get_value("Employee", {"user_id": doc.purchase_t_approval}, "full_name") 

            # Send email
            frappe.custom_sendmail(
                recipients=recipient_emails,
                subject=f"Vendor {vendor_master.vendor_name} approved by Purchase Team {full_name} ",
                cc=doc.registered_by, 
                message=f"""
                    <p>Dear Purchase Head,</p>
                    <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed its onboarding form.<br><strong>{ frappe.db.get_value("Employee", {"user_id": doc.purchase_t_approval}, "full_name") }</strong>
                        from <strong>Purchase Team</strong> has approved the Vendor Onboarding form.</p>
                    <p>Please Log-in into Portal, Review the details and take necessary actions.</p>
                    <p>
                        <a href="{http_server}" style="
                            background-color: #28a745;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            display: inline-block;
                            font-weight: bold;
                        ">
                            Log-in into Portal
                        </a>
                    </p>
                    
                    <p style="margin-top: 15px">Thanks,<br>VMS Team</p>
                """,
                now=True,
            )

            # doc.mail_sent_to_purchase_head = 1
            # frappe.db.commit()
            frappe.db.set_value("Vendor Onboarding", doc.name, "mail_sent_to_purchase_head", 1)


            return {
                "status": "success",
                "message": "Email sent successfully."
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Error")
        return {
            "status": "error",
            "message": "Failed to send email.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def send_mail_account_team(doc, method=None):
    try:
        if doc:
            vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)
            
            recipient_emails = []
            
            # Get company from doc (simple field)
            company_name = doc.company_name
            
            if company_name:
                # Get all employees where designation is "Accounts Team" 
                # and company child table contains the matching company
                employees = frappe.get_all(
                    "Employee", 
                    filters={
                        "designation": "Accounts Team"
                    }, 
                    fields=["name", "user_id"]
                )
                
                # Filter employees who have the matching company in their company child table
                for employee in employees:
                    if employee.user_id:
                        # print("employee user_id:", employee.user_id)
                        # Get the employee document to check company child table
                        emp_doc = frappe.get_doc("Employee", employee.name)
                        # print("emp_doc.company:", emp_doc.company)
                        
                        # Check if the company exists in employee's company child table
                        if hasattr(emp_doc, 'company') and emp_doc.company:
                            for company_row in emp_doc.company:
                                try:
                                    # print("company_row:", company_row)
                                    # print("company_row.company_name:", company_row.company_name)
                                    # print("comparing with doc.company:", company_name)
                                    
                                    if company_row.company_name == company_name:
                                        if employee.user_id not in recipient_emails:
                                            recipient_emails.append(employee.user_id)
                                            # print("Added to recipients:", employee.user_id)
                                        break  # Found match, no need to check other companies
                                except Exception as row_error:
                                    # print("Error processing company row:", str(row_error))
                                    # print("Company row type:", type(company_row))
                                    # print("Company row dict:", company_row.__dict__ if hasattr(company_row, '__dict__') else 'No __dict__')
                                    continue
            
            # Check if we found any recipients
            if not recipient_emails:
                return {
                    "status": "error",
                    "message": "No employees found with designation 'Accounts Team' in the specified company."
                }
            conf = frappe.conf
            http_server = conf.get("frontend_http")
            full_name = frappe.db.get_value("Employee", {"user_id": doc.purchase_h_approval}, "full_name") 

            # Send email to all recipients
            frappe.custom_sendmail(
                recipients=recipient_emails,
                subject=f"Vendor {vendor_master.vendor_name} approved by Purchase Head {full_name} ",
                cc=doc.registered_by,
                message=f"""
                    <p>Dear Accounts Team,</p>
                    <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed the onboarding form ({doc.name}).<br><strong>{ frappe.db.get_value("Employee", {"user_id": doc.purchase_h_approval}, "full_name") }</strong> 
                        (Purchase Head) has approved the Vendor Onboarding form.</p>
                    <p>Please Log-in into Portal, Review the details and take necessary actions.</p>
                    <p>
                        <a href="{http_server}" style="
                            background-color: #28a745;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            display: inline-block;
                            font-weight: bold;
                        ">
                            Log-in into Portal
                        </a>
                    </p>
                    <p style="margin-top: 15px">Thanks,<br>VMS Team</p>
                """,
                now=True,
            )

            # Mark as mail sent
            # doc.mail_sent_to_purchase_team = 1
            frappe.db.set_value("Vendor Onboarding", doc.name, "mail_sent_to_account_team", 1)

            return {
                "status": "success",
                "message": f"Email sent successfully to {len(recipient_emails)} recipients.",
                "recipients": recipient_emails
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Error")
        return {
            "status": "error",
            "message": "Failed to send email.",
            "error": str(e)
        }
    

# sent rejection email to vendor with reason

def send_rejection_email(doc, method=None):
    try:
        if not doc:
            return {
                "status": "error",
                "message": "Document not found."
            }

        vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)

        vendor_email = vendor_master.office_email_primary or vendor_master.office_email_secondary
        if not vendor_email:
            return {
                "status": "error",
                "message": "Vendor email not found."
            }

        conf = frappe.conf
        http_server = conf.get("frontend_http")

        document_details = (
            f"{http_server}/vendor-details-form"
            f"?tabtype=Company%20Detail"
            f"&refno={vendor_master.name}"
            f"&vendor_onboarding={doc.name}"
        )

        # Build CC list based on conditions
        cc_list = []
        if doc.purchase_h_approval:
            if doc.purchase_t_approval:
                cc_list.append(doc.purchase_t_approval)

        if doc.accounts_t_approval:
            if doc.purchase_t_approval:
                cc_list.append(doc.purchase_t_approval)
            if doc.purchase_h_approval:
                cc_list.append(doc.purchase_h_approval)
            
        if doc.accounts_head_approval:
            if doc.accounts_t_approval:
                cc_list.append(doc.accounts_t_approval)

        # Remove duplicates and empty values
        cc_list = list({email for email in cc_list if email})

        frappe.custom_sendmail(
            recipients=cc_list,
            cc=[vendor_email],
            subject=f"Vendor {vendor_master.vendor_name} has been Rejected",
            message=f"""
                <p>Dear Sir/Madam,</p>
                <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has been rejected because of <strong>{doc.reason_for_rejection}</strong>.</p>
                
                <p>Please Log-in into Portal, Review the details and take necessary actions.</p>
                
                <p>
                    <a href="{document_details}" style="
                        background-color: #28a745;
                        color: white;
                        padding: 10px 20px;
                        text-decoration: none;
                        border-radius: 5px;
                        display: inline-block;
                        font-weight: bold;
                    ">
                        Log-in into Portal
                    </a>
                </p>
                
                <p style="margin-top: 15px">Thanks,<br>VMS Team</p>
            """,
            now=True,
        )
        frappe.db.set_value("Vendor Onboarding", doc.name, "rejected_mail_sent", 1)

        return {
            "status": "success",
            "message": "Email sent successfully."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Error")
        return {
            "status": "error",
            "message": "Failed to send email.",
            "error": str(e)
        }



# update the vendor onboarding record table with the latest status and data in the table (present in vendor master)
@frappe.whitelist(allow_guest=True)
def update_ven_onb_record_table(doc, method=None):
    try:
        vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)

        found = False

        for row in vendor_master.vendor_onb_records:
            if row.vendor_onboarding_no == doc.name:
                row.onboarding_form_status = doc.onboarding_form_status
                row.registered_by = doc.registered_by
                row.purchase_team_approval = doc.purchase_t_approval
                row.purchase_head_approval = doc.purchase_h_approval
                row.accounts_team_approval = doc.accounts_t_approval
                found = True
                break

        if not found:
            vendor_master.append("vendor_onb_records", {
                "vendor_onboarding_no": doc.name,
                "onboarding_form_status": doc.onboarding_form_status,
                "registered_by": doc.registered_by,
                "purchase_team_approval": doc.purchase_t_approval,
                "purchase_head_approval": doc.purchase_h_approval,
                "accounts_team_approval": doc.accounts_t_approval
            })

        vendor_master.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Record table updated successfully."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Vendor Onboarding Record Error")
        return {
            "status": "error",
            "message": "Failed to update Vendor Onboarding Record table.",
            "error": str(e)
        }
    


def update_van_core_docs(doc, method=None):
    if doc.head_target == 1 and doc.registered_for_multi_companies == 1:
        core_docs = frappe.get_all("Vendor Onboarding", filters = {"unique_multi_comp_id":doc.unique_multi_comp_id, "head_target": 0}, fields=["name"])
        if len(core_docs)<1:
            return
        
        for core_doc in core_docs:
            vn_onb = frappe.get_doc("Vendor Onboarding", core_doc)
            vn_onb.qms_form_link = doc.qms_form_link
            vn_onb.form_fully_submitted_by_vendor = doc.form_fully_submitted_by_vendor
            vn_onb.qms_form_filled = doc.qms_form_filled
            vn_onb.sent_registration_email_link = doc.sent_registration_email_link
            vn_onb.sent_qms_form_link = doc.sent_qms_form_link
            
            vn_onb.enterprise = doc.enterprise
            vn_onb.number_of_employee = []
            vn_onb.machinery_detail = []
            vn_onb.testing_detail = []
            vn_onb.reputed_partners = []
            vn_onb.contact_details = []


            for noe in doc.number_of_employee:
                vn_onb.append("number_of_employee", {
                    "production": noe.production,
                    "qaqc": noe.qaqc,
                    "logistics": noe.logistics,
                    "marketing": noe.marketing,
                    "r_d": noe.r_d,
                    "hse": noe.hse,
                    "other": noe.other
                    })
                
            
            for md in doc.machinery_detail:
                vn_onb.append("machinery_detail", {
                    "equipment_name": md.equipment_name,
                    "equipment_qty": md.equipment_qty,
                    "capacity": md.capacity,
                    "remarks": md.remarks
                    })
                
            for td in doc.testing_detail:
                vn_onb.append("testing_detail", {
                    "equipment_name": td.equipment_name,
                    "equipment_qty": td.equipment_qty,
                    "capacity": td.capacity,
                    "remarks": td.remarks
                    })
                
                
            for rp in doc.reputed_partners:
                vn_onb.append("reputed_partners", {
                    "company_name": rp.company_name,
                    "test": rp.test,
                    "supplied_qtyyear": rp.supplied_qtyyear,
                    "remark": rp.remark
                    })
                
                
            for cd in doc.contact_details:
                vn_onb.append("contact_details", {
                    "first_name": cd.first_name,
                    "last_name": cd.last_name,
                    "designation": cd.designation,
                    "email": cd.email,
                    "contact_number": cd.contact_number,
                    "department_name": cd.department_name
                    })
                
            vn_onb.save()
                
                
            
def sent_asa_form_link(doc, method=None):
    try:
        if doc.ref_no:
            vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)

            # Only send if ASA is required and not already sent
            if doc.asa_required and not vendor_master.asa_required:
                http_server = frappe.conf.get("backend_http")
                subject = "Fill ASA Form Link"
                link = f"{http_server}/annual-supplier-assessment-questionnaire/new?vendor_ref_no={vendor_master.name}"

                message = f"""
                    Hello {vendor_master.vendor_name},<br><br>
                    Kindly fill the ASA Form for your Vendor Onboarding.<br>
                    Click the link below:<br>
                    <a href="{link}">{link}</a><br><br>
                    Thank You.<br><br>
                    Regards,<br>
                    Team VMS
                """

                recipients = vendor_master.office_email_primary or vendor_master.office_email_secondary
                if recipients:
                    frappe.custom_sendmail(
                        recipients=recipients,
                        subject=subject,
                        message=message
                    )

                vendor_master.asa_required = 1
                vendor_master.save()
            else:
                pass

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error in sent_asa_form_link")





















def sync_maintain(doc, method= None):
    # Server Script for Vendor Onboarding
    if doc.onboarding_form_status == "Approved":
        # Check if not already synced
        if not frappe.db.get_value("Vendor Onboarding", doc.name, "data_sent_to_sap"):
            frappe.call(
                "vms.vendor_onboarding.vendor_document_management.sync_vendor_documents_on_approval",
                vendor_onboarding_name=doc.name
            )
            
            # Mark as synced
            frappe.db.set_value("Vendor Onboarding", doc.name, {
                "data_sent_to_sap": 1
            }, update_modified=False)
            
            frappe.msgprint("Vendor documents synced to Vendor Master successfully")


# Accounts team approval emails-----------------------------------------------

def send_approval_mail_accounts_team(doc, method=None):
    try:
        if doc:
            vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)
            
            recipient_emails = doc.registered_by
            
            # company_name = doc.company_name
            
            # if company_name:
            # employees = frappe.get_all(
            #     "Employee", 
            #     filters={
            #         "designation": "Accounts Team"
            #     }, 
            #     fields=["name", "user_id"]
            # )
            
                # for employee in employees:
                #     if employee.user_id:
                #         emp_doc = frappe.get_doc("Employee", employee.name)
                        
                #         if hasattr(emp_doc, 'company') and emp_doc.company:
                #             for company_row in emp_doc.company:
                #                 try:
                #                     if company_row.company_name == company_name:
                #                         if employee.user_id not in recipient_emails:
                #                             recipient_emails.append(employee.user_id)
                #                         break  # Found match, no need to check other companies
                #                 except Exception as row_error:
                #                     continue

            # for emp in employees:
            #     if emp.get("user_id") and emp["user_id"] not in recipient_emails:
            #         recipient_emails.append(emp["user_id"])

            # Check if we found any recipients
            if not recipient_emails:
                return {
                    "status": "error",
                    "message": "No User ID present in Registered_by field ."
                }
            conf = frappe.conf
            http_server = conf.get("frontend_http")

            # Send email to all recipients
            frappe.custom_sendmail(
                recipients=recipient_emails,
                subject=f"Vendor {vendor_master.vendor_name} has completed its Onboarding form.",
                message=f"""
                    <p>Dear Accounts Team,</p>
                    <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed its onboarding form.</p>
                    <p>Please Log-in into Portal, Review the details and take necessary actions.</p>
                    
                    <p>
                        <a href="{http_server}" style="
                            background-color: #28a745;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            display: inline-block;
                            font-weight: bold;
                        ">
                            Log-in into Portal
                        </a>
                    </p>
                    
                    <p style="margin-top: 15px">Thanks,<br>VMS Team</p>
                """,
                now=True,
            )

            frappe.db.set_value("Vendor Onboarding", doc.name, "mail_sent_to_account_team", 1)

            return {
                "status": "success",
                "message": f"Email sent successfully to {len(recipient_emails)} recipients.",
                "recipients": recipient_emails
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Error")
        return {
            "status": "error",
            "message": "Failed to send email.",
            "error": str(e)
        }



def send_approval_mail_accounts_head(doc, method=None):
    try:
        if doc:
            vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)
            
            recipient_emails = []
            
            company_name = doc.company_name
            
            if company_name:
                employees = frappe.get_all(
                    "Employee", 
                    filters={
                        "designation": "Accounts Head"
                    }, 
                    fields=["name", "user_id"]
                )
                
                for employee in employees:
                    if employee.user_id:
                        emp_doc = frappe.get_doc("Employee", employee.name)
                        
                        if hasattr(emp_doc, 'company') and emp_doc.company:
                            for company_row in emp_doc.company:
                                try:
                                    if company_row.company_name == company_name:
                                        if employee.user_id not in recipient_emails:
                                            recipient_emails.append(employee.user_id)
                                        break  # Found match, no need to check other companies
                                except Exception as row_error:
                                    continue
            
            # for emp in employees:
            #     if emp.get("user_id") and emp["user_id"] not in recipient_emails:
            #         recipient_emails.append(emp["user_id"])

            # Check if we found any recipients
            if not recipient_emails:
                return {
                    "status": "error",
                    "message": "No employees found with designation 'Accounts Head' in the specified company."
                }
            
            conf = frappe.conf
            http_server = conf.get("frontend_http")
            full_name = frappe.db.get_value("Employee", {"user_id": doc.accounts_t_approval}, "full_name")


            # Send email to all recipients
            frappe.custom_sendmail(
                recipients=recipient_emails,
                subject=f"Vendor {vendor_master.vendor_name} Onboarding details has been approved by Accounts Team {full_name} ",
                message=f"""
                    <p>Dear Accounts Head,</p>
                    <p>The vendor <strong>{vendor_master.vendor_name} ({doc.ref_no})</strong> has completed the onboarding form ({doc.name}).<br><strong>{ frappe.db.get_value("Employee", {"user_id": doc.accounts_t_approval}, "full_name") }</strong> 
                        from (Accounts Team) has approved the vendor onboarding form.</p></p>
                    <p>Please Log-in into Portal, Review the details and take necessary actions.</p>
                    
                    <p>
                        <a href="{http_server}" style="
                            background-color: #28a745;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            display: inline-block;
                            font-weight: bold;
                        ">
                            Log-in into Portal
                        </a>
                    </p>
                    
                    <p style="margin-top: 15px">Thanks,<br>VMS Team</p>
                """,
                now=True,
            )

            frappe.db.set_value("Vendor Onboarding", doc.name, "mail_sent_to_account_head", 1)

            return {
                "status": "success",
                "message": f"Email sent successfully to {len(recipient_emails)} recipients.",
                "recipients": recipient_emails
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Error")
        return {
            "status": "error",
            "message": "Failed to send email.",
            "error": str(e)
        }
    

#set qms required value for mul company code
def set_qms_required_value(doc, method=None):
    if doc.registered_for_multi_companies == 1:
        for row in doc.multiple_company:
            if row.company == doc.company_name and row.qms_required == "Yes":
                doc.qms_required = "Yes"
            elif row.company == doc.company_name and row.qms_required == "No":
                doc.qms_required = "No"
            else:
                pass





def on_update_check_fields(self, method=None):
    """
    Silent validation function that returns a detailed validation summary
    without showing any messages or popups
    """
    result = validate_mandatory_data(self.name)
    
    if result["success"]:
        # Update database directly
        self.mandatory_data_filled = 1
        frappe.db.set_value("Vendor Onboarding", self.name, "mandatory_data_filled", 1)
        
        # Store success message with data summary in mandatory_data_for_sap field
        success_message = f"""✅ VALIDATION SUCCESSFUL ✅

🎉 All mandatory SAP data has been validated successfully!

📊 VALIDATION SUMMARY:
• Vendor Type: {result.get("vendor_type", "Unknown")}
• Companies Processed: {len(result.get("data", []))}
• Banking Validation: ✅ Passed
• All Required Fields: ✅ Complete

📋 DATA READY FOR SAP INTEGRATION:
{json.dumps(result.get("data", []), indent=2)}

🚀 Status: Ready to send to SAP
📅 Validated On: {frappe.utils.now()}
"""
        frappe.db.set_value("Vendor Onboarding", self.name, "mandatory_data_for_sap", success_message)
    else:
        # Update database directly
        self.mandatory_data_filled = 0
        frappe.db.set_value("Vendor Onboarding", self.name, "mandatory_data_filled", 0)
        
        # Store detailed error information in mandatory_data_for_sap field
        error_message = f"""❌ VALIDATION FAILED ❌

🚫 Mandatory data validation did not pass. Please complete the required fields below:

📊 VALIDATION SUMMARY:
• Vendor Type: {result.get("vendor_type", "Unknown")}
• Companies Processed: {len(result.get("data", []))}

🔍 MISSING/INCOMPLETE DATA:
{result.get("message", "Unknown validation error")}

📋 STEPS TO RESOLVE:
1. Complete all missing mandatory fields listed above
2. Ensure banking details are properly filled:
   - For India: Bank Name, IFSC Code, Account Number, Account Holder Name
   - For International: International Bank Details table with beneficiary information
   - For International with Intermediate: Intermediate Bank Details table
3. Save the document again to re-validate
4. Once validation passes, data will be ready for SAP integration

📅 Last Validation Attempt: {frappe.utils.now()}
"""
        
        self.mandatory_data_for_sap = error_message
        frappe.db.set_value("Vendor Onboarding", self.name, "mandatory_data_for_sap", error_message)

    # html_content = generate_sap_validation_html(result)
    # frappe.db.set_value("Vendor Onboarding", self.name, "sap_validation_html", html_content)
    
    # Commit the database changes
    frappe.db.commit()


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