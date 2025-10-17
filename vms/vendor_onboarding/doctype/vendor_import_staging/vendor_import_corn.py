# File: vms/vms_masters/doctype/company_vendor_code/company_vendor_code_cron.py

import frappe
from frappe.utils import now_datetime, add_days, get_datetime
import json

def update_vendor_code_addresses():
    """
    Cron job to update address fields in Vendor Code child table of Company Vendor Code
    Handles both domestic and international addresses
    Updates: city, address_line_1, address_line_2, district, zip_code, country
    Sources: Vendor Onboarding Company Details, Vendor Import Staging, Vendor Master
    """
    try:
        frappe.logger().info("Starting Vendor Code Address Update Cron Job")
        
        # Get all Company Vendor Code documents
        company_vendor_codes = frappe.get_all(
            "Company Vendor Code",
            fields=["name", "vendor_ref_no", "company_name"]
        )
        
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        for cvc in company_vendor_codes:
            try:
                # Load the full document
                doc = frappe.get_doc("Company Vendor Code", cvc.name)
                
                if not doc.vendor_code:
                    skipped_count += 1
                    continue
                
                # Priority 1: Get from Vendor Onboarding Company Details (company-specific)
                company_address_data = get_vendor_onboarding_company_address(
                    doc.vendor_ref_no, 
                    doc.company_name
                )
                
                # Priority 2: Get from Vendor Import Staging
                if not company_address_data:
                    company_address_data = get_vendor_import_staging_address(
                        doc.vendor_ref_no,
                        doc.company_name
                    )
                
                # Priority 3: Get from Vendor Master (fallback)
                vendor_address_data = None
                if not company_address_data and doc.vendor_ref_no:
                    vendor_address_data = get_vendor_address_from_master(doc.vendor_ref_no)
                
                # Determine which address data to use
                address_data = company_address_data or vendor_address_data
                
                if not address_data:
                    skipped_count += 1
                    continue
                
                # Update each vendor code row in the child table
                has_changes = False
                for row in doc.vendor_code:
                    # Check if row's state/country matches address type
                    is_domestic = is_domestic_address(row.state, row.country)
                    
                    # Get appropriate address data (domestic or international)
                    if is_domestic and address_data.get("domestic"):
                        selected_address = address_data["domestic"]
                    elif not is_domestic and address_data.get("international"):
                        selected_address = address_data["international"]
                    else:
                        # Use fallback if specific type not available
                        selected_address = address_data.get("domestic") or address_data.get("international") or {}
                    
                    # Update fields if they exist and are different
                    if update_field(row, 'city', selected_address.get("city")):
                        has_changes = True
                    
                    if update_field(row, 'address_line_1', selected_address.get("address_line1")):
                        has_changes = True
                    
                    if update_field(row, 'address_line_2', selected_address.get("address_line2")):
                        has_changes = True
                    
                    if update_field(row, 'district', selected_address.get("district")):
                        has_changes = True
                    
                    if update_field(row, 'zip_code', selected_address.get("zip_code")):
                        has_changes = True
                    
                    if update_field(row, 'country', selected_address.get("country")):
                        has_changes = True
                
                # Save the document if there were changes
                if has_changes:
                    doc.flags.ignore_permissions = True
                    doc.flags.ignore_mandatory = True
                    doc.save()
                    frappe.db.commit()
                    updated_count += 1
                    frappe.logger().info(f"Updated Company Vendor Code: {doc.name}")
                else:
                    skipped_count += 1
            
            except Exception as e:
                error_count += 1
                frappe.log_error(
                    message=f"Error updating Company Vendor Code {cvc.name}: {str(e)}\n{frappe.get_traceback()}",
                    title="Vendor Code Address Update Error"
                )
                continue
        
        # Log summary
        summary = f"""
        Vendor Code Address Update Completed
        =====================================
        Total Processed: {len(company_vendor_codes)}
        Successfully Updated: {updated_count}
        Skipped (No Changes/Data): {skipped_count}
        Errors: {error_count}
        Timestamp: {now_datetime()}
        """
        frappe.logger().info(summary)
        
        return {
            "status": "success",
            "total_processed": len(company_vendor_codes),
            "updated": updated_count,
            "skipped": skipped_count,
            "errors": error_count
        }
    
    except Exception as e:
        frappe.log_error(
            message=f"Vendor Code Address Update Cron Failed: {str(e)}\n{frappe.get_traceback()}",
            title="Vendor Code Address Cron Error"
        )
        return {
            "status": "error",
            "message": str(e)
        }


def update_field(row, fieldname, new_value):
    """
    Update field only if new value exists and is different
    Returns True if field was updated
    """
    if new_value and str(getattr(row, fieldname, "")) != str(new_value):
        setattr(row, fieldname, new_value)
        return True
    return False


def is_domestic_address(state, country):
    """
    Determine if address is domestic (India) or international
    Returns True for domestic, False for international
    """
    if not country:
        return True  # Default to domestic if no country specified
    
    # Check if country is India
    india_identifiers = ["India", "INDIA", "IN", "IND"]
    
    if isinstance(country, str):
        return country.strip() in india_identifiers
    
    # If country is a link, check the actual country name
    try:
        country_name = frappe.db.get_value("Country Master", country, "country_name")
        return country_name in india_identifiers if country_name else True
    except:
        return True


def get_vendor_address_from_master(vendor_ref_no):
    """
    Get address details from Vendor Master
    Returns dict with domestic and international addresses
    """
    try:
        if not frappe.db.exists("Vendor Master", vendor_ref_no):
            return None
        
        vendor_master = frappe.get_doc("Vendor Master", vendor_ref_no)
        
        # Build address data
        address_data = {
            "domestic": {
                "city": vendor_master.get("city") or "",
                "address_line1": vendor_master.get("address_line_1") or vendor_master.get("address_line1") or "",
                "address_line2": vendor_master.get("address_line_2") or vendor_master.get("address_line2") or "",
                "district": vendor_master.get("district") or "",
                "zip_code": vendor_master.get("pincode") or vendor_master.get("zip_code") or "",
                "country": vendor_master.get("country") or "India"
            },
            "international": {
                "city": vendor_master.get("international_city") or "",
                "address_line1": vendor_master.get("address_line_1") or "",
                "address_line2": vendor_master.get("address_line_2") or "",
                "district": "",
                "zip_code": vendor_master.get("international_zipcode") or "",
                "country": vendor_master.get("international_country") or ""
            }
        }
        
        return address_data
    
    except Exception as e:
        frappe.logger().error(f"Error fetching vendor address for {vendor_ref_no}: {str(e)}")
        return None


def get_vendor_onboarding_company_address(vendor_ref_no, company_name):
    """
    Get address details from Vendor Onboarding Company Details
    Returns dict with domestic and international addresses
    """
    try:
        if not vendor_ref_no or not company_name:
            return None
        
        # Find the company details document
        company_details = frappe.get_all(
            "Vendor Onboarding Company Details",
            filters={
                "ref_no": vendor_ref_no,
                "company_name": company_name
            },
            fields=["name"],
            limit=1
        )
        
        if not company_details:
            return None
        
        doc = frappe.get_doc("Vendor Onboarding Company Details", company_details[0].name)
        
        # Domestic address (Indian address)
        domestic_address = {
            "city": doc.get("city") or "",
            "address_line1": doc.get("address_line_1") or "",
            "address_line2": doc.get("address_line_2") or "",
            "district": doc.get("district") or "",
            "zip_code": doc.get("pincode") or "",
            "country": doc.get("country") or "India"
        }
        
        # International address
        international_address = {
            "city": doc.get("international_city") or "",
            "address_line1": doc.get("address_line_1") or "",  # May use same address lines
            "address_line2": doc.get("address_line_2") or "",
            "district": "",
            "zip_code": doc.get("international_zipcode") or "",
            "country": doc.get("international_country") or ""
        }
        
        address_data = {
            "domestic": domestic_address,
            "international": international_address
        }
        
        return address_data
    
    except Exception as e:
        frappe.logger().error(
            f"Error fetching company address for {vendor_ref_no}, {company_name}: {str(e)}"
        )
        return None


def get_vendor_import_staging_address(vendor_ref_no, company_name):
    """
    Get address details from Vendor Import Staging
    Returns dict with domestic and international addresses
    """
    try:
        if not vendor_ref_no:
            return None
        
        # Find staging records linked to this vendor
        staging_records = frappe.get_all(
            "Vendor Import Staging",
            filters={
                "vendor_master_id": vendor_ref_no,
                "company_code": ["like", f"%{company_name}%"] if company_name else ["is", "set"]
            },
            fields=["name"],
            limit=1
        )
        
        if not staging_records:
            # Try alternate lookup by vendor code
            staging_records = frappe.get_all(
                "Vendor Import Staging",
                filters={
                    "vendor_code": ["like", f"%{vendor_ref_no}%"]
                },
                fields=["name"],
                limit=1
            )
        
        if not staging_records:
            return None
        
        doc = frappe.get_doc("Vendor Import Staging", staging_records[0].name)
        
        # Check if vendor is domestic or international based on available fields
        # In staging, address fields are stored directly
        has_state = doc.get("state") and doc.get("state") != ""
        
        if has_state:
            # Domestic vendor
            domestic_address = {
                "city": doc.get("city") or "",
                "address_line1": doc.get("address01") or "",
                "address_line2": doc.get("address02") or "",
                "district": "",  # Not available in staging
                "zip_code": doc.get("pincode") or "",
                "country": "India"
            }
            
            address_data = {
                "domestic": domestic_address,
                "international": {}
            }
        else:
            # International vendor (no state in India)
            international_address = {
                "city": doc.get("city") or "",
                "address_line1": doc.get("address01") or "",
                "address_line2": doc.get("address02") or "",
                "district": "",
                "zip_code": doc.get("pincode") or "",
                "country": doc.get("country") or ""
            }
            
            address_data = {
                "domestic": {},
                "international": international_address
            }
        
        return address_data
    
    except Exception as e:
        frappe.logger().error(
            f"Error fetching staging address for {vendor_ref_no}: {str(e)}"
        )
        return None


# Whitelisted method to manually trigger the cron
@frappe.whitelist()
def trigger_vendor_code_address_update():
    """
    Manually trigger the vendor code address update
    Can be called via API or button
    """
    frappe.enqueue(
        update_vendor_code_addresses,
        queue='long',
        timeout=3000,
        is_async=True,
        job_name='update_vendor_code_addresses'
    )
    
    return {
        "status": "success",
        "message": "Vendor Code Address Update job has been queued"
    }


@frappe.whitelist()
def update_single_vendor_code_address(company_vendor_code_name):
    """
    Update address for a single Company Vendor Code document
    Useful for manual updates or testing
    """
    try:
        doc = frappe.get_doc("Company Vendor Code", company_vendor_code_name)
        
        if not doc.vendor_code:
            return {
                "status": "error",
                "message": "No vendor codes found in this document"
            }
        
        # Get address data
        company_address_data = get_vendor_onboarding_company_address(
            doc.vendor_ref_no, 
            doc.company_name
        )
        
        if not company_address_data:
            company_address_data = get_vendor_import_staging_address(
                doc.vendor_ref_no,
                doc.company_name
            )
        
        vendor_address_data = None
        if not company_address_data and doc.vendor_ref_no:
            vendor_address_data = get_vendor_address_from_master(doc.vendor_ref_no)
        
        address_data = company_address_data or vendor_address_data
        
        if not address_data:
            return {
                "status": "error",
                "message": "No address data found"
            }
        
        # Update vendor codes
        has_changes = False
        for row in doc.vendor_code:
            is_domestic = is_domestic_address(row.state, row.country)
            
            if is_domestic and address_data.get("domestic"):
                selected_address = address_data["domestic"]
            elif not is_domestic and address_data.get("international"):
                selected_address = address_data["international"]
            else:
                selected_address = address_data.get("domestic") or address_data.get("international") or {}
            
            if update_field(row, 'city', selected_address.get("city")):
                has_changes = True
            if update_field(row, 'address_line_1', selected_address.get("address_line1")):
                has_changes = True
            if update_field(row, 'address_line_2', selected_address.get("address_line2")):
                has_changes = True
            if update_field(row, 'district', selected_address.get("district")):
                has_changes = True
            if update_field(row, 'zip_code', selected_address.get("zip_code")):
                has_changes = True
            if update_field(row, 'country', selected_address.get("country")):
                has_changes = True
        
        if has_changes:
            doc.flags.ignore_permissions = True
            doc.flags.ignore_mandatory = True
            doc.save()
            frappe.db.commit()
            
            return {
                "status": "success",
                "message": f"Updated {len(doc.vendor_code)} vendor code(s)"
            }
        else:
            return {
                "status": "info",
                "message": "No changes required"
            }
    
    except Exception as e:
        frappe.log_error(
            message=f"Error updating single vendor code: {str(e)}\n{frappe.get_traceback()}",
            title="Single Vendor Code Update Error"
        )
        return {
            "status": "error",
            "message": str(e)
        }