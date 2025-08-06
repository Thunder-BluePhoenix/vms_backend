import frappe
from vms.vendor_onboarding.vendor_document_management import VendorDocumentManager

def execute():
    """Migrate existing vendor onboardings to new document structure"""
    
    # Get all approved vendor onboardings
    onboardings = frappe.get_all(
        "Vendor Onboarding",
        filters={
            "onboarding_form_status": ["in", ["Approved", "Completed"]],
            "ref_no": ["is", "set"]
        },
        fields=["name", "ref_no"]
    )
    
    success_count = 0
    error_count = 0
    
    for onboarding in onboardings:
        try:
            # Check if vendor master exists
            if frappe.db.exists("Vendor Master", onboarding.ref_no):
                result = VendorDocumentManager.create_or_update_vendor_master_docs(onboarding.name)
                
                if result.get("status") == "success":
                    success_count += 1
                    print(f"✓ Synced {onboarding.name}")
                else:
                    error_count += 1
                    print(f"✗ Failed {onboarding.name}: {result.get('message')}")
            else:
                error_count += 1
                print(f"✗ Vendor Master {onboarding.ref_no} not found")
                
        except Exception as e:
            error_count += 1
            print(f"✗ Error processing {onboarding.name}: {str(e)}")
    
    print(f"\nMigration Complete: {success_count} successful, {error_count} errors")