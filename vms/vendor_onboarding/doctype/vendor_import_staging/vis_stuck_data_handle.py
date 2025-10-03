import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date, get_datetime
import json

@frappe.whitelist()
def analyze_and_recover_stuck_records():
    """
    Comprehensive analysis and recovery of stuck processing records
    
    This method:
    1. Finds records stuck in Processing status > 2 hours
    2. Checks if Vendor Master already exists with complete data
    3. Takes appropriate recovery action based on analysis
    
    Returns:
        dict: Recovery report with statistics
    """
    
    try:
        frappe.flags.in_recovery_mode = True
        
        # Find stuck records
        stuck_threshold = add_to_date(now_datetime(), hours=-2)
        
        stuck_records = frappe.get_all(
            "Vendor Import Staging",
            filters={
                "import_status": "Processing",
                "modified": ["<", stuck_threshold]
            },
            fields=[
                "name", "vendor_name", "vendor_code", "c_code", 
                "primary_email", "email_id", "gstn_no", "state",
                "modified", "import_attempts", "error_log"
            ]
        )
        
        if not stuck_records:
            return {
                "status": "success",
                "message": "No stuck records found",
                "total": 0,
                "already_completed": 0,
                "reprocessed": 0,
                "failed": 0
            }
        
        # Initialize counters
        stats = {
            "total": len(stuck_records),
            "already_completed": 0,
            "reprocessed": 0,
            "failed": 0,
            "details": []
        }
        
        # Process each stuck record
        for record in stuck_records:
            try:
                result = analyze_and_recover_single_record(record)
                
                if result["action"] == "completed":
                    stats["already_completed"] += 1
                elif result["action"] == "reprocessed":
                    stats["reprocessed"] += 1
                elif result["action"] == "failed":
                    stats["failed"] += 1
                
                stats["details"].append({
                    "record": record.name,
                    "vendor": record.vendor_name,
                    "action": result["action"],
                    "message": result.get("message", "")
                })
                
            except Exception as e:
                stats["failed"] += 1
                stats["details"].append({
                    "record": record.name,
                    "vendor": record.vendor_name,
                    "action": "failed",
                    "message": str(e)
                })
                frappe.log_error(
                    f"Error recovering record {record.name}: {str(e)}", 
                    "Stuck Record Recovery Error"
                )
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": f"Recovered {stats['already_completed'] + stats['reprocessed']} of {stats['total']} stuck records",
            **stats
        }
        
    except Exception as e:
        frappe.log_error(f"Error in analyze_and_recover_stuck_records: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


def analyze_and_recover_single_record(staging_record):
    """
    Analyze single stuck record and take appropriate recovery action
    
    Args:
        staging_record: Vendor Import Staging record dict
        
    Returns:
        dict: Action taken and result details
    """
    
    result = {
        "action": None,
        "message": "",
        "vendor_master_name": None
    }
    
    # Check if Vendor Master already exists
    vendor_status = check_vendor_master_completeness(staging_record)
    
    if vendor_status["exists"] and vendor_status["is_complete"]:
        # Data already fully processed - mark staging as completed
        frappe.db.set_value(
            "Vendor Import Staging",
            staging_record.name,
            {
                "import_status": "Completed",
                "processed_records": 1,
                "processing_progress": 100,
                "error_log": f"Auto-completed: Vendor Master {vendor_status['vendor_name']} already exists with complete data",
                "last_processed": now_datetime()
            }
        )
        
        result["action"] = "completed"
        result["message"] = f"Vendor Master {vendor_status['vendor_name']} already complete"
        result["vendor_master_name"] = vendor_status["vendor_name"]
        
    elif vendor_status["exists"] and not vendor_status["is_complete"]:
        # Partially processed - complete the processing
        frappe.db.set_value(
            "Vendor Import Staging",
            staging_record.name,
            {
                "import_status": "Pending",
                "error_log": f"Partial data found - completing processing. Missing: {', '.join(vendor_status['missing_data'])}"
            }
        )
        
        # Process to complete missing data
        process_result = process_single_staging_record(staging_record.name)
        
        result["action"] = "reprocessed"
        result["message"] = f"Completed missing data: {', '.join(vendor_status['missing_data'])}"
        result["vendor_master_name"] = vendor_status["vendor_name"]
        
    else:
        # Not processed at all - reset and reprocess
        frappe.db.set_value(
            "Vendor Import Staging",
            staging_record.name,
            {
                "import_status": "Pending",
                "processing_progress": 0,
                "error_log": "Reset from stuck processing state - revalidating and reprocessing",
                "import_attempts": (staging_record.get("import_attempts") or 0) + 1
            }
        )
        
        # Revalidate first
        staging_doc = frappe.get_doc("Vendor Import Staging", staging_record.name)
        staging_doc.set_validation_status()
        staging_doc.save(ignore_permissions=True)
        
        # Then process if valid
        if staging_doc.validation_status == "Valid":
            process_result = process_single_staging_record(staging_record.name)
            result["action"] = "reprocessed"
            result["message"] = "Reset and reprocessed from scratch"
        else:
            result["action"] = "failed"
            result["message"] = f"Validation failed: {staging_doc.error_log}"
    
    return result


def check_vendor_master_completeness(staging_record):
    """
    Check if Vendor Master exists and verify data completeness
    
    Args:
        staging_record: Vendor Import Staging record dict
        
    Returns:
        dict: Status with exists, is_complete, vendor_name, and missing_data
    """
    
    status = {
        "exists": False,
        "is_complete": False,
        "vendor_name": None,
        "missing_data": []
    }
    
    # Try to find vendor by email or name
    vendor_master = None
    
    # Search by email
    primary_email = staging_record.get("primary_email") or staging_record.get("email_id")
    if primary_email:
        vendor_master = frappe.db.exists("Vendor Master", {
            "office_email_primary": primary_email
        })
    
    # Search by vendor name if not found by email
    if not vendor_master and staging_record.get("vendor_name"):
        vendor_master = frappe.db.exists("Vendor Master", {
            "vendor_name": staging_record.vendor_name
        })
    
    if not vendor_master:
        return status
    
    status["exists"] = True
    status["vendor_name"] = vendor_master
    
    # Get full vendor document
    vendor_doc = frappe.get_doc("Vendor Master", vendor_master)
    
    # Check required fields
    required_fields = ["vendor_name", "office_email_primary", "country"]
    for field in required_fields:
        if not getattr(vendor_doc, field, None):
            status["missing_data"].append(f"Main: {field}")
    
    # Check child tables
    if staging_record.get("c_code"):
        # Check Multiple Company Data
        has_company_data = False
        if hasattr(vendor_doc, "multiple_company_data") and vendor_doc.multiple_company_data:
            for row in vendor_doc.multiple_company_data:
                if row.company_name and staging_record.c_code in str(row.company_name):
                    has_company_data = True
                    break
        
        if not has_company_data:
            status["missing_data"].append("Child: Multiple Company Data")
    
    # Check related documents
    # Company Vendor Code
    if staging_record.get("vendor_code") and staging_record.get("c_code"):
        company_code_exists = frappe.db.exists("Company Vendor Code", {
            "vendor_ref_no": vendor_master
        })
        if not company_code_exists:
            status["missing_data"].append("Related: Company Vendor Code")
    
    # Vendor Onboarding Company Details
    company_details_exists = frappe.db.exists("Vendor Onboarding Company Details", {
        "ref_no": vendor_master
    })
    if not company_details_exists:
        status["missing_data"].append("Related: Company Details")
    
    # Bank Details (if staging has bank info)
    if staging_record.get("bank_name") or staging_record.get("account_number"):
        bank_details_exists = frappe.db.exists("Vendor Bank Details", {
            "ref_no": vendor_master
        })
        if not bank_details_exists:
            status["missing_data"].append("Related: Bank Details")
    
    # Determine completeness
    status["is_complete"] = len(status["missing_data"]) == 0
    
    return status


@frappe.whitelist()
def get_stuck_records_report():
    """
    Generate detailed report of stuck records with vendor status
    
    Returns:
        dict: Detailed report for each stuck record
    """
    
    try:
        stuck_threshold = add_to_date(now_datetime(), hours=-2)
        
        stuck_records = frappe.get_all(
            "Vendor Import Staging",
            filters={
                "import_status": "Processing",
                "modified": ["<", stuck_threshold]
            },
            fields=[
                "name", "vendor_name", "vendor_code", "c_code",
                "primary_email", "email_id", "modified", 
                "import_attempts", "error_log"
            ]
        )
        
        report = {
            "total_stuck": len(stuck_records),
            "records": []
        }
        
        for record in stuck_records:
            vendor_status = check_vendor_master_completeness(record)
            
            report["records"].append({
                "staging_name": record.name,
                "vendor_name": record.vendor_name,
                "stuck_since": str(record.modified),
                "attempts": record.import_attempts or 0,
                "vendor_exists": vendor_status["exists"],
                "vendor_master": vendor_status["vendor_name"],
                "is_complete": vendor_status["is_complete"],
                "missing_data": vendor_status["missing_data"],
                "recommended_action": get_recommended_action(vendor_status)
            })
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating stuck records report: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


def get_recommended_action(vendor_status):
    """Get recommended recovery action based on vendor status"""
    
    if not vendor_status["exists"]:
        return "Reset and reprocess from scratch"
    elif vendor_status["is_complete"]:
        return "Mark as completed (data already exists)"
    else:
        return f"Complete missing data: {', '.join(vendor_status['missing_data'])}"


@frappe.whitelist()
def schedule_stuck_records_recovery():
    """
    Schedule background job to recover stuck records
    This can be called via API or added to scheduler
    """
    
    frappe.enqueue(
        method="vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.analyze_and_recover_stuck_records",
        queue="long",
        timeout=3600,
        job_name="Stuck Records Recovery",
        is_async=True
    )
    
    return {
        "status": "success",
        "message": "Stuck records recovery job scheduled"
    }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
# In Frappe Console or via API:

# 1. Get detailed report of stuck records
frappe.call({
    method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_stuck_records_report',
    callback: function(r) {
        console.log(r.message.report);
    }
});

# 2. Analyze and recover all stuck records
frappe.call({
    method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.analyze_and_recover_stuck_records',
    callback: function(r) {
        console.log(r.message);
    }
});

# 3. Schedule as background job
frappe.call({
    method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.schedule_stuck_records_recovery'
});

# 4. Add to hooks.py for automatic scheduling:
# scheduler_events = {
#     "hourly": [
#         "vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.analyze_and_recover_stuck_records"
#     ]
# }
"""


# ============================================================================
# ENHANCED VENDOR IMPORT STAGING MONITOR
# Add to: vms/vendor_onboarding/doctype/vendor_import_staging/vendor_import_staging.py
# ============================================================================

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date, cint
import json


# ============================================================================
# IMPROVED SINGLE RECORD PROCESSING
# ============================================================================

@frappe.whitelist()
def process_single_staging_record(docname):
    """
    IMPROVED: Process a single staging record to vendor master with better error handling
    
    This version:
    - Validates before processing
    - Uses create_vendor_master_from_staging (the correct function)
    - Better error handling and logging
    - Updates status properly
    """
    
    try:
        # Get staging document
        staging_doc = frappe.get_doc("Vendor Import Staging", docname)
        
        # Check validation status
        if staging_doc.validation_status == "Invalid":
            return {
                "status": "error",
                "error": "Cannot process invalid record. Please fix validation errors first.",
                "error_log": staging_doc.error_log
            }
        
        # Update status to Processing
        staging_doc.db_set("import_status", "Processing", update_modified=False)
        frappe.db.commit()
        
        # Use the correct processing function
        result = create_vendor_master_from_staging(staging_doc)
        
        if result["status"] == "success":
            # Update staging record to Completed
            staging_doc.db_set("import_status", "Completed", update_modified=False)
            staging_doc.db_set("processed_records", 1, update_modified=False)
            staging_doc.db_set("processing_progress", 100, update_modified=False)
            staging_doc.db_set("last_processed", now_datetime(), update_modified=False)
            
            # Clear any old error logs
            staging_doc.db_set("error_log", "", update_modified=False)
            
            frappe.db.commit()
            
            return {
                "status": "success",
                "vendor_name": result.get("vendor_name"),
                "message": f"Vendor Master {result.get('vendor_name')} created/updated successfully",
                "details": result.get("details", {})
            }
        else:
            # Update staging record to Failed
            staging_doc.db_set("import_status", "Failed", update_modified=False)
            staging_doc.db_set("failed_records", 1, update_modified=False)
            staging_doc.db_set("error_log", result.get("error", "Unknown error"), update_modified=False)
            staging_doc.db_set("import_attempts", (staging_doc.import_attempts or 0) + 1, update_modified=False)
            
            frappe.db.commit()
            
            return {
                "status": "error",
                "error": result.get("error", "Failed to create vendor master"),
                "error_log": result.get("error", "")
            }
            
    except Exception as e:
        error_message = f"Error processing single staging record: {str(e)}"
        frappe.log_error(error_message, "Single Staging Processing Error")
        
        # Update status to Failed
        try:
            frappe.db.set_value("Vendor Import Staging", docname, {
                "import_status": "Failed",
                "error_log": error_message,
                "failed_records": 1,
                "import_attempts": frappe.db.get_value("Vendor Import Staging", docname, "import_attempts") + 1 or 1
            })
            frappe.db.commit()
        except:
            pass
        
        return {
            "status": "error",
            "error": error_message
        }


# ============================================================================
# QUEUED RECORDS MONITOR (2.5 HOURS)
# ============================================================================

def monitor_queued_records():
    """
    Monitor records stuck in "Queued" status for more than 2.5 hours
    
    This function:
    1. Finds all Queued records > 2.5 hours
    2. Checks if Vendor Master data is populated
    3. Verifies vendor_code child table in Company Vendor Code
    4. If not populated: Reset to Pending and reprocess
    5. If populated: Mark as Completed
    
    Should be scheduled to run every 30 minutes via hooks.py
    """
    
    try:
        # Find queued records older than 2.5 hours
        queued_threshold = add_to_date(now_datetime(), hours=-2.5)
        
        queued_records = frappe.get_all(
            "Vendor Import Staging",
            filters={
                "import_status": "Queued",
                "modified": ["<", queued_threshold]
            },
            fields=[
                "name", "vendor_name", "vendor_code", "c_code",
                "primary_email", "email_id", "gstn_no", "state",
                "modified", "import_attempts"
            ]
        )
        
        if not queued_records:
            # No stuck queued records
            return
        
        # Log found stuck queued records
        frappe.log_error(
            f"Found {len(queued_records)} records stuck in Queued status for > 2.5 hours",
            "Queued Records Monitor"
        )
        
        stats = {
            "total": len(queued_records),
            "already_completed": 0,
            "reset_and_reprocess": 0,
            "failed": 0
        }
        
        # Process each queued record
        for record in queued_records:
            try:
                result = check_and_recover_queued_record(record)
                
                if result["action"] == "completed":
                    stats["already_completed"] += 1
                elif result["action"] == "reprocessed":
                    stats["reset_and_reprocess"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                stats["failed"] += 1
                frappe.log_error(
                    f"Error processing queued record {record.name}: {str(e)}",
                    "Queued Record Recovery Error"
                )
        
        frappe.db.commit()
        
        # Log summary
        frappe.log_error(
            f"Queued Records Recovery Summary:\n"
            f"Total: {stats['total']}\n"
            f"Already Completed: {stats['already_completed']}\n"
            f"Reset & Reprocessed: {stats['reset_and_reprocess']}\n"
            f"Failed: {stats['failed']}",
            "Queued Records Monitor Summary"
        )
        
    except Exception as e:
        frappe.log_error(
            f"Error in monitor_queued_records: {str(e)}",
            "Queued Monitor Error"
        )


def check_and_recover_queued_record(staging_record):
    """
    Check if queued record's data is populated and take appropriate action
    
    Returns:
        dict: Action taken (completed/reprocessed/failed)
    """
    
    result = {
        "action": None,
        "message": "",
        "vendor_master_name": None
    }
    
    # Check if Vendor Master exists and is complete
    vendor_status = check_vendor_and_child_tables(staging_record)
    
    if vendor_status["exists"] and vendor_status["is_complete"]:
        # Data is fully populated - mark as completed
        frappe.db.set_value(
            "Vendor Import Staging",
            staging_record.name,
            {
                "import_status": "Completed",
                "processed_records": 1,
                "processing_progress": 100,
                "error_log": f"Auto-completed: Data already exists in Vendor Master {vendor_status['vendor_name']}",
                "last_processed": now_datetime()
            }
        )
        
        result["action"] = "completed"
        result["message"] = f"Data already complete in {vendor_status['vendor_name']}"
        result["vendor_master_name"] = vendor_status["vendor_name"]
        
    else:
        # Data NOT populated - reset to Pending and reprocess
        frappe.db.set_value(
            "Vendor Import Staging",
            staging_record.name,
            {
                "import_status": "Pending",
                "processing_progress": 0,
                "error_log": f"Reset from Queued (> 2.5 hours). Missing data: {', '.join(vendor_status['missing_data']) if vendor_status['missing_data'] else 'Vendor not created'}",
                "import_attempts": (staging_record.get("import_attempts") or 0) + 1
            }
        )
        
        # Revalidate
        staging_doc = frappe.get_doc("Vendor Import Staging", staging_record.name)
        staging_doc.set_validation_status()
        staging_doc.save(ignore_permissions=True)
        
        # Reprocess if valid
        if staging_doc.validation_status == "Valid":
            process_result = process_single_staging_record(staging_record.name)
            
            if process_result["status"] == "success":
                result["action"] = "reprocessed"
                result["message"] = "Reset and reprocessed successfully"
            else:
                result["action"] = "failed"
                result["message"] = f"Reprocessing failed: {process_result.get('error', 'Unknown error')}"
        else:
            result["action"] = "failed"
            result["message"] = f"Validation failed: {staging_doc.error_log}"
    
    return result


def check_vendor_and_child_tables(staging_record):
    """
    COMPREHENSIVE CHECK: Verify Vendor Master + all child tables including vendor_code
    
    This specifically checks:
    1. Vendor Master exists
    2. Required fields populated
    3. Multiple Company Data child table
    4. Company Vendor Code document exists
    5. CRITICAL: vendor_code child table in Company Vendor Code has entries
    
    Returns:
        dict: Status with exists, is_complete, vendor_name, missing_data
    """
    
    status = {
        "exists": False,
        "is_complete": False,
        "vendor_name": None,
        "missing_data": []
    }
    
    # Find Vendor Master
    vendor_master = None
    
    # Search by email
    primary_email = staging_record.get("primary_email") or staging_record.get("email_id")
    if primary_email:
        vendor_master = frappe.db.exists("Vendor Master", {
            "office_email_primary": primary_email
        })
    
    # Search by vendor name if not found
    if not vendor_master and staging_record.get("vendor_name"):
        vendor_master = frappe.db.exists("Vendor Master", {
            "vendor_name": staging_record.vendor_name
        })
    
    if not vendor_master:
        status["missing_data"].append("Vendor Master not created")
        return status
    
    status["exists"] = True
    status["vendor_name"] = vendor_master
    
    # Get full vendor document
    vendor_doc = frappe.get_doc("Vendor Master", vendor_master)
    
    # Check required main fields
    required_fields = ["vendor_name", "office_email_primary", "country"]
    for field in required_fields:
        if not getattr(vendor_doc, field, None):
            status["missing_data"].append(f"Main Field: {field}")
    
    # Check Multiple Company Data child table
    if staging_record.get("c_code"):
        has_company_data = False
        if hasattr(vendor_doc, "multiple_company_data") and vendor_doc.multiple_company_data:
            for row in vendor_doc.multiple_company_data:
                if row.company_name and staging_record.c_code in str(row.company_name):
                    has_company_data = True
                    break
        
        if not has_company_data:
            status["missing_data"].append("Child Table: Multiple Company Data")
    
    # Check Company Vendor Code document
    if staging_record.get("vendor_code") and staging_record.get("c_code"):
        company_code_status = check_company_vendor_code_table(
            vendor_master, 
            staging_record
        )
        
        if not company_code_status["exists"]:
            status["missing_data"].append("Company Vendor Code document not created")
        elif not company_code_status["has_vendor_code_entries"]:
            status["missing_data"].append("Company Vendor Code: vendor_code child table is empty")
        elif not company_code_status["has_matching_entry"]:
            status["missing_data"].append(
                f"Company Vendor Code: Missing entry for vendor_code={staging_record.vendor_code}, "
                f"state={staging_record.state}"
            )
    
    # Check Vendor Onboarding Company Details
    company_details_exists = frappe.db.exists("Vendor Onboarding Company Details", {
        "ref_no": vendor_master
    })
    if not company_details_exists:
        status["missing_data"].append("Vendor Onboarding Company Details not created")
    
    # Check Bank Details (if staging has bank info)
    if staging_record.get("bank_name") or staging_record.get("account_number"):
        bank_details_exists = frappe.db.exists("Vendor Bank Details", {
            "ref_no": vendor_master
        })
        if not bank_details_exists:
            status["missing_data"].append("Vendor Bank Details not created")
    
    # Determine completeness
    status["is_complete"] = len(status["missing_data"]) == 0
    
    return status


def check_company_vendor_code_table(vendor_master_name, staging_record):
    """
    CRITICAL CHECK: Verify vendor_code child table in Company Vendor Code
    
    This is the most important check because vendor codes might be missing
    even if the parent Company Vendor Code document exists
    
    Args:
        vendor_master_name: Vendor Master document name
        staging_record: Staging record dict
        
    Returns:
        dict: Status of Company Vendor Code and its vendor_code child table
    """
    
    status = {
        "exists": False,
        "has_vendor_code_entries": False,
        "has_matching_entry": False,
        "vendor_code_count": 0
    }
    
    try:
        # Find Company Vendor Code document
        company_vendor_code = frappe.db.exists("Company Vendor Code", {
            "vendor_ref_no": vendor_master_name
        })
        
        if not company_vendor_code:
            return status
        
        status["exists"] = True
        
        # Check vendor_code child table using SQL for better performance
        vendor_code_entries = frappe.db.sql("""
            SELECT 
                vendor_code, state, gst_no
            FROM 
                `tabVendor Code`
            WHERE 
                parent = %s
                AND parenttype = 'Company Vendor Code'
        """, (company_vendor_code,), as_dict=True)
        
        status["vendor_code_count"] = len(vendor_code_entries)
        status["has_vendor_code_entries"] = len(vendor_code_entries) > 0
        
        # Check for matching entry
        if vendor_code_entries and staging_record.get("vendor_code"):
            for entry in vendor_code_entries:
                entry_vendor_code = str(entry.vendor_code or "").strip()
                entry_state = str(entry.state or "").strip()
                staging_vendor_code = str(staging_record.vendor_code or "").strip()
                staging_state = str(staging_record.state or "").strip()
                
                if (entry_vendor_code == staging_vendor_code and 
                    entry_state == staging_state):
                    status["has_matching_entry"] = True
                    break
        
        return status
        
    except Exception as e:
        frappe.log_error(
            f"Error checking Company Vendor Code table: {str(e)}",
            "Company Vendor Code Check Error"
        )
        return status


# ============================================================================
# API ENDPOINTS FOR MANUAL TRIGGERING
# ============================================================================

@frappe.whitelist()
def manually_check_queued_records():
    """
    Manually trigger queued records check
    Can be called from UI or API
    """
    
    try:
        monitor_queued_records()
        
        return {
            "status": "success",
            "message": "Queued records check completed. Check error logs for details."
        }
        
    except Exception as e:
        frappe.log_error(f"Error in manual queued check: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


@frappe.whitelist()
def get_queued_records_status():
    """
    Get detailed status of all queued records
    
    Returns:
        dict: Detailed report of queued records and their data population status
    """
    
    try:
        queued_threshold = add_to_date(now_datetime(), hours=-2.5)
        
        queued_records = frappe.get_all(
            "Vendor Import Staging",
            filters={
                "import_status": "Queued",
                "modified": ["<", queued_threshold]
            },
            fields=[
                "name", "vendor_name", "vendor_code", "c_code",
                "primary_email", "email_id", "state", "modified",
                "import_attempts"
            ]
        )
        
        report = {
            "total_stuck_queued": len(queued_records),
            "threshold": str(queued_threshold),
            "records": []
        }
        
        for record in queued_records:
            vendor_status = check_vendor_and_child_tables(record)
            
            # Check Company Vendor Code specifically
            cvc_status = {"exists": False, "has_entries": False, "entry_count": 0}
            if vendor_status["exists"]:
                cvc_check = check_company_vendor_code_table(
                    vendor_status["vendor_name"],
                    record
                )
                cvc_status = {
                    "exists": cvc_check["exists"],
                    "has_entries": cvc_check["has_vendor_code_entries"],
                    "entry_count": cvc_check["vendor_code_count"],
                    "has_matching": cvc_check["has_matching_entry"]
                }
            
            report["records"].append({
                "staging_name": record.name,
                "vendor_name": record.vendor_name,
                "vendor_code": record.vendor_code,
                "queued_since": str(record.modified),
                "hours_queued": (now_datetime() - record.modified).total_seconds() / 3600,
                "vendor_exists": vendor_status["exists"],
                "vendor_master": vendor_status["vendor_name"],
                "is_complete": vendor_status["is_complete"],
                "missing_data": vendor_status["missing_data"],
                "company_vendor_code_status": cvc_status,
                "recommended_action": "Mark as Completed" if vendor_status["is_complete"] else "Reset and Reprocess"
            })
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting queued records status: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# HOOKS.PY CONFIGURATION
# ============================================================================

"""
Add these to your hooks.py file for automatic monitoring:

# Monitor Processing records (every 5 minutes)
scheduler_events = {
    "cron": {
        # Every 5 minutes - monitor processing records (> 2 hours)
        "*/5 * * * *": [
            "vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.monitor_background_jobs"
        ],
        
        # Every 30 minutes - monitor queued records (> 2.5 hours)
        "*/30 * * * *": [
            "vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.monitor_queued_records"
        ]
    }
}
"""


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
# 1. Manually check queued records
frappe.call({
    method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.manually_check_queued_records',
    callback: function(r) {
        console.log(r.message);
    }
});

# 2. Get detailed queued records report
frappe.call({
    method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_queued_records_status',
    callback: function(r) {
        console.log(r.message.report);
    }
});

# 3. Process single record with improved function
frappe.call({
    method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_single_staging_record',
    args: {
        docname: 'VIS-2024-00001'
    },
    callback: function(r) {
        console.log(r.message);
    }
});
"""