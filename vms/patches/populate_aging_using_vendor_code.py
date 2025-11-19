# vms/patches/v1_0/install_qr_dependencies.py

import frappe

# def execute():
#     """Install QR code and other dependencies during migration"""
    
#     frappe.flags.in_patch = True
    
#     try:
#         versions = frappe.get_all(
#             "Version",
#             filters={"ref_doctype": "Company Vendor Code"},
#             fields=["name", "docname", "ref_doctype", "data", "modified"],
#         )


#         for item in versions[:]:
#             parent_name = item.get("docname")
#             company_vendor_code_doc = frappe.get_doc("Company Vendor Code", parent_name)
#             creation_time = company_vendor_code_doc.creation

#             vendor_master_doc = frappe.get_doc("Vendor Master", company_vendor_code_doc.vendor_ref_no)
#             vendor_onboarding_number = vendor_master_doc.onboarding_ref_no

#             # update child rows in-memory then save parent
#             updated = False
#             dateUpdated = False
#             for row in company_vendor_code_doc.get("vendor_code") or []:
#                 # replace "vendor_onboarding" with actual child fieldname if different
#                 if row.get("vendor_onboarding") != vendor_onboarding_number:
#                     row.vendor_onboarding = vendor_onboarding_number
#                     updated = True
#                 if "datetime" in row.as_dict():
#                     row.set("datetime", creation_time)
#                     dateUpdated = True

#             if updated or dateUpdated:
#                 company_vendor_code_doc.save(ignore_permissions=True)
#                 print(row.vendor_onboarding, row.datetime)
#         frappe.db.commit()
            
#     except Exception as e:
#         error_msg = f"Dependency installation failed: {str(e)}"
#         print(f"\n❌ {error_msg}")
#         frappe.log_error(error_msg, "VMS Dependency Installation Patch")
        
#     finally:
#         frappe.flags.in_patch = False

def execute():
    try:
        vendor_onboarding_entries = frappe.db.get_all( "Vendor Aging Tracker", fields=['vendor_onboarding_link'] )
        
        for entry in vendor_onboarding_entries:
            onb_link = entry['vendor_onboarding_link']  # To be used to set later in vendor code
            onb_doc = frappe.get_doc('Vendor Onboarding', onb_link)
            
            if onb_doc.onboarding_form_status == "Approved":
                multiple_company_data = get_company_name_and_vendor_code_vendor_master(onb_doc.ref_no)
                company = get_company_name_for_onboarding_doc(onb_doc)

                company_vendor_codes = check_matched_company_data(multiple_company_data, company)
                try:
                    for code in company_vendor_codes:
                            # Skip missing vendor code
                        if not code or code in ("", None):
                            frappe.log_error(
                                message=f"Encountered empty company vendor code for company {company}. Skipping.",
                                title="VMS Patch"
                            )
                            continue
                        company_vendor_code_doc = frappe.get_doc("Company Vendor Code", code)
        
                        creation_date = company_vendor_code_doc.creation # To set later in vendor code
                        child_table = company_vendor_code_doc.vendor_code
                        for row in child_table:
                            row.set('vendor_onboarding', onb_link)
                            row.set('datetime', creation_date)
                        
                        company_vendor_code_doc.save()
                    
                except Exception as e:
                    pass

        print("Patch performed successfully!")
        frappe.db.commit()

    except Exception as e:
        frappe.db.rollback()
        error_msg = f"Dependency installation failed: {str(e)}"
        frappe.log_error(
            message=error_msg,
            title="VMS Patch Failure"
        )


# def update_company_vendor_child_table(company_vendor_codes, onboarding_ref):
#     """
#     Takes a list of Company Vendor Code doc names and updates
#     their child table rows by setting vendor_onboarding and datetime.
#     """

#     for code in company_vendor_codes:
#         company_doc = frappe.get_doc("Company Vendor Code", code)
#         creation_date = company_doc.creation

#         for row in company_doc.vendor_code:
#             row.set("vendor_onboarding", onboarding_ref)
#             row.set("datetime", creation_date)

#         company_doc.save()



def check_matched_company_data(list_of_companies, company_data):
    result = list()

    for entry in list_of_companies:
        if entry['company_name'] == company_data:
            result.append(entry['company_vendor_code'])
    return result

def get_company_name_for_onboarding_doc(doc):
    doc_company_name = doc.company_name
    return doc_company_name

def get_company_name_and_vendor_code_vendor_master(doc_ref):
    vendor = frappe.get_doc("Vendor Master", doc_ref)

    results = []
    for row in vendor.multiple_company_data:
        results.append({
            "company_name": row.company_name,
            "company_vendor_code": row.company_vendor_code
        })

    return results
