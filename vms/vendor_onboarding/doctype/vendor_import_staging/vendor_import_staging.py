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
        if not hasattr(vendor_doc, 'company_details') or not vendor_doc.company_details:
            company_detail = vendor_doc.append("company_details", {})
        else:
            company_detail = vendor_doc.company_details[0]
        
        company_detail.company_name = self.vendor_name
        company_detail.gst = self.gstn_no
        company_detail.company_pan_number = self.pan_no
        company_detail.address_line_1 = self.address01
        company_detail.address_line_2 = self.address02
        company_detail.city = self.city
        company_detail.state = self.state
        company_detail.country = self.country or "India"
        company_detail.pincode = self.pincode
        company_detail.telephone_number = self.contact_no
        company_detail.nature_of_business = self.nature_of_services
        
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
