import frappe
import json
from frappe import _
from datetime import datetime
from frappe.utils import now_datetime, cint, nowdate, format_date

@frappe.whitelist()
def bulk_validate_vendor_codes_optimized(batch_size=2000):
    """
    Optimized bulk validation of vendor codes using raw SQL queries
    Processes all Purchase Orders in batches without using ORM methods
    
    Args:
        batch_size: Number of records to process in each batch (default: 2000)
    """
    try:
        batch_size = cint(batch_size) or 2000
        
        frappe.logger().info("Starting optimized bulk vendor validation")
        
        # Get total count using raw SQL
        total_count = frappe.db.sql("""
                                    SELECT COUNT(*) as count
                                    FROM `tabPurchase Order`
                                    WHERE docstatus != 2
                                    AND sent_to_vendor != 1
                                     """, as_dict=True)[0].count

        if not total_count:
            return {
                "status": "success",
                "message": "No Purchase Orders to validate",
                "total": 0,
                "updated": 0,
                "errors": 0
            }

        total_batches = (total_count // batch_size) + (1 if total_count % batch_size else 0)
        frappe.logger().info(f"Total POs: {total_count}, Batches: {total_batches}, Batch Size: {batch_size}")

        updated_count = 0
        error_count = 0

        # Process in batches
        for batch_num in range(total_batches):
            offset = batch_num * batch_size
            
            try:
                frappe.logger().info(f"Processing batch {batch_num + 1}/{total_batches}")
                
                # Single SQL query to validate and determine vendor_code_invalid status
                validation_results = frappe.db.sql("""
                    SELECT 
                        po.name,
                        po.vendor_code,
                        po.company_code,
                        po.vendor_code_invalid as current_status,
                        CASE
                            WHEN po.vendor_code IS NULL OR po.vendor_code = '' THEN 1
                            WHEN po.company_code IS NULL OR po.company_code = '' THEN 1
                            WHEN cvc.name IS NULL THEN 1
                            WHEN vm.name IS NULL THEN 1
                            WHEN vm.is_blocked = 1 THEN 1
                            WHEN vm.validity_status != 'Valid' THEN 1
                            ELSE 0
                        END as new_status
                    FROM `tabPurchase Order` po
                    LEFT JOIN `tabCompany Vendor Code` cvc 
                        ON cvc.company_code = po.company_code
                    LEFT JOIN `tabVendor Code` vc 
                        ON vc.parent = cvc.name 
                        AND vc.vendor_code = po.vendor_code
                    LEFT JOIN `tabVendor Master` vm 
                        ON vm.name = cvc.vendor_ref_no
                    WHERE po.docstatus != 2
                    AND po.sent_to_vendor != 1
                    LIMIT %s OFFSET %s
                """, (batch_size, offset), as_dict=True)

                if not validation_results:
                    break

                # Prepare bulk update data - only for records where status changes
                updates_to_apply = []
                for row in validation_results:
                    if row.current_status != row.new_status:
                        updates_to_apply.append((row.new_status, row.name))

                # Bulk update - execute individual updates in a transaction
                if updates_to_apply:
                    for new_status, po_name in updates_to_apply:
                        frappe.db.sql("""
                            UPDATE `tabPurchase Order`
                            SET vendor_code_invalid = %s
                            WHERE name = %s
                        """, (new_status, po_name))
                    
                    updated_count += len(updates_to_apply)

                # Commit after each batch
                frappe.db.commit()
                
                frappe.logger().info(
                    f"Batch {batch_num + 1}/{total_batches} completed. "
                    f"Processed: {len(validation_results)}, Updated: {len(updates_to_apply)}"
                )

            except Exception as batch_error:
                error_count += batch_size
                frappe.log_error(
                    f"Error in batch {batch_num + 1}: {str(batch_error)}\n{frappe.get_traceback()}",
                    "Bulk Vendor Validation Batch Error"
                )
                frappe.db.rollback()
                continue

        result = {
            "status": "success",
            "message": f"Validation completed. Total: {total_count}, Updated: {updated_count}, Errors: {error_count}",
            "total": total_count,
            "updated": updated_count,
            "errors": error_count,
            "total_batches": total_batches,
            "batch_size": batch_size
        }

        frappe.logger().info(f"Bulk validation completed: {result['message']}")
        
        return result

    except Exception as e:
        frappe.log_error(
            f"Critical error in bulk vendor validation: {str(e)}\n{frappe.get_traceback()}",
            "Bulk Vendor Validation Critical Error"
        )
        return {
            "status": "error",
            "message": f"Critical error: {str(e)}",
            "total": 0,
            "updated": 0,
            "errors": 0
        }


@frappe.whitelist()
def enqueue_bulk_validate_vendor_codes(batch_size=2000):
    """
    Enqueue bulk validation as a background job
    
    Args:
        batch_size: Number of records to process in each batch (default: 2000)
    
    Returns:
        Success message indicating job has been queued
    """
    try:
        batch_size = cint(batch_size) or 2000
        
        # Enqueue the job
        job = frappe.enqueue(
            method="vms.purchase.doctype.purchase_order.po_vm_validation_corn.bulk_validate_vendor_codes_optimized",
            queue="long",
            timeout=7200,  # 2 hours timeout
            is_async=True,
            batch_size=batch_size,
            job_name=f"Bulk Vendor Validation - {now_datetime()}"
        )
        
        frappe.msgprint(
            msg="Bulk vendor validation job has been queued successfully. You will be notified once completed.",
            title="Job Queued",
            indicator="blue"
        )
        
        return {
            "status": "success",
            "message": "Bulk validation job enqueued successfully. Check background jobs for progress.",
            "job_id": job.id if hasattr(job, 'id') else None,
            "batch_size": batch_size
        }
        
    except Exception as e:
        frappe.log_error(
            f"Error enqueueing bulk validation job: {str(e)}\n{frappe.get_traceback()}",
            "Enqueue Bulk Validation Error"
        )
        return {
            "status": "error",
            "message": f"Failed to enqueue job: {str(e)}"
        }