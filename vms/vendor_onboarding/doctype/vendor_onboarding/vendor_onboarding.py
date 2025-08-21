# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
import json
from vms.utils.custom_send_mail import custom_sendmail

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
	
# def on_update_check_fields(self,method=None):
#     """
#     Alternative function that returns a detailed validation summary
#     """
#     result = validate_mandatory_data(self.name)

#     # set_vendor_onboarding_status(self,method=None)

#     if result["success"]:
#         self.mandatory_data_filled = 1
#         # frappe.db.commit()
#         return f"✅ Validation passed for {len(result['data'])} company records"
#     else:
#         return f"❌ Validation failed: {result['message']}"

def on_update_check_fields(self, method=None):
    """
    Silent validation function that returns a detailed validation summary
    without showing any messages or popups
    """
    result = validate_mandatory_data(self.name)
    
    if result["success"]:
        self.mandatory_data_filled = 1
        # return result
        pass
    else:
        self.mandatory_data_filled = 0
        # return result
        pass



def validate_mandatory_data(onb_ref):
    try:
        
        onb = frappe.get_doc("Vendor Onboarding", onb_ref)
        onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
        onb_pmd = frappe.get_doc("Vendor Onboarding Payment Details", onb.payment_detail)
        pur_org = frappe.get_doc("Purchase Organization Master", onb.purchase_organization)
        pur_grp = frappe.get_doc("Purchase Group Master", onb.purchase_group)
        acc_grp = frappe.get_doc("Account Group Master", onb.account_group)
        onb_reco = frappe.get_doc("Reconciliation Account", onb.reconciliation_account)
        onb_pm_term = frappe.get_doc("Terms of Payment Master", onb.terms_of_payment)
        onb_inco = frappe.get_doc("Incoterm Master", onb.incoterms)
        onb_bank = frappe.get_doc("Bank Master", onb_pmd.bank_name)

        # Boolean field mappings
        payee = 'X' if onb.payee_in_document == 1 else ''
        gr_based_inv_ver = 'X' if onb.gr_based_inv_ver == 1 else ''
        service_based_inv_ver = 'X' if onb.service_based_inv_ver == 1 else ''
        check_double_invoice = 'X' if onb.check_double_invoice == 1 else ''

        # Get vendor type names
        vendor_type_names = []
        for row in onb_vm.vendor_types:
            if row.vendor_type:
                vendor_type_doc = frappe.get_doc("Vendor Type Master", row.vendor_type)
                vendor_type_names.append(vendor_type_doc.vendor_type_name)
        vendor_type_names_str = ", ".join(vendor_type_names)

        validation_errors = []
#--------------------------- impt bnk details check
        # Check for missing table validations first
        # if not onb_pmd.international_bank_details or len(onb_pmd.international_bank_details) == 0:
        #     validation_errors.append("International Bank Details table is empty (Vendor Onboarding Payment Details)")
        
        # if not onb_pmd.intermediate_bank_details or len(onb_pmd.intermediate_bank_details) == 0:
        #     validation_errors.append("Intermediate Bank Details table is empty (Vendor Onboarding Payment Details)")

#-----------------------------------------------------------------------




        # If tables are missing, don't proceed with company-specific validation
        # if validation_errors:
        #     error_message = "Missing Required Tables:\n" + "\n".join(validation_errors)
        #     frappe.log_error(error_message, "Mandatory Data Validation Failed")
        #     return {
        #         "success": False,
        #         "message": error_message,
        #         "data": None
        #     }

        data_list = []

        for company in onb.vendor_company_details:
            vcd = frappe.get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
            com_vcd = frappe.get_doc("Company Master", vcd.company_name)

            # Build data dictionary
            data = {
                "Bukrs": com_vcd.company_code,
                "Ekorg": pur_org.purchase_organization_code,
                "Ktokk": acc_grp.account_group_code,
                "Title": "",
                "Name1": onb_vm.vendor_name,
                "Name2": "",
                "Sort1": onb_vm.search_term,
                "Street": vcd.address_line_1,
                "StrSuppl1": vcd.address_line_2,
                "StrSuppl2": "",
                "StrSuppl3": "",
                "PostCode1": vcd.pincode,
                "City1": vcd.city,
                "Country": vcd.country,
                "J1kftind": "",
                "Region": vcd.state,
                "TelNumber": "",
                "MobNumber": onb_vm.mobile_number,
                "SmtpAddr": onb_vm.office_email_primary,
                "SmtpAddr1": onb_vm.office_email_secondary,
                "Zuawa": "",
                "Akont": onb_reco.reconcil_account_code,
                "Waers": onb_pmd.currency_code,
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
                "J1ipanno": vcd.company_pan_number,
                "J1ipanref": onb_vm.vendor_name,
                "Namev": onb_vm.first_name or "",
                "Name11": onb_vm.last_name or "",
                "Bankl": onb_bank.bank_code,
                "Bankn": onb_pmd.account_number,
                "Bkref": onb_bank.bank_name,
                "Banka": onb_pmd.ifsc_code,
                "Xezer": "",
                "Refno": onb.ref_no,
                "Vedno": "",
                "Zmsg": ""
            }

            # Check if international banking details exist
            # if not onb_pmd.international_bank_details or len(onb_pmd.international_bank_details) == 0:
            #     validation_errors.append(f"Company {com_vcd.company_code}: International bank details are mandatory but missing")
            #     # Set empty values for international bank fields
            #     data.update({
            #         "ZZBENF_NAME": "",
            #         "ZZBEN_BANK_NM": "",
            #         "ZZBEN_ACCT_NO": "",
            #         "ZZBENF_IBAN": "",
            #         "ZZBENF_BANKADDR": "",
            #         "ZZBENF_SHFTADDR": "",
            #         "ZZBENF_ACH_NO": "",
            #         "ZZBENF_ABA_NO": "",
            #         "ZZBENF_ROUTING": "",
            #     })
            # else:
            #     intl_bank = onb_pmd.international_bank_details[0]
            #     data.update({
            #         "ZZBENF_NAME": intl_bank.beneficiary_name,
            #         "ZZBEN_BANK_NM": intl_bank.beneficiary_bank_name,
            #         "ZZBEN_ACCT_NO": intl_bank.beneficiary_account_no,
            #         "ZZBENF_IBAN": intl_bank.beneficiary_iban_no,
            #         "ZZBENF_BANKADDR": intl_bank.beneficiary_bank_address,
            #         "ZZBENF_SHFTADDR": intl_bank.beneficiary_swift_code,
            #         "ZZBENF_ACH_NO": intl_bank.beneficiary_ach_no,
            #         "ZZBENF_ABA_NO": intl_bank.beneficiary_aba_no,
            #         "ZZBENF_ROUTING": intl_bank.beneficiary_routing_no,
            #     })

            # Check if intermediate banking details exist
            # if not onb_pmd.intermediate_bank_details or len(onb_pmd.intermediate_bank_details) == 0:
            #     validation_errors.append(f"Company {com_vcd.company_code}: Intermediate bank details are mandatory but missing")
            #     # Set empty values for intermediate bank fields
            #     data.update({
            #         "ZZINTR_ACCT_NO": "",
            #         "ZZINTR_IBAN": "",
            #         "ZZINTR_BANK_NM": "",
            #         "ZZINTR_BANKADDR": "",
            #         "ZZINTR_SHFTADDR": "",
            #         "ZZINTR_ACH_NO": "",
            #         "ZZINTR_ABA_NO": "",
            #         "ZZINTR_ROUTING": "",
            #     })
            # else:
            #     inter_bank = onb_pmd.intermediate_bank_details[0]
            #     data.update({
            #         "ZZINTR_ACCT_NO": inter_bank.intermediate_account_no,
            #         "ZZINTR_IBAN": inter_bank.intermediate_iban_no,
            #         "ZZINTR_BANK_NM": inter_bank.intermediate_bank_name,
            #         "ZZINTR_BANKADDR": inter_bank.intermediate_bank_address,
            #         "ZZINTR_SHFTADDR": inter_bank.intermediate_swift_code,
            #         "ZZINTR_ACH_NO": inter_bank.intermediate_ach_no,
            #         "ZZINTR_ABA_NO": inter_bank.intermediate_aba_no,
            #         "ZZINTR_ROUTING": inter_bank.intermediate_routing_no,
            #     })

            # Define fields that are intentionally allowed to be empty (these won't be validated)
            allowed_empty_fields = {
                "Title", "Name2", "StrSuppl1", "StrSuppl2", "StrSuppl3", "TelNumber", "Namev", "Name11",
                "SmtpAddr1", "J1kftind", "Zuawa", "Kalsk", "Xezer", "Vedno", "Zmsg"
            }
            
            # Field descriptions with doctype information for better error messages
            field_descriptions = {
                "Bukrs": "Company Code (Company Master)",
                "Ekorg": "Purchase Organization Code (Purchase Organization Master)", 
                "Ktokk": "Account Group Code (Account Group Master)",
                "Name1": "Vendor Name (Vendor Master)",
                "Sort1": "Search Term (Vendor Master)",
                "Street": "Address Line 1 (Vendor Onboarding Company Details)",
                "PostCode1": "Pin Code (Vendor Onboarding Company Details)",
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
                "Namev": "First Name (Vendor Master)",
                "Name11": "Last Name (Vendor Master)",
                "Bankl": "Bank Code (Bank Master)",
                "Bankn": "Account Number (Vendor Onboarding Payment Details)",
                "Bkref": "Bank Name (Bank Master)",
                "Banka": "IFSC Code (Bank Master)",
                "ZZBENF_NAME": "Beneficiary Name (International Bank Details)",
                "ZZBEN_BANK_NM": "Beneficiary Bank Name (International Bank Details)",
                "ZZBEN_ACCT_NO": "Beneficiary Account Number (International Bank Details)",
                "ZZBENF_IBAN": "Beneficiary IBAN Number (International Bank Details)",
                "ZZBENF_BANKADDR": "Beneficiary Bank Address (International Bank Details)",
                "ZZBENF_SHFTADDR": "Beneficiary SWIFT Code (International Bank Details)",
                "ZZBENF_ACH_NO": "Beneficiary ACH Number (International Bank Details)",
                "ZZBENF_ABA_NO": "Beneficiary ABA Number (International Bank Details)",
                "ZZBENF_ROUTING": "Beneficiary Routing Number (International Bank Details)",
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

            # Check for missing mandatory data (all fields except those allowed to be empty)
            # print("Runninggggggggggggggggggggggggggggggggggggg@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@11")
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
            # Don't throw exception, just continue with flow
            return {
                "success": False,
                "message": error_message,
                "data": data_list  # Return data even if validation fails
            }
        else:
            # Update the onboarding document to mark mandatory data as filled
            # print("Runninggggggggggggggggggggggggggggggggggggg@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            onb.mandatory_data_filled = 1
            # frappe.db.commit()
            # onb.db_update()
            return {
                "success": True,
                "message": "Validation successful",
                "data": data_list
            }

    except Exception as e:
        error_msg = f"Error during validation: {str(e)}"
        frappe.log_error(error_msg, "Mandatory Data Validation Error")
        # Don't throw exception, just continue with flow
        return {
            "success": False,
            "message": error_msg,
            "data": None
        }


# def get_validation_summary(onb_ref):
#     """
#     Alternative function that returns a detailed validation summary
#     """
#     result = validate_mandatory_data(onb_ref)
    
#     if result["success"]:
#         return f"✅ Validation passed for {len(result['data'])} company records"
#     else:
#         return f"❌ Validation failed: {result['message']}"


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
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@send_approval_mail_accounts_team")
            elif doc.accounts_team_undertaking == 1 and doc.accounts_head_undertaking == 0 and doc.mail_sent_to_account_head == 0:
                send_approval_mail_accounts_head(doc, method=None)
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@send_approval_mail_accounts_head")
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
            
            frappe.sendmail(
                recipients=[purchase_team_id],
                subject="Vendor has completed the onboarding form",
                message=f"""
                    <p>Dear Purchase Team,</p>
                    <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed the onboarding form ({doc.name}).</p>
                    <p>Please review the details and take necessary actions.</p>
                    
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
                            Review Onboarding
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

            # Send email
            frappe.sendmail(
                recipients=recipient_emails,
                subject="Vendor Approved by Purchase Team",
                cc=doc.registered_by, 
                message=f"""
                    <p>Dear Purchase Head,</p>
                    <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed the onboarding form ({doc.name}).<br>The <strong>{ frappe.db.get_value("Employee", {"user_id": doc.purchase_t_approval}, "full_name") }</strong>
                        (Purchase Team) already approved the process.</p>
                    <p>Please review the details and take necessary actions.</p>
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
                            Review Onboarding
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

            # Send email to all recipients
            frappe.sendmail(
                recipients=recipient_emails,
                subject="Vendor Approved by Purchase Head",
                cc=doc.registered_by,
                message=f"""
                    <p>Dear Accounts Team,</p>
                    <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed the onboarding form ({doc.name}).<br>The <strong>{ frappe.db.get_value("Employee", {"user_id": doc.purchase_h_approval}, "full_name") }</strong> 
                        (Purchase Head) already approved the process.</p>
                    <p>Please review the details and take necessary actions.</p>
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
                            Review Onboarding
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

        # Remove duplicates and empty values
        cc_list = list({email for email in cc_list if email})

        frappe.sendmail(
            recipients=[vendor_email],
            cc=cc_list,
            subject="Vendor Onboarding has been Rejected",
            message=f"""
                <p>Dear {vendor_master.vendor_name},</p>
                <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has been rejected because of <strong>{doc.reason_for_rejection}</strong>.</p>
                
                <p>Please review the details and take necessary actions.</p>
                
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
                        Review Onboarding
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
                    frappe.sendmail(
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
            frappe.sendmail(
                recipients=recipient_emails,
                subject="Vendor has completed the onboarding form",
                message=f"""
                    <p>Dear Accounts Team,</p>
                    <p>The vendor {vendor_master.vendor_name} <strong>({doc.ref_no})</strong> has completed the onboarding form ({doc.name}).</p>
                    <p>Please review the details and take necessary actions.</p>
                    
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
                            Review Onboarding
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


            # Send email to all recipients
            frappe.sendmail(
                recipients=recipient_emails,
                subject="Vendor Onboarding Approved by Accounts Team",
                message=f"""
                    <p>Dear Accounts Head,</p>
                    <p>The vendor <strong>{vendor_master.vendor_name} ({doc.ref_no})</strong> has completed the onboarding form ({doc.name}).<br>The <strong>{ frappe.db.get_value("Employee", {"user_id": doc.accounts_t_approval}, "full_name") }</strong> 
                        (Accounts Team) already approved the process.</p></p>
                    <p>Please review the details and take necessary actions.</p>
                    
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
                            Review Onboarding
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
