# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
import json
from frappe.utils import now_datetime
from datetime import timedelta
from vms.utils.custom_send_mail import custom_sendmail

# Import all the existing functions to maintain functionality
from vms.APIs.sap.sap import update_sap_vonb
from vms.vendor_onboarding.vendor_document_management import on_vendor_onboarding_submit
from vms.APIs.vendor_onboarding.vendor_registration_helper import populate_vendor_data_from_existing_onboarding
from vms.vendor_onboarding.doctype.vendor_onboarding.update_related_doc import VendorDataPopulator
from vms.utils.execute_if_allowed import execute_if_allowed
from vms.utils.next_approver import update_next_approver
from vms.utils.notification_triggers import NotificationTrigger
from vms.APIs.approval.helpers.get_approval_matrix import get_stage_info
from vms.utils.get_approver_employee import (
    get_approval_employee,
    get_user_for_role_short,
)
from vms.utils.approval_utils import get_approval_next_role
from vms.utils.verify_user import get_current_user_document

populator = VendorDataPopulator()




class VendorOnboarding(Document):
    # def after_save(self):
    #     # sync_maintain(self, method= None)
    #     # frappe.clear_cache(doctype=self.doctype, name=self.name)
    #     # frappe.db.commit()
    #     # self.reload()
    #     set_vonb_status_onupdate(self, method=None)
    #     print("RUNNING after save @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        
    #     # Notify frontend about the update
    #     frappe.publish_realtime(
    #         event="vendor_onboarding_updated",
    #         message={
    #             "name": self.name,
    #             "modified": self.modified
    #         },
    #         user=frappe.session.user
    #     )

    
     

    
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

        self.add_first_in_approval_workflow()
        self.update_next_approver_role()
        


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

    def before_save(self):
            
            update_van_core_docs(self, method=None)
            update_van_core_docs_multi_case(self, method=None) 


    def on_update(self):
            
            vendor_company_update(self,method=None)
            
            on_update_check_fields(self,method=None)
            
            
            set_qms_required_value(self, method=None)         
            update_sap_vonb(self, method= None)
            set_vonb_status_onupdate(self, method=None)
            check_vnonb_send_mails(self, method=None)
            update_ven_onb_record_table(self, method=None)
            sync_maintain(self, method= None)
            on_vendor_onboarding_submit(self, method=None)
            

            send_doc_change_req_email(self, method=None)


            frappe.enqueue(
                method=self.run_delayed_vonb_status_update,
                queue='default',
                timeout=300,
                # enqueue_after_commit=True,
                now=False,
                job_name=f'vendor_onboarding_status_update_check_{self.name}',
            )


            self.reload()
            
            # Notify frontend about the update
            frappe.publish_realtime(
                event="vendor_onboarding_updated",
                message={
                    "name": self.name,
                    "modified": self.modified
                },
                user=frappe.session.user
            )

            self.update_next_approver_role()
            update_next_approver(self)

    def update_next_approver_role(self):
        approvals = self.get("approvals") or []
        if not approvals:
            self.db_set("next_approver_role", "")
            return

        last = approvals[-1]
        updated = last.get("next_action_role", "")

        if not updated:
            self.db_set("next_approver_role", updated)
            return

        if updated != self.get("next_approver_role", ""):
            self.db_set("next_approver_role", updated)
        


    
    def add_first_in_approval_workflow(self, approval_stage=None):
        try:
            #getting the first stage info from approval matrix
            stage_info = get_stage_info(
                "Vendor Onboarding", self, approval_stage
            )

            if not stage_info or not stage_info.get("cur_stage_info"):
                frappe.log_error(f"No approval matrix found for {self.name}")
                self.approval_status = "Pending Review"
                self.save(ignore_permissions=True)
                return
            
            self.approval_matrix = stage_info.get("approval_matrix", "")
            cur_stage = stage_info["cur_stage_info"]
            

            role = cur_stage.get("role", "") if cur_stage else ""
            from_hierarchy = cur_stage.get("from_hierarchy") if cur_stage else None

            approver = cur_stage.get("user") if cur_stage else ""
            stage_count = (
                cur_stage.get("approval_stage") if cur_stage.get("approval_stage") else 0
            )
            

            next_approver_role = ""

            
            next_approver_role = get_approval_next_role(cur_stage)
        

            if not next_approver_role and not approver:
                

                company = self.get("company")
                
                emp = (
                    get_approval_employee(
                        cur_stage.role,
                        company_list=[company],
                        fields=["user_id"],
                        doc=self,
                    )
                    if cur_stage
                    else None
                )
                

                approver = (
                    cur_stage.get("user")
                    if cur_stage
                    and cur_stage.get("approver_type") == "User"
                    and cur_stage.get("user")
                    else emp.get("user_id") if emp else ""
                )
                
                if not approver:
                    return self.add_first_in_approval_workflow(cur_stage.get("approval_stage") + 1)

            self.approval_status = cur_stage.get("approval_stage_name") or ""
            self.append(
                "approvals",
                {
                    "for_doc_type": "Vendor Onboarding",
                    "approval_stage": 0,
                    "approval_stage_name": cur_stage.get("approval_stage_name"),
                    "approved_by": "",
                    "approval_status": 0,
                    "next_approval_stage": stage_count,
                    "action": "",
                    "next_action_by": "" if next_approver_role else approver,
                    "next_action_role": next_approver_role,
                    "remark": "",
                },
            )
            

            self.save(ignore_permissions=True)

        except frappe.DoesNotExistError:
            frappe.log_error(f"No approval matrix configured for {self.name}")
            self.approval_status = "Pending Review"
            self.save(ignore_permissions=True)
            return

        except Exception as e:
            frappe.log_error(f"Approval workflow error: {str(e)}")
            self.approval_status = "Pending Review"  
            self.save(ignore_permissions=True)
            return
            


    @frappe.whitelist()
    def run_delayed_vonb_status_update(docname):
        try:
            time.sleep(15)
            doc = frappe.get_doc("Vendor Onboarding", docname)

            set_vonb_status_onupdate(doc, method=None)
            
            doc.reload()
            
            # Notify frontend about the update
            frappe.publish_realtime(
                event="vendor_onboarding_updated",
                message={
                    "name": doc.name,
                    "modified": doc.modified
                },
                user=frappe.session.user
            )
            frappe.log_error(f"Delayed set_vonb_status_onupdate executed for {docname}")
        except Exception as e:
            frappe.log_error(f"Error in delayed vonb_status update for {docname}: {str(e)}")

	



def set_vonb_status_onupdate(doc, method=None):
    new_status = None
    new_rejected = None

    if doc.invalid == 0:
        if doc.register_by_account_team == 0 and doc.rejected == 0:
            if doc.purchase_team_undertaking and doc.accounts_team_undertaking and doc.purchase_head_undertaking and doc.data_sent_to_sap:
                new_status = "Approved"
                new_rejected = False
            elif doc.purchase_team_undertaking and doc.accounts_team_undertaking and doc.purchase_head_undertaking and doc.data_sent_to_sap != 1:
                new_status = "SAP Error"
                new_rejected = False
            elif doc.rejected:
                new_status = "Rejected"
            else:
                new_status = "Pending"

        elif doc.register_by_account_team == 1 and doc.rejected == 0:
            if doc.accounts_team_undertaking and doc.accounts_head_undertaking and doc.data_sent_to_sap:
                new_status = "Approved"
                new_rejected = False
            elif doc.accounts_team_undertaking and doc.accounts_head_undertaking and doc.data_sent_to_sap != 1:
                new_status = "SAP Error"
                new_rejected = False
            elif doc.rejected:
                new_status = "Rejected"
            else:
                new_status = "Pending"
        
        elif doc.rejected:
            new_status = "Rejected"
        else:
            new_status = "Pending"

    else:
        new_status = "Invalid"

    # Update database directly
    if new_status and new_status != doc.onboarding_form_status:
        frappe.db.set_value(doc.doctype, doc.name, "onboarding_form_status", new_status)
        doc.onboarding_form_status = new_status  # Update the doc object too
    
    if new_rejected is not None and new_rejected != doc.rejected:
        frappe.db.set_value(doc.doctype, doc.name, "rejected", new_rejected)
        doc.rejected = new_rejected  # Update the doc object too
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@RUNING@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    
    frappe.db.commit()





@frappe.whitelist(allow_guest=True)
def set_vendor_onboarding_status(doc, method=None):
    # print("before save start@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    try:
        if doc.register_by_account_team == 0 and doc.rejected ==0:
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

        elif doc.register_by_account_team == 1 and doc.rejected ==0:
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
    # print("Mail function shoot@@@@@@@@@@@@@@@@@@@@@@@@@@")
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
            frappe.db.set_value("Vendor Onboarding", doc.name, "approvals_mail_sent_time", now_datetime())

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
        

# @frappe.whitelist(allow_guest=True)
# def send_mail_purchase_head(doc, method=None):
#     try:
#         if doc:
#             vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)

#             # Get team of the registered_by employee
#             team = frappe.db.get_value("Employee", {"user_id": doc.registered_by}, "team")

#             if not team:
#                 return {
#                     "status": "error",
#                     "message": "Team not found for the registered_by user."
#                 }

#             # Get user_ids of employees with designation 'Purchase Head' in the same team
#             purchase_heads = frappe.get_all(
#                 "Employee",
#                 filters={"team": team, "designation": "Purchase Head"},
#                 fields=["user_id"]
#             )

#             recipient_emails = [emp.user_id for emp in purchase_heads if emp.user_id]

#             if not recipient_emails:
#                 return {
#                     "status": "error",
#                     "message": "No Purchase Head found in the same team."
#                 }
#             conf = frappe.conf
#             http_server = conf.get("frontend_http")
#             full_name = frappe.db.get_value("Employee", {"user_id": doc.purchase_t_approval}, "full_name") 

#             # Send email
#             frappe.custom_sendmail(
#                 recipients=recipient_emails,
#                 subject=f"Vendor {vendor_master.vendor_name} approved by Purchase Team {full_name} ",
#                 cc=doc.registered_by, 
#                 message=f"""
#                     <p>Dear Purchase Head,</p>
#                     <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed its onboarding form.<br><strong>{ frappe.db.get_value("Employee", {"user_id": doc.purchase_t_approval}, "full_name") }</strong>
#                         from <strong>Purchase Team</strong> has approved the Vendor Onboarding form.</p>
#                     <p>Please Log-in into Portal, Review the details and take necessary actions.</p>
#                     <p>
#                         <a href="{http_server}" style="
#                             background-color: #28a745;
#                             color: white;
#                             padding: 10px 20px;
#                             text-decoration: none;
#                             border-radius: 5px;
#                             display: inline-block;
#                             font-weight: bold;
#                         ">
#                             Log-in into Portal
#                         </a>
#                     </p>
                    
#                     <p style="margin-top: 15px">Thanks,<br>VMS Team</p>
#                 """,
#                 now=True,
#             )

#             # doc.mail_sent_to_purchase_head = 1
#             # frappe.db.commit()
#             frappe.db.set_value("Vendor Onboarding", doc.name, "mail_sent_to_purchase_head", 1)


#             return {
#                 "status": "success",
#                 "message": "Email sent successfully."
#             }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Email Error")
#         return {
#             "status": "error",
#             "message": "Failed to send email.",
#             "error": str(e)
#         }


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
            
            # check if multiple purchase heads is check or not in team doc
            mul_purchase_heads = frappe.db.get_value("Team Master", team, "multiple_purchase_heads")
            
            recipient_emails = []

            if mul_purchase_heads:
                employee = frappe.get_doc("Employee", {"user_id": doc.registered_by})

                if employee.get("multiple_purchase_heads"):
                    for row in employee.get("purchase_heads", []):
                        if row.user_id:
                            recipient_emails.append(row.user_id)

            else:
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
            frappe.db.set_value("Vendor Onboarding", doc.name, "approvals_mail_sent_time", now_datetime())

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
            frappe.db.set_value("Vendor Onboarding", doc.name, "approvals_mail_sent_time", now_datetime())

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

        employee_name, employee_designation = frappe.db.get_value(
            "Employee",
            {"user_id": doc.rejected_by},
            ["full_name", "designation"]
        )

        frappe.custom_sendmail(
            recipients=cc_list,
            cc=[vendor_email],
            subject=f"Vendor {vendor_master.vendor_name} has been Rejected",
            message=f"""
                <p>Dear Sir/Madam,</p>
                 <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has been rejected 
                    by {employee_name} ({employee_designation}). The reason of rejection is : 
                    <strong>{doc.reason_for_rejection}</strong>.</p>
                
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
        frappe.db.set_value("Vendor Onboarding", doc.name, "approvals_mail_sent_time", now_datetime())

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





def update_vendor_master_onb_status(doc, method = None):
    if doc.onboarding_form_status != None:
        vm = frappe.get_doc("Vendor Master", doc.ref_no)
        for vonb in vm.vendor_onb_records:
            if vonb.vendor_onboarding_no == doc.name:
                vonb.onboarding_form_status = doc.onboarding_form_status

        vm.save()














def sync_maintain(doc, method= None):
    # Server Script for Vendor Onboarding
    if doc.onboarding_form_status == "Approved" and doc.data_sent_to_sap==1:
        # Check if not already synced
        if not frappe.db.get_value("Vendor Onboarding", doc.name, "synced_vendor_master"):
            frappe.call(
                "vms.vendor_onboarding.vendor_document_management.sync_vendor_documents_on_approval",
                vendor_onboarding_name=doc.name
            )
            
            # Mark as synced
            frappe.db.set_value("Vendor Onboarding", doc.name, {
                "synced_vendor_master": 1
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
            frappe.db.set_value("Vendor Onboarding", doc.name, "approvals_mail_sent_time", now_datetime())

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
            frappe.db.set_value("Vendor Onboarding", doc.name, "approvals_mail_sent_time", now_datetime())

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
            if row.company == doc.company_name:
                frappe.db.set_value(
                    doc.doctype, 
                    doc.name, 
                    "qms_required", 
                    row.qms_required
                )
                break  






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


def safe_get(doc, table_field, index, field_name):
    """
    Safely get field from table record matching SAP integration function
    """
    try:
        if hasattr(doc, table_field):
            table_data = getattr(doc, table_field)
            if table_data and len(table_data) > index:
                return getattr(table_data[index], field_name, "") or ""
        return ""
    except:
        return ""


def validate_mandatory_data(onb_ref):
    """
    Enhanced validation function that matches SAP integration logic exactly
    Handles domestic (India), international, and Not-Registered GST vendors
    """
    try:
        # Get main documents
        onb = safe_get_doc("Vendor Onboarding", onb_ref)

        onb_vm = safe_get_doc("Vendor Master", getattr(onb, "ref_no", None))
        onb_pmd = safe_get_doc("Vendor Onboarding Payment Details", getattr(onb, "payment_detail", None))
        pur_org = safe_get_doc("Purchase Organization Master", getattr(onb, "purchase_organization", None))
        pur_grp = safe_get_doc("Purchase Group Master", getattr(onb, "purchase_group", None))
        acc_grp = safe_get_doc("Account Group Master", getattr(onb, "account_group", None))
        onb_reco = safe_get_doc("Reconciliation Account", getattr(onb, "reconciliation_account", None))
        onb_pm_term = safe_get_doc("Terms of Payment Master", getattr(onb, "terms_of_payment", None))
        onb_inco = safe_get_doc("Incoterm Master", getattr(onb, "incoterms", None))
        onb_bank = safe_get_doc("Bank Master", getattr(onb_pmd, "bank_name", None))
        onb_legal_doc = safe_get_doc("Legal Documents", getattr(onb, "document_details", None))


        # Boolean field mappings
        payee = 'X' if onb.payee_in_document == 1 else ''
        gr_based_inv_ver = 'X' if onb.gr_based_inv_ver == 1 else ''
        service_based_inv_ver = 'X' if onb.service_based_inv_ver == 1 else ''
        check_double_invoice = 'X' if onb.check_double_invoice == 1 else ''

        # Get vendor type names
        vendor_type_names = []
        for row in onb.vendor_types:
            if row.vendor_type:
                vendor_type_names.append(row.vendor_type)

        validation_errors = []
        data_list = []

        # Check vendor country to determine if domestic or international
        is_domestic_vendor = onb.vendor_country == "India"

        # Validate banking details based on vendor country
        banking_validation_errors = validate_banking_details(onb_pmd, is_domestic_vendor)
        if banking_validation_errors:
            validation_errors.extend(banking_validation_errors)

        # Process each company in vendor_company_details
        for company in onb.vendor_company_details:
            vcd = safe_get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
            com_vcd = safe_get_doc("Company Master", vcd.company_name)
            
            # Get country information for this company
            country_doc = safe_get_doc("Country Master", onb.vendor_country)
            country_code = country_doc.country_code
            
            # Set Zuawa based on SAP client code logic from integration
            sap_client_code = com_vcd.sap_client_code
            Zuawa = "001"  # Default value as per integration code

            if is_domestic_vendor:
                # **DOMESTIC VENDOR - Process GST entries**
                print(f"Processing Domestic Vendor - Company: {vcd.company_name}")
                
                if not hasattr(vcd, 'comp_gst_table') or not vcd.comp_gst_table:
                    validation_errors.append(f"Company {com_vcd.company_code}: No GST entries found for domestic vendor")
                    continue
                
                # Process each GST entry for domestic vendors
                for gst_index, gst_table in enumerate(vcd.comp_gst_table):
                    # Get GST-specific data
                    gst_ven_type = gst_table.gst_ven_type
                    gst_state = gst_table.gst_state
                    gst_num = gst_table.gst_number or "0"
                    gst_pin = gst_table.pincode
                    
                    # Get address details
                    gst_addrs = safe_get_doc("Pincode Master", gst_pin)
                    gst_city = gst_addrs.city
                    gst_country = gst_addrs.country
                    gst_district = gst_addrs.district
                    gst_state_doc = safe_get_doc("State Master", gst_state)
                    
                    # Build address text as per integration logic
                    gst_address_text = ", ".join(filter(None, [
                        gst_city,
                        gst_district,
                        gst_state
                    ]))

                    # Build complete data dictionary following SAP integration structure
                    data = {
                        "Bukrs": com_vcd.company_code,
                        "Ekorg": pur_org.purchase_organization_code,
                        "Ktokk": acc_grp.account_group_code,
                        "Title": "",
                        "Name1": onb_vm.vendor_name,
                        "Name2": "",
                        "Sort1": onb_vm.search_term if hasattr(onb_vm, 'search_term') else "",
                        "Street": vcd.address_line_1,
                        "StrSuppl1": gst_address_text or "",
                        "StrSuppl2": "",
                        "StrSuppl3": "",
                        "PostCode1": gst_pin,
                        "City1": gst_city,
                        "Country": country_code,
                        "J1kftind": "",
                        "Region": gst_state_doc.sap_state_code if hasattr(gst_state_doc, 'sap_state_code') else "",
                        "TelNumber": "",
                        "MobNumber": onb_vm.mobile_number,
                        "SmtpAddr": onb_vm.office_email_primary,
                        "SmtpAddr1": onb_vm.office_email_secondary if hasattr(onb_vm, 'office_email_secondary') else "",
                        "Zuawa": Zuawa,
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
                        "Stcd3": gst_num if gst_ven_type != "Not-Registered" else "0",
                        "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
                        "J1ipanno": vcd.company_pan_number if gst_ven_type != "Not-Registered" and hasattr(vcd, 'company_pan_number') else "0",
                        "J1ipanref": onb_legal_doc.name_on_company_pan if hasattr(onb_legal_doc, 'name_on_company_pan') else "",
                        "Namev": safe_get_contact_detail(onb, "first_name"),
                        "Name11": safe_get_contact_detail(onb, "last_name"),
                        "Bankl": onb_bank.bank_code if onb_bank else "",
                        "Bankn": onb_pmd.account_number if hasattr(onb_pmd, 'account_number') else "",
                        "Bkref": onb_pmd.ifsc_code if hasattr(onb_pmd, 'ifsc_code') else "",
                        "Banka": onb_bank.bank_name if onb_bank else "",
                        "Koinh": onb_pmd.name_of_account_holder if hasattr(onb_pmd, 'name_of_account_holder') else "",
                        "Xezer": "",
                        # International bank fields (empty for domestic)
                        "ZZBENF_NAME": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_name"),
                        "ZZBEN_BANK_NM": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_name"),
                        "ZZBEN_ACCT_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_account_no"),
                        "ZZBENF_IBAN": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_iban_no"),
                        "ZZBENF_BANKADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_address"),
                        "ZZBENF_SHFTADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_swift_code"),
                        "ZZBENF_ACH_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_ach_no"),
                        "ZZBENF_ABA_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_aba_no"),
                        "ZZBENF_ROUTING": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_routing_no"),
                        # Intermediate bank fields (empty for domestic)
                        "ZZINTR_ACCT_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_account_no"),
                        "ZZINTR_IBAN": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_iban_no"),
                        "ZZINTR_BANK_NM": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_name"),
                        "ZZINTR_BANKADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_address"),
                        "ZZINTR_SHFTADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_swift_code"),
                        "ZZINTR_ACH_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_ach_no"),
                        "ZZINTR_ABA_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_aba_no"),
                        "ZZINTR_ROUTING": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_routing_no"),
                        "Refno": onb.ref_no,
                        "Vedno": "",
                        "Zmsg": ""
                    }
                    
                    # Validate this GST entry
                    validation_result = validate_data_fields(data, f"Company {com_vcd.company_code} - GST Entry {gst_index + 1} ({gst_num})", is_domestic_vendor, gst_ven_type)
                    if validation_result["errors"]:
                        validation_errors.extend(validation_result["errors"])
                    
                    data_list.append(data)

            else:
                # **INTERNATIONAL VENDOR - Single entry per company**
                print(f"Processing International Vendor - Company: {vcd.company_name}")
                
                # Get international address details
                gst_state = vcd.international_state if hasattr(vcd, 'international_state') else ""
                gst_pin = vcd.international_zipcode if hasattr(vcd, 'international_zipcode') else ""
                gst_city = vcd.international_city if hasattr(vcd, 'international_city') else ""
                gst_country = vcd.international_country if hasattr(vcd, 'international_country') else ""
                
                # Build address text for international
                gst_address_text = ", ".join(filter(None, [
                    gst_city,
                    gst_country,
                    gst_state
                ]))

                # Build data for international vendor
                data = {
                    "Bukrs": com_vcd.company_code,
                    "Ekorg": pur_org.purchase_organization_code,
                    "Ktokk": acc_grp.account_group_code,
                    "Title": "",
                    "Name1": onb_vm.vendor_name,
                    "Name2": "",
                    "Sort1": onb_vm.search_term if hasattr(onb_vm, 'search_term') else "",
                    "Street": vcd.address_line_1,
                    "StrSuppl1": gst_address_text or "",
                    "StrSuppl2": "",
                    "StrSuppl3": "",
                    "PostCode1": gst_pin,
                    "City1": gst_city,
                    "Country": country_code,
                    "J1kftind": "",
                    "Region": "ZZ",  # Fixed value for international as per integration
                    "TelNumber": "",
                    "MobNumber": onb_vm.mobile_number,
                    "SmtpAddr": onb_vm.office_email_primary,
                    "SmtpAddr1": onb_vm.office_email_secondary if hasattr(onb_vm, 'office_email_secondary') else "",
                    "Zuawa": Zuawa,
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
                    "Stcd3": "0",  # Fixed value for international
                    "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
                    "J1ipanno": "0",  # Fixed value for international
                    "J1ipanref": onb_legal_doc.name_on_company_pan if hasattr(onb_legal_doc, 'name_on_company_pan') else "",
                    "Namev": safe_get_contact_detail(onb, "first_name"),
                    "Name11": safe_get_contact_detail(onb, "last_name"),
                    "Bankl": onb_bank.bank_code if onb_bank else "",
                    "Bankn": onb_pmd.account_number if hasattr(onb_pmd, 'account_number') else "",
                    "Bkref": onb_pmd.ifsc_code if hasattr(onb_pmd, 'ifsc_code') else "",
                    "Banka": onb_bank.bank_name if onb_bank else "",
                    "Koinh": onb_pmd.name_of_account_holder if hasattr(onb_pmd, 'name_of_account_holder') else "",
                    "Xezer": "",
                    # International bank fields (mandatory for international)
                    "ZZBENF_NAME": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_name"),
                    "ZZBEN_BANK_NM": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_name"),
                    "ZZBEN_ACCT_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_account_no"),
                    "ZZBENF_IBAN": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_iban_no"),
                    "ZZBENF_BANKADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_address"),
                    "ZZBENF_SHFTADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_swift_code"),
                    "ZZBENF_ACH_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_ach_no"),
                    "ZZBENF_ABA_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_aba_no"),
                    "ZZBENF_ROUTING": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_routing_no"),
                    # Intermediate bank fields (optional for international)
                    "ZZINTR_ACCT_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_account_no"),
                    "ZZINTR_IBAN": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_iban_no"),
                    "ZZINTR_BANK_NM": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_name"),
                    "ZZINTR_BANKADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_address"),
                    "ZZINTR_SHFTADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_swift_code"),
                    "ZZINTR_ACH_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_ach_no"),
                    "ZZINTR_ABA_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_aba_no"),
                    "ZZINTR_ROUTING": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_routing_no"),
                    "Refno": onb.ref_no,
                    "Vedno": "",
                    "Zmsg": ""
                }
                
                # Validate international vendor data
                validation_result = validate_data_fields(data, f"Company {com_vcd.company_code} - International", is_domestic_vendor, "International")
                if validation_result["errors"]:
                    validation_errors.extend(validation_result["errors"])
                
                data_list.append(data)
				
        # Return results based on validation
        if validation_errors:
            error_message = "Missing Mandatory Fields:\n" + "\n".join(validation_errors)
            frappe.log_error(error_message, "Mandatory Data Validation Failed")
            return {
                "success": False,
                "message": error_message,
                "data": data_list,
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


def validate_data_fields(data, context_label, is_domestic_vendor, gst_ven_type):
    """
    Validate data fields based on vendor type and GST registration status
    """
    validation_errors = []
    
    # Field descriptions for better error messages
    field_descriptions = {
        "Bukrs": "Company Code (Company Master)",
        "Ekorg": "Purchase Organization Code (Purchase Organization Master)",
        "Ktokk": "Account Group Code (Account Group Master)",
        "Name1": "Vendor Name (Vendor Master)",
        "Street": "Address Line 1 (Vendor Onboarding Company Details)",
        "PostCode1": "Pincode (Vendor Onboarding Company Details)",
        "City1": "City (Vendor Onboarding Company Details)",
        "Country": "Country (Vendor Onboarding Company Details)",
        "Region": "State/Region (State Master or International)",
        "MobNumber": "Mobile Number (Vendor Master)",
        "SmtpAddr": "Primary Email (Vendor Master)",
        "Akont": "Reconciliation Account Code (Reconciliation Account)",
        "Waers": "Currency Code (Vendor Onboarding Payment Details)",
        "Zterm": "Terms of Payment Code (Terms of Payment Master)",
        "Inco1": "Incoterm Code (Incoterm Master)",
        "Inco2": "Incoterm Name (Incoterm Master)",
        "Ekgrp": "Purchase Group Code (Purchase Group Master)",
        "J1ivtyp": "Vendor Type (Vendor Type Master)",
        "Refno": "Reference Number (Vendor Onboarding)",
        # Banking fields
        "Bankl": "Bank Code (Bank Master)",
        "Bankn": "Account Number (Vendor Onboarding Payment Details)",
        "Bkref": "IFSC Code (Vendor Onboarding Payment Details)",
        "Banka": "Bank Name (Bank Master)",
        "Koinh": "Name of Account Holder (Vendor Onboarding Payment Details)",
        # International bank fields
        "ZZBENF_NAME": "Beneficiary Name (International Bank Details)",
        "ZZBEN_BANK_NM": "Beneficiary Bank Name (International Bank Details)",
        "ZZBEN_ACCT_NO": "Beneficiary Account Number (International Bank Details)",
        "ZZBENF_SHFTADDR": "Beneficiary SWIFT Code (International Bank Details)",
        # Intermediate bank fields
        "ZZINTR_BANK_NM": "Intermediate Bank Name (Intermediate Bank Details)",
        "ZZINTR_SHFTADDR": "Intermediate SWIFT Code (Intermediate Bank Details)",
    }

    # Fields allowed to be empty based on vendor type and GST status
    allowed_empty_fields = {
        "Title", "Name2", "StrSuppl2", "StrSuppl3", "J1kftind", "Zuawa", 
        "Kalsk", "TelNumber", "SmtpAddr1", "Namev", "Name11", "Sort1",
        "Xezer", "Vedno", "Zmsg", "StrSuppl1"
    }
    
    # Add conditional allowed empty fields based on vendor type
    if is_domestic_vendor:
        # For domestic vendors, international/intermediate bank fields can be empty
        allowed_empty_fields.update({
            "ZZBENF_NAME", "ZZBEN_BANK_NM", "ZZBEN_ACCT_NO", "ZZBENF_IBAN",
            "ZZBENF_BANKADDR", "ZZBENF_SHFTADDR", "ZZBENF_ACH_NO", "ZZBENF_ABA_NO",
            "ZZBENF_ROUTING", "ZZINTR_ACCT_NO", "ZZINTR_IBAN", "ZZINTR_BANK_NM",
            "ZZINTR_BANKADDR", "ZZINTR_SHFTADDR", "ZZINTR_ACH_NO", "ZZINTR_ABA_NO",
            "ZZINTR_ROUTING"
        })
        
        # For Not-Registered GST vendors, GST-related fields can be empty/default
        if gst_ven_type == "Not-Registered":
            allowed_empty_fields.update({"Stcd3", "J1ipanno"})
        
    else:
        # For international vendors, domestic bank fields can be empty, but some international fields are mandatory
        allowed_empty_fields.update({
            "Bankl", "Bankn", "Bkref", "Banka", "Koinh", "Stcd3", "J1ipanno"
        })
        
        # Additional international fields that can be empty
        allowed_empty_fields.update({
            "J1ipanref", "ZZBENF_IBAN", "ZZBENF_ACH_NO", "ZZBENF_ABA_NO", "ZZBENF_ROUTING"
        })
        
        # Intermediate bank fields are optional for international vendors
        allowed_empty_fields.update({
            "ZZINTR_ACCT_NO", "ZZINTR_IBAN", "ZZINTR_BANK_NM",
            "ZZINTR_BANKADDR", "ZZINTR_SHFTADDR", "ZZINTR_ACH_NO", 
            "ZZINTR_ABA_NO", "ZZINTR_ROUTING"
        })

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
        validation_errors.append(f"{context_label}: Missing mandatory fields - {', '.join(missing_fields)}")
    
    return {"errors": validation_errors}


def validate_banking_details(payment_details, is_domestic_vendor):
    """
    Validate banking details based on vendor country - matches SAP integration logic
    India = domestic bank validation
    Other countries = international + intermediate bank validation
    """
    validation_errors = []
    
    if is_domestic_vendor:
        # Validate domestic banking details for Indian vendors
        if not hasattr(payment_details, 'bank_name') or not payment_details.bank_name:
            validation_errors.append("Bank Name is required for domestic vendors")
        if not hasattr(payment_details, 'ifsc_code') or not payment_details.ifsc_code:
            validation_errors.append("IFSC Code is required for domestic vendors")
        if not hasattr(payment_details, 'account_number') or not payment_details.account_number:
            validation_errors.append("Account Number is required for domestic vendors")
        if not hasattr(payment_details, 'name_of_account_holder') or not payment_details.name_of_account_holder:
            validation_errors.append("Name of Account Holder is required for domestic vendors")
    else:
        # Validate international banking details for foreign vendors
        if not hasattr(payment_details, 'international_bank_details') or not payment_details.international_bank_details or len(payment_details.international_bank_details) == 0:
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
            if not hasattr(payment_details, 'intermediate_bank_details') or not payment_details.intermediate_bank_details or len(payment_details.intermediate_bank_details) == 0:
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


# Additional helper function for testing validation
@frappe.whitelist(allow_guest=True)
def test_validation_with_sap_structure(onb_ref):
    """
    Test function to validate data structure matches SAP integration exactly
    Returns detailed comparison between validation and SAP integration logic
    """
    try:
        # Run validation
        validation_result = validate_mandatory_data(onb_ref)
        
        # Get the same documents for comparison
        onb = frappe.get_doc("Vendor Onboarding", onb_ref)
        onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
        
        is_domestic_vendor = onb.vendor_country == "India"
        
        comparison_result = {
            "validation_result": validation_result,
            "vendor_type_detected": "Domestic" if is_domestic_vendor else "International",
            "vendor_country": onb.vendor_country,
            "companies_count": len(onb.vendor_company_details),
            "data_records_generated": len(validation_result.get("data", [])),
            "validation_passed": validation_result.get("success", False)
        }
        
        # Add GST processing info for domestic vendors
        if is_domestic_vendor:
            total_gst_entries = 0
            for company in onb.vendor_company_details:
                vcd = frappe.get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
                if hasattr(vcd, 'comp_gst_table') and vcd.comp_gst_table:
                    total_gst_entries += len(vcd.comp_gst_table)
            
            comparison_result["total_gst_entries"] = total_gst_entries
            comparison_result["expected_data_records"] = total_gst_entries
        else:
            comparison_result["total_gst_entries"] = 0
            comparison_result["expected_data_records"] = len(onb.vendor_company_details)
        
        # Check if data record count matches expected
        comparison_result["data_count_matches"] = (
            comparison_result["data_records_generated"] == 
            comparison_result["expected_data_records"]
        )
        
        return comparison_result
        
    except Exception as e:
        return {
            "error": f"Test validation failed: {str(e)}",
            "validation_result": None
        }


# Additional helper function to preview SAP data structure
@frappe.whitelist(allow_guest=True)
def preview_sap_data_structure(onb_ref):
    """
    Preview the exact data structure that will be sent to SAP
    Useful for debugging and verification
    """
    try:
        validation_result = validate_mandatory_data(onb_ref)
        
        if not validation_result.get("data"):
            return {
                "error": "No data generated",
                "validation_result": validation_result
            }
        
        # Show structure of first data record
        sample_data = validation_result["data"][0]
        
        # Categorize fields for better understanding
        categorized_fields = {
            "company_info": {},
            "vendor_basic": {},
            "address_info": {},
            "contact_info": {},
            "sap_config": {},
            "banking_domestic": {},
            "banking_international": {},
            "banking_intermediate": {},
            "reference_info": {}
        }
        
        field_categories = {
            # Company and organizational
            "Bukrs": "company_info", "Ekorg": "company_info", "Ktokk": "company_info",
            "Ekgrp": "company_info", "Zuawa": "company_info",
            
            # Vendor basic info
            "Name1": "vendor_basic", "Name2": "vendor_basic", "Sort1": "vendor_basic",
            "Title": "vendor_basic", "J1ivtyp": "vendor_basic",
            
            # Address
            "Street": "address_info", "StrSuppl1": "address_info", "StrSuppl2": "address_info",
            "StrSuppl3": "address_info", "PostCode1": "address_info", "City1": "address_info",
            "Country": "address_info", "Region": "address_info",
            
            # Contact
            "TelNumber": "contact_info", "MobNumber": "contact_info", 
            "SmtpAddr": "contact_info", "SmtpAddr1": "contact_info",
            "Namev": "contact_info", "Name11": "contact_info",
            
            # SAP Configuration
            "Akont": "sap_config", "Waers": "sap_config", "Zterm": "sap_config",
            "Inco1": "sap_config", "Inco2": "sap_config", "Kalsk": "sap_config",
            "Xzemp": "sap_config", "Reprf": "sap_config", "Webre": "sap_config",
            "Lebre": "sap_config", "Stcd3": "sap_config", "J1ipanno": "sap_config",
            "J1ipanref": "sap_config", "J1kftind": "sap_config", "Xezer": "sap_config",
            
            # Domestic Banking
            "Bankl": "banking_domestic", "Bankn": "banking_domestic", 
            "Bkref": "banking_domestic", "Banka": "banking_domestic", 
            "Koinh": "banking_domestic",
            
            # International Banking
            "ZZBENF_NAME": "banking_international", "ZZBEN_BANK_NM": "banking_international",
            "ZZBEN_ACCT_NO": "banking_international", "ZZBENF_IBAN": "banking_international",
            "ZZBENF_BANKADDR": "banking_international", "ZZBENF_SHFTADDR": "banking_international",
            "ZZBENF_ACH_NO": "banking_international", "ZZBENF_ABA_NO": "banking_international",
            "ZZBENF_ROUTING": "banking_international",
            
            # Intermediate Banking
            "ZZINTR_ACCT_NO": "banking_intermediate", "ZZINTR_IBAN": "banking_intermediate",
            "ZZINTR_BANK_NM": "banking_intermediate", "ZZINTR_BANKADDR": "banking_intermediate",
            "ZZINTR_SHFTADDR": "banking_intermediate", "ZZINTR_ACH_NO": "banking_intermediate",
            "ZZINTR_ABA_NO": "banking_intermediate", "ZZINTR_ROUTING": "banking_intermediate",
            
            # Reference
            "Refno": "reference_info", "Vedno": "reference_info", "Zmsg": "reference_info"
        }
        
        # Categorize the sample data
        for field, value in sample_data.items():
            category = field_categories.get(field, "other")
            if category not in categorized_fields:
                categorized_fields[category] = {}
            categorized_fields[category][field] = value
        
        return {
            "success": True,
            "total_records": len(validation_result["data"]),
            "vendor_type": validation_result.get("vendor_type"),
            "sample_data_structure": categorized_fields,
            "validation_status": validation_result.get("success"),
            "validation_message": validation_result.get("message"),
            "all_sap_fields": list(sample_data.keys())
        }
        
    except Exception as e:
        return {
            "error": f"Preview failed: {str(e)}"
        }
    




def update_van_core_docs_multi_case(doc, method=None):
    if doc.head_target == 1 and doc.registered_for_multi_companies == 1 and doc.form_fully_submitted_by_vendor == 1:
        core_docs = frappe.get_all("Vendor Onboarding", filters = {"unique_multi_comp_id":doc.unique_multi_comp_id, "head_target": 0})
        vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)
        if len(core_docs)<1:
            return
        if doc.multi_records_populated != 1:
            for vend_onb_doc in core_docs:
                result = populate_vendor_data_from_existing_onboarding(
                    vendor_master.name, 
                    vendor_master.office_email_primary,
                    vend_onb_doc,
                    doc.name
                )
            
            if result['status'] != 'success':
                frappe.log_error(f"Population failed for {vend_onb_doc}: {result['message']}", 
                               "Multi Company Population Error")
                
            doc.multi_records_populated = 1
            frappe.db.set_value("Vendor Onboarding", doc.name, "multi_records_populated", 1)





def optimized_update_van_core_docs_multi_case(doc, method=None):
    """
    Optimized version of your multi-company update function
    """
    if not (doc.head_target == 1 and doc.registered_for_multi_companies == 1 and 
            doc.form_fully_submitted_by_vendor == 1):
        return
    
    if doc.multi_records_populated == 1:
        return  # Already populated
    
    try:
        # Get all core documents in one query
        core_docs = frappe.db.sql("""
            SELECT name 
            FROM `tabVendor Onboarding` 
            WHERE unique_multi_comp_id = %s AND head_target = 0
        """, (doc.unique_multi_comp_id,), as_dict=True)
        
        if not core_docs:
            return
        
        # Get vendor master
        vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)
        
        # Use optimized populator
        populator = VendorDataPopulator()
        
        for vend_onb_doc in core_docs:
            result = populator.populate_vendor_data_from_existing_onboarding(
                vendor_master.name, 
                vendor_master.office_email_primary,
                vend_onb_doc['name'],
                doc.name
            )
            
            if result['status'] != 'success':
                frappe.log_error(f"Population failed for {vend_onb_doc['name']}: {result['message']}", 
                               "Multi Company Population Error")
        
        # Mark as populated
        frappe.db.set_value("Vendor Onboarding", doc.name, "multi_records_populated", 1)
        frappe.db.commit()
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Multi company update error: {frappe.get_traceback()}", 
                        "Multi Company Update Error")


# Monitoring and debugging functions
@frappe.whitelist()
def get_population_status(vendor_onboarding_name):
    """
    Get status of data population for a vendor onboarding record
    """
    try:
        # Get basic info
        basic_info = frappe.db.sql("""
            SELECT name, ref_no, onboarding_form_status, multi_records_populated,
                   document_details, payment_detail, manufacturing_details, certificate_details
            FROM `tabVendor Onboarding` 
            WHERE name = %s
        """, (vendor_onboarding_name,), as_dict=True)
        
        if not basic_info:
            return {"status": "error", "message": "Vendor onboarding record not found"}
        
        info = basic_info[0]
        
        # Check if related documents have data
        status = {
            "vendor_onboarding": info['name'],
            "vendor_master": info['ref_no'],
            "form_status": info['onboarding_form_status'],
            "multi_records_populated": info['multi_records_populated'],
            "documents": {}
        }
        
        # Check each document type
        if info['document_details']:
            legal_data = frappe.db.sql("SELECT COUNT(*) as count FROM `tabGST Table` WHERE parent = %s", 
                                     (info['document_details'],), as_dict=True)
            status["documents"]["legal_documents"] = {
                "name": info['document_details'],
                "gst_records": legal_data[0]['count'] if legal_data else 0
            }
        
        if info['payment_detail']:
            banker_data = frappe.db.sql("SELECT COUNT(*) as count FROM `tabBanker Details` WHERE parent = %s", 
                                      (info['payment_detail'],), as_dict=True)
            status["documents"]["payment_details"] = {
                "name": info['payment_detail'],
                "banker_records": banker_data[0]['count'] if banker_data else 0
            }
        
        if info['manufacturing_details']:
            material_data = frappe.db.sql("SELECT COUNT(*) as count FROM `tabMaterials Supplied` WHERE parent = %s", 
                                        (info['manufacturing_details'],), as_dict=True)
            status["documents"]["manufacturing_details"] = {
                "name": info['manufacturing_details'],
                "material_records": material_data[0]['count'] if material_data else 0
            }
        
        if info['certificate_details']:
            cert_data = frappe.db.sql("SELECT COUNT(*) as count FROM `tabCertificates` WHERE parent = %s", 
                                    (info['certificate_details'],), as_dict=True)
            status["documents"]["certificate_details"] = {
                "name": info['certificate_details'],
                "certificate_records": cert_data[0]['count'] if cert_data else 0
            }
        
        return {"status": "success", "data": status}
        
    except Exception as e:
        return {"status": "error", "message": f"Status check failed: {str(e)}"}


# Integration with your existing code
def enhanced_update_van_core_docs_multi_case(doc, method=None):
    """
    Enhanced version that can replace your existing function
    """
    if not (doc.head_target == 1 and doc.registered_for_multi_companies == 1 and 
            doc.form_fully_submitted_by_vendor == 1):
        return
    
    if doc.multi_records_populated == 1:
        return
    
    # Use the optimized function
    optimized_update_van_core_docs_multi_case(doc, method)
    
    # Log the operation
    frappe.log_error(f"Multi-company records populated for {doc.name}", "Multi Company Population Success")





def safe_get_doc(doctype, name):
    try:
        if name:  # only try if not None/empty
            return frappe.get_doc(doctype, name)
    except frappe.DoesNotExistError:
        return None
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error fetching {doctype} {name}")
        return None
    return None



# Send the Emails to Purchase, Accounts team for approval of Changes in Vendor Document details

@frappe.whitelist()
def send_doc_change_req_email(doc, method=None):
    if doc.register_by_account_team == 0:
        if doc.onboarding_form_status == "Approved" and doc.allow_to_change_document_details_by_purchase_team == 1:
            send_doc_change_req_email_accounts_team(doc, method=None)
        else:
            pass

    elif doc.register_by_account_team == 1:
        if doc.onboarding_form_status == "Approved" and doc.allow_to_change_document_details_by_accounts_team == 1:
            send_doc_change_req_email_accounts_head(doc, method=None)
        else:
            pass   
    
    else:
        pass


# for Accounts Team (purchase team flow)-------------------

def send_doc_change_req_email_accounts_team(doc, method=None):
    try:
        http_server = frappe.conf.get("backend_http")
        vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)

        register_by = frappe.db.get_value(
            "User",
            {"name": doc.registered_by},
            "full_name"
        )

        accounts_team = frappe.db.get_value(
            "User",
            {"name": doc.accounts_t_approval},
            "full_name"
        )
       
        subject = f"Change Request for Vendor: {vendor_master.vendor_name}"

        # Generate action URLs
        allow_url = f"{http_server}/api/method/vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.set_accounts_team_approval_check?vendor_onboarding={doc.name}&action=allow"
        reject_url = f"{http_server}/api/method/vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.set_accounts_team_approval_check?vendor_onboarding={doc.name}&action=reject"
    
        # Email body
        message = f"""
                <p>Dear {accounts_team},</p>
                <p>
                    The vendor <b>{vendor_master.vendor_name}</b> has requested changes to its details.  
                    {register_by} (Purchase Team) already approved the request.
                    Kindly review the request and take appropriate action by clicking one of the buttons below:
                </p>
                <p>
                    <a href="{allow_url}" style="background-color:green;color:white;padding:8px 16px;
                    text-decoration:none;border-radius:4px;">Allow</a>
                    
                    &nbsp;&nbsp;
                    
                    <a href="{reject_url}" style="background-color:red;color:white;padding:8px 16px;
                    text-decoration:none;border-radius:4px;">Reject</a>
                </p>
                <br>
                <p><b>Remarks from vendor:</b> {doc.vendor_remarks}</p>
                <p>Thank you,<br>Vendor Management System</p>
            """
        
        frappe.custom_sendmail(
            recipients=[doc.accounts_t_approval],
            subject=subject,
            message=message,
            now=True
        )
    
        # Mark mail as sent
        frappe.db.set_value(
            "Vendor Onboarding",
            doc.name,
            "change_details_req_mail_sent_to_accounts_team",
            1
        )
    
        return {
            "status": "success",
            "message": "Email sent successfully"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "send_doc_change_req_email_accounts_team")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def set_accounts_team_approval_check(vendor_onboarding: str, action: str):
    try:
        if not vendor_onboarding or not action:
            return {
                "status": "error",
                "message": "Missing required parameters (vendor_onboarding, action)."
            }

        doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        if doc.get("allow_to_change_document_details_by_accounts_team") == 1:
            return {
                "status": "error",
                "message": f"This vendor onboarding ({vendor_onboarding}) has already been processed."
            }

        if action == "allow":
            doc.allow_to_change_document_details_by_accounts_team = 1
            status = "Allowed"
        elif action == "reject":
            doc.allow_to_change_document_details_by_accounts_team = 0
            status = "Rejected"
        else:
            return {
                "status": "error",
                "message": "Invalid action. Must be 'allow' or 'reject'."
            }

        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Your response has been recorded for Vendor Onboarding {vendor_onboarding}.",
            "action": status
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "set_approval_check")
        return {
            "status": "error",
            "message": "Failed to update.",
            "error": str(e)
        }


# For Accounts Head (accounts team approval flow)----------------------------------------------------------

def send_doc_change_req_email_accounts_head(doc, method=None):
    try:
        http_server = frappe.conf.get("backend_http")
        vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)

        register_by = frappe.db.get_value(
            "User",
            {"name": doc.registered_by},
            "full_name"
        )

        accounts_head = frappe.db.get_value(
            "User",
            {"name": doc.accounts_head_approval},
            "full_name"
        )
       
        subject = f"Change Request for Vendor: {vendor_master.vendor_name}"

        # Generate action URLs
        allow_url = f"{http_server}/api/method/vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.set_accounts_head_approval_check?vendor_onboarding={doc.name}&action=allow"
        reject_url = f"{http_server}/api/method/vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.set_accounts_head_approval_check?vendor_onboarding={doc.name}&action=reject"
    
        # Email body
        message = f"""
                <p>Dear {accounts_head},</p>
                <p>
                    The vendor <b>{vendor_master.vendor_name}</b> has requested changes to its details.  
                    {register_by} (Accounts Team) already approved the request.
                    Kindly review the request and take appropriate action by clicking one of the buttons below:
                </p>
                <p>
                    <a href="{allow_url}" style="background-color:green;color:white;padding:8px 16px;
                    text-decoration:none;border-radius:4px;">Allow</a>
                    
                    &nbsp;&nbsp;
                    
                    <a href="{reject_url}" style="background-color:red;color:white;padding:8px 16px;
                    text-decoration:none;border-radius:4px;">Reject</a>
                </p>
                <br>
                <p><b>Remarks from vendor:</b> {doc.vendor_remarks}</p>
                <p>Thank you,<br>Vendor Management System</p>
            """
        
        frappe.custom_sendmail(
            recipients=[doc.accounts_head_approval],
            subject=subject,
            message=message,
            now=True
        )
    
        # Mark mail as sent
        frappe.db.set_value(
            "Vendor Onboarding",
            doc.name,
            "change_details_req_mail_sent_to_accounts_head",
            1
        )
    
        return {
            "status": "success",
            "message": "Email sent successfully"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "send_doc_change_req_email_accounts_team")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def set_accounts_head_approval_check(vendor_onboarding: str, action: str):
    try:
        if not vendor_onboarding or not action:
            return {
                "status": "error",
                "message": "Missing required parameters (vendor_onboarding, action)."
            }

        doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        if doc.get("allow_to_change_document_details_by_accounts_head") == 1:
            return {
                "status": "error",
                "message": f"This vendor onboarding ({vendor_onboarding}) has already been processed."
            }

        if action == "allow":
            doc.allow_to_change_document_details_by_accounts_head = 1
            status = "Allowed"
        elif action == "reject":
            doc.allow_to_change_document_details_by_accounts_head = 0
            status = "Rejected"
        else:
            return {
                "status": "error",
                "message": "Invalid action. Must be 'allow' or 'reject'."
            }

        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Your response has been recorded for Vendor Onboarding {vendor_onboarding}.",
            "action": status
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "set_approval_check")
        return {
            "status": "error",
            "message": "Failed to update.",
            "error": str(e)
        }