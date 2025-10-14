// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

// File: vms/vms_masters/doctype/company_vendor_code/company_vendor_code.js

frappe.ui.form.on('Company Vendor Code', {
    refresh: function(frm) {
        // Add button to sync addresses for this specific company vendor code
        if (!frm.is_new() && frm.doc.vendor_ref_no) {
            frm.add_custom_button(__('Sync Addresses from Source'), function() {
                frappe.confirm(
                    __('This will update address fields in vendor codes from the source data. Continue?'),
                    function() {
                        frappe.call({
                            method: 'vms.vms_masters.doctype.company_vendor_code.corn_system_vendor_code.sync_single_vendor_addresses',
                            args: {
                                vendor_master_name: frm.doc.vendor_ref_no
                            },
                            callback: function(r) {
                                if (r.message) {
                                    if (r.message.status === 'success') {
                                        frappe.show_alert({
                                            message: __(r.message.message),
                                            indicator: 'green'
                                        }, 5);
                                        frm.reload_doc();
                                    } else {
                                        frappe.msgprint({
                                            title: __(r.message.status === 'info' ? 'Info' : 'Error'),
                                            message: __(r.message.message),
                                            indicator: r.message.status === 'info' ? 'blue' : 'red'
                                        });
                                    }
                                }
                            }
                        });
                    }
                );
            }, __('Actions'));
        }
    }
});