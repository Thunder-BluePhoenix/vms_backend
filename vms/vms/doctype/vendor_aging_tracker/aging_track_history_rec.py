import frappe
from frappe.utils import now_datetime, get_datetime, getdate
import json


@frappe.whitelist()
def process_historical_vendor_onboarding_records(batch_size=50):
    """
    Process historical Vendor Onboarding records to create Vendor Aging Tracker
    Creates aging tracker with all data in one go - no ORM modify errors
    Handles different statuses:
    - Approved: Create aging tracker with SAP log data
    - Rejected: Create aging tracker with Inactive status
    - Other: Create aging tracker only
    """
    try:
        # Get all Vendor Onboarding records that don't have aging trackers yet
        onboarding_records = frappe.db.sql("""
            SELECT vo.name, vo.onboarding_form_status, vo.rejected,
                   vo.vendor_name, vo.ref_no, vo.creation
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabVendor Aging Tracker` vat 
                ON vat.vendor_onboarding_link = vo.name
            WHERE vat.name IS NULL
            ORDER BY vo.creation ASC
            LIMIT %s
        """, (batch_size,), as_dict=1)
        
        if not onboarding_records:
            frappe.msgprint("No pending Vendor Onboarding records to process")
            return {
                "status": "completed",
                "processed": 0,
                "message": "All records already processed"
            }
        
        success_count = 0
        error_count = 0
        skipped_sap_count = 0
        sap_processed_count = 0
        errors = []
        
        for record in onboarding_records:
            try:
                # Create aging tracker in one go
                result = create_aging_tracker_with_sap_data(
                    record.name,
                    record.onboarding_form_status,
                    record.rejected
                )
                
                if result["success"]:
                    success_count += 1
                    sap_processed_count += result.get("sap_logs_processed", 0)
                    if result.get("sap_skipped", False):
                        skipped_sap_count += 1
                else:
                    error_count += 1
                    errors.append({
                        "record": record.name,
                        "error": result.get("error", "Unknown error")
                    })
                
            except Exception as e:
                error_count += 1
                errors.append({
                    "record": record.name,
                    "error": str(e)
                })
                frappe.log_error(
                    f"Error processing Vendor Onboarding {record.name}: {frappe.get_traceback()}",
                    "Batch Processing Error"
                )
        
        # Commit after processing batch
        frappe.db.commit()
        
        result = {
            "status": "success",
            "processed": success_count,
            "errors": error_count,
            "skipped_sap": skipped_sap_count,
            "sap_logs_processed": sap_processed_count,
            "total_in_batch": len(onboarding_records),
            "error_details": errors if errors else None
        }
        
        frappe.msgprint(
            f"Processed {success_count} records successfully. "
            f"{sap_processed_count} SAP logs processed. "
            f"{skipped_sap_count} marked for no SAP processing. "
            f"{error_count} errors."
        )
        return result
        
    except Exception as e:
        frappe.log_error(
            f"Batch processing failed: {frappe.get_traceback()}",
            "Batch Processing Critical Error"
        )
        frappe.db.rollback()
        return {
            "status": "failed",
            "error": str(e)
        }


def create_aging_tracker_with_sap_data(vendor_onboarding_name, onboarding_status, rejected):
    """
    Create Vendor Aging Tracker with all data in one go
    Collects data from Vendor Onboarding and SAP logs, then creates document once
    Returns: dict with success status and counts
    """
    try:
        # Get vendor onboarding data
        onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding_name)
        
        # Initialize aging tracker data
        aging_data = {
            "doctype": "Vendor Aging Tracker",
            "ag_id": vendor_onboarding_name,
            "vendor_onboarding_link": vendor_onboarding_name,
            "vendor_name": onboarding_doc.vendor_name or "",
            "vendor_ref_no": onboarding_doc.ref_no or "",
            "vendor_creation_date": onboarding_doc.creation,
            "vendor_onboarding_date": onboarding_doc.creation,
            "vendor_codes_by_company": []
        }
        
        # Set vendor status based on onboarding status
        if onboarding_status == "Rejected" or rejected:
            aging_data["vendor_status"] = "Inactive"
            should_process_sap = False
        elif onboarding_status == "Approved":
            aging_data["vendor_status"] = "Active"
            should_process_sap = True
        else:
            aging_data["vendor_status"] = "Pending"
            should_process_sap = False
        
        # Process company details from vendor onboarding
        primary_code_set = False
        for idx, company_detail in enumerate(onboarding_doc.vendor_company_details):
            if not company_detail.vendor_company_details:
                continue
            
            onb_com = frappe.get_doc("Vendor Onboarding Company Details", company_detail.vendor_company_details)
            sap_client_code = None
            
            if not primary_code_set:
                aging_data["company_code"] = onb_com.company_name or ""
                aging_data["gst_number"] = onb_com.gst or ""
                
                # Get SAP client code from company master
                if onb_com.company_name:
                    try:
                        company_master = frappe.get_doc("Company Master", onb_com.company_name)
                        if hasattr(company_master, 'sap_client_code'):
                            aging_data["sap_client_code"] = company_master.sap_client_code
                            sap_client_code = company_master.sap_client_code
                    except:
                        pass
                
                primary_code_set = True
            
            # Add to vendor codes child table
            for cgt in onb_com.comp_gst_table:
                aging_data["vendor_codes_by_company"].append({
                    "company": onb_com.company_name or "",
                    "company_code": onb_com.company_name or "",
                    "sap_client_code": sap_client_code or "",
                    "gst_number": cgt.gst_number or "",
                    "state": cgt.gst_state or ""
                })
        
        # Process SAP logs if approved
        sap_logs_processed = 0
        if should_process_sap:
            # Get all successful SAP logs for this vendor onboarding
            sap_logs = frappe.db.sql("""
                SELECT name, creation, total_transaction
                FROM `tabVMS SAP Logs`
                WHERE vendor_onboarding_link = %s
                AND status = 'Success'
                AND total_transaction IS NOT NULL
                AND total_transaction != ''
                ORDER BY creation ASC
            """, (vendor_onboarding_name,), as_dict=1)
            
            for sap_log in sap_logs:
                try:
                    transaction_data = json.loads(sap_log.total_transaction)
                    vendor_code = (
                        transaction_data.get("transaction_summary", {}).get("vendor_code")
                        or transaction_data.get("response_details", {}).get("vendor_code")
                    )
                    
                    if not vendor_code:
                        continue
                    
                    request_details = transaction_data.get("request_details", {})
                    payload = request_details.get("payload", {})
                    
                    # Set parent fields from first SAP log
                    if sap_logs_processed == 0:
                        aging_data["vendor_name"] = payload.get("Name1", aging_data["vendor_name"])
                        aging_data["primary_vendor_code"] = vendor_code
                        aging_data["company_code"] = request_details.get("company_name", aging_data["company_code"])
                        aging_data["sap_client_code"] = request_details.get("sap_client_code", aging_data["sap_client_code"])
                        aging_data["gst_number"] = request_details.get("gst_number", aging_data["gst_number"])
                        aging_data["vendor_ref_no"] = request_details.get("vendor_ref_no", aging_data["vendor_ref_no"])
                        aging_data["sap_log_reference"] = sap_log.name
                        aging_data["vendor_creation_date_sap"] = get_datetime(sap_log.creation)
                    
                    # Add/update child table entry
                    company_code = request_details.get("company_name", "")
                    gst_number = request_details.get("gst_number", "")
                    sap_client_code = request_details.get("sap_client_code", "")
                    
                    # Check if this combination already exists in child table
                    existing_row = None
                    for row in aging_data["vendor_codes_by_company"]:
                        if (row.get("company_code") == company_code and 
                            row.get("gst_number") == gst_number and 
                            row.get("sap_client_code") == sap_client_code):
                            existing_row = row
                            break
                    
                    if existing_row:
                        # Update existing row
                        existing_row["vendor_code"] = vendor_code
                        existing_row["vendor_code_generation_time"] = get_datetime(sap_log.creation)
                        existing_row["vms_sap_log"] = sap_log.name
                    else:
                        # Add new row
                        aging_data["vendor_codes_by_company"].append({
                            "company_code": company_code,
                            "gst_number": gst_number,
                            "sap_client_code": sap_client_code,
                            "vendor_code": vendor_code,
                            "vendor_code_generation_time": get_datetime(sap_log.creation),
                            "vms_sap_log": sap_log.name
                        })
                    
                    sap_logs_processed += 1
                    
                except Exception as sap_error:
                    frappe.log_error(
                        f"Error processing SAP log {sap_log.name} in batch: {str(sap_error)}",
                        "SAP Log Processing Error"
                    )
                    continue
        
        # Create the aging tracker document with all data at once
        aging_doc = frappe.get_doc(aging_data)
        aging_doc.flags.ignore_permissions = True
        aging_doc.insert()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "aging_tracker": aging_doc.name,
            "sap_logs_processed": sap_logs_processed,
            "sap_skipped": not should_process_sap
        }
        
    except Exception as e:
        frappe.log_error(
            f"Error creating aging tracker for {vendor_onboarding_name}: {frappe.get_traceback()}",
            "Aging Tracker Creation Error"
        )
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def process_historical_sap_logs(batch_size=50):
    """
    Process historical SAP Log records to update existing Vendor Aging Trackers
    Only processes SAP logs where vendor onboarding status is 'Approved'
    This is for cases where aging tracker exists but SAP logs were not processed
    """
    try:
        # Get successful SAP logs that haven't been processed yet
        # ONLY for Approved vendor onboardings with existing aging trackers
        sap_logs = frappe.db.sql("""
            SELECT vsl.name, vsl.vendor_onboarding_link, vsl.total_transaction, vsl.creation
            FROM `tabVMS SAP Logs` vsl
            INNER JOIN `tabVendor Onboarding` vo 
                ON vo.name = vsl.vendor_onboarding_link
            INNER JOIN `tabVendor Aging Tracker` vat
                ON vat.vendor_onboarding_link = vo.name
            WHERE vsl.status = 'Success'
            AND vsl.total_transaction IS NOT NULL
            AND vsl.total_transaction != ''
            AND vo.onboarding_form_status = 'Approved'
            AND NOT EXISTS (
                SELECT 1 
                FROM `tabVendor Aging Company Codes` vacc
                WHERE vacc.vms_sap_log = vsl.name
            )
            ORDER BY vsl.creation ASC
            LIMIT %s
        """, (batch_size,), as_dict=1)
        
        if not sap_logs:
            frappe.msgprint("No pending SAP Log records to process")
            return {
                "status": "completed",
                "processed": 0,
                "message": "All SAP logs already processed"
            }
        
        success_count = 0
        error_count = 0
        errors = []
        
        for log in sap_logs:
            try:
                # Process SAP log and update aging tracker
                result = update_aging_tracker_from_sap_log(log.name, log.vendor_onboarding_link, log.total_transaction, log.creation)
                
                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append({
                        "record": log.name,
                        "error": result.get("error", "Unknown error")
                    })
                
            except Exception as e:
                error_count += 1
                errors.append({
                    "record": log.name,
                    "error": str(e)
                })
                frappe.log_error(
                    f"Error processing SAP Log {log.name}: {frappe.get_traceback()}",
                    "Batch Processing Error"
                )
        
        # Commit after processing batch
        frappe.db.commit()
        
        result = {
            "status": "success",
            "processed": success_count,
            "errors": error_count,
            "total_in_batch": len(sap_logs),
            "error_details": errors if errors else None
        }
        
        frappe.msgprint(f"Processed {success_count} SAP logs successfully. {error_count} errors.")
        return result
        
    except Exception as e:
        frappe.log_error(
            f"SAP Log batch processing failed: {frappe.get_traceback()}",
            "Batch Processing Critical Error"
        )
        frappe.db.rollback()
        return {
            "status": "failed",
            "error": str(e)
        }


def update_aging_tracker_from_sap_log(sap_log_name, vendor_onboarding_link, total_transaction, sap_creation):
    """
    Update existing Vendor Aging Tracker with SAP log data
    Uses direct SQL updates to avoid ORM modify errors
    """
    try:
        transaction_data = json.loads(total_transaction)
        vendor_code = (
            transaction_data.get("transaction_summary", {}).get("vendor_code")
            or transaction_data.get("response_details", {}).get("vendor_code")
        )
        
        if not vendor_code:
            return {"success": False, "error": "No vendor code found"}
        
        request_details = transaction_data.get("request_details", {})
        payload = request_details.get("payload", {})
        
        # Get aging tracker name
        aging_tracker_name = frappe.db.get_value(
            "Vendor Aging Tracker",
            {"vendor_onboarding_link": vendor_onboarding_link},
            "name"
        )
        
        if not aging_tracker_name:
            return {"success": False, "error": "Aging tracker not found"}
        
        # Update parent fields using direct SQL to avoid timestamp issues
        frappe.db.sql("""
            UPDATE `tabVendor Aging Tracker`
            SET 
                primary_vendor_code = COALESCE(primary_vendor_code, %s),
                vendor_name = COALESCE(NULLIF(vendor_name, ''), %s),
                vendor_creation_date_sap = COALESCE(vendor_creation_date_sap, %s),
                sap_log_reference = COALESCE(sap_log_reference, %s)
            WHERE name = %s
        """, (
            vendor_code,
            payload.get("Name1", ""),
            get_datetime(sap_creation),
            sap_log_name,
            aging_tracker_name
        ))
        
        # Check if child row already exists
        company_code = request_details.get("company_name", "")
        gst_number = request_details.get("gst_number", "")
        sap_client_code = request_details.get("sap_client_code", "")
        
        existing_child = frappe.db.sql("""
            SELECT name
            FROM `tabVendor Aging Company Codes`
            WHERE parent = %s
            AND company_code = %s
            AND gst_number = %s
            AND sap_client_code = %s
        """, (aging_tracker_name, company_code, gst_number, sap_client_code), as_dict=1)
        
        if existing_child:
            # Update existing child row
            frappe.db.sql("""
                UPDATE `tabVendor Aging Company Codes`
                SET 
                    vendor_code = %s,
                    vendor_code_generation_time = %s,
                    vms_sap_log = %s
                WHERE name = %s
            """, (
                vendor_code,
                get_datetime(sap_creation),
                sap_log_name,
                existing_child[0].name
            ))
        else:
            # Insert new child row
            child_doc = frappe.get_doc({
                "doctype": "Vendor Aging Company Codes",
                "parent": aging_tracker_name,
                "parenttype": "Vendor Aging Tracker",
                "parentfield": "vendor_codes_by_company",
                "company_code": company_code,
                "gst_number": gst_number,
                "sap_client_code": sap_client_code,
                "vendor_code": vendor_code,
                "vendor_code_generation_time": get_datetime(sap_creation),
                "vms_sap_log": sap_log_name
            })
            child_doc.flags.ignore_permissions = True
            child_doc.insert()
        
        return {"success": True}
        
    except Exception as e:
        frappe.log_error(
            f"Error updating aging tracker from SAP log {sap_log_name}: {frappe.get_traceback()}",
            "SAP Update Error"
        )
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def process_all_historical_records():
    """
    Process all historical records in sequence
    Call this from a scheduled job or manually
    """
    results = {
        "timestamp": now_datetime(),
        "vendor_onboarding": None,
        "sap_logs": None
    }
    
    # Process Vendor Onboarding records first (includes SAP processing)
    frappe.publish_realtime(
        "processing_status",
        {"message": "Processing Vendor Onboarding records with SAP data..."},
        user=frappe.session.user
    )
    results["vendor_onboarding"] = process_historical_vendor_onboarding_records(batch_size=100)
    
    # Then process any remaining SAP Logs for existing trackers
    frappe.publish_realtime(
        "processing_status",
        {"message": "Processing remaining SAP Log records..."},
        user=frappe.session.user
    )
    results["sap_logs"] = process_historical_sap_logs(batch_size=100)
    
    return results


def scheduled_batch_processor():
    """
    Function to be called by Frappe scheduler
    Processes records in smaller batches to avoid timeout
    Add this to hooks.py:
    
    scheduler_events = {
        "cron": {
            "0 2 * * *": [  # Runs at 2 AM daily
                "vms_application.vms_application.doctype.vendor_aging_tracker.batch_processor.scheduled_batch_processor"
            ]
        }
    }
    
    OR use hourly/daily:
    
    scheduler_events = {
        "hourly": [
            "vms_application.vms_application.doctype.vendor_aging_tracker.batch_processor.scheduled_batch_processor"
        ]
    }
    """
    try:
        # Process in small batches to avoid timeout
        batch_size = 25
        
        # Process Vendor Onboarding (includes SAP processing)
        vo_result = process_historical_vendor_onboarding_records(batch_size=batch_size)
        
        # Process remaining SAP Logs
        sap_result = process_historical_sap_logs(batch_size=batch_size)
        
        # Log the results
        if vo_result["processed"] > 0 or sap_result["processed"] > 0:
            frappe.log_error(
                f"Batch Processor Summary:\n"
                f"Vendor Onboarding: {vo_result['processed']} processed, {vo_result.get('errors', 0)} errors\n"
                f"SAP Logs: {sap_result['processed']} processed, {sap_result.get('errors', 0)} errors",
                "Batch Processor Success"
            )
        
    except Exception as e:
        frappe.log_error(
            f"Scheduled batch processor failed: {frappe.get_traceback()}",
            "Scheduled Batch Processor Error"
        )


@frappe.whitelist()
def get_processing_status():
    """
    Get current status of records that need processing
    """
    try:
        # Count pending Vendor Onboarding records by status
        pending_vo_all = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabVendor Aging Tracker` vat 
                ON vat.vendor_onboarding_link = vo.name
            WHERE vat.name IS NULL
        """, as_dict=1)[0].count
        
        pending_vo_approved = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabVendor Aging Tracker` vat 
                ON vat.vendor_onboarding_link = vo.name
            WHERE vat.name IS NULL
            AND vo.onboarding_form_status = 'Approved'
        """, as_dict=1)[0].count
        
        pending_vo_rejected = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabVendor Aging Tracker` vat 
                ON vat.vendor_onboarding_link = vo.name
            WHERE vat.name IS NULL
            AND (vo.onboarding_form_status = 'Rejected' OR vo.rejected = 1)
        """, as_dict=1)[0].count
        
        pending_vo_other = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding` vo
            LEFT JOIN `tabVendor Aging Tracker` vat 
                ON vat.vendor_onboarding_link = vo.name
            WHERE vat.name IS NULL
            AND vo.onboarding_form_status NOT IN ('Approved', 'Rejected')
            AND (vo.rejected IS NULL OR vo.rejected = 0)
        """, as_dict=1)[0].count
        
        # Count pending SAP Log records (only for Approved vendors with existing trackers)
        pending_sap = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVMS SAP Logs` vsl
            INNER JOIN `tabVendor Onboarding` vo 
                ON vo.name = vsl.vendor_onboarding_link
            INNER JOIN `tabVendor Aging Tracker` vat
                ON vat.vendor_onboarding_link = vo.name
            WHERE vsl.status = 'Success'
            AND vsl.total_transaction IS NOT NULL
            AND vsl.total_transaction != ''
            AND vo.onboarding_form_status = 'Approved'
            AND NOT EXISTS (
                SELECT 1 
                FROM `tabVendor Aging Company Codes` vacc
                WHERE vacc.vms_sap_log = vsl.name
            )
        """, as_dict=1)[0].count
        
        # Count total Vendor Aging Trackers
        total_trackers = frappe.db.count("Vendor Aging Tracker")
        
        # Count trackers by status
        active_trackers = frappe.db.count("Vendor Aging Tracker", {"vendor_status": "Active"})
        inactive_trackers = frappe.db.count("Vendor Aging Tracker", {"vendor_status": "Inactive"})
        pending_trackers = frappe.db.count("Vendor Aging Tracker", {"vendor_status": "Pending"})
        
        return {
            "pending_vendor_onboarding": {
                "total": pending_vo_all,
                "approved": pending_vo_approved,
                "rejected": pending_vo_rejected,
                "other": pending_vo_other
            },
            "pending_sap_logs": pending_sap,
            "total_aging_trackers": total_trackers,
            "aging_trackers_by_status": {
                "active": active_trackers,
                "inactive": inactive_trackers,
                "pending": pending_trackers
            },
            "estimated_batches_vo": (pending_vo_all // 50) + (1 if pending_vo_all % 50 else 0),
            "estimated_batches_sap": (pending_sap // 50) + (1 if pending_sap % 50 else 0)
        }
        
    except Exception as e:
        frappe.log_error(
            f"Error getting processing status: {str(e)}",
            "Status Check Error"
        )
        return {"error": str(e)}