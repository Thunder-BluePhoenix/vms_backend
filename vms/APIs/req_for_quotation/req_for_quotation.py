import frappe

@frappe.whitelist(allow_guest=True)
def vendor_list(rfq_type):
    pass
    # try:
    #     vendor_list = frappe.get_all("Vendor Master", for doc in vendor_types (vendor_type: rfq_type), names)

    #     for vendor in vendor_list:
    #         vendor_master = frappe.get_doc("vendor master", vendor_list.name)



    #         return {
    #             "refno": vendor_master.name,
    #             "vendor name": vendor_master.vendor_name
    #             "office_email_primary name": vendor_master.office_email_primary,
    #             "mobile_number name": vendor_master.mobile_number,
    #             "country name": vendor_master.country                
    #         }