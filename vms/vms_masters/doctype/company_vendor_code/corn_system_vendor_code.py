# File: vms/vms_masters/doctype/company_vendor_code/company_vendor_code_address_sync_cron.py

import frappe
from frappe.utils import now_datetime
import json

def sync_vendor_code_addresses_from_sources():
    """
    Main cron job to sync addresses from Vendor Import Staging or VMS SAP Logs
    to Company Vendor Code child table
    
    Logic Flow:
    1. For each Vendor Master → Multiple Company Data rows
    2. Check via_import flag (0 or 1)
    3. If via_import = 1: Fetch from Vendor Import Staging
    4. If via_import = 0: Fetch from VMS SAP Logs → Vendor Onboarding Company Details
    """
    try:
        frappe.logger().info("=" * 80)
        frappe.logger().info("Starting Vendor Code Address Sync from Sources")
        frappe.logger().info("=" * 80)
        
        # Get all Vendor Master documents
        vendor_masters = frappe.get_all("Vendor Master", fields=["name", "vendor_name"])
        
        total_vendors = len(vendor_masters)
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for idx, vm in enumerate(vendor_masters, 1):
            try:
                frappe.logger().info(f"\n[{idx}/{total_vendors}] Processing Vendor: {vm.name} - {vm.vendor_name}")
                
                # Load full vendor master document
                vendor_doc = frappe.get_doc("Vendor Master", vm.name)
                
                # Check if multiple_company_data exists
                if not hasattr(vendor_doc, 'multiple_company_data') or not vendor_doc.multiple_company_data:
                    frappe.logger().info(f"  ⊘ No multiple company data found")
                    skipped_count += 1
                    continue
                
                # Process each company in Multiple Company Data
                for mcd_row in vendor_doc.multiple_company_data:
                    try:
                        if not mcd_row.company_vendor_code:
                            frappe.logger().info(f"  ⊘ No Company Vendor Code for company: {mcd_row.company_name}")
                            continue
                        
                        frappe.logger().info(f"\n  → Processing Company: {mcd_row.company_name}")
                        frappe.logger().info(f"    Company Vendor Code: {mcd_row.company_vendor_code}")
                        frappe.logger().info(f"    Via Import: {mcd_row.via_import}")
                        
                        # Get Company Vendor Code document
                        cvc_doc = frappe.get_doc("Company Vendor Code", mcd_row.company_vendor_code)
                        
                        if not hasattr(cvc_doc, 'vendor_code') or not cvc_doc.vendor_code:
                            frappe.logger().info(f"    ⊘ No vendor codes in child table")
                            continue
                        
                        # Check via_import flag to determine source
                        if mcd_row.via_import == 1:
                            # Source: Vendor Import Staging
                            frappe.logger().info(f"    📥 Source: Vendor Import Staging")
                            result = update_from_vendor_import_staging(
                                cvc_doc, 
                                mcd_row.company_name,
                                vendor_doc.name
                            )
                        else:
                            # Source: VMS SAP Logs → Vendor Onboarding Company Details
                            frappe.logger().info(f"    📥 Source: VMS SAP Logs → Vendor Onboarding")
                            result = update_from_sap_logs_onboarding(
                                cvc_doc,
                                mcd_row.company_name,
                                vendor_doc.name
                            )
                        
                        if result.get("updated"):
                            updated_count += 1
                            frappe.logger().info(f"    ✓ Updated {result.get('rows_updated', 0)} vendor code(s)")
                        else:
                            frappe.logger().info(f"    ⊘ {result.get('message', 'No updates needed')}")
                    
                    except Exception as e:
                        error_count += 1
                        frappe.log_error(
                            message=f"Error processing company {mcd_row.company_name} for vendor {vm.name}: {str(e)}\n{frappe.get_traceback()}",
                            title="Company Address Sync Error"
                        )
                        continue
            
            except Exception as e:
                error_count += 1
                frappe.log_error(
                    message=f"Error processing vendor {vm.name}: {str(e)}\n{frappe.get_traceback()}",
                    title="Vendor Address Sync Error"
                )
                continue
        
        # Summary
        summary = f"""
        ╔══════════════════════════════════════════════════════════╗
        ║        Vendor Code Address Sync - Summary                ║
        ╠══════════════════════════════════════════════════════════╣
        ║  Total Vendors Processed: {total_vendors:>4}                        ║
        ║  Successfully Updated:    {updated_count:>4}                        ║
        ║  Skipped:                 {skipped_count:>4}                        ║
        ║  Errors:                  {error_count:>4}                        ║
        ║  Timestamp: {str(now_datetime()):<37} ║
        ╚══════════════════════════════════════════════════════════╝
        """
        frappe.logger().info(summary)
        
        return {
            "status": "success",
            "total_vendors": total_vendors,
            "updated": updated_count,
            "skipped": skipped_count,
            "errors": error_count
        }
    
    except Exception as e:
        frappe.log_error(
            message=f"Address Sync Cron Failed: {str(e)}\n{frappe.get_traceback()}",
            title="Address Sync Cron Error"
        )
        return {
            "status": "error",
            "message": str(e)
        }


def update_from_vendor_import_staging(cvc_doc, company_name, vendor_ref_no):
    """
    Update addresses from Vendor Import Staging using db_set
    Matches by: c_code (company_code) and vendor_code
    """
    try:
        # Get company_code from Company Vendor Code
        company_code = cvc_doc.company_code
        
        if not company_code:
            return {"updated": False, "message": "No company code found"}
        
        frappe.logger().info(f"      Searching Vendor Import Staging with:")
        frappe.logger().info(f"        Company Code: {company_code}")
        
        has_changes = False
        rows_updated = 0
        
        # Process each vendor code in child table
        for vc_row in cvc_doc.vendor_code:
            vendor_code = vc_row.vendor_code
            
            if not vendor_code:
                continue
            
            frappe.logger().info(f"        Vendor Code: {vendor_code}")
            
            # Search Vendor Import Staging
            staging_records = frappe.db.sql("""
                SELECT 
                    name, city, address01, address02, address03, 
                    pincode, state, country
                FROM `tabVendor Import Staging`
                WHERE c_code = %s 
                AND vendor_code = %s
                LIMIT 1
            """, (company_code, vendor_code), as_dict=True)
            
            if not staging_records:
                frappe.logger().info(f"          ⊘ No staging record found")
                continue
            
            staging = staging_records[0]
            frappe.logger().info(f"          ✓ Found staging record: {staging.name}")
            
            # Update fields using db_set on the child row object
            updates = []
            
            if staging.city and vc_row.city != staging.city:
                vc_row.db_set("city", staging.city, update_modified=False)
                updates.append("city")
                has_changes = True
            
            if staging.address01 and vc_row.address_line_1 != staging.address01:
                vc_row.db_set("address_line_1", staging.address01, update_modified=False)
                updates.append("address_line_1")
                has_changes = True
            
            if staging.address02 and vc_row.address_line_2 != staging.address02:
                vc_row.db_set("address_line_2", staging.address02, update_modified=False)
                updates.append("address_line_2")
                has_changes = True

            if staging.address03 and vc_row.address_line_3 != staging.address03:
                vc_row.db_set("address_line_3", staging.address03, update_modified=False)
                updates.append("address_line_3")
                has_changes = True
            
            # Note: Vendor Code child table doesn't have address_line_3 field
            # So we skip address03
            
            # if staging.district and vc_row.district != staging.district:
            #     vc_row.db_set("district", staging.district, update_modified=False)
            #     updates.append("district")
            #     has_changes = True
            
            if staging.pincode and vc_row.zip_code != staging.pincode:
                vc_row.db_set("zip_code", staging.pincode, update_modified=False)
                updates.append("zip_code")
                has_changes = True
            
            if staging.country and vc_row.country != staging.country:
                vc_row.db_set("country", staging.country, update_modified=False)
                updates.append("country")
                has_changes = True
            
            if updates:
                rows_updated += 1
                frappe.logger().info(f"          ✓ Updated: {', '.join(updates)}")
        
        # Commit changes
        if has_changes:
            frappe.db.commit()
            return {
                "updated": True,
                "rows_updated": rows_updated,
                "message": f"Updated {rows_updated} row(s) from Vendor Import Staging"
            }
        
        return {"updated": False, "message": "No changes needed"}
    
    except Exception as e:
        frappe.logger().error(f"Error in update_from_vendor_import_staging: {str(e)}")
        raise


def update_from_sap_logs_onboarding(cvc_doc, company_name, vendor_ref_no):
    """
    Update addresses from VMS SAP Logs → Vendor Onboarding → Company Details using db_set
    Matches by: ref_no, company_name in total_transaction, then vendor_code
    """
    try:
        company_code = cvc_doc.company_code
        
        if not company_code:
            return {"updated": False, "message": "No company code found"}
        
        frappe.logger().info(f"      Searching VMS SAP Logs with:")
        frappe.logger().info(f"        Ref No: {vendor_ref_no}")
        frappe.logger().info(f"        Company Code: {company_code}")
        
        has_changes = False
        rows_updated = 0
        
        # Get all SAP logs for this vendor
        sap_logs = frappe.db.sql("""
            SELECT 
                name, total_transaction, vendor_onboarding_link, status
            FROM `tabVMS SAP Logs`
            WHERE ref_no = %s
            AND status = 'Success'
            AND total_transaction IS NOT NULL
            AND total_transaction != ''
            ORDER BY creation DESC
        """, (vendor_ref_no,), as_dict=True)
        
        if not sap_logs:
            frappe.logger().info(f"        ⊘ No SAP logs found")
            return {"updated": False, "message": "No SAP logs found"}
        
        frappe.logger().info(f"        ✓ Found {len(sap_logs)} SAP log(s)")
        
        # Process each vendor code in child table
        for vc_row in cvc_doc.vendor_code:
            vendor_code = vc_row.vendor_code
            
            if not vendor_code:
                continue
            
            frappe.logger().info(f"        Processing Vendor Code: {vendor_code}")
            
            # Find matching SAP log
            matching_log = None
            for log in sap_logs:
                try:
                    transaction_data = json.loads(log.total_transaction)
                    
                    # Check transaction_summary
                    trans_summary = transaction_data.get("transaction_summary", {})
                    log_vendor_code = trans_summary.get("vendor_code", "")
                    log_company_name = trans_summary.get("company_name", "")
                    
                    # Match vendor_code and company_name
                    if log_vendor_code == vendor_code and log_company_name == company_code:
                        matching_log = log
                        frappe.logger().info(f"          ✓ Found matching SAP log: {log.name}")
                        break
                
                except Exception as e:
                    frappe.logger().error(f"          Error parsing log {log.name}: {str(e)}")
                    continue
            
            if not matching_log:
                frappe.logger().info(f"          ⊘ No matching SAP log found")
                continue
            
            # Get vendor_onboarding_link
            vendor_onboarding_link = matching_log.vendor_onboarding_link
            
            if not vendor_onboarding_link:
                frappe.logger().info(f"          ⊘ No vendor onboarding link in SAP log")
                continue
            
            frappe.logger().info(f"          Vendor Onboarding: {vendor_onboarding_link}")
            
            # Get Vendor Onboarding document
            try:
                vonb_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding_link)
            except:
                frappe.logger().info(f"          ⊘ Vendor Onboarding not found")
                continue
            
            # Find Company of Vendor matching the company_name
            company_details_link = None
            
            if hasattr(vonb_doc, 'vendor_company_details'):
                for cov_row in vonb_doc.vendor_company_details:
                    if cov_row.vendor_company_details:
                        try:
                            # Get the actual Vendor Onboarding Company Details doc
                            temp_doc = frappe.get_doc("Vendor Onboarding Company Details", cov_row.vendor_company_details)
                            
                            # Check if company_name matches
                            if temp_doc.company_name == company_name:
                                company_details_link = cov_row.vendor_company_details
                                frappe.logger().info(f"          ✓ Found Company Details: {company_details_link}")
                                break
                        except:
                            continue
            
            if not company_details_link:
                frappe.logger().info(f"          ⊘ No matching Company Details found")
                continue
            
            # Get Vendor Onboarding Company Details
            try:
                vocd_doc = frappe.get_doc("Vendor Onboarding Company Details", company_details_link)
            except:
                frappe.logger().info(f"          ⊘ Company Details not found")
                continue
            
            # Determine if domestic or international
            is_domestic = vonb_doc.vendor_country in ["India", "IN", "IND"] if vocd_doc.country else True
            
            # Update fields using db_set based on domestic/international
            updates = []
            
            if is_domestic:
                # Use domestic address fields
                if vocd_doc.city and vc_row.city != vocd_doc.city:
                    vc_row.db_set("city", vocd_doc.city, update_modified=False)
                    updates.append("city")
                    has_changes = True
                
                if vocd_doc.district and vc_row.district != vocd_doc.district:
                    vc_row.db_set("district", vocd_doc.district, update_modified=False)
                    updates.append("district")
                    has_changes = True
                
                if vocd_doc.pincode and vc_row.zip_code != vocd_doc.pincode:
                    vc_row.db_set("zip_code", vocd_doc.pincode, update_modified=False)
                    updates.append("zip_code")
                    has_changes = True
                
                if vocd_doc.country and vc_row.country != vocd_doc.country:
                    vc_row.db_set("country", vocd_doc.country, update_modified=False)
                    updates.append("country")
                    has_changes = True
            else:
                # Use international address fields
                if vocd_doc.international_city and vc_row.city != vocd_doc.international_city:
                    vc_row.db_set("city", vocd_doc.international_city, update_modified=False)
                    updates.append("city")
                    has_changes = True
                
                # International doesn't have district in most cases
                
                if vocd_doc.international_zipcode and vc_row.zip_code != vocd_doc.international_zipcode:
                    vc_row.db_set("zip_code", vocd_doc.international_zipcode, update_modified=False)
                    updates.append("zip_code")
                    has_changes = True
                
                if vocd_doc.international_country and vc_row.country != vocd_doc.international_country:
                    vc_row.db_set("country", vocd_doc.international_country, update_modified=False)
                    updates.append("country")
                    has_changes = True
            
            # Common address fields (both domestic and international)
            if vocd_doc.address_line_1 and vc_row.address_line_1 != vocd_doc.address_line_1:
                vc_row.db_set("address_line_1", vocd_doc.address_line_1, update_modified=False)
                updates.append("address_line_1")
                has_changes = True
            
            if vocd_doc.address_line_2 and vc_row.address_line_2 != vocd_doc.address_line_2:
                vc_row.db_set("address_line_2", vocd_doc.address_line_2, update_modified=False)
                updates.append("address_line_2")
                has_changes = True
            
            if updates:
                rows_updated += 1
                address_type = "domestic" if is_domestic else "international"
                frappe.logger().info(f"          ✓ Updated ({address_type}): {', '.join(updates)}")
        
        # Commit changes
        if has_changes:
            frappe.db.commit()
            return {
                "updated": True,
                "rows_updated": rows_updated,
                "message": f"Updated {rows_updated} row(s) from Vendor Onboarding"
            }
        
        return {"updated": False, "message": "No changes needed"}
    
    except Exception as e:
        frappe.logger().error(f"Error in update_from_sap_logs_onboarding: {str(e)}")
        raise


# Whitelisted methods for manual triggers
@frappe.whitelist()
def trigger_address_sync():
    """
    Manually trigger the address sync job
    """
    frappe.enqueue(
        sync_vendor_code_addresses_from_sources,
        queue='long',
        timeout=6000,
        is_async=True,
        job_name='sync_vendor_code_addresses'
    )
    
    return {
        "status": "success",
        "message": "Address sync job has been queued"
    }


@frappe.whitelist()
def sync_single_vendor_addresses(vendor_master_name):
    """
    Sync addresses for a single vendor using db_set
    """
    try:
        vendor_doc = frappe.get_doc("Vendor Master", vendor_master_name)
        
        if not hasattr(vendor_doc, 'multiple_company_data') or not vendor_doc.multiple_company_data:
            return {
                "status": "error",
                "message": "No multiple company data found"
            }
        
        updated_companies = []
        
        for mcd_row in vendor_doc.multiple_company_data:
            if not mcd_row.company_vendor_code:
                continue
            
            cvc_doc = frappe.get_doc("Company Vendor Code", mcd_row.company_vendor_code)
            
            if mcd_row.via_import == 1:
                result = update_from_vendor_import_staging(
                    cvc_doc, 
                    mcd_row.company_name,
                    vendor_doc.name
                )
            else:
                result = update_from_sap_logs_onboarding(
                    cvc_doc,
                    mcd_row.company_name,
                    vendor_doc.name
                )
            
            if result.get("updated"):
                updated_companies.append(mcd_row.company_name)
        
        if updated_companies:
            return {
                "status": "success",
                "message": f"Updated addresses for {len(updated_companies)} company(ies)",
                "companies": updated_companies
            }
        else:
            return {
                "status": "info",
                "message": "No updates needed"
            }
    
    except Exception as e:
        frappe.log_error(
            message=f"Error syncing single vendor: {str(e)}\n{frappe.get_traceback()}",
            title="Single Vendor Sync Error"
        )
        return {
            "status": "error",
            "message": str(e)
        }