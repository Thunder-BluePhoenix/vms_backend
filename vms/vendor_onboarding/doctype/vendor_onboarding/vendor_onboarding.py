# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
import json
from frappe.utils import now_datetime
from datetime import timedelta

# Import all the existing functions to maintain functionality
from vms.APIs.sap.sap import update_sap_vonb
from vms.vendor_onboarding.vendor_document_management import on_vendor_onboarding_submit
from vms.APIs.vendor_onboarding.vendor_registration_helper import populate_vendor_data_from_existing_onboarding
from vms.vendor_onboarding.doctype.vendor_onboarding.update_related_doc import VendorDataPopulator

populator = VendorDataPopulator()




class VendorOnboarding(Document):
    
    def validate(self):
        """
        Validation method - runs before save
        Keep lightweight validation here only
        """
        try:
            # Basic validation only - no heavy operations
            # self.validate_basic_fields()
            pass
            
        except Exception as e:
            frappe.log_error(f"Validation error in VendorOnboarding {self.name}: {str(e)}")
            frappe.throw(f"Validation failed: {str(e)}")
    
    def validate_basic_fields(self):
        """Basic field validation only"""
        if not self.vendor_name:
            frappe.throw("Vendor Name is required")
        
        if self.ref_no and not self.is_new():
            # Check for duplicate ref_no
            existing = frappe.db.exists("Vendor Onboarding", {
                "ref_no": self.ref_no,
                "name": ["!=", self.name]
            })
            if existing:
                frappe.throw(f"Reference Number {self.ref_no} already exists")
    
    def before_save(self):
        """
        Before save hook - for data manipulation before saving
        NO database commits or heavy operations here
        """
        try:
            # Store original document for comparison
            if not self.is_new():
                self._original_doc = self.get_doc_before_save()
            
            # Set status based on current state (no DB commits)
            self.set_status_before_save()
            
            # Update related documents safely (without commits)
            if not self.is_new():
                self.update_related_documents_safe()
                
            # Set QMS required value for multi-company
            self.set_qms_required_value_safe()
                
        except Exception as e:
            frappe.log_error(f"Before save error in VendorOnboarding {self.name}: {str(e)}")
            # Don't throw here to prevent save failure unless critical
    
    def set_status_before_save(self):
        """
        Set onboarding status based on current field values
        NO database commits - just field updates
        """
        new_status = None
        new_rejected = None

        if self.invalid == 0:
            if self.register_by_account_team == 0 and self.rejected == 0:
                if (self.purchase_team_undertaking and 
                    self.accounts_team_undertaking and 
                    self.purchase_head_undertaking and 
                    self.data_sent_to_sap == 1):
                    new_status = "Approved"
                    new_rejected = False
                elif (self.purchase_team_undertaking and 
                      self.accounts_team_undertaking and 
                      self.purchase_head_undertaking and 
                      self.data_sent_to_sap != 1):
                    new_status = "SAP Error"
                    new_rejected = False
                elif self.rejected:
                    new_status = "Rejected"
                else:
                    new_status = "Pending"

            elif self.register_by_account_team == 1 and self.rejected == 0:
                if (self.accounts_team_undertaking and 
                    self.accounts_head_undertaking and 
                    self.data_sent_to_sap == 1):
                    new_status = "Approved"
                    new_rejected = False
                elif (self.accounts_team_undertaking and 
                      self.accounts_head_undertaking and 
                      self.data_sent_to_sap != 1):
                    new_status = "SAP Error"
                    new_rejected = False
                elif self.rejected:
                    new_status = "Rejected"
                else:
                    new_status = "Pending"
                    
            elif self.rejected:
                new_status = "Rejected"
            else:
                new_status = "Pending"
        else:
            new_status = "Invalid"

        # Only update if status actually changed
        if new_status and new_status != self.onboarding_form_status:
            self.onboarding_form_status = new_status
            
        if new_rejected is not None and new_rejected != self.rejected:
            self.rejected = new_rejected
    
    def set_qms_required_value_safe(self):
        """Set QMS required value for multi-company without DB commits"""
        try:
            if self.registered_for_multi_companies == 1:
                for row in self.multiple_company:
                    if row.company == self.company_name:
                        self.qms_required = row.qms_required
                        break
        except Exception as e:
            frappe.log_error(f"Error setting QMS required value for {self.name}: {str(e)}")
    
    def update_related_documents_safe(self):
        """
        Safely update related documents without causing recursion
        NO database commits here
        """
        try:
            # Mark this update to prevent recursive calls
            if not hasattr(frappe.local, 'vendor_onboarding_updating'):
                frappe.local.vendor_onboarding_updating = set()
            
            if self.name in frappe.local.vendor_onboarding_updating:
                return  # Prevent recursion
                
            frappe.local.vendor_onboarding_updating.add(self.name)
            
            # Update core documents (without commits) - only if significant changes
            if self.has_significant_changes():
                update_van_core_docs(self, method=None)
                update_van_core_docs_multi_case(self, method=None)
            
            # Remove from updating set
            frappe.local.vendor_onboarding_updating.discard(self.name)
            
        except Exception as e:
            frappe.log_error(f"Error updating related docs for {self.name}: {str(e)}")
            frappe.local.vendor_onboarding_updating.discard(self.name)
    
    def after_insert(self):
        """
        After insert hook - for post-creation tasks
        """
        try:
            # Set up expiration handling
            self.setup_expiration_handling()
            
            # Send ASA form link in background
            frappe.enqueue(
                method="vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.send_asa_form_link_job",
                queue='default',
                timeout=300,
                now=False,
                job_name=f'send_asa_form_link_{self.name}',
                doc_name=self.name
            )
            
        except Exception as e:
            frappe.log_error(f"After insert error in VendorOnboarding {self.name}: {str(e)}")
    
    def setup_expiration_handling(self):
        """Setup vendor onboarding expiration"""
        try:
            exp_doc = frappe.get_doc("Vendor Onboarding Settings")
            exp_t_sec = float(exp_doc.vendor_onboarding_form_validity) if exp_doc else 604800
            
            # Enqueue expiration job
            frappe.enqueue(
                method="vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.handle_expiration_job",
                queue='default',
                timeout=exp_t_sec + 800,
                now=False,
                job_name=f'vendor_onboarding_expiration_{self.name}',
                doc_name=self.name,
                exp_seconds=exp_t_sec
            )
            
        except Exception as e:
            frappe.log_error(f"Error setting up expiration for {self.name}: {str(e)}")
    
    def on_update(self):
        """
        On update hook - MINIMAL operations only
        Only enqueue background tasks - NO heavy operations here
        """
        try:
            # Prevent recursive updates
            if getattr(self, '_skip_on_update', False):
                return
            
            # Only enqueue tasks if there are significant changes
            if self.has_significant_changes():
                self.enqueue_post_update_tasks()
            
        except Exception as e:
            frappe.log_error(f"On update error in VendorOnboarding {self.name}: {str(e)}")
    
    def has_significant_changes(self):
        """
        Check if document has changes that require heavy processing
        """
        try:
            if self.is_new():
                return True
                
            if not hasattr(self, '_original_doc') or not self._original_doc:
                return True
                
            # Check critical fields that require heavy processing
            critical_fields = [
                'vendor_name', 'vendor_country', 'onboarding_form_status',
                'purchase_team_undertaking', 'purchase_head_undertaking',
                'accounts_team_undertaking', 'accounts_head_undertaking',
                'data_sent_to_sap', 'form_fully_submitted_by_vendor',
                'mandatory_data_filled', 'company_name'
            ]
            
            # Check if any critical field changed
            for field in critical_fields:
                if self.get(field) != self._original_doc.get(field):
                    return True
                    
            return False
            
        except Exception as e:
            frappe.log_error(f"Error checking significant changes for {self.name}: {str(e)}")
            return True  # Assume changes if error occurs
    
    def enqueue_post_update_tasks(self):
        """
        Enqueue heavy operations to run after the save is complete
        """
        try:
            # Enqueue all heavy tasks
            frappe.enqueue(
                method="vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.run_post_update_tasks",
                queue='default',
                timeout=600,
                now=False,
                job_name=f'post_update_tasks_{self.name}_{frappe.utils.now_datetime().strftime("%Y%m%d_%H%M%S")}',
                doc_name=self.name,
                user=frappe.session.user,
                is_new=self.is_new()
            )
                
        except Exception as e:
            frappe.log_error(f"Error enqueuing post-update tasks for {self.name}: {str(e)}")


# Background job methods (outside the class)

@frappe.whitelist()
def run_post_update_tasks(doc_name, user=None, is_new=False):
    """
    Run heavy post-update tasks in background
    This replaces the old on_update method functionality
    """
    try:
        # Set user context
        if user:
            frappe.set_user(user)
            
        doc = frappe.get_doc("Vendor Onboarding", doc_name)
        
        # Mark document to skip on_update during these operations
        doc._skip_on_update = True
        
        # Run tasks in sequence with error handling
        task_results = {}
        
        # 1. Validate mandatory fields
        task_results['validation'] = run_field_validation(doc)
        
        # 2. Update company data
        task_results['company_update'] = run_company_update(doc)
        
        # 3. Update tracking tables
        task_results['tracking_update'] = run_tracking_update(doc)
        
        # 4. Send emails if needed
        task_results['email_notifications'] = run_email_notifications(doc)
        
        # 5. Sync and maintain records
        task_results['sync_maintain'] = run_sync_maintain(doc)
        
        # 6. SAP integration (only if ready and not already sent)
        if should_trigger_sap_update(doc):
            task_results['sap_update'] = run_sap_integration(doc)
        
        # 7. Document submission handling
        if doc.onboarding_form_status == "Approved":
            task_results['submission_handling'] = run_submission_handling(doc)
        
        # 8. Send document change emails
        task_results['doc_change_emails'] = run_doc_change_emails(doc)
        
        # Log success
        frappe.logger().info(f"Post-update tasks completed for {doc_name}: {task_results}")
        
        # Notify frontend
        frappe.publish_realtime(
            event="vendor_onboarding_updated",
            message={
                "name": doc_name,
                "status": doc.onboarding_form_status,
                "modified": doc.modified,
                "task_results": task_results
            },
            user=user or frappe.session.user
        )
        
    except Exception as e:
        frappe.log_error(f"Error in post-update tasks for {doc_name}: {str(e)}")
        frappe.logger().error(f"Post-update tasks failed for {doc_name}: {str(e)}")


def run_field_validation(doc):
    """Run field validation - replaces on_update_check_fields"""
    try:
        on_update_check_fields(doc, method=None)
        return {"status": "success", "message": "Field validation completed"}
    except Exception as e:
        frappe.log_error(f"Field validation error for {doc.name}: {str(e)}")
        return {"status": "error", "message": str(e)}


def run_company_update(doc):
    """Run company update - replaces vendor_company_update"""
    try:
        vendor_company_update(doc, method=None)
        return {"status": "success", "message": "Company update completed"}
    except Exception as e:
        frappe.log_error(f"Company update error for {doc.name}: {str(e)}")
        return {"status": "error", "message": str(e)}


def run_tracking_update(doc):
    """Run tracking table updates - replaces update_ven_onb_record_table"""
    try:
        update_ven_onb_record_table(doc, method=None)
        return {"status": "success", "message": "Tracking update completed"}
    except Exception as e:
        frappe.log_error(f"Tracking update error for {doc.name}: {str(e)}")
        return {"status": "error", "message": str(e)}


def run_email_notifications(doc):
    """Run email notifications - replaces check_vnonb_send_mails"""
    try:
        check_vnonb_send_mails(doc, method=None)
        return {"status": "success", "message": "Email notifications completed"}
    except Exception as e:
        frappe.log_error(f"Email notification error for {doc.name}: {str(e)}")
        return {"status": "error", "message": str(e)}


def run_sync_maintain(doc):
    """Run sync maintain - replaces sync_maintain"""
    try:
        sync_maintain(doc, method=None)
        return {"status": "success", "message": "Sync maintain completed"}
    except Exception as e:
        frappe.log_error(f"Sync maintain error for {doc.name}: {str(e)}")
        return {"status": "error", "message": str(e)}


def run_doc_change_emails(doc):
    """Run document change emails - replaces send_doc_change_req_email"""
    try:
        send_doc_change_req_email(doc, method=None)
        return {"status": "success", "message": "Document change emails completed"}
    except Exception as e:
        frappe.log_error(f"Document change email error for {doc.name}: {str(e)}")
        return {"status": "error", "message": str(e)}


def should_trigger_sap_update(doc):
    """
    Determine if SAP update should be triggered
    Only trigger if all conditions are met and not already sent
    """
    try:
        # Check if ready for SAP
        is_ready_for_sap = False
        
        if doc.register_by_account_team == 0:
            # Regular registration path
            is_ready_for_sap = (
                doc.purchase_team_undertaking and 
                doc.accounts_team_undertaking and 
                doc.purchase_head_undertaking
            )
        else:
            # Account team registration path
            is_ready_for_sap = (
                doc.accounts_team_undertaking and 
                doc.accounts_head_undertaking
            )
        
        # Only trigger if ready, not already sent, and has mandatory data
        return (
            is_ready_for_sap and
            doc.data_sent_to_sap != 1 and
            doc.mandatory_data_filled == 1 and
            not doc.rejected and
            not doc.expired
        )
        
    except Exception as e:
        frappe.log_error(f"Error checking SAP trigger conditions for {doc.name}: {str(e)}")
        return False


def run_sap_integration(doc):
    """Run SAP integration safely - replaces update_sap_vonb"""
    try:
        # Use the existing SAP integration function
        result = update_sap_vonb(doc, method=None)
        
        if result and result.get('status') == 'success':
            return {"status": "success", "message": "SAP integration completed", "result": result}
        else:
            return {"status": "partial", "message": "SAP integration completed with warnings", "result": result}
            
    except Exception as e:
        frappe.log_error(f"SAP integration error for {doc.name}: {str(e)}")
        return {"status": "error", "message": str(e)}


def run_submission_handling(doc):
    """Run submission handling - replaces on_vendor_onboarding_submit"""
    try:
        on_vendor_onboarding_submit(doc, method=None)
        return {"status": "success", "message": "Submission handling completed"}
    except Exception as e:
        frappe.log_error(f"Submission handling error for {doc.name}: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def handle_expiration_job(doc_name, exp_seconds):
    """Handle vendor onboarding expiration - replaces handle_expiration"""
    try:
        time.sleep(float(exp_seconds))
        
        doc = frappe.get_doc("Vendor Onboarding", doc_name)
        
        if doc.form_fully_submitted_by_vendor == 0:
            doc.db_set('expired', 1, update_modified=False)
            doc.db_set('onboarding_form_status', "Expired", update_modified=False)
            frappe.db.commit()
            
            frappe.logger().info(f"Vendor onboarding {doc_name} expired")
            
    except Exception as e:
        frappe.log_error(f"Error handling expiration for {doc_name}: {str(e)}")


@frappe.whitelist()
def send_asa_form_link_job(doc_name):
    """Send ASA form link - replaces sent_asa_form_link"""
    try:
        doc = frappe.get_doc("Vendor Onboarding", doc_name)
        sent_asa_form_link(doc, method=None)
        
    except Exception as e:
        frappe.log_error(f"Error sending ASA form link for {doc_name}: {str(e)}")



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
    




@frappe.whitelist()
def cleanup_stuck_sap_status():
    """Cron job to identify and fix documents stuck in processing"""
    try:
        stuck_docs = frappe.db.sql("""
            SELECT name, ref_no, vendor_name, onboarding_form_status
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status = 'SAP Error'
                AND data_sent_to_sap != 1
                AND purchase_team_undertaking = 1
                AND accounts_team_undertaking = 1
                AND purchase_head_undertaking = 1
                AND accounts_head_undertaking = 1
                AND modified < DATE_SUB(NOW(), INTERVAL 2 HOUR)
        """, as_dict=True)
        
        fixed_count = 0
        
        for doc_data in stuck_docs:
            try:
                # Check if there are successful SAP entries for this vendor
                sap_success = frappe.db.sql("""
                    SELECT COUNT(*) as count
                    FROM `tabVMS SAP Logs`
                    WHERE 
                        vendor_onboarding = %s
                        AND transaction_status = 'Success'
                        AND creation > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """, (doc_data.name,), as_dict=True)
                
                if sap_success and sap_success[0].count > 0:
                    # Has successful SAP entries, update status
                    frappe.db.sql("""
                        UPDATE `tabVendor Onboarding` 
                        SET 
                            onboarding_form_status = 'Approved',
                            data_sent_to_sap = 1,
                            modified = %s,
                            modified_by = %s
                        WHERE name = %s
                    """, (frappe.utils.now(), "Administrator", doc_data.name))
                    
                    fixed_count += 1
                    
                    # Log the correction
                    frappe.get_doc({
                        "doctype": "Comment",
                        "comment_type": "Info",
                        "reference_doctype": "Vendor Onboarding",
                        "reference_name": doc_data.name,
                        "content": f"Auto-corrected SAP status based on successful SAP logs",
                        "comment_email": "Administrator",
                        "comment_by": "Administrator"
                    }).insert(ignore_permissions=True)
                    
            except Exception as e:
                frappe.log_error(f"Error fixing stuck document {doc_data.name}: {str(e)}")
                continue
                
        if fixed_count > 0:
            frappe.db.commit()
            frappe.logger().info(f"Fixed {fixed_count} stuck SAP status documents")
            
    except Exception as e:
        frappe.log_error(f"Error in cleanup_stuck_sap_status: {str(e)}")


@frappe.whitelist()
def manual_fix_vendor_onboarding(onb_name):
    """Manual utility to fix a specific vendor onboarding document"""
    try:
        if not frappe.has_permission("Vendor Onboarding", "write"):
            return {"status": "error", "message": "Insufficient permissions"}
            
        doc = frappe.get_doc("Vendor Onboarding", onb_name)
        
        # Check if document should be approved
        should_be_approved = (
            doc.purchase_team_undertaking and 
            doc.accounts_team_undertaking and 
            doc.purchase_head_undertaking and
            doc.accounts_head_undertaking and
            doc.mandatory_data_filled == 1
        )
        
        if should_be_approved:
            # Check SAP logs for this vendor
            sap_logs = frappe.db.sql("""
                SELECT transaction_status, COUNT(*) as count
                FROM `tabVMS SAP Logs`
                WHERE vendor_onboarding = %s
                GROUP BY transaction_status
            """, (onb_name,), as_dict=True)
            
            success_count = 0
            error_count = 0
            
            for log in sap_logs:
                if log.transaction_status == 'Success':
                    success_count = log.count
                else:
                    error_count = log.count
            
            # Determine correct status
            if success_count > 0:
                new_status = "Approved"
                data_sent_to_sap = 1
                message = f"Fixed to Approved status (Found {success_count} successful SAP entries)"
            elif error_count > 0:
                new_status = "SAP Error"
                data_sent_to_sap = 0
                message = f"Status set to SAP Error ({error_count} failed SAP attempts)"
            else:
                # No SAP attempts yet, trigger SAP integration
                new_status = "Pending SAP"
                data_sent_to_sap = 0
                message = "Ready for SAP integration"
                
                # Enqueue SAP integration
                frappe.enqueue(
                    method="vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.run_sap_integration",
                    queue='default',
                    timeout=600,
                    now=False,
                    job_name=f'manual_sap_integration_{onb_name}',
                    doc=doc
                )
            
            # Update the document
            frappe.db.sql("""
                UPDATE `tabVendor Onboarding` 
                SET 
                    onboarding_form_status = %s,
                    data_sent_to_sap = %s,
                    modified = %s,
                    modified_by = %s
                WHERE name = %s
            """, (new_status, data_sent_to_sap, frappe.utils.now(), frappe.session.user, onb_name))
            
            frappe.db.commit()
            
            # Log the manual fix
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Info",
                "reference_doctype": "Vendor Onboarding",
                "reference_name": onb_name,
                "content": f"Manual fix applied by {frappe.session.user}: {message}",
                "comment_email": frappe.session.user,
                "comment_by": frappe.session.user
            }).insert(ignore_permissions=True)
            
            return {
                "status": "success", 
                "message": message,
                "new_status": new_status,
                "sap_success_count": success_count,
                "sap_error_count": error_count
            }
        else:
            missing = []
            if not doc.purchase_team_undertaking:
                missing.append("Purchase Team Approval")
            if not doc.accounts_team_undertaking:
                missing.append("Accounts Team Approval")
            if not doc.purchase_head_undertaking:
                missing.append("Purchase Head Approval")
            if not doc.accounts_head_undertaking:
                missing.append("Accounts Head Approval")
            if doc.mandatory_data_filled != 1:
                missing.append("Mandatory Data Validation")
                
            return {
                "status": "error", 
                "message": f"Document not ready for approval. Missing: {', '.join(missing)}"
            }
            
    except Exception as e:
        frappe.log_error(f"Error in manual_fix_vendor_onboarding for {onb_name}: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def check_vendor_onboarding_health(onb_name):
    """Health check utility for vendor onboarding documents"""
    try:
        doc = frappe.get_doc("Vendor Onboarding", onb_name)
        
        health_report = {
            "document_name": onb_name,
            "current_status": doc.onboarding_form_status,
            "checks": [],
            "recommendations": [],
            "linked_documents": {},
            "sap_status": {},
            "overall_health": "good"
        }
        
        # Check linked documents
        linked_docs = ["payment_detail", "document_details", "certificate_details", "manufacturing_details"]
        for link_field in linked_docs:
            link_value = doc.get(link_field)
            if link_value:
                try:
                    # Try to fetch the linked document
                    if link_field == "payment_detail":
                        linked_doc = frappe.get_doc("Vendor Onboarding Payment Details", link_value)
                    elif link_field == "document_details":
                        linked_doc = frappe.get_doc("Legal Documents", link_value)
                    elif link_field == "certificate_details":
                        linked_doc = frappe.get_doc("Vendor Onboarding Certificates", link_value)
                    elif link_field == "manufacturing_details":
                        linked_doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", link_value)
                    
                    health_report["linked_documents"][link_field] = {
                        "status": "exists",
                        "name": link_value,
                        "modified": linked_doc.modified
                    }
                except:
                    health_report["linked_documents"][link_field] = {
                        "status": "missing",
                        "name": link_value
                    }
                    health_report["overall_health"] = "warning"
                    health_report["recommendations"].append(f"Check {link_field} document: {link_value}")
            else:
                health_report["linked_documents"][link_field] = {"status": "not_set"}
        
        # Check approvals
        approval_fields = [
            "purchase_team_undertaking", "purchase_head_undertaking",
            "accounts_team_undertaking", "accounts_head_undertaking"
        ]
        
        approved_count = sum(1 for field in approval_fields if doc.get(field))
        health_report["checks"].append({
            "name": "Approvals",
            "status": "complete" if approved_count == 4 else "pending",
            "details": f"{approved_count}/4 approvals completed"
        })
        
        # Check mandatory data
        health_report["checks"].append({
            "name": "Mandatory Data",
            "status": "complete" if doc.mandatory_data_filled == 1 else "incomplete",
            "details": "All mandatory fields filled" if doc.mandatory_data_filled == 1 else "Missing mandatory data"
        })
        
        # Check SAP status
        sap_logs = frappe.db.sql("""
            SELECT transaction_status, COUNT(*) as count, MAX(creation) as last_attempt
            FROM `tabVMS SAP Logs`
            WHERE vendor_onboarding = %s
            GROUP BY transaction_status
            ORDER BY last_attempt DESC
        """, (onb_name,), as_dict=True)
        
        for log in sap_logs:
            health_report["sap_status"][log.transaction_status] = {
                "count": log.count,
                "last_attempt": log.last_attempt
            }
        
        # Check for child table data
        child_tables = ["vendor_types", "contact_details", "number_of_employee", "machinery_detail"]
        for table in child_tables:
            table_data = doc.get(table) or []
            health_report["checks"].append({
                "name": f"Child Table: {table}",
                "status": "has_data" if len(table_data) > 0 else "empty",
                "details": f"{len(table_data)} rows"
            })
        
        # Overall health assessment
        error_count = sum(1 for check in health_report["checks"] if check["status"] in ["incomplete", "missing"])
        if error_count > 2:
            health_report["overall_health"] = "critical"
        elif error_count > 0:
            health_report["overall_health"] = "warning"
        
        return health_report
        
    except Exception as e:
        return {
            "document_name": onb_name,
            "overall_health": "error",
            "error": str(e)
        }


@frappe.whitelist()
def reset_vendor_onboarding_status(onb_name, new_status="Pending"):
    """Reset vendor onboarding status for testing/debugging"""
    try:
        if not frappe.has_permission("Vendor Onboarding", "write"):
            return {"status": "error", "message": "Insufficient permissions"}
            
        # Reset key fields
        frappe.db.sql("""
            UPDATE `tabVendor Onboarding` 
            SET 
                onboarding_form_status = %s,
                data_sent_to_sap = 0,
                modified = %s,
                modified_by = %s
            WHERE name = %s
        """, (new_status, frappe.utils.now(), frappe.session.user, onb_name))
        
        frappe.db.commit()
        
        # Log the reset
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Vendor Onboarding",
            "reference_name": onb_name,
            "content": f"Status reset to {new_status} by {frappe.session.user}",
            "comment_email": frappe.session.user,
            "comment_by": frappe.session.user
        }).insert(ignore_permissions=True)
        
        return {"status": "success", "message": f"Status reset to {new_status}"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def force_sap_integration(onb_name):
    """Force SAP integration for a specific vendor onboarding"""
    try:
        if not frappe.has_permission("Vendor Onboarding", "write"):
            return {"status": "error", "message": "Insufficient permissions"}
            
        doc = frappe.get_doc("Vendor Onboarding", onb_name)
        
        # Enqueue SAP integration regardless of current status
        frappe.enqueue(
            method="vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.run_sap_integration",
            queue='default',
            timeout=600,
            now=False,
            job_name=f'force_sap_integration_{onb_name}_{frappe.utils.now_datetime().strftime("%Y%m%d_%H%M%S")}',
            doc=doc
        )
        
        return {"status": "success", "message": "SAP integration enqueued"}
        
    except Exception as e:
        frappe.log_error(f"Error in force_sap_integration for {onb_name}: {str(e)}")
        return {"status": "error", "message": str(e)}


# Legacy function support for backward compatibility
@frappe.whitelist(allow_guest=True)
def set_vendor_onboarding_status(vendor_onboarding_name, status):
    """
    Legacy function for setting vendor onboarding status
    Maintained for backward compatibility
    """
    try:
        doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding_name)
        doc.onboarding_form_status = status
        doc.save(ignore_permissions=True)
        return {"status": "success", "message": f"Status updated to {status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Testing and validation functions

@frappe.whitelist()
def test_vendor_onboarding_fixes():
    """Comprehensive test suite for vendor onboarding fixes"""
    test_results = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "detailed_results": [],
        "overall_status": "unknown"
    }
    
    try:
        # Test 1: Create a test vendor onboarding
        test_results["tests_run"] += 1
        try:
            test_doc = create_test_vendor_onboarding()
            test_results["tests_passed"] += 1
            test_results["detailed_results"].append({
                "test": "Create Test Document",
                "status": "PASS",
                "message": f"Created test document: {test_doc.name}"
            })
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["detailed_results"].append({
                "test": "Create Test Document",
                "status": "FAIL",
                "message": str(e)
            })
            return test_results
        
        # Test 2: Test child table data preservation
        test_results["tests_run"] += 1
        try:
            result = test_child_table_preservation(test_doc)
            if result["success"]:
                test_results["tests_passed"] += 1
                test_results["detailed_results"].append({
                    "test": "Child Table Preservation",
                    "status": "PASS",
                    "message": result["message"]
                })
            else:
                test_results["tests_failed"] += 1
                test_results["detailed_results"].append({
                    "test": "Child Table Preservation",
                    "status": "FAIL",
                    "message": result["message"]
                })
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["detailed_results"].append({
                "test": "Child Table Preservation",
                "status": "FAIL",
                "message": str(e)
            })
        
        # Test 3: Test status update logic
        test_results["tests_run"] += 1
        try:
            result = test_status_update_logic(test_doc)
            if result["success"]:
                test_results["tests_passed"] += 1
                test_results["detailed_results"].append({
                    "test": "Status Update Logic",
                    "status": "PASS",
                    "message": result["message"]
                })
            else:
                test_results["tests_failed"] += 1
                test_results["detailed_results"].append({
                    "test": "Status Update Logic",
                    "status": "FAIL",
                    "message": result["message"]
                })
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["detailed_results"].append({
                "test": "Status Update Logic",
                "status": "FAIL",
                "message": str(e)
            })
        
        # Cleanup test document
        try:
            frappe.delete_doc("Vendor Onboarding", test_doc.name, force=True)
        except:
            pass
        
        # Calculate overall status
        if test_results["tests_failed"] == 0:
            test_results["overall_status"] = "ALL TESTS PASSED"
        elif test_results["tests_passed"] > test_results["tests_failed"]:
            test_results["overall_status"] = "MOSTLY PASSED"
        else:
            test_results["overall_status"] = "CRITICAL ISSUES"
        
        return test_results
        
    except Exception as e:
        test_results["detailed_results"].append({
            "test": "Overall Test Suite",
            "status": "FAIL",
            "message": f"Test suite failed: {str(e)}"
        })
        test_results["overall_status"] = "CRITICAL ERROR"
        return test_results


def create_test_vendor_onboarding():
    """Create a test vendor onboarding document"""
    doc = frappe.get_doc({
        "doctype": "Vendor Onboarding",
        "vendor_name": f"Test Vendor {frappe.utils.random_string(5)}",
        "ref_no": f"TEST-{frappe.utils.random_string(5)}",
        "vendor_country": "India",
        "registered_by": frappe.session.user,
        "register_by_account_team": 0
    })
    
    # Add some child table data
    doc.append("contact_details", {
        "name_of_contact_person": "Test Contact",
        "designation": "Manager",
        "phone_number": "1234567890",
        "email_id": "test@example.com"
    })
    
    doc.append("vendor_types", {
        "vendor_type": "Service Provider"
    })
    
    doc.insert(ignore_permissions=True)
    return doc


def test_child_table_preservation(test_doc):
    """Test if child table data is preserved during updates"""
    try:
        # Record original child table data
        original_contacts = len(test_doc.contact_details)
        original_vendor_types = len(test_doc.vendor_types)
        
        # Update the document
        test_doc.vendor_name = f"Updated {test_doc.vendor_name}"
        test_doc.save()
        
        # Reload and check if child table data is preserved
        test_doc.reload()
        
        new_contacts = len(test_doc.contact_details)
        new_vendor_types = len(test_doc.vendor_types)
        
        if new_contacts == original_contacts and new_vendor_types == original_vendor_types:
            return {
                "success": True,
                "message": f"Child table data preserved: {new_contacts} contacts, {new_vendor_types} vendor types"
            }
        else:
            return {
                "success": False,
                "message": f"Child table data lost: contacts {original_contacts}→{new_contacts}, types {original_vendor_types}→{new_vendor_types}"
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_status_update_logic(test_doc):
    """Test the status update logic"""
    try:
        # Test initial status
        if test_doc.onboarding_form_status != "Pending":
            return {"success": False, "message": f"Initial status should be Pending, got {test_doc.onboarding_form_status}"}
        
        # Set approvals
        test_doc.purchase_team_undertaking = 1
        test_doc.accounts_team_undertaking = 1
        test_doc.purchase_head_undertaking = 1
        test_doc.accounts_head_undertaking = 1
        test_doc.mandatory_data_filled = 1
        test_doc.save()
        
        # Check if status updates correctly
        test_doc.reload()
        expected_status = "SAP Error"  # Should be SAP Error since data_sent_to_sap != 1
        
        if test_doc.onboarding_form_status == expected_status:
            return {
                "success": True,
                "message": f"Status correctly updated to {expected_status}"
            }
        else:
            return {
                "success": False,
                "message": f"Status should be {expected_status}, got {test_doc.onboarding_form_status}"
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)}