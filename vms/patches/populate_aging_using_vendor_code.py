# vms/patches/v1_0/install_qr_dependencies.py

import frappe
import subprocess
import sys
import os

def execute():
    """Install QR code and other dependencies during migration"""
    
    frappe.flags.in_patch = True
    
    try:
        versions = frappe.get_all(
            "Version",
            filters={"ref_doctype": "Company Vendor Code"},
            fields=["name", "docname", "ref_doctype", "data", "modified"],
        )


        for item in versions[:]:
            parent_name = item.get("docname")
            company_vendor_code_doc = frappe.get_doc("Company Vendor Code", parent_name)
            creation_time = company_vendor_code_doc.creation

            vendor_master_doc = frappe.get_doc("Vendor Master", company_vendor_code_doc.vendor_ref_no)
            vendor_onboarding_number = vendor_master_doc.onboarding_ref_no

            # update child rows in-memory then save parent
            updated = False
            dateUpdated = False
            for row in company_vendor_code_doc.get("vendor_code") or []:
                # replace "vendor_onboarding" with actual child fieldname if different
                if row.get("vendor_onboarding") != vendor_onboarding_number:
                    row.vendor_onboarding = vendor_onboarding_number
                    updated = True
                if "datetime" in row.as_dict():
                    row.set("datetime", creation_time)
                    dateUpdated = True

            if updated or dateUpdated:
                company_vendor_code_doc.save(ignore_permissions=True)
                print(row.vendor_onboarding, row.datetime)
        frappe.db.commit()
            
    except Exception as e:
        error_msg = f"Dependency installation failed: {str(e)}"
        print(f"\n❌ {error_msg}")
        frappe.log_error(error_msg, "VMS Dependency Installation Patch")
        
    finally:
        frappe.flags.in_patch = False