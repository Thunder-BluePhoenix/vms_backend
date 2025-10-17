// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

frappe.ui.form.on("Requestor Master", {
    refresh(frm) {
        // Add "SEND To SAP" button
        frm.add_custom_button(__('SEND To SAP'), function() {
            // Confirm before sending
            frappe.confirm(
                'Are you sure you want to send this to SAP?',
                function() {
                    // On confirmation, call your server-side method
                    frappe.call({
                        method: 'vms.APIs.sap.erp_to_sap_mo.erp_to_sap_material_onboarding',
                        args: {
                            requestor_ref: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: __('Sending to SAP...'),
                        callback: function(r) {
                            if (r.message) {
                                frappe.msgprint({
                                    title: __('Success'),
                                    indicator: 'green',
                                    message: __('Successfully sent to SAP')
                                });
                                frm.reload_doc();
                            }
                        },
                        error: function(r) {
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: __('Failed to send to SAP')
                            });
                        }
                    });
                }
            );
        });
    },
});