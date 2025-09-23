# vendor_import_staging.py
# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
import re
from frappe.utils import now_datetime, cint, flt, cstr, today, add_days
from frappe.utils.background_jobs import enqueue
from frappe import _


class VendorImportStaging(Document):
    def validate(self):
        """Validate staging record before save"""
        # Set title if not provided
        if not self.title and self.vendor_name:
            self.title = f"{self.vendor_name} - {self.vendor_code or ''}"
        elif not self.title:
            self.title = f"Staging Record - {self.name or 'New'}"
    
    def before_save(self):
        """Execute before saving the document"""
        # Update progress calculation
        if self.total_records and self.total_records > 0:
            processed = (self.processed_records or 0)
            self.processing_progress = (processed / self.total_records) * 100
        
        # Set validation status based on data quality
        self.set_validation_status()
    
    def set_validation_status(self):
        """Set validation status based on data completeness and quality"""
        errors = []
        warnings = []
        
        # Required field validations
        if not self.vendor_name:
            errors.append("Vendor Name is required")
        
        if not self.vendor_code:
            errors.append("Vendor Code is required")
        
        if not self.c_code:
            errors.append("Company Code is required")
        
        # GST validation
        if self.gstn_no:
            if len(self.gstn_no) != 15:
                errors.append("GSTN No should be 15 characters")
            if not self.gstn_no.isalnum():
                warnings.append("GSTN No contains special characters")
        
        # PAN validation
        if self.pan_no:
            if len(self.pan_no) != 10:
                errors.append("PAN No should be 10 characters")
        
        # Email validation
        email_fields = [self.email_id, self.primary_email, self.secondary_email]
        for email in email_fields:
            if email and "@" not in email:
                errors.append(f"Invalid email format: {email}")
        
        # Set status
        if errors:
            self.validation_status = "Invalid"
            self.error_log = "\n".join(errors) + ("\n" + "\n".join(warnings) if warnings else "")
        elif warnings:
            self.validation_status = "Warning"
            self.error_log = "\n".join(warnings)
        else:
            self.validation_status = "Valid"
            self.error_log = ""

    def create_vendor_master(self):
        """Create or update vendor master record with proper Company Vendor Code handling"""
        try:
            # Check if vendor already exists
            existing_vendor = frappe.db.exists("Vendor Master", {
                "office_email_primary": self.primary_email
            })
            
            if existing_vendor:
                vendor_doc = frappe.get_doc("Vendor Master", existing_vendor)
                frappe.logger().info(f"Updating existing vendor: {vendor_doc.name}")
            else:
                vendor_doc = frappe.new_doc("Vendor Master")
                vendor_doc.flags.ignore_permissions = True
            
            # Map staging fields to vendor master
            self.map_to_vendor_master(vendor_doc)
            
            # Save vendor master
            vendor_doc.save()
            frappe.logger().info(f"Saved vendor master: {vendor_doc.name}")
            
            # Handle Company Vendor Code logic (critical step)
            if self.vendor_code and self.c_code:
                company_code_result = self.handle_company_vendor_code(
                    vendor_doc.name,
                    self.vendor_code,
                    self.c_code,
                    self.state,
                    self.gstn_no
                )
                
                if company_code_result.get("warnings"):
                    warning_msg = "\n".join(company_code_result["warnings"])
                    self.error_log = (self.error_log or "") + "\nWarnings: " + warning_msg
            
            # Update staging record
            self.processed_records = (self.processed_records or 0) + 1
            self.import_status = "Completed"
            self.last_processed = now_datetime()
            
            frappe.logger().info(f"Successfully processed staging record: {self.name}")
            return vendor_doc.name
            
        except Exception as e:
            # Log error
            error_msg = f"Error creating vendor master: {str(e)}"
            self.error_log = (self.error_log or "") + "\n" + error_msg
            self.failed_records = (self.failed_records or 0) + 1
            self.import_attempts = (self.import_attempts or 0) + 1
            self.import_status = "Failed"
            
            frappe.log_error(f"{error_msg}\nStaging Record: {self.name}", "Vendor Import Staging Error")
            return None

    def handle_company_vendor_code(self, vendor_ref_no, vendor_code, company_code, state, gst_no):
        """Enhanced handling of Company Vendor Code with proper duplicate logic + Vendor Master sync"""
        
        result = {
            "company_code_action": None,
            "warnings": []
        }
        
        try:
            # Find company master
            company_master = frappe.db.exists("Company Master", {"company_code": company_code})
            if not company_master:
                result["warnings"].append(f"Company with code {company_code} not found. Please create company master first.")
                return result
            
            company_doc = frappe.get_doc("Company Master", company_master)
            
            # Check if Company Vendor Code exists for this vendor + company combination
            existing_cvc = frappe.db.exists("Company Vendor Code", {
                "vendor_ref_no": vendor_ref_no,
                "company_name": company_doc.name
            })
            
            if existing_cvc:
                # Update existing Company Vendor Code
                cvc_doc = frappe.get_doc("Company Vendor Code", existing_cvc)
                
                # Check if this vendor code + state + GST combination already exists
                duplicate_found = False
                
                if hasattr(cvc_doc, 'vendor_code') and cvc_doc.vendor_code:
                    for vc_row in cvc_doc.vendor_code:
                        if (str(vc_row.vendor_code).strip() == vendor_code and 
                            str(vc_row.state).strip() == state and 
                            str(vc_row.gst_no).strip() == gst_no):
                            duplicate_found = True
                            result["warnings"].append(
                                f"Vendor code {vendor_code} for state {state} with GST {gst_no} already exists"
                            )
                            break
                
                # If no duplicate, add new vendor code row
                if not duplicate_found:
                    cvc_doc.append("vendor_code", {
                        "vendor_code": vendor_code,
                        "state": state,
                        "gst_no": gst_no
                    })
                    result["company_code_action"] = "updated"
            
            else:
                # Create new Company Vendor Code
                cvc_doc = frappe.new_doc("Company Vendor Code")
                cvc_doc.vendor_ref_no = vendor_ref_no
                cvc_doc.company_name = company_doc.name
                
                # Add vendor code row
                cvc_doc.append("vendor_code", {
                    "vendor_code": vendor_code,
                    "state": state,
                    "gst_no": gst_no
                })
                result["company_code_action"] = "created"
            
            cvc_doc.imported = 1
            cvc_doc.save(ignore_permissions=True)
            frappe.logger().info(f"Saved Company Vendor Code: {cvc_doc.name}")
            
            # 🔹 Critical: Update Vendor Master with Company Vendor Code reference
            vm_doc = frappe.get_doc("Vendor Master", vendor_ref_no)
            mc_row_found = False
            
            if hasattr(vm_doc, 'multiple_company_data') and vm_doc.multiple_company_data:
                for mc_row in vm_doc.multiple_company_data:
                    if mc_row.company_name == company_doc.name:
                        mc_row.company_vendor_code = cvc_doc.name  # This is the key reference!
                        mc_row_found = True
                        break
            
            if not mc_row_found:
                vm_doc.append("multiple_company_data", {
                    "company_name": company_doc.name,
                    "company_vendor_code": cvc_doc.name,  # This is the key reference!
                    "purchase_organization": self.purchase_organization,
                    "account_group": self.account_group,
                    "terms_of_payment": self.terms_of_payment,
                    "purchase_group": self.purchase_group,
                    "order_currency": self.order_currency,
                    "incoterm": self.incoterm,
                    "reconciliation_account": self.reconciliation_account
                })
            
            vm_doc.save(ignore_permissions=True)
            frappe.logger().info(f"Updated Vendor Master multiple_company_data: {vm_doc.name}")
            
        except Exception as e:
            error_msg = f"Error in Company Vendor Code handling: {str(e)}"
            result["warnings"].append(error_msg)
            frappe.log_error(error_msg, "Company Vendor Code Error")
        
        return result
    
    def map_to_vendor_master(self, vendor_doc):
        """Map staging fields to vendor master document"""
        
        # Basic vendor information
        vendor_doc.vendor_name = self.vendor_name
        vendor_doc.office_email_primary = self.primary_email or self.email_id
        vendor_doc.office_email_secondary = self.secondary_email
        vendor_doc.mobile_number = self.contact_no
        vendor_doc.country = self.country or "India"
        
        # Handle vendor types (child table)
        if self.vendor_type:
            if hasattr(vendor_doc, 'vendor_types') and vendor_doc.vendor_types:
                # Check for duplicates
                exists = any(row.vendor_type == self.vendor_type for row in vendor_doc.vendor_types)
                if not exists:
                    vendor_doc.append("vendor_types", {"vendor_type": self.vendor_type})
            else:
                # If table is empty, add the first row
                vendor_doc.append("vendor_types", {"vendor_type": self.vendor_type})
        
        # Set checkbox defaults (from existing logic)
        vendor_doc.payee_in_document = 1 if not hasattr(self, 'payee_in_document') or not self.payee_in_document else cint(self.payee_in_document)
        vendor_doc.gr_based_inv_ver = 1 if not hasattr(self, 'gr_based_inv_ver') or not self.gr_based_inv_ver else cint(self.gr_based_inv_ver)
        vendor_doc.service_based_inv_ver = 1 if not hasattr(self, 'service_based_inv_ver') or not self.service_based_inv_ver else cint(self.service_based_inv_ver)
        vendor_doc.check_double_invoice = 1 if not hasattr(self, 'check_double_invoice') or not self.check_double_invoice else cint(self.check_double_invoice)
        
        # Set validity and remarks fields (from existing logic)
        vendor_doc.validity = self.validity
        validity_options = [
            "GSTN No is Invalid",
            "State and GST No Mistmatch", 
            "PAN No is Invalid",
            "GST Not match with PAN No"
        ]
        
        if not self.validity:
            vendor_doc.validity_label = "Blank"
        elif self.validity in validity_options:
            vendor_doc.validity_label = self.validity
        else:
            vendor_doc.validity_label = "Not matched with any Validity"
        
        vendor_doc.remarks = self.remarks
        if self.remarks and re.sub(r'[^a-z0-9]', '', self.remarks.lower()).strip() == "ok":
            vendor_doc.remarks_ok = 1
        
        # Handle blocked status
        if self.blocked:
            vendor_doc.is_blocked = 1
        
        # Set additional fields (from existing logic)
        vendor_doc.status = "Active"
        vendor_doc.registered_date = today()
        vendor_doc.registered_by = frappe.session.user
        vendor_doc.via_data_import = 1
        
        # Create or update company details child record
        # if not hasattr(vendor_doc, 'company_details') or not vendor_doc.company_details:
        #     company_detail = vendor_doc.append("company_details", {})
        # else:
        #     company_detail = vendor_doc.company_details[0]
        
        # company_detail.company_name = self.vendor_name
        # company_detail.gst = self.gstn_no
        # company_detail.company_pan_number = self.pan_no
        # company_detail.address_line_1 = self.address01
        # company_detail.address_line_2 = self.address02
        # company_detail.city = self.city
        # company_detail.state = self.state
        # company_detail.country = self.country or "India"
        # company_detail.pincode = self.pincode
        # company_detail.telephone_number = self.contact_no
        # company_detail.nature_of_business = self.nature_of_services
        
        # Bank details
        if any([self.bank_name, self.ifsc_code, self.account_number]):
            # Check if bank details already exist to avoid duplicates
            existing_bank = None
            if hasattr(vendor_doc, 'vendor_bank_details') and vendor_doc.vendor_bank_details:
                for bank in vendor_doc.vendor_bank_details:
                    if (bank.ifsc_code == self.ifsc_code and 
                        bank.account_number == self.account_number):
                        existing_bank = bank
                        break
            
            if not existing_bank:
                bank_detail = vendor_doc.append("vendor_bank_details", {})
                bank_detail.bank_name = self.bank_name
                bank_detail.ifsc_code = self.ifsc_code
                bank_detail.account_number = self.account_number
                bank_detail.name_of_account_holder = self.name_of_account_holder
                bank_detail.type_of_account = self.type_of_account
                bank_detail.company_name = self.vendor_name
                
                # International bank details if present
                if any([self.beneficiary_name, self.beneficiary_swift_code]):
                    intl_bank = bank_detail.append("international_bank_details", {})
                    intl_bank.beneficiary_name = self.beneficiary_name
                    intl_bank.beneficiary_swift_code = self.beneficiary_swift_code
                    intl_bank.beneficiary_iban_no = self.beneficiary_iban_no
                    intl_bank.beneficiary_aba_no = self.beneficiary_aba_no
                    intl_bank.beneficiary_bank_address = self.beneficiary_bank_address
                    intl_bank.beneficiary_bank_name = self.beneficiary_bank_name
                    intl_bank.beneficiary_account_no = self.beneficiary_account_no
                    intl_bank.beneficiary_ach_no = self.beneficiary_ach_no
                    intl_bank.beneficiary_routing_no = self.beneficiary_routing_no
                    intl_bank.beneficiary_currency = self.beneficiary_currency
                    
                # Intermediate bank details if present
                if any([self.intermediate_name, self.intermediate_swift_code]):
                    intermediate_bank = bank_detail.append("intermediate_bank_details", {})
                    intermediate_bank.intermediate_name = self.intermediate_name
                    intermediate_bank.intermediate_bank_name = self.intermediate_bank_name
                    intermediate_bank.intermediate_swift_code = self.intermediate_swift_code
                    intermediate_bank.intermediate_iban_no = self.intermediate_iban_no
                    intermediate_bank.intermediate_aba_no = self.intermediate_aba_no
                    intermediate_bank.intermediate_bank_address = self.intermediate_bank_address
                    intermediate_bank.intermediate_account_no = self.intermediate_account_no
                    intermediate_bank.intermediate_ach_no = self.intermediate_ach_no
                    intermediate_bank.intermediate_routing_no = self.intermediate_routing_no
                    intermediate_bank.intermediate_currency = self.intermediate_currency


# Background Processing Functions
def create_staging_records_from_import(import_doc_name, batch_size=100):
    """Create staging records from existing vendor import in batches"""
    
    try:
        # Get the import document
        import_doc = frappe.get_doc("Existing Vendor Import", import_doc_name)
        
        if not import_doc.vendor_data:
            frappe.throw(_("No vendor data found in import document"))
        
        # Parse vendor data
        vendor_data = json.loads(import_doc.vendor_data)
        field_mapping = json.loads(import_doc.field_mapping) if import_doc.field_mapping else {}
        
        total_records = len(vendor_data)
        
        # Process in batches
        batch_count = 0
        for i in range(0, total_records, batch_size):
            batch_data = vendor_data[i:i + batch_size]
            batch_count += 1
            
            # Enqueue batch processing
            enqueue(
                method="vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_batch",
                queue="default",
                timeout=3600,  # 1 hour timeout
                job_name=f"vendor_staging_batch_{import_doc_name}_{batch_count}",
                import_doc_name=import_doc_name,
                batch_data=batch_data,
                field_mapping=field_mapping,
                batch_id=f"BATCH-{import_doc_name}-{batch_count:03d}",
                batch_number=batch_count,
                total_batches=((total_records - 1) // batch_size) + 1
            )
        
        frappe.msgprint(_(f"Queued {batch_count} batches for processing. Total records: {total_records}"))
        
        return {
            "status": "success",
            "total_batches": batch_count,
            "total_records": total_records,
            "batch_size": batch_size
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating staging records: {str(e)}", "Vendor Staging Creation Error")
        frappe.throw(_("Error creating staging records: {0}").format(str(e)))


def process_batch(import_doc_name, batch_data, field_mapping, batch_id, batch_number, total_batches):
    """Process a batch of vendor records and create staging documents"""
    
    try:
        success_count = 0
        error_count = 0
        errors = []
        
        for idx, row_data in enumerate(batch_data):
            try:
                # Create staging record
                staging_doc = frappe.new_doc("Vendor Import Staging")
                staging_doc.flags.ignore_permissions = True
                
                # Map data from CSV to staging fields
                map_csv_to_staging(staging_doc, row_data, field_mapping)
                
                # Set batch information
                staging_doc.import_source = import_doc_name
                staging_doc.batch_id = batch_id
                staging_doc.import_status = "Pending"
                staging_doc.total_records = len(batch_data)
                
                # Save staging record
                staging_doc.save()
                success_count += 1
                
                # Commit every 50 records to avoid memory issues
                if success_count % 50 == 0:
                    frappe.db.commit()
                    
            except Exception as e:
                error_count += 1
                error_msg = f"Row {idx + 1}: {str(e)}"
                errors.append(error_msg)
                frappe.log_error(error_msg, f"Batch Processing Error - {batch_id}")
        
        # Final commit
        frappe.db.commit()
        
        # Update batch status
        update_batch_status(batch_id, success_count, error_count, errors)
        
        # Send progress notification
        send_batch_progress_notification(
            import_doc_name, batch_number, total_batches, success_count, error_count
        )
        
        return {
            "status": "completed",
            "success_count": success_count,
            "error_count": error_count,
            "batch_id": batch_id
        }
        
    except Exception as e:
        frappe.log_error(f"Critical error in batch processing: {str(e)}", f"Batch Error - {batch_id}")
        return {
            "status": "failed",
            "error": str(e),
            "batch_id": batch_id
        }


def map_csv_to_staging(staging_doc, row_data, field_mapping):
    """Map CSV row data to staging document fields"""
    
    # Define field mapping from CSV columns to staging fields
    csv_to_staging_mapping = {
        "C.Code": "c_code",
        "Vendor Code": "vendor_code", 
        "Vendor Name": "vendor_name",
        "State": "state",
        "Country": "country",
        "GSTN No": "gstn_no",
        "PAN No": "pan_no",
        "Check": "check_field",
        "Vendor Type": "vendor_type",
        "Vendor GST Classification": "vendor_gst_classification",
        "Address01": "address01",
        "Address02": "address02",
        "Address03": "address03",
        "Address04": "address04",
        "Address05": "address05",
        "City": "city",
        "Pincode": "pincode",
        "Contact No": "contact_no",
        "Alternate No": "alternate_no",
        "Email-Id": "email_id",
        "Validity": "validity",
        "Created On": "created_on",
        "Count": "count_field",
        "Account Group": "account_group",
        "Type of Industry": "type_of_industry",
        "Contact Person": "contact_person",
        "HOD": "hod",
        "Nature Of Services": "nature_of_services",
        "Nature": "nature",
        "Remarks": "remarks",
        "Primary Email": "primary_email",
        "Secondary Email": "secondary_email",
        "Purchase Organization": "purchase_organization",
        "Purchase Group": "purchase_group",
        "Vendor Type_1": "vendor_type_1",
        "Terms of Payment": "terms_of_payment",
        "Incoterm": "incoterm",
        "Reconciliation Account": "reconciliation_account",
        "Order Currency": "order_currency",
        "Blocked": "blocked",
        "Bank Name": "bank_name",
        "Bank Key": "bank_key",
        "IFSC Code": "ifsc_code",
        "Account Number": "account_number",
        "Name of Account Holder": "name_of_account_holder",
        "Type of Account": "type_of_account",
        "Enterprise Registration No.": "enterprise_registration_no",
        "GST Vendor Type": "gst_vendor_type",
        "Beneficiary Name": "beneficiary_name",
        "Beneficiary Swift Code": "beneficiary_swift_code",
        "Beneficiary IBAN No.": "beneficiary_iban_no",
        "Beneficiary ABA No.": "beneficiary_aba_no",
        "Beneficiary Bank Address": "beneficiary_bank_address",
        "Beneficiary Bank Name": "beneficiary_bank_name",
        "Beneficiary Account No.": "beneficiary_account_no",
        "Beneficiary ACH No.": "beneficiary_ach_no",
        "Beneficiary Routing No.": "beneficiary_routing_no",
        "Beneficiary Currency": "beneficiary_currency",
        "Intermediate Name": "intermediate_name",
        "Intermediate Bank Name": "intermediate_bank_name",
        "Intermediate Swift Code": "intermediate_swift_code",
        "Intermediate IBAN No.": "intermediate_iban_no",
        "Intermediate ABA No.": "intermediate_aba_no",
        "Intermediate Bank Address": "intermediate_bank_address",
        "Intermediate Account No.": "intermediate_account_no",
        "Intermediate ACH No.": "intermediate_ach_no",
        "Intermediate Routing No.": "intermediate_routing_no",
        "Intermediate Currency": "intermediate_currency"
    }
    
    # Apply mapping
    for csv_field, staging_field in csv_to_staging_mapping.items():
        if csv_field in row_data and staging_field:
            value = row_data[csv_field]
            
            # Clean and convert value
            if value is not None:
                if staging_field == "blocked":
                    # Convert to boolean
                    staging_doc.set(staging_field, cint(value) == 1)
                elif staging_field in ["count_field", "pincode"]:
                    # Convert to int
                    staging_doc.set(staging_field, cint(value) if value else None)
                else:
                    # String fields
                    staging_doc.set(staging_field, cstr(value).strip() if value else "")


def update_batch_status(batch_id, success_count, error_count, errors):
    """Update batch processing status"""
    
    try:
        # Create or update batch status record
        batch_status = {
            "batch_id": batch_id,
            "success_count": success_count,
            "error_count": error_count,
            "total_processed": success_count + error_count,
            "status": "Completed" if error_count == 0 else "Completed with Errors",
            "processed_at": now_datetime(),
            "errors": "\n".join(errors[:50])  # Store first 50 errors
        }
        
        # Store in custom doctype or log
        frappe.log_error(
            f"Batch {batch_id} completed: {success_count} success, {error_count} errors",
            "Batch Processing Status"
        )
        
    except Exception as e:
        frappe.log_error(f"Error updating batch status: {str(e)}", "Batch Status Update Error")


def send_batch_progress_notification(import_doc_name, batch_number, total_batches, success_count, error_count):
    """Send progress notification for batch completion"""
    
    try:
        progress_percentage = (batch_number / total_batches) * 100
        
        message = f"""
        Vendor Import Staging Progress Update:
        
        Import Document: {import_doc_name}
        Batch: {batch_number} of {total_batches}
        Progress: {progress_percentage:.1f}%
        
        Batch Results:
        - Successful: {success_count}
        - Errors: {error_count}
        
        {f"Processing complete!" if batch_number == total_batches else "Processing continues..."}
        """
        
        # Send notification to users with Vendor Manager role
        users = frappe.get_all("Has Role", 
            filters={"role": "Vendor Manager", "parenttype": "User"},
            fields=["parent"]
        )
        
        for user in users:
            frappe.share.add(
                "Existing Vendor Import", 
                import_doc_name, 
                user.parent, 
                notify=1,
                message=message
            )
            
    except Exception as e:
        frappe.log_error(f"Error sending progress notification: {str(e)}", "Progress Notification Error")


# API Methods for List View Button Integration
@frappe.whitelist()
def initiate_staging_import(import_doc_name, batch_size=100):
    """API method to initiate staging import process"""
    
    # Validate permissions
    if not frappe.has_permission("Vendor Import Staging", "create"):
        frappe.throw(_("Insufficient permissions to create staging records"))
    
    # Check if import document exists and has data
    if not frappe.db.exists("Existing Vendor Import", import_doc_name):
        frappe.throw(_("Import document not found"))
    
    import_doc = frappe.get_doc("Existing Vendor Import", import_doc_name)
    if not import_doc.vendor_data:
        frappe.throw(_("No vendor data found in import document"))
    
    # Start the staging process
    result = create_staging_records_from_import(import_doc_name, cint(batch_size))
    
    return result


@frappe.whitelist()
def process_bulk_staging_to_vendor_master(record_names, batch_size=50):
    """Process multiple staging records to vendor master via background jobs"""
    
    if not record_names:
        return {"status": "error", "error": "No records provided"}
    
    if isinstance(record_names, str):
        record_names = json.loads(record_names)
    
    try:
        batch_size = cint(batch_size)
        total_records = len(record_names)
        
        # Process in batches via background jobs
        batch_count = 0
        for i in range(0, total_records, batch_size):
            batch_records = record_names[i:i + batch_size]
            batch_count += 1
            
            # Enqueue batch processing
            enqueue(
                method="vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_staging_batch_to_vendor_master",
                queue="default",
                timeout=3600,  # 1 hour timeout
                job_name=f"vendor_master_creation_batch_{batch_count}",
                record_names=batch_records,
                batch_number=batch_count,
                total_batches=((total_records - 1) // batch_size) + 1
            )
        
        return {
            "status": "success",
            "message": f"Initiated {batch_count} background jobs for {total_records} records",
            "total_batches": batch_count,
            "total_records": total_records
        }
        
    except Exception as e:
        frappe.log_error(f"Error initiating bulk processing: {str(e)}", "Bulk Processing Initiation Error")
        return {"status": "error", "error": str(e)}



@frappe.whitelist()
def process_single_staging_record(docname):
    """Process a single staging record to vendor master"""
    
    try:
        staging_doc = frappe.get_doc("Vendor Import Staging", docname)
        
        if staging_doc.validation_status == "Invalid":
            return {
                "status": "error",
                "error": "Cannot process invalid record. Please fix validation errors first."
            }
        
        vendor_name = staging_doc.create_vendor_master()
        
        if vendor_name:
            return {
                "status": "success",
                "vendor_name": vendor_name,
                "message": f"Vendor Master {vendor_name} created/updated successfully"
            }
        else:
            return {
                "status": "error", 
                "error": "Failed to create vendor master. Check error log for details."
            }
            
    except Exception as e:
        frappe.log_error(f"Error processing single staging record: {str(e)}", "Single Staging Processing Error")
        return {
            "status": "error",
            "error": str(e)
        }


@frappe.whitelist()
def process_bulk_staging_records(record_names):
    """Process multiple staging records in background"""
    
    if not record_names:
        return {"status": "error", "error": "No records provided"}
    
    if isinstance(record_names, str):
        record_names = json.loads(record_names)
    
    # Enqueue background job for bulk processing
    frappe.enqueue(
        method="vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_staging_to_vendor_master",
        queue="default",
        timeout=3600,
        job_name=f"bulk_staging_process_{len(record_names)}_records",
        batch_size=len(record_names)
    )
    
    return {
        "status": "success",
        "message": f"Bulk processing initiated for {len(record_names)} records"
    }


@frappe.whitelist()
def retry_bulk_staging_records(record_names):
    """Retry processing for failed staging records"""
    
    if not record_names:
        return {"status": "error", "error": "No records provided"}
    
    if isinstance(record_names, str):
        record_names = json.loads(record_names)
    
    try:
        # Reset status of failed records
        for name in record_names:
            frappe.db.set_value("Vendor Import Staging", name, {
                "import_status": "Pending",
                "error_log": ""
            })
        
        frappe.db.commit()
        
        # Enqueue for processing
        frappe.enqueue(
            method="vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_staging_to_vendor_master",
            queue="default",
            timeout=3600,
            job_name=f"retry_staging_process_{len(record_names)}_records",
            batch_size=len(record_names)
        )
        
        return {
            "status": "success",
            "message": f"Retry initiated for {len(record_names)} records"
        }
        
    except Exception as e:
        frappe.log_error(f"Error retrying bulk staging records: {str(e)}", "Bulk Retry Error")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def revalidate_staging_record(docname):
    """Re-validate a single staging record"""
    
    try:
        staging_doc = frappe.get_doc("Vendor Import Staging", docname)
        staging_doc.set_validation_status()
        staging_doc.save()
        
        return {
            "status": "success",
            "validation_status": staging_doc.validation_status,
            "error_log": staging_doc.error_log
        }
        
    except Exception as e:
        frappe.log_error(f"Error revalidating staging record: {str(e)}", "Staging Revalidation Error")
        return {"status": "error", "error": str(e)}


@frappe.whitelist() 
def revalidate_bulk_staging_records(record_names):
    """Re-validate multiple staging records"""
    
    if not record_names:
        return {"status": "error", "error": "No records provided"}
    
    if isinstance(record_names, str):
        record_names = json.loads(record_names)
    
    try:
        success_count = 0
        error_count = 0
        
        for name in record_names:
            try:
                staging_doc = frappe.get_doc("Vendor Import Staging", name)
                staging_doc.set_validation_status()
                staging_doc.save()
                success_count += 1
            except Exception as e:
                error_count += 1
                frappe.log_error(f"Error revalidating {name}: {str(e)}", "Individual Revalidation Error")
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": f"Revalidated {success_count} records, {error_count} errors",
            "success_count": success_count,
            "error_count": error_count
        }
        
    except Exception as e:
        frappe.log_error(f"Error in bulk revalidation: {str(e)}", "Bulk Revalidation Error")
        return {"status": "error", "error": str(e)}







# Add these methods to vendor_import_staging.py

import frappe
import json
from frappe import _
from frappe.utils import cint, now_datetime, add_to_date, get_datetime
from frappe.utils.background_jobs import enqueue


# CORRECTED BACKEND METHODS FOR vendor_import_staging.py
# Replace the existing methods with these corrected versions

def create_vendor_master_from_staging(staging_doc):
    """
    Create vendor master from staging document using correct doctype references
    """
    
    try:
        # Prepare mapped data using the same structure as existing vendor import
        mapped_row = prepare_mapped_data_from_staging(staging_doc)
        
        if not mapped_row.get('vendor_name'):
            return {
                "status": "error",
                "error": "Vendor name is required"
            }
        
        result = {
            "vendor_action": None,
            "company_details_action": None,
            "company_code_action": None,
            "payment_details_action": None,
            "warnings": []
        }
        
        # Step 1: Find or create Vendor Master
        vendor_master = find_or_create_vendor_master_from_staging(mapped_row)
        vendor_exists = frappe.db.exists("Vendor Master", {"vendor_name": mapped_row['vendor_name']})
        result["vendor_action"] = "updated" if vendor_exists else "created"
        
        # Step 2: Create/update Vendor Onboarding Company Details
        company_details_result = create_company_details_from_staging(vendor_master.name, mapped_row)
        result["company_details_action"] = company_details_result.get("action", "none")
        
        # Step 3: Handle Company Vendor Code
        if mapped_row.get('vendor_code') and mapped_row.get('company_code'):
            company_code_result = handle_company_vendor_code_from_staging(
                vendor_master.name, 
                mapped_row
            )
            result["company_code_action"] = company_code_result.get("company_code_action", "none")
            if company_code_result.get('warnings'):
                result["warnings"].extend(company_code_result['warnings'])
        
        # Step 4: Create Multiple Company Data
        create_multiple_company_data_from_staging(vendor_master.name, mapped_row)
        
        # Step 5: Create Payment Details
        payment_result = create_payment_details_from_staging(mapped_row, vendor_master.name)
        result["payment_details_action"] = payment_result.get('action', 'none')
        
        if payment_result.get('warnings'):
            result["warnings"].extend(payment_result['warnings'])
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "vendor_name": vendor_master.name,
            "action": result["vendor_action"],
            "details": result
        }
        
    except Exception as e:
        frappe.db.rollback()
        error_message = f"Error creating vendor master from staging: {str(e)}"
        frappe.log_error(error_message, "Vendor Master Creation Error")
        return {
            "status": "error",
            "error": error_message
        }


def create_company_details_from_staging(vendor_ref_no, mapped_row):
	"""
	Create or update Vendor Onboarding Company Details (not Company Details)
	"""
    
	try:
		result = {"action": "none"}
		
		# Check if company details already exist for this vendor
		# existing_details = frappe.db.exists("Vendor Onboarding Company Details", {
		#     "ref_no": vendor_ref_no
		# })
		
		# if existing_details:
		#     # Update existing
		#     details_doc = frappe.get_doc("Vendor Onboarding Company Details", existing_details)
		#     result["action"] = "updated"
		# else:
			# Create new
		details_doc = frappe.new_doc("Vendor Onboarding Company Details")
		details_doc.ref_no = vendor_ref_no
		result["action"] = "created"
		
		# Map staging fields to company details fields
		if mapped_row.get('vendor_name'):
			details_doc.company_name = mapped_row.get('c_code')
			details_doc.vendor_name = mapped_row.get('vendor_name')
		
		if mapped_row.get('gst'):
			details_doc.gst = mapped_row.get('gst')
		
		if mapped_row.get('company_pan_number'):
			details_doc.company_pan_number = mapped_row.get('company_pan_number')
		
		# Address fields
		if mapped_row.get('address_line_1'):
			details_doc.address_line_1 = mapped_row.get('address_line_1')
		
		if mapped_row.get('address_line_2'):
			details_doc.address_line_2 = mapped_row.get('address_line_2')
		
		if mapped_row.get('city'):
			details_doc.city = mapped_row.get('city')
		
		if mapped_row.get('state'):
			details_doc.state = mapped_row.get('state')
		
		if mapped_row.get('country'):
			details_doc.country = mapped_row.get('country')
		else:
			details_doc.country = "India"  # Default
		
		if mapped_row.get('pincode'):
			details_doc.pincode = mapped_row.get('pincode')
		
		# Contact fields
		if mapped_row.get('telephone_number'):
			details_doc.telephone_number = mapped_row.get('telephone_number')
		
		if mapped_row.get('office_email_primary'):
			details_doc.office_email_primary = mapped_row.get('office_email_primary')
		
		if mapped_row.get('office_email_secondary'):
			details_doc.office_email_secondary = mapped_row.get('office_email_secondary')
		
		# Business fields
		if mapped_row.get('nature_of_business'):
			details_doc.nature_of_business = mapped_row.get('nature_of_business')
		
		if mapped_row.get('type_of_business'):
			details_doc.type_of_business = mapped_row.get('type_of_business')
		
		if mapped_row.get('corporate_identification_number'):
			details_doc.corporate_identification_number = mapped_row.get('corporate_identification_number')
		
		if mapped_row.get('established_year'):
			details_doc.established_year = mapped_row.get('established_year')
		
		# Save the document
		details_doc.save(ignore_permissions=True)
		
		return result
		
	except Exception as e:
		error_message = f"Error creating company details: {str(e)}"
		frappe.log_error(error_message, "Company Details Creation Error")
		return {
			"action": "error",
			"error": error_message
		}


def handle_company_vendor_code_from_staging(vendor_ref_no, mapped_row):
    """
    Handle company vendor code creation using correct Company Master reference
    """
    
    result = {
        "company_code_action": None,
        "warnings": []
    }
    
    try:
        vendor_code = str(mapped_row.get('vendor_code', '')).strip()
        company_code = str(mapped_row.get('company_code', '')).strip()
        state = str(mapped_row.get('state', '')).strip()
        gst_no = str(mapped_row.get('gst_no', '') or mapped_row.get('gst', '')).strip()
        
        if not all([vendor_code, company_code]):
            return result
        
        # Find company master using correct doctype name
        company_master = frappe.db.exists("Company Master", {"company_code": company_code})
        if not company_master:
            result["warnings"].append(f"Company Master with code {company_code} not found")
            return result

        company_doc = frappe.get_doc("Company Master", company_master)

        # Check if Company Vendor Code exists for this vendor + company combination
        existing_cvc = frappe.db.exists("Company Vendor Code", {
            "vendor_ref_no": vendor_ref_no,
            "company_name": company_doc.name
        })

        if existing_cvc:
            # Update existing Company Vendor Code
            cvc_doc = frappe.get_doc("Company Vendor Code", existing_cvc)

            # Check for duplicates in child table
            duplicate_found = False
            if hasattr(cvc_doc, 'vendor_code') and cvc_doc.vendor_code:
                for vc_row in cvc_doc.vendor_code:
                    if (str(vc_row.vendor_code).strip() == vendor_code and 
                        str(vc_row.state).strip() == state and 
                        str(vc_row.gst_no).strip() == gst_no):
                        duplicate_found = True
                        result["warnings"].append(
                            f"Vendor code {vendor_code} for state {state} with GST {gst_no} already exists"
                        )
                        break

            # If no duplicate, add new vendor code row
            if not duplicate_found:
                cvc_doc.append("vendor_code", {
                    "vendor_code": vendor_code,
                    "state": state,
                    "gst_no": gst_no
                })
                result["company_code_action"] = "updated"

        else:
            # Create new Company Vendor Code
            cvc_doc = frappe.new_doc("Company Vendor Code")
            cvc_doc.vendor_ref_no = vendor_ref_no
            cvc_doc.company_name = company_doc.name

            # Add vendor code row
            cvc_doc.append("vendor_code", {
                "vendor_code": vendor_code,
                "state": state,
                "gst_no": gst_no
            })
            result["company_code_action"] = "created"

        cvc_doc.imported = 1
        cvc_doc.save(ignore_permissions=True)

        # Update Vendor Master with Company Vendor Code reference
        update_vendor_master_multiple_company_data(vendor_ref_no, company_doc.name, cvc_doc.name, mapped_row)
        
        return result
        
    except Exception as e:
        error_message = f"Error in Company Vendor Code handling: {str(e)}"
        result["warnings"].append(error_message)
        frappe.log_error(error_message, "Company Vendor Code Error")
        return result


def update_vendor_master_multiple_company_data(vendor_ref_no, company_name, company_vendor_code_name, mapped_row):
    """
    Update Vendor Master with multiple company data using correct child table
    """
    
    try:
        vm_doc = frappe.get_doc("Vendor Master", vendor_ref_no)
        
        # Check if multiple_company_data child table exists and find existing row
        mc_row_found = False
        if hasattr(vm_doc, 'multiple_company_data') and vm_doc.multiple_company_data:
            for mc_row in vm_doc.multiple_company_data:
                if mc_row.company_name == company_name:
                    # Update existing row
                    mc_row.company_vendor_code = company_vendor_code_name
                    # Update other fields from mapped data
                    if mapped_row.get('purchase_organization'):
                        mc_row.purchase_organization = mapped_row.get('purchase_organization')
                    if mapped_row.get('account_group'):
                        mc_row.account_group = mapped_row.get('account_group')
                    if mapped_row.get('terms_of_payment'):
                        mc_row.terms_of_payment = mapped_row.get('terms_of_payment')
                    if mapped_row.get('purchase_group'):
                        mc_row.purchase_group = mapped_row.get('purchase_group')
                    if mapped_row.get('order_currency'):
                        mc_row.order_currency = mapped_row.get('order_currency')
                    if mapped_row.get('incoterm'):
                        mc_row.incoterm = mapped_row.get('incoterm')
                    if mapped_row.get('reconciliation_account'):
                        mc_row.reconciliation_account = mapped_row.get('reconciliation_account')
                    
                    mc_row_found = True
                    break
        
        if not mc_row_found:
            # Add new row to multiple company data
            vm_doc.append("multiple_company_data", {
                "company_name": company_name,
                "company_vendor_code": company_vendor_code_name,
                "purchase_organization": mapped_row.get('purchase_organization'),
                "account_group": mapped_row.get('account_group'),
                "terms_of_payment": mapped_row.get('terms_of_payment'),
                "purchase_group": mapped_row.get('purchase_group'),
                "order_currency": mapped_row.get('order_currency'),
                "incoterm": mapped_row.get('incoterm'),
                "reconciliation_account": mapped_row.get('reconciliation_account')
            })

        vm_doc.save(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Error updating vendor master multiple company data: {str(e)}", "Multiple Company Data Update Error")


def create_multiple_company_data_from_staging(vendor_ref_no, mapped_row):
    """
    Create multiple company data - this is now handled in update_vendor_master_multiple_company_data
    This method is kept for compatibility but delegates to the main update function
    """
    
    company_code = str(mapped_row.get('company_code', '')).strip()
    if not company_code:
        return
    
    # Find company master
    company_master = frappe.db.exists("Company Master", {"company_code": company_code})
    if not company_master:
        return
    
    company_doc = frappe.get_doc("Company Master", company_master)
    
    # This is handled in update_vendor_master_multiple_company_data now
    # Just ensure the data is there if not already handled
    try:
        vm_doc = frappe.get_doc("Vendor Master", vendor_ref_no)
        
        # Check if the company data already exists
        company_exists = False
        if hasattr(vm_doc, 'multiple_company_data') and vm_doc.multiple_company_data:
            for mc_row in vm_doc.multiple_company_data:
                if mc_row.company_name == company_doc.name:
                    company_exists = True
                    break
        
        # If not exists, add it (this handles cases where company vendor code creation was skipped)
        if not company_exists:
            vm_doc.append("multiple_company_data", {
                "company_name": company_doc.name,
                "purchase_organization": mapped_row.get('purchase_organization'),
                "account_group": mapped_row.get('account_group'),
                "terms_of_payment": mapped_row.get('terms_of_payment'),
                "purchase_group": mapped_row.get('purchase_group'),
                "order_currency": mapped_row.get('order_currency'),
                "incoterm": mapped_row.get('incoterm'),
                "reconciliation_account": mapped_row.get('reconciliation_account')
            })
            
            vm_doc.save(ignore_permissions=True)
    
    except Exception as e:
        frappe.log_error(f"Error in multiple company data creation: {str(e)}", "Multiple Company Data Error")


# The prepare_mapped_data_from_staging, find_or_create_vendor_master_from_staging, 
# set_vendor_master_fields_from_staging, update_vendor_master_fields_from_staging,
# and create_payment_details_from_staging methods remain the same as they use correct doctype names

# Just update the field mapping to ensure we're using the right field names
def prepare_mapped_data_from_staging(staging_doc):
    """
    Prepare mapped data from staging document fields - CORRECTED VERSION
    """
    
    # Map staging fields to the expected field names used in existing vendor import
    mapped_data = {
        # Vendor Master fields
        'vendor_name': staging_doc.vendor_name,
        'office_email_primary': staging_doc.primary_email or staging_doc.email_id,
        'office_email_secondary': staging_doc.secondary_email,
        'mobile_number': staging_doc.contact_no,
        'country': staging_doc.country or "India",
        
        # Vendor Onboarding Company Details fields (corrected doctype name)
        'company_name': staging_doc.c_code,  # Use vendor name as company name
        'gst': staging_doc.gstn_no,
        'company_pan_number': staging_doc.pan_no,
        'address_line_1': staging_doc.address01,
        'address_line_2': staging_doc.address02,
        'city': staging_doc.city,
        'state': staging_doc.state,
        'pincode': staging_doc.pincode,
        'telephone_number': staging_doc.contact_no,
        'office_email_primary': staging_doc.primary_email or staging_doc.email_id,
        'office_email_secondary': staging_doc.secondary_email,
        'nature_of_business': staging_doc.nature_of_services,
        'type_of_business': staging_doc.type_of_industry,
        'corporate_identification_number': staging_doc.enterprise_registration_no,
        'established_year': staging_doc.created_on,  # Map to appropriate field
        
        # Company Vendor Code fields
        'company_code': staging_doc.c_code,
        'vendor_code': staging_doc.vendor_code,
        'gst_no': staging_doc.gstn_no,
        
        # Multiple Company Data fields
        'purchase_organization': staging_doc.purchase_organization,
        'account_group': staging_doc.account_group,
        'terms_of_payment': staging_doc.terms_of_payment,
        'purchase_group': staging_doc.purchase_group,
        'order_currency': staging_doc.order_currency,
        'incoterm': staging_doc.incoterm,
        'reconciliation_account': staging_doc.reconciliation_account,
        
        # Payment Details fields
        'bank_name': staging_doc.bank_name,
        'bank_key': staging_doc.bank_key,
        'ifsc_code': staging_doc.ifsc_code,
        'account_number': staging_doc.account_number,
        'name_of_account_holder': staging_doc.name_of_account_holder,
        'type_of_account': staging_doc.type_of_account,
        'enterprise_registration_no': staging_doc.enterprise_registration_no,
        'gst_vendor_type': staging_doc.gst_vendor_type,
        
        # Beneficiary fields
        'beneficiary_name': staging_doc.beneficiary_name,
        'beneficiary_swift_code': staging_doc.beneficiary_swift_code,
        'beneficiary_iban_no': staging_doc.beneficiary_iban_no,
        'beneficiary_aba_no': staging_doc.beneficiary_aba_no,
        'beneficiary_bank_address': staging_doc.beneficiary_bank_address,
        'beneficiary_bank_name': staging_doc.beneficiary_bank_name,
        'beneficiary_account_no': staging_doc.beneficiary_account_no,
        'beneficiary_ach_no': staging_doc.beneficiary_ach_no,
        'beneficiary_routing_no': staging_doc.beneficiary_routing_no,
        'beneficiary_currency': staging_doc.beneficiary_currency,
        
        # Intermediate bank fields
        'intermediate_name': staging_doc.intermediate_name,
        'intermediate_bank_name': staging_doc.intermediate_bank_name,
        'intermediate_swift_code': staging_doc.intermediate_swift_code,
        'intermediate_iban_no': staging_doc.intermediate_iban_no,
        'intermediate_aba_no': staging_doc.intermediate_aba_no,
        'intermediate_bank_address': staging_doc.intermediate_bank_address,
        'intermediate_account_no': staging_doc.intermediate_account_no,
        'intermediate_ach_no': staging_doc.intermediate_ach_no,
        'intermediate_routing_no': staging_doc.intermediate_routing_no,
        'intermediate_currency': staging_doc.intermediate_currency,
        
        # Additional fields
        'remarks': staging_doc.remarks,
        'validity': staging_doc.validity,
        'is_blocked': staging_doc.blocked,
        'vendor_type': staging_doc.vendor_type,
        'vendor_gst_classification': staging_doc.vendor_gst_classification
    }
    
    return mapped_data


# REMAINING BACKEND METHODS FOR vendor_import_staging.py
# These methods don't need changes as they use correct doctype references

def find_or_create_vendor_master_from_staging(mapped_row):
    """
    Find existing vendor or create new one - uses correct Vendor Master doctype
    """
    
    vendor_name = str(mapped_row.get('vendor_name', '')).strip()
    office_email = str(mapped_row.get('office_email_primary', '')).strip()
    
    # Try to find existing vendor by name or email
    existing_vendor = None
    
    # Search by vendor name first
    if vendor_name:
        existing_vendor = frappe.db.exists("Vendor Master", {"vendor_name": vendor_name})
    
    # If not found by name, search by email
    if not existing_vendor and office_email:
        existing_vendor = frappe.db.exists("Vendor Master", {"office_email_primary": office_email})
    
    if existing_vendor:
        # Update existing vendor
        vendor_master = frappe.get_doc("Vendor Master", existing_vendor)
        update_vendor_master_fields_from_staging(vendor_master, mapped_row)
    else:
        # Create new vendor
        vendor_master = frappe.new_doc("Vendor Master")
        set_vendor_master_fields_from_staging(vendor_master, mapped_row)
    
    vendor_master.via_data_import = 1
    
    # Handle validity and remarks
    validity = mapped_row.get('validity')
    remarks = mapped_row.get('remarks')
    
    vendor_master.validity = validity
    validity_options = [
        "GSTN No is Invalid",
        "State and GST No Mismatch",
        "PAN No is Invalid",
        "GST Not match with PAN No"
    ]

    if not validity:
        vendor_master.validity_label = "Blank"
    elif validity in validity_options:
        vendor_master.validity_label = validity
    else:
        vendor_master.validity_label = "Not matched with any Validity"
    
    vendor_master.remarks = remarks
    if remarks:
        import re
        norm_remarks = re.sub(r'[^a-z0-9]', '', remarks.lower()).strip()
        if norm_remarks == "ok":
            vendor_master.remarks_ok = 1

    # Handle blocked status
    is_blocked = mapped_row.get('is_blocked')
    if is_blocked in [1, "1", "1.0", True]:
        vendor_master.is_blocked = 1

    vendor_master.save(ignore_permissions=True)
    return vendor_master


def set_vendor_master_fields_from_staging(vendor_master, mapped_row):
    """Set fields for new vendor master"""
    
    vendor_master.vendor_name = mapped_row.get('vendor_name')
    vendor_master.office_email_primary = mapped_row.get('office_email_primary')
    vendor_master.office_email_secondary = mapped_row.get('office_email_secondary')
    vendor_master.mobile_number = mapped_row.get('mobile_number')
    vendor_master.country = mapped_row.get('country') or "India"
    
    # Handle vendor types (child table)
    vendor_type = mapped_row.get('vendor_type')
    if vendor_type:
        vendor_master.append("vendor_types", {"vendor_type": vendor_type})


def update_vendor_master_fields_from_staging(vendor_master, mapped_row):
    """Update fields for existing vendor master"""
    
    # Update basic fields
    if mapped_row.get('office_email_primary'):
        vendor_master.office_email_primary = mapped_row.get('office_email_primary')
    if mapped_row.get('office_email_secondary'):
        vendor_master.office_email_secondary = mapped_row.get('office_email_secondary')
    if mapped_row.get('mobile_number'):
        vendor_master.mobile_number = mapped_row.get('mobile_number')
    if mapped_row.get('country'):
        vendor_master.country = mapped_row.get('country')
    
    # Handle vendor types (avoid duplicates)
    vendor_type = mapped_row.get('vendor_type')
    if vendor_type:
        if hasattr(vendor_master, 'vendor_types') and vendor_master.vendor_types:
            exists = any(row.vendor_type == vendor_type for row in vendor_master.vendor_types)
            if not exists:
                vendor_master.append("vendor_types", {"vendor_type": vendor_type})
        else:
            vendor_master.append("vendor_types", {"vendor_type": vendor_type})


def create_payment_details_from_staging(mapped_row, vendor_master_name):
	"""Create payment details using Vendor Bank Details doctype"""

	result = {
		'action': 'none',
		'warnings': [],
		'payment_doc_name': None
	}

	try:
		# Check if any payment-related fields are present
		payment_fields = [
			'bank_name', 'ifsc_code', 'account_number', 'name_of_account_holder', 
			'type_of_account', 'bank_key', 'beneficiary_name', 'beneficiary_swift_code', 
			'beneficiary_iban_no'
		]
		
		has_payment_data = any(mapped_row.get(field) for field in payment_fields)
		
		if not has_payment_data:
			result['warnings'].append(f"No payment data found for vendor {mapped_row.get('vendor_name')}")
			return result
		
		vendor_name = mapped_row.get('vendor_name', '').strip()
		if not vendor_name:
			result['warnings'].append("Vendor name is required for payment details")
			return result
		
		# Check if payment details already exist
		# existing_payment = frappe.db.exists("Vendor Bank Details", {
		#     "ref_no": vendor_master_name
		# })
		
		# if existing_payment:
		#     payment_doc = frappe.get_doc("Vendor Bank Details", existing_payment)
		#     result['action'] = 'updated'
		# else:
		payment_doc = frappe.new_doc("Vendor Bank Details")
		payment_doc.ref_no = vendor_master_name
		result['action'] = 'created'
		
		# Map basic payment fields
		if mapped_row.get('bank_name'):
			payment_doc.bank_name = mapped_row.get('bank_name')
		if mapped_row.get('bank_key'):
			payment_doc.bank_key = mapped_row.get('bank_key')
		if mapped_row.get('ifsc_code'):
			payment_doc.ifsc_code = mapped_row.get('ifsc_code')
		if mapped_row.get('account_number'):
			payment_doc.account_number = mapped_row.get('account_number')
		if mapped_row.get('name_of_account_holder'):
			payment_doc.name_of_account_holder = mapped_row.get('name_of_account_holder')
		if mapped_row.get('type_of_account'):
			payment_doc.type_of_account = mapped_row.get('type_of_account')
		if mapped_row.get('enterprise_registration_no'):
			payment_doc.enterprise_registration_no = mapped_row.get('enterprise_registration_no')
		if mapped_row.get('gst_vendor_type'):
			payment_doc.gst_vendor_type = mapped_row.get('gst_vendor_type')
		
		# Handle banker details child table
		banker_data = {
			'bank_name': mapped_row.get('bank_name'),
			'ifsc_code': mapped_row.get('ifsc_code'),
			'account_number': mapped_row.get('account_number'),
			'name_of_account_holder': mapped_row.get('name_of_account_holder'),
			'type_of_account': mapped_row.get('type_of_account')
		}
		
		if any(banker_data.values()):
			# Clear existing banker details and add new ones
			payment_doc.banker_details = []
			payment_doc.append("banker_details", banker_data)
		
		# Handle international bank details child table  
		intl_bank_data = {
			'beneficiary_name': mapped_row.get('beneficiary_name'),
			'beneficiary_swift_code': mapped_row.get('beneficiary_swift_code'),
			'beneficiary_iban_no': mapped_row.get('beneficiary_iban_no'),
			'beneficiary_aba_no': mapped_row.get('beneficiary_aba_no'),
			'beneficiary_bank_address': mapped_row.get('beneficiary_bank_address'),
			'beneficiary_bank_name': mapped_row.get('beneficiary_bank_name'),
			'beneficiary_account_no': mapped_row.get('beneficiary_account_no'),
			'beneficiary_ach_no': mapped_row.get('beneficiary_ach_no'),
			'beneficiary_routing_no': mapped_row.get('beneficiary_routing_no'),
			'beneficiary_currency': mapped_row.get('beneficiary_currency')
		}
		
		if any(intl_bank_data.values()):
			# Clear existing international bank details and add new ones
			payment_doc.international_bank_details = []
			payment_doc.append("international_bank_details", intl_bank_data)
		
		# Handle intermediate bank details child table
		intermediate_bank_data = {
			'intermediate_name': mapped_row.get('intermediate_name'),
			'intermediate_bank_name': mapped_row.get('intermediate_bank_name'),
			'intermediate_swift_code': mapped_row.get('intermediate_swift_code'),
			'intermediate_iban_no': mapped_row.get('intermediate_iban_no'),
			'intermediate_aba_no': mapped_row.get('intermediate_aba_no'),
			'intermediate_bank_address': mapped_row.get('intermediate_bank_address'),
			'intermediate_account_no': mapped_row.get('intermediate_account_no'),
			'intermediate_ach_no': mapped_row.get('intermediate_ach_no'),
			'intermediate_routing_no': mapped_row.get('intermediate_routing_no'),
			'intermediate_currency': mapped_row.get('intermediate_currency')
		}
		
		if any(intermediate_bank_data.values()):
			# Clear existing intermediate bank details and add new ones
			payment_doc.intermediate_bank_details = []
			payment_doc.append("intermediate_bank_details", intermediate_bank_data)
		
		payment_doc.imported = 1
		payment_doc.save(ignore_permissions=True)
        

		vm_doc = frappe.get_doc("Vendor Master", vendor_master_name)
		vm_doc.bank_details = payment_doc.name
		vm_doc.save()
		
		result['payment_doc_name'] = payment_doc.name
		
	except Exception as e:
		result['warnings'].append(f"Error creating payment details: {str(e)}")
		frappe.log_error(f"Payment details creation error: {str(e)}", "Payment Details Error")

	return result


# Add the main processing methods that call these functions

@frappe.whitelist()
def process_bulk_staging_to_vendor_master(record_names, batch_size=50):
    """
    Process multiple staging records to vendor master via background jobs
    This is the main entry point called from the list view button
    """
    
    if not record_names:
        return {"status": "error", "error": "No records provided"}
    
    if isinstance(record_names, str):
        record_names = json.loads(record_names)
    
    # Validate permissions
    if not frappe.has_permission("Vendor Import Staging", "write"):
        frappe.throw(_("Insufficient permissions to process staging records"))
    
    try:
        batch_size = cint(batch_size) or 50
        total_records = len(record_names)
        
        # Filter out records that are already processing or completed
        valid_records = []
        skipped_records = []
        
        for record_name in record_names:
            staging_doc = frappe.get_doc("Vendor Import Staging", record_name)
            
            if staging_doc.import_status in ["Pending"] and staging_doc.validation_status != "Invalid":
                valid_records.append(record_name)
                # Update status to Queued immediately
                staging_doc.db_set("import_status", "Queued", update_modified=False)
            else:
                skipped_records.append({
                    "name": record_name,
                    "reason": f"Status: {staging_doc.import_status}, Validation: {staging_doc.validation_status}"
                })
        
        frappe.db.commit()
        
        if not valid_records:
            return {
                "status": "error",
                "error": "No valid records to process",
                "skipped_records": skipped_records
            }
        
        # Process in batches via background jobs
        batch_count = 0
        job_names = []
        
        for i in range(0, len(valid_records), batch_size):
            batch_records = valid_records[i:i + batch_size]
            batch_count += 1
            
            job_name = f"vendor_master_creation_batch_{batch_count}_{now_datetime().strftime('%Y%m%d_%H%M%S')}"
            job_names.append(job_name)
            
            # Enqueue batch processing
            enqueue(
                method="vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_staging_batch_to_vendor_master",
                queue="default",
                timeout=7200,  # 2 hour timeout for large batches
                job_name=job_name,
                record_names=batch_records,
                batch_number=batch_count,
                total_batches=batch_count,
                enqueue_after_commit=True
            )
        
        return {
            "status": "success",
            "message": f"Initiated {batch_count} background jobs for {len(valid_records)} valid records",
            "total_batches": batch_count,
            "total_records": len(valid_records),
            "skipped_records": skipped_records,
            "job_names": job_names
        }
        
    except Exception as e:
        frappe.log_error(f"Error initiating bulk processing: {str(e)}", "Bulk Staging Processing Error")
        return {"status": "error", "error": str(e)}


def process_staging_batch_to_vendor_master(record_names, batch_number, total_batches):
    """
    Background job method to process a batch of staging records to vendor masters
    """
    
    try:
        frappe.flags.in_background_job = True
        success_count = 0
        error_count = 0
        errors = []
        processed_vendors = []
        
        for record_name in record_names:
            try:
                # Get staging record
                staging_doc = frappe.get_doc("Vendor Import Staging", record_name)
                
                # Skip if already processed or invalid
                if staging_doc.import_status not in ["Queued", "Processing"]:
                    continue
                
                # Update status to Processing
                staging_doc.db_set("import_status", "Processing", update_modified=False)
                frappe.db.commit()
                
                # Create vendor master using the corrected logic
                result = create_vendor_master_from_staging(staging_doc)
                
                if result["status"] == "success":
                    # Update staging record status
                    staging_doc.db_set("import_status", "Completed", update_modified=False)
                    staging_doc.db_set("processing_progress", 100, update_modified=False)
                    staging_doc.db_set("processed_records", 1, update_modified=False)
                    
                    success_count += 1
                    processed_vendors.append({
                        "staging_name": record_name,
                        "vendor_name": result.get("vendor_name"),
                        "action": result.get("action", "created")
                    })
                    
                else:
                    # Update with error
                    error_message = result.get("error", "Unknown error")
                    staging_doc.db_set("import_status", "Failed", update_modified=False)
                    staging_doc.db_set("error_log", error_message, update_modified=False)
                    staging_doc.db_set("failed_records", 1, update_modified=False)
                    
                    error_count += 1
                    errors.append({
                        "staging_name": record_name,
                        "error": error_message
                    })
                
                # Commit after each record to avoid losing progress
                frappe.db.commit()
                
            except Exception as e:
                error_message = f"Error processing {record_name}: {str(e)}"
                frappe.log_error(error_message, "Staging Record Processing Error")
                
                # Update staging record with error
                try:
                    staging_doc = frappe.get_doc("Vendor Import Staging", record_name)
                    staging_doc.db_set("import_status", "Failed", update_modified=False)
                    staging_doc.db_set("error_log", error_message, update_modified=False)
                    staging_doc.db_set("failed_records", 1, update_modified=False)
                    frappe.db.commit()
                except:
                    pass
                
                error_count += 1
                errors.append({
                    "staging_name": record_name,
                    "error": error_message
                })
        
        # Log batch completion
        batch_summary = {
            "batch_number": batch_number,
            "total_batches": total_batches,
            "records_processed": len(record_names),
            "success_count": success_count,
            "error_count": error_count,
            "processed_vendors": processed_vendors,
            "errors": errors
        }
        
        frappe.log_error(
            f"Batch {batch_number}/{total_batches} completed: {success_count} success, {error_count} errors",
            "Vendor Master Batch Processing"
        )
        
        return batch_summary
        
    except Exception as e:
        error_message = f"Batch processing failed: {str(e)}"
        frappe.log_error(error_message, "Batch Processing Error")
        
        # Update all records in this batch as failed
        for record_name in record_names:
            try:
                staging_doc = frappe.get_doc("Vendor Import Staging", record_name)
                staging_doc.db_set("import_status", "Failed", update_modified=False)
                staging_doc.db_set("error_log", error_message, update_modified=False)
                frappe.db.commit()
            except:
                pass
        
        return {
            "batch_number": batch_number,
            "total_batches": total_batches,
            "records_processed": 0,
            "success_count": 0,
            "error_count": len(record_names),
            "error": error_message
        }
    
    finally:
        frappe.flags.in_background_job = False


@frappe.whitelist()
def get_processing_status():
    """Get current processing status for monitoring"""
    
    try:
        # Get status counts
        status_counts = {}
        statuses = ["Pending", "Queued", "Processing", "Completed", "Failed", "Partially Completed"]
        
        for status in statuses:
            count = frappe.db.count("Vendor Import Staging", {"import_status": status})
            status_counts[status.lower().replace(" ", "_")] = count
        
        # Get recent background jobs (if RQ is available)
        recent_jobs = []
        try:
            from rq import Worker, Queue
            from frappe.utils.background_jobs import get_redis_conn
            
            redis_conn = get_redis_conn()
            queue = Queue(connection=redis_conn, name='default')
            
            # Get recent jobs related to vendor processing
            jobs = queue.jobs[-10:] if hasattr(queue, 'jobs') else []
            for job in jobs:
                if 'vendor_master_creation' in str(job.id):
                    recent_jobs.append({
                        'job_name': str(job.id),
                        'status': job.get_status(),
                        'started_at': job.started_at.strftime('%Y-%m-%d %H:%M:%S') if job.started_at else None,
                        'progress': getattr(job.meta, 'progress', None) if hasattr(job, 'meta') else None
                    })
        except Exception as job_error:
            frappe.log_error(f"Error getting job status: {str(job_error)}", "Job Status Error")
            pass
        
        return {
            "completed": status_counts.get("completed", 0),
            "processing": status_counts.get("processing", 0),
            "queued": status_counts.get("queued", 0),
            "failed": status_counts.get("failed", 0),
            "pending": status_counts.get("pending", 0),
            "recent_jobs": recent_jobs
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting processing status: {str(e)}", "Processing Status Error")
        return {
            "completed": 0,
            "processing": 0,
            "queued": 0,
            "failed": 0,
            "pending": 0,
            "recent_jobs": []
        }


@frappe.whitelist()
def retry_failed_records():
    """Retry processing failed staging records"""
    
    try:
        failed_records = frappe.get_all("Vendor Import Staging", 
            filters={"import_status": "Failed"},
            fields=["name"]
        )
        
        if not failed_records:
            return {
                "status": "info",
                "message": "No failed records found to retry"
            }
        
        # Reset status to Pending for retry
        for record in failed_records:
            frappe.db.set_value("Vendor Import Staging", record.name, {
                "import_status": "Pending",
                "error_log": "",
                "failed_records": 0,
                "processing_progress": 0
            })
        
        frappe.db.commit()
        
        # Process the retried records
        record_names = [record.name for record in failed_records]
        result = process_bulk_staging_to_vendor_master(record_names)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error retrying failed records: {str(e)}", "Retry Failed Records Error")
        return {
            "status": "error",
            "error": str(e)
        }












# Add these monitoring utilities to vendor_import_staging.py

def monitor_background_jobs():
    """
    Scheduled function to monitor background job processing
    This runs every 5 minutes via scheduler
    """
    
    try:
        # Check for stuck processing records (processing for more than 2 hours)
        stuck_threshold = add_to_date(now_datetime(), hours=-2)
        
        stuck_records = frappe.get_all("Vendor Import Staging",
            filters={
                "import_status": "Processing",
                "modified": ["<", stuck_threshold]
            },
            fields=["name", "vendor_name", "modified"]
        )
        
        if stuck_records:
            for record in stuck_records:
                # Reset stuck records to Pending for retry
                frappe.db.set_value("Vendor Import Staging", record.name, {
                    "import_status": "Pending",
                    "error_log": "Reset from stuck processing state",
                    "processing_progress": 0
                })
                
            frappe.db.commit()
            frappe.log_error(f"Reset {len(stuck_records)} stuck processing records", "Background Job Monitor")
        
        # Check for long queued records (queued for more than 1 hour)
        queue_threshold = add_to_date(now_datetime(), hours=-1)
        
        long_queued = frappe.get_all("Vendor Import Staging",
            filters={
                "import_status": "Queued",
                "modified": ["<", queue_threshold]
            },
            fields=["name"]
        )
        
        if long_queued:
            # Log warning about long queued records
            frappe.log_error(
                f"Found {len(long_queued)} records queued for more than 1 hour. Check background job processing.",
                "Long Queued Records Warning"
            )
        
        # Clean up old error logs (older than 30 days)
        cleanup_threshold = add_to_date(now_datetime(), days=-30)
        
        old_failed_records = frappe.get_all("Vendor Import Staging",
            filters={
                "import_status": "Failed",
                "modified": ["<", cleanup_threshold]
            },
            fields=["name"]
        )
        
        if old_failed_records:
            for record in old_failed_records:
                frappe.db.set_value("Vendor Import Staging", record.name, {
                    "error_log": "",
                    "import_status": "Pending"  # Allow retry for old failed records
                })
            
            frappe.db.commit()
            frappe.log_error(f"Cleaned up {len(old_failed_records)} old failed records", "Background Job Cleanup")
        
    except Exception as e:
        frappe.log_error(f"Error in background job monitoring: {str(e)}", "Background Job Monitor Error")


@frappe.whitelist()
def get_bulk_processing_summary():
    """Get summary of bulk processing operations"""
    
    try:
        # Get processing statistics
        total_records = frappe.db.count("Vendor Import Staging")
        
        status_summary = {}
        statuses = ["Pending", "Queued", "Processing", "Completed", "Failed", "Partially Completed"]
        
        for status in statuses:
            count = frappe.db.count("Vendor Import Staging", {"import_status": status})
            percentage = (count / total_records * 100) if total_records > 0 else 0
            status_summary[status] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        # Get recent activity (last 24 hours)
        yesterday = add_to_date(now_datetime(), days=-1)
        
        recent_activity = {
            "completed_today": frappe.db.count("Vendor Import Staging", {
                "import_status": "Completed",
                "modified": [">=", yesterday]
            }),
            "failed_today": frappe.db.count("Vendor Import Staging", {
                "import_status": "Failed", 
                "modified": [">=", yesterday]
            }),
            "processed_today": frappe.db.count("Vendor Import Staging", {
                "import_status": ["in", ["Completed", "Failed"]],
                "modified": [">=", yesterday]
            })
        }
        
        # Get error summary
        recent_errors = frappe.get_all("Vendor Import Staging",
            filters={
                "import_status": "Failed",
                "modified": [">=", yesterday],
                "error_log": ["!=", ""]
            },
            fields=["error_log"],
            limit=10
        )
        
        error_patterns = {}
        for error_record in recent_errors:
            error_msg = error_record.error_log[:100]  # First 100 chars
            error_patterns[error_msg] = error_patterns.get(error_msg, 0) + 1
        
        return {
            "total_records": total_records,
            "status_summary": status_summary,
            "recent_activity": recent_activity,
            "top_errors": error_patterns
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting bulk processing summary: {str(e)}", "Bulk Processing Summary Error")
        return {
            "total_records": 0,
            "status_summary": {},
            "recent_activity": {},
            "top_errors": {}
        }


@frappe.whitelist() 
def reset_all_processing_records():
    """Reset all processing records to pending (emergency function)"""
    
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Only System Manager can reset processing records"))
    
    try:
        # Reset Processing records to Pending
        processing_records = frappe.get_all("Vendor Import Staging",
            filters={"import_status": "Processing"},
            fields=["name"]
        )
        
        for record in processing_records:
            frappe.db.set_value("Vendor Import Staging", record.name, {
                "import_status": "Pending",
                "error_log": "Reset by System Manager",
                "processing_progress": 0
            })
        
        # Reset Queued records to Pending  
        queued_records = frappe.get_all("Vendor Import Staging",
            filters={"import_status": "Queued"},
            fields=["name"]
        )
        
        for record in queued_records:
            frappe.db.set_value("Vendor Import Staging", record.name, {
                "import_status": "Pending",
                "error_log": "Reset by System Manager",
                "processing_progress": 0
            })
        
        frappe.db.commit()
        
        total_reset = len(processing_records) + len(queued_records)
        
        return {
            "status": "success",
            "message": f"Reset {total_reset} records to Pending status",
            "processing_reset": len(processing_records),
            "queued_reset": len(queued_records)
        }
        
    except Exception as e:
        frappe.log_error(f"Error resetting processing records: {str(e)}", "Reset Processing Records Error")
        return {
            "status": "error",
            "error": str(e)
        }


@frappe.whitelist()
def validate_staging_data_quality():
    """Validate data quality of staging records before processing"""
    
    try:
        # Get all pending records
        pending_records = frappe.get_all("Vendor Import Staging",
            filters={"import_status": "Pending"},
            fields=["name", "vendor_name", "c_code", "vendor_code", "gstn_no", "pan_no"]
        )
        
        validation_results = {
            "total_pending": len(pending_records),
            "valid_records": 0,
            "invalid_records": 0,
            "validation_issues": [],
            "field_completeness": {}
        }
        
        # Required fields for vendor master creation
        required_fields = ["vendor_name", "c_code", "vendor_code"]
        optional_fields = ["gstn_no", "pan_no"]
        
        # Track field completeness
        field_stats = {}
        for field in required_fields + optional_fields:
            field_stats[field] = {"filled": 0, "empty": 0}
        
        for record in pending_records:
            issues = []
            
            # Check required fields
            for field in required_fields:
                value = record.get(field)
                if value:
                    field_stats[field]["filled"] += 1
                else:
                    field_stats[field]["empty"] += 1
                    issues.append(f"Missing required field: {field}")
            
            # Check optional fields
            for field in optional_fields:
                value = record.get(field)
                if value:
                    field_stats[field]["filled"] += 1
                else:
                    field_stats[field]["empty"] += 1
            
            # Validate GST format if present
            gstn = record.get("gstn_no")
            if gstn and len(str(gstn).strip()) != 15:
                issues.append("Invalid GST format (should be 15 characters)")
            
            # Validate PAN format if present
            pan = record.get("pan_no")
            if pan:
                import re
                pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
                if not re.match(pan_pattern, str(pan).strip().upper()):
                    issues.append("Invalid PAN format")
            
            if issues:
                validation_results["invalid_records"] += 1
                validation_results["validation_issues"].append({
                    "record_name": record.name,
                    "vendor_name": record.vendor_name,
                    "issues": issues
                })
                
                # Update validation status in database
                frappe.db.set_value("Vendor Import Staging", record.name, 
                    "validation_status", "Invalid")
            else:
                validation_results["valid_records"] += 1
                # Update validation status in database
                frappe.db.set_value("Vendor Import Staging", record.name, 
                    "validation_status", "Valid")
        
        # Calculate field completeness percentages
        for field, stats in field_stats.items():
            total = stats["filled"] + stats["empty"]
            completeness = (stats["filled"] / total * 100) if total > 0 else 0
            validation_results["field_completeness"][field] = {
                "filled": stats["filled"],
                "empty": stats["empty"],
                "completeness_percentage": round(completeness, 2)
            }
        
        frappe.db.commit()
        
        return validation_results
        
    except Exception as e:
        frappe.log_error(f"Error validating staging data quality: {str(e)}", "Data Quality Validation Error")
        return {
            "total_pending": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "validation_issues": [],
            "field_completeness": {},
            "error": str(e)
        }


@frappe.whitelist()
def bulk_update_validation_status():
    """Bulk update validation status for all staging records"""
    
    try:
        # Get all records that need validation
        all_records = frappe.get_all("Vendor Import Staging",
            filters={"validation_status": ["in", ["", None]]},
            fields=["name"]
        )
        
        if not all_records:
            return {
                "status": "info",
                "message": "All records already have validation status"
            }
        
        # Process in batches to avoid timeout
        batch_size = 100
        updated_count = 0
        
        for i in range(0, len(all_records), batch_size):
            batch_records = all_records[i:i + batch_size]
            
            for record in batch_records:
                staging_doc = frappe.get_doc("Vendor Import Staging", record.name)
                
                # Validate record
                is_valid = True
                validation_errors = []
                
                # Check required fields
                if not staging_doc.vendor_name:
                    is_valid = False
                    validation_errors.append("Vendor name is required")
                
                if not staging_doc.c_code:
                    is_valid = False
                    validation_errors.append("Company code is required")
                
                # Update validation status
                if is_valid:
                    staging_doc.db_set("validation_status", "Valid")
                else:
                    staging_doc.db_set("validation_status", "Invalid")
                    staging_doc.db_set("error_log", "; ".join(validation_errors))
                
                updated_count += 1
            
            # Commit batch
            frappe.db.commit()
        
        return {
            "status": "success", 
            "message": f"Updated validation status for {updated_count} records"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in bulk validation update: {str(e)}", "Bulk Validation Update Error")
        return {
            "status": "error",
            "error": str(e)
        }


# Performance optimization utilities

def optimize_staging_queries():
    """Add database indexes for better query performance"""
    
    try:
        # Add indexes for frequently queried fields
        index_fields = [
            "import_status",
            "validation_status", 
            "vendor_name",
            "c_code",
            "vendor_code",
            "batch_id"
        ]
        
        for field in index_fields:
            try:
                frappe.db.sql(f"""
                    ALTER TABLE `tabVendor Import Staging` 
                    ADD INDEX IF NOT EXISTS `idx_{field}` (`{field}`)
                """)
            except Exception as e:
                # Index might already exist
                pass
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error optimizing staging queries: {str(e)}", "Query Optimization Error")


def cleanup_old_staging_records():
    """Clean up old completed staging records"""
    
    try:
        # Delete completed records older than 90 days
        cleanup_date = add_to_date(now_datetime(), days=-90)
        
        old_completed = frappe.get_all("Vendor Import Staging",
            filters={
                "import_status": "Completed",
                "modified": ["<", cleanup_date]
            },
            fields=["name"]
        )
        
        deleted_count = 0
        for record in old_completed:
            frappe.delete_doc("Vendor Import Staging", record.name, ignore_permissions=True)
            deleted_count += 1
        
        if deleted_count > 0:
            frappe.db.commit()
            frappe.log_error(f"Cleaned up {deleted_count} old completed staging records", "Staging Cleanup")
        
        return deleted_count
        
    except Exception as e:
        frappe.log_error(f"Error cleaning up old staging records: {str(e)}", "Staging Cleanup Error")
        return 0


# Batch processing utilities

def estimate_processing_time(record_count):
    """Estimate processing time based on record count"""
    
    # Based on average processing time of ~2 seconds per record
    avg_time_per_record = 2  # seconds
    total_seconds = record_count * avg_time_per_record
    
    # Add 20% buffer for database operations and overhead
    total_seconds = total_seconds * 1.2
    
    if total_seconds < 60:
        return f"{int(total_seconds)} seconds"
    elif total_seconds < 3600:
        return f"{int(total_seconds / 60)} minutes"
    else:
        hours = int(total_seconds / 3600)
        minutes = int((total_seconds % 3600) / 60)
        return f"{hours} hours {minutes} minutes"


@frappe.whitelist()
def get_processing_estimate(record_count):
    """Get processing time estimate for given record count"""
    
    try:
        record_count = cint(record_count)
        if record_count <= 0:
            return {
                "estimated_time": "0 seconds",
                "batch_count": 0,
                "recommended_batch_size": 50
            }
        
        # Determine optimal batch size
        if record_count <= 100:
            batch_size = 25
        elif record_count <= 1000:
            batch_size = 50
        elif record_count <= 10000:
            batch_size = 100
        else:
            batch_size = 200
        
        batch_count = (record_count - 1) // batch_size + 1
        estimated_time = estimate_processing_time(record_count)
        
        return {
            "estimated_time": estimated_time,
            "batch_count": batch_count,
            "recommended_batch_size": batch_size,
            "total_records": record_count
        }
        
    except Exception as e:
        return {
            "estimated_time": "Unable to estimate",
            "batch_count": 0,
            "recommended_batch_size": 50,
            "error": str(e)
        }


# API for external monitoring

@frappe.whitelist()
def get_system_health():
    """Get overall system health for staging processing"""
    
    try:
        # Check database connection
        db_healthy = True
        try:
            frappe.db.sql("SELECT 1")
        except:
            db_healthy = False
        
        # Check background job queue
        queue_healthy = True
        queue_length = 0
        try:
            from frappe.utils.background_jobs import get_queue_list
            queues = get_queue_list()
            queue_length = sum(len(q.jobs) for q in queues if hasattr(q, 'jobs'))
        except:
            queue_healthy = False
        
        # Check for stuck records
        stuck_count = frappe.db.count("Vendor Import Staging", {
            "import_status": "Processing",
            "modified": ["<", add_to_date(now_datetime(), hours=-2)]
        })
        
        # Calculate overall health score
        health_score = 100
        if not db_healthy:
            health_score -= 50
        if not queue_healthy:
            health_score -= 20
        if queue_length > 100:
            health_score -= 15
        if stuck_count > 0:
            health_score -= 15
        
        health_status = "Healthy"
        if health_score < 70:
            health_status = "Critical"
        elif health_score < 85:
            health_status = "Warning"
        
        return {
            "health_status": health_status,
            "health_score": health_score,
            "database_healthy": db_healthy,
            "queue_healthy": queue_healthy,
            "queue_length": queue_length,
            "stuck_records": stuck_count,
            "timestamp": now_datetime()
        }
        
    except Exception as e:
        return {
            "health_status": "Error",
            "health_score": 0,
            "error": str(e),
            "timestamp": now_datetime()
        }