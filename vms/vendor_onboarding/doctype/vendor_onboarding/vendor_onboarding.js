// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Vendor Onboarding", {
// 	refresh(frm) {....&& frm.doc.mandatory_data_filled

// 	},
// });
frappe.ui.form.on('Vendor Onboarding', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && !frm.doc.data_sent_to_sap && frm.doc.mandatory_data_filled) {
            frm.add_custom_button(__('Send to SAP'), function() {
                let btn = $(event.target);
                
                frappe.call({
                    method: 'vms.APIs.sap.sap.send_vendor_to_sap',
                    args: {
                        doc_name: frm.doc.name
                    },
                    btn: btn, 
                    freeze: true, 
                    freeze_message: __('Sending data to SAP...'), 
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                        
                            frappe.show_alert({
                                message: __('Data sent to SAP successfully'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: __('Error sending data to SAP')
                            });
                        }
                    },
                    error: function(error) {
                      
                        frappe.msgprint({
                            title: __('Error'),
                            indicator: 'red',
                            message: __('Failed to send data to SAP. Please try again.')
                        });
                        console.error('SAP API Error:', error);
                    }
                });
            }).addClass('btn-primary'); 
        }
    }
});