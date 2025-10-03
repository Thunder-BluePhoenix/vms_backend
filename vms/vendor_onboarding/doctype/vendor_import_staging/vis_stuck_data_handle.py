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