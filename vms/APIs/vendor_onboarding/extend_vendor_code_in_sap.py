import frappe
import json
from frappe.utils.file_manager import save_file
import os
import shutil
from datetime import datetime
import logging
from urllib.parse import quote

# send vendor code extend mail to sap team 

@frappe.whitelist(allow_guest=True)
def send_vendor_code_extend_mail(ref_no=None, prev_company=None, extend_company=None, purchase_org = None):
    try:
        if not ref_no and not prev_company and not extend_company:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Please provide ref_no, prev_company and extend_company."
            }
        
        http_server = frappe.conf.get("backend_http")
        vendor_master = frappe.get_doc("Vendor Master", ref_no)
        vendor_name = vendor_master.vendor_name

        # Find matching previous company row
        prev_row = None
        for row in vendor_master.multiple_company_data:
            if row.company_name == prev_company:
                prev_row = row
                break

        if not prev_row:
            return {
                "status": "error",
                "message": f"No matching company {prev_company} found in Vendor Master."
            }

        prev_company_doc = frappe.get_doc("Company Master", prev_company)
        prev_company_code = prev_company_doc.company_code
        prev_company_name = prev_company_doc.company_name

        vendor_codes = []
        if prev_row.company_vendor_code:
            company_vendor_code_doc = frappe.get_doc("Company Vendor Code", prev_row.company_vendor_code)
            vendor_codes = [vc.vendor_code for vc in company_vendor_code_doc.vendor_code]

        vendor_codes_str = ", ".join(vendor_codes) if vendor_codes else "N/A"

        # New company details
        new_company_doc = frappe.get_doc("Company Master", extend_company)
        new_company_code = new_company_doc.company_code
        new_company_name = new_company_doc.company_name

        extend_url = f"{http_server}/api/method/vms.APIs.vendor_onboarding.extend_vendor_code_in_sap.create_vendor_data_from_existing_onboarding?ref_no={quote(str(ref_no))}&prev_company={quote(str(prev_company))}&extend_company={quote(str(extend_company))}&purchase_org={quote(str(purchase_org))}&action=extend"

        subject = f"Please Extend the Vendor Code for {vendor_name}"
        message = f"""
        <p>Dear SAP Team,</p>
        <p>
            Kindly extend <b>{vendor_name}</b> as a vendor in <b>Company {new_company_code} - {new_company_name}</b>.
            Please note, this vendor already exists in <b>Company {prev_company_code} - {prev_company_name}</b>.
        </p>

        <p><b>Vendor Codes:</b> {vendor_codes_str}<br>
        <b>Purchase Organization:</b> {prev_row.purchase_organization}<br>
        <b>Purchase Group:</b> {prev_row.purchase_group}<br>
        <b>Account Group:</b> {prev_row.account_group}<br>
        <b>Reconciliation Account:</b> {prev_row.reconciliation_account}<br>
        <b>Incoterm:</b> {prev_row.incoterm}<br>
        <b>Terms of Payment:</b> {prev_row.terms_of_payment}<br>
        <b>Order Currency:</b> {prev_row.order_currency}</p>

        <p>
            Request you to kindly update accordingly and click on the below<b>Extend</b> button.
        </p>

        <a href="{extend_url}"
            style="background-color:green;
            color:white;
            padding:8px 16px;
            text-decoration:none;
            border-radius:4px;">
            Extend
        </a>
        """

        frappe.sendmail(
            recipients=["rishi.hingad@merillife.com", "abhishek@mail.hybrowlabs.com", "thunder00799@gmail.com"],
            subject=subject,
            message=message
        )

        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": f"Extend mail sent successfully for vendor {vendor_name}."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Code Extend Mail Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": f"Failed to send email due to: {str(e)}"
        }


# Populate Vendor data from exisiting Onboarding Record for Extend company

@frappe.whitelist(allow_guest=True)
def create_vendor_data_from_existing_onboarding(ref_no=None, prev_company=None, extend_company=None, purchase_org=None):
    try:
        if not ref_no or not prev_company or not extend_company:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Please provide ref_no, prev_company and extend_company."
            }

        if not frappe.db.exists("Vendor Master", ref_no):
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": f"Vendor Master with ref_no {ref_no} not found."
            }

        vendor_master = frappe.get_doc("Vendor Master", ref_no)
        vendor_name = vendor_master.vendor_name

        # Find matching previous company row
        prev_row = next((row for row in vendor_master.multiple_company_data if row.company_name == prev_company), None)

        if not prev_row:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": f"No matching company {prev_company} found in Vendor Master {ref_no}."
            }

        # Append new row in Vendor Master → multiple_company_data
        new_row = vendor_master.append("multiple_company_data", {
            "company_name": extend_company,
            "purchase_organization": purchase_org,
            "account_group": prev_row.account_group,
            "terms_of_payment": prev_row.terms_of_payment,
            "purchase_group": prev_row.purchase_group,
            "order_currency": prev_row.order_currency,
            "incoterm": prev_row.incoterm,
            "reconciliation_account": prev_row.reconciliation_account,
        })
        vendor_master.save(ignore_permissions=True)

        # Prepare new Company Vendor Code if prev exists
        extend_company_vendor_code = None
        if prev_row.company_vendor_code and frappe.db.exists("Company Vendor Code", prev_row.company_vendor_code):
            prev_company_vendor_code = frappe.get_doc("Company Vendor Code", prev_row.company_vendor_code)

            extend_company_vendor_code = frappe.new_doc("Company Vendor Code")
            extend_company_vendor_code.vendor_ref_no = ref_no
            extend_company_vendor_code.company_name = extend_company

            for prev_code in prev_company_vendor_code.vendor_code:
                extend_company_vendor_code.append("vendor_code", {
                    "state": prev_code.state,
                    "gst_no": prev_code.gst_no,
                    "vendor_code": prev_code.vendor_code
                })

            extend_company_vendor_code.insert(ignore_permissions=True)

        
        # Copy Vendor Onboarding's related doc and creating for extend Company

        prev_vendor_onb_list = frappe.get_all("Vendor Onboarding", 
                                            filters={"ref_no": ref_no, "onboarding_form_status": "Approved"}, 
                                            limit=1)
        
        if not prev_vendor_onb_list:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": f"No approved Vendor Onboarding found for company {prev_company}."
            }

        prev_vendor_onb = frappe.get_doc("Vendor Onboarding", prev_vendor_onb_list[0].name)

        # Create new Vendor Onboarding for extend company
        extend_vendor_onb = frappe.new_doc("Vendor Onboarding")
        
        # Copy all basic fields from previous onboarding
        exclude_fields = ['name', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 
                         'company_name', 'company', 'purchase_organization', 'vendor_company_details', 'payment_detail',
                         'document_details', 'certificate_details', 'manufacturing_details']
        
        for field in prev_vendor_onb.meta.fields:
            if field.fieldname not in exclude_fields and hasattr(prev_vendor_onb, field.fieldname):
                setattr(extend_vendor_onb, field.fieldname, getattr(prev_vendor_onb, field.fieldname))
        
        # Set the new company
        extend_vendor_onb.company_name = extend_company
        extend_vendor_onb.purchase_organization = purchase_org

        extend_vendor_onb.insert(ignore_permissions=True)
        
        # Copy vendor company details
        for row in prev_vendor_onb.vendor_company_details:
            if row.vendor_company_details:
                prev_vendor_company_details = frappe.get_doc("Vendor Onboarding Company Details", row.vendor_company_details)

                extend_vendor_company_details = frappe.new_doc("Vendor Onboarding Company Details")
                
                # Copy all fields except excluded ones
                exclude_company_fields = ['name', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'vendor_onboarding', 'company_name']
                
                for field in prev_vendor_company_details.meta.fields:
                    if field.fieldname not in exclude_company_fields and hasattr(prev_vendor_company_details, field.fieldname):
                        value = getattr(prev_vendor_company_details, field.fieldname)
                        setattr(extend_vendor_company_details, field.fieldname, value)
                
                extend_vendor_company_details.vendor_onboarding = extend_vendor_onb.name
                extend_vendor_company_details.company_name = extend_company

                extend_vendor_company_details.insert(ignore_permissions=True)
                
                # Append to vendor onboarding
                extend_vendor_onb.append("vendor_company_details", {
                    "vendor_company_details": extend_vendor_company_details.name
                })
                # extend_vendor_onb.save(ignore_permissions=True)


        # Copy Payment Details
        if prev_vendor_onb.payment_detail:
            prev_vendor_payment_details = frappe.get_doc("Vendor Onboarding Payment Details", prev_vendor_onb.payment_detail)

            extend_vendor_payment_details = frappe.new_doc("Vendor Onboarding Payment Details")
            
            # Copy all fields except excluded ones
            exclude_payment_fields = ['name', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'vendor_onboarding']
            
            for field in prev_vendor_payment_details.meta.fields:
                if field.fieldname not in exclude_payment_fields and hasattr(prev_vendor_payment_details, field.fieldname):
                    value = getattr(prev_vendor_payment_details, field.fieldname)

                    if field.fieldtype == "Table":
                        # Handle child tables
                        for child_row in value:
                            new_child = {}
                            for child_field in child_row.meta.fields:
                                if child_field.fieldname not in ['name', 'parent', 'parenttype', 'parentfield', 'creation', 'modified', 'modified_by', 'owner', 'docstatus']:
                                    new_child[child_field.fieldname] = getattr(child_row, child_field.fieldname)
                            extend_vendor_payment_details.append(field.fieldname, new_child)
                    else:
                        setattr(extend_vendor_payment_details, field.fieldname, value)
            
            extend_vendor_payment_details.vendor_onboarding = extend_vendor_onb.name
            extend_vendor_payment_details.insert(ignore_permissions=True)

            extend_vendor_onb.payment_detail = extend_vendor_payment_details.name
            # extend_vendor_onb.save(ignore_permissions=True)


        # Copy Legal Documents
        if prev_vendor_onb.document_details:
            prev_vendor_legal_documents = frappe.get_doc("Legal Documents", prev_vendor_onb.document_details)

            extend_vendor_legal_documents = frappe.new_doc("Legal Documents")
            
            # Copy all fields except excluded ones
            # exclude_legal_fields = ['name', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'vendor_onboarding']
            
            # for field in prev_vendor_legal_documents.meta.fields:
            #     if field.fieldname not in exclude_legal_fields and hasattr(prev_vendor_legal_documents, field.fieldname):
            #         value = getattr(prev_vendor_legal_documents, field.fieldname)

            #         if field.fieldtype == "Table":
            #             # Handle child tables
            #             for child_row in value:
            #                 new_child = {}
            #                 for child_field in child_row.meta.fields:
            #                     if child_field.fieldname not in ['name', 'parent', 'parenttype', 'parentfield', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'company']:
            #                         new_child[child_field.fieldname] = getattr(child_row, child_field.fieldname)
                        
            #                 new_child["company"] = extend_company
            #                 extend_vendor_legal_documents.append(field.fieldname, new_child)
            #         else:
            #             setattr(extend_vendor_legal_documents, field.fieldname, value)

            extend_vendor_legal_documents.vendor_onboarding = extend_vendor_onb.name
            extend_vendor_legal_documents.insert(ignore_permissions=True)

            extend_vendor_onb.document_details = extend_vendor_legal_documents.name
            # extend_vendor_onb.save(ignore_permissions=True)

        
        # Copy Certificate Details
        if prev_vendor_onb.certificate_details:
            prev_vendor_certificate_details = frappe.get_doc("Vendor Onboarding Certificates", prev_vendor_onb.certificate_details)

            extend_vendor_certificate_details = frappe.new_doc("Vendor Onboarding Certificates")
            
            # Copy all fields except excluded ones
            exclude_cert_fields = ['name', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'vendor_onboarding']
            
            for field in prev_vendor_certificate_details.meta.fields:
                if field.fieldname not in exclude_cert_fields and hasattr(prev_vendor_certificate_details, field.fieldname):
                    value = getattr(prev_vendor_certificate_details, field.fieldname)
                    if field.fieldtype == "Table":
                        # Handle child tables
                        for child_row in value:
                            new_child = {}
                            for child_field in child_row.meta.fields:
                                if child_field.fieldname not in ['name', 'parent', 'parenttype', 'parentfield', 'creation', 'modified', 'modified_by', 'owner', 'docstatus']:
                                    new_child[child_field.fieldname] = getattr(child_row, child_field.fieldname)
                            extend_vendor_certificate_details.append(field.fieldname, new_child)
                    else:
                        setattr(extend_vendor_certificate_details, field.fieldname, value)
            
            extend_vendor_certificate_details.vendor_onboarding = extend_vendor_onb.name
            extend_vendor_certificate_details.insert(ignore_permissions=True)

            extend_vendor_onb.certificate_details = extend_vendor_certificate_details.name
            # extend_vendor_onb.save(ignore_permissions=True)


        # Copy Manufacturing Details
        if prev_vendor_onb.manufacturing_details:
            prev_vendor_manufacturing_details = frappe.get_doc("Vendor Onboarding Manufacturing Details", prev_vendor_onb.manufacturing_details)

            extend_vendor_manufacturing_details = frappe.new_doc("Vendor Onboarding Manufacturing Details")
            
            # Copy all fields except excluded ones
            exclude_mfg_fields = ['name', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'vendor_onboarding']
            
            for field in prev_vendor_manufacturing_details.meta.fields:
                if field.fieldname not in exclude_mfg_fields and hasattr(prev_vendor_manufacturing_details, field.fieldname):
                    value = getattr(prev_vendor_manufacturing_details, field.fieldname)
                    if field.fieldtype == "Table":
                        # Handle child tables
                        for child_row in value:
                            new_child = {}
                            for child_field in child_row.meta.fields:
                                if child_field.fieldname not in ['name', 'parent', 'parenttype', 'parentfield', 'creation', 'modified', 'modified_by', 'owner', 'docstatus']:
                                    new_child[child_field.fieldname] = getattr(child_row, child_field.fieldname)
                            extend_vendor_manufacturing_details.append(field.fieldname, new_child)
                    else:
                        setattr(extend_vendor_manufacturing_details, field.fieldname, value)
            
            extend_vendor_manufacturing_details.vendor_onboarding = extend_vendor_onb.name
            extend_vendor_manufacturing_details.insert(ignore_permissions=True)

            extend_vendor_onb.manufacturing_details = extend_vendor_manufacturing_details.name
            # extend_vendor_onb.save(ignore_permissions=True)

        
        # Copy all table fields from the main vendor onboarding document
        # for field in prev_vendor_onb.meta.fields:
        #     if field.fieldtype == "Table" and hasattr(prev_vendor_onb, field.fieldname):
        #         table_data = getattr(prev_vendor_onb, field.fieldname)
        #         for row in table_data:
        #             new_row = {}
        #             for child_field in row.meta.fields:
        #                 if child_field.fieldname not in ['name', 'parent', 'parenttype', 'parentfield', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'column_break_sejv']:
        #                     new_row[child_field.fieldname] = getattr(row, child_field.fieldname)
        #             extend_vendor_onb.append(field.fieldname, new_row)
        
        # Insert the new vendor onboarding record
        # extend_vendor_onb.insert(ignore_permissions=True)
        
        extend_vendor_onb.save(ignore_permissions=True)

        if prev_vendor_onb.document_details:
            prev_vendor_legal_documents = frappe.get_doc("Legal Documents", prev_vendor_onb.document_details)
            extend_vendor_legal_documents = frappe.get_doc("Legal Documents", extend_vendor_onb.document_details)

            exclude_legal_fields = ['name', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'vendor_onboarding']

            for field in prev_vendor_legal_documents.meta.fields:
                fieldname = field.fieldname
                if fieldname not in exclude_legal_fields and hasattr(prev_vendor_legal_documents, fieldname):
                    value = getattr(prev_vendor_legal_documents, fieldname)

                    if field.fieldtype == "Table" and value:
                        extend_vendor_legal_documents.set(fieldname, [])

                        for child_row in value:
                            new_child = {}

                            child_meta = frappe.get_meta(child_row.doctype)

                            for child_field in child_meta.fields:
                                child_fieldname = child_field.fieldname
                                if child_fieldname not in ['name', 'parent', 'parenttype', 'parentfield', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'company']:
                                    new_child[child_fieldname] = getattr(child_row, child_fieldname)

                            new_child["company"] = extend_company

                            extend_vendor_legal_documents.append(fieldname, new_child)

                    else:
                        setattr(extend_vendor_legal_documents, fieldname, value)

            extend_vendor_legal_documents.save(ignore_permissions=True)

        frappe.db.commit()

        created_docs = {
            "vendor_onboarding": extend_vendor_onb.name,
            "company_vendor_code": extend_company_vendor_code.name if extend_company_vendor_code else None,
            "payment_detail": extend_vendor_payment_details.name if extend_vendor_payment_details else None,
            "legal_documents": extend_vendor_legal_documents.name if extend_vendor_legal_documents else None,
            "certificate_details": extend_vendor_certificate_details.name if extend_vendor_certificate_details else None,
            "manufacturing_details": extend_vendor_manufacturing_details.name if extend_vendor_manufacturing_details else None
        }

        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": f"Vendor data extended successfully from {prev_company} to {extend_company} for {vendor_name}.",
            "vendor_master": vendor_master.name,
            "new_company_vendor_code": extend_company_vendor_code.name if extend_company_vendor_code else None,
            **created_docs
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Data Extend Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": f"Failed to extend vendor data: {str(e)}"
        }


# still there is problem in above function
# 1. The table data is not populated in legal documents doc
# 2. in vendor onb doc, check table data duplicate entries are created







@frappe.whitelist(allow_guest=True)
def send_vendor_code_extend_mail_for_sap_team(ref_no=None, prev_company=None, extend_company=None):
    """
    Streamlined version that directly fetches vendor code information without depending on multiple_company_data
    """
    try:
        if not ref_no or not prev_company or not extend_company:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Please provide ref_no, prev_company and extend_company."
            }
        
        # Validate vendor master exists
        if not frappe.db.exists("Vendor Master", ref_no):
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": f"Vendor Master {ref_no} not found."
            }
        
        vendor_master = frappe.get_doc("Vendor Master", ref_no)
        vendor_name = vendor_master.vendor_name

        # Validate company masters exist
        if not frappe.db.exists("Company Master", prev_company):
            return {
                "status": "error", 
                "message": f"Previous company {prev_company} not found in Company Master."
            }
            
        if not frappe.db.exists("Company Master", extend_company):
            return {
                "status": "error",
                "message": f"Extend company {extend_company} not found in Company Master."
            }

        prev_company_doc = frappe.get_doc("Company Master", prev_company)
        prev_company_code = prev_company_doc.company_code
        prev_company_name = prev_company_doc.company_name

        # Directly fetch vendor codes from Company Vendor Code for previous company
        prev_cvc = frappe.db.exists("Company Vendor Code", {
            "vendor_ref_no": ref_no,
            "company_name": prev_company
        })
        
        vendor_codes = []
        purchase_org = "N/A"
        purchase_group = "N/A"
        account_group = "N/A"
        reconciliation_account = "N/A"
        incoterm = "N/A"
        terms_of_payment = "N/A"
        order_currency = "N/A"
        
        if prev_cvc:
            prev_cvc_doc = frappe.get_doc("Company Vendor Code", prev_cvc)
            vendor_codes = [vc.vendor_code for vc in prev_cvc_doc.vendor_code if vc.vendor_code]
            
            # Try to get additional details from multiple_company_data if available
            for row in vendor_master.multiple_company_data:
                if row.company_name == prev_company:
                    purchase_org = getattr(row, 'purchase_organization', 'N/A')
                    purchase_group = getattr(row, 'purchase_group', 'N/A')
                    account_group = getattr(row, 'account_group', 'N/A')
                    reconciliation_account = getattr(row, 'reconciliation_account', 'N/A')
                    incoterm = getattr(row, 'incoterm', 'N/A')
                    terms_of_payment = getattr(row, 'terms_of_payment', 'N/A')
                    order_currency = getattr(row, 'order_currency', 'N/A')
                    break

        vendor_codes_str = ", ".join(vendor_codes) if vendor_codes else "N/A"

        # New company details
        new_company_doc = frappe.get_doc("Company Master", extend_company)
        new_company_code = new_company_doc.company_code
        new_company_name = new_company_doc.company_name

        subject = f"Please Extend the Vendor Code for {vendor_name}"
        message = f"""
        <p>Dear SAP Team,</p>
        <p>
            Kindly extend <b>{vendor_name}</b> as a vendor in <b>Company {new_company_code} - {new_company_name}</b>.
            Please note, this vendor already exists in <b>Company {prev_company_code} - {prev_company_name}</b>.
        </p>

        <p><b>Vendor Details:</b><br>
        <b>Vendor Name:</b> {vendor_name}<br>
        <b>Reference Number:</b> {ref_no}<br>
        <b>Existing Vendor Codes:</b> {vendor_codes_str}<br>
        <b>Purchase Organization:</b> {purchase_org}<br>
        <b>Purchase Group:</b> {purchase_group}<br>
        <b>Account Group:</b> {account_group}<br>
        <b>Reconciliation Account:</b> {reconciliation_account}<br>
        <b>Incoterm:</b> {incoterm}<br>
        <b>Terms of Payment:</b> {terms_of_payment}<br>
        <b>Order Currency:</b> {order_currency}</p>

        <p>
            Request you to kindly extend the vendor code from <b>{prev_company_name}</b> to <b>{new_company_name}</b> 
            and update the system accordingly.
        </p>
        <p>
            <i>This is an automated notification triggered by duplicate vendor code detection.</i>
        </p>
        """

        frappe.sendmail(
            recipients=["rishi.hingad@merillife.com", "abhishek@mail.hybrowlabs.com", "thunder00799@gmail.com"],
            subject=subject,
            message=message
        )

        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": f"Extend mail sent successfully for vendor {vendor_name}.",
            "vendor_name": vendor_name,
            "prev_company": prev_company_name,
            "extend_company": new_company_name,
            "vendor_codes": vendor_codes_str
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Code Extend Mail Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": f"Failed to send email due to: {str(e)}"
        }