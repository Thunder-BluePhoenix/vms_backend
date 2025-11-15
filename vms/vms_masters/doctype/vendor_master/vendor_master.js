frappe.ui.form.on('Vendor Master', {
    refresh: function(frm) {
        // Add custom buttons for document management
        if (!frm.is_new()) {
            // View Document History button
            frm.add_custom_button(__('View History'), function() {
                frappe.call({
                    method: 'vms.vendor_onboarding.vendor_document_management.get_vendor_document_history',
                    args: {
                        vendor_master_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            show_document_history(r.message);
                        }
                    }
                });
            }, __('Vendor Documents'));
            
            // Sync from Latest Onboarding button
            if (frm.doc.vendor_onb_records && frm.doc.vendor_onb_records.length > 0) {
                frm.add_custom_button(__('Sync from Latest'), function() {
                    // Find the latest onboarding
                    let latest = frm.doc.vendor_onb_records[frm.doc.vendor_onb_records.length - 1];
                    
                    frappe.confirm(
                        __('This will sync documents from onboarding {0}. Continue?', [latest.vendor_onboarding_no]),
                        function() {
                            frappe.call({
                                method: 'vms.vendor_onboarding.vendor_document_management.sync_vendor_documents_on_approval',
                                args: {
                                    vendor_onboarding_name: latest.vendor_onboarding_no
                                },
                                callback: function(r) {
                                    if (r.message && r.message.status === 'success') {
                                        frappe.msgprint(__('Documents synced successfully'));
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    );
                }, __('Vendor Documents'));
            }
        }
        frm.page.add_menu_item(__('Danger'), function() {
            frappe.confirm(
                '⚠️ This will unlink and delete this Vendor and all related docs. Are you 100% sure?',
                () => {
                    frappe.call({
                        method: "vms.vms_masters.doctype.vendor_master.vendor_master.danger_action",  // 🔗 update path to your app
                        args: { vendor_name: frm.doc.name },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(r.message.message);
                                frappe.set_route("List", "Vendor Master");
                            }
                        }
                    });
                
                },
                () => {
                    // ❌ Cancelled
                }
            );
        }, true);
        setTimeout(() => {
            $('.dropdown-menu li:contains("Danger") a').css({
                'color': 'red',
                'font-weight': 'bold'
            });
        }, 300);

        if (frm.doc.via_data_import === 1 && 
            frm.doc.user_create === 0 && 
            frm.doc.is_blocked === 0 && 
            frm.doc.office_email_primary) {
            
            
            frm.add_custom_button(__('Create User & Send Email'), function() {
                frappe.confirm(
                    __('This will create a user and send login credentials to {0}. Continue?', 
                       [frm.doc.office_email_primary]),
                    function() {
                        // Show processing message
                        frappe.show_alert({
                            message: __('Processing vendor...'),
                            indicator: 'blue'
                        }, 3);
                        
                        // Call backend function
                        frappe.call({
                            method: 'vms.utils.bulk_vendor_user_creation.process_single_vendor',
                            args: {
                                vendor_name: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __('Creating user and sending email...'),
                            callback: function(r) {
                                if (r.message) {
                                    if (r.message.status === 'success') {
                                        frappe.show_alert({
                                            message: r.message.message,
                                            indicator: 'green'
                                        }, 5);
                                        // Reload form to update user_create field
                                        frm.reload_doc();
                                    } else if (r.message.status === 'info') {
                                        frappe.show_alert({
                                            message: r.message.message,
                                            indicator: 'blue'
                                        }, 5);
                                        // Reload form
                                        frm.reload_doc();
                                    } else {
                                        frappe.msgprint({
                                            title: __('Error'),
                                            message: r.message.message,
                                            indicator: 'red'
                                        });
                                    }
                                }
                            }
                        });
                    }
                );
            }, __('Vendor CODE Actions'));
        }
        
        // Show indicator if user already created
        if (frm.doc.via_data_import === 1 && frm.doc.user_create === 1) {
            frm.dashboard.add_indicator(__('User Created'), 'green');
        }
        
        // Show indicator if pending user creation
        if (frm.doc.via_data_import === 1 && 
            frm.doc.user_create === 0 && 
            frm.doc.is_blocked === 0 && 
            frm.doc.office_email_primary) {
            frm.dashboard.add_indicator(__('Pending User Creation'), 'orange');
        }


    vendor_code_doc_sync(frm);
    }
});

function show_document_history(data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Vendor Document History'),
        size: 'large'
    });
    
    let html = `
        <div class="vendor-doc-history">
            <h5>Current Documents</h5>
            <table class="table table-bordered">
                <tr>
                    <td><strong>Bank Details:</strong></td>
                    <td>${data.current_documents.bank_details || 'Not Set'}</td>
                </tr>
                <tr>
                    <td><strong>Document Details:</strong></td>
                    <td>${data.current_documents.document_details || 'Not Set'}</td>
                </tr>
                <tr>
                    <td><strong>Manufacturing Details:</strong></td>
                    <td>${data.current_documents.manufacturing_details || 'Not Set'}</td>
                </tr>
            </table>
            
            <h5 class="mt-3">Onboarding History</h5>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Onboarding ID</th>
                        <th>Status</th>
                        <th>Current</th>
                        <th>Synced Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>`;
    
    data.onboarding_history.forEach(function(record) {
        html += `
            <tr>
                <td>${frappe.datetime.str_to_user(record.date)}</td>
                <td><a href="/app/vendor-onboarding/${record.onboarding_id}">${record.onboarding_id}</a></td>
                <td>${record.status}</td>
                <td>${record.is_current ? '<span class="badge badge-success">Yes</span>' : 'No'}</td>
                <td>${record.synced_date ? frappe.datetime.str_to_user(record.synced_date) : '-'}</td>
                <td>
                    <button class="btn btn-xs btn-primary" 
                        onclick="restore_from_onboarding('${record.onboarding_id}')">
                        Restore
                    </button>
                </td>
            </tr>`;
    });
    
    html += `
                </tbody>
            </table>
        </div>`;
    
    dialog.$body.html(html);
    dialog.show();
}

// Global function for restore button
window.restore_from_onboarding = function(onboarding_id) {
    frappe.confirm(
        __('Restore documents from this onboarding?'),
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.vendor_document_management.restore_from_onboarding',
                args: {
                    vendor_master_name: cur_frm.doc.name,
                    onboarding_name: onboarding_id
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.msgprint(__('Documents restored successfully'));
                        cur_frm.reload_doc();
                        $('.modal').modal('hide');
                    }
                }
            });
        }
    );
};





// File: vms/vms/doctype/vendor_master/vendor_master.js.....vms.vms_masters.doctype.company_vendor_code.corn_system_vendor_code.py
function vendor_code_doc_sync(frm) {
        // Add button to sync addresses for this vendor only
        if (!frm.is_new()) {
            frm.add_custom_button(__('Sync Vendor Code Addresses'), function() {
                frappe.confirm(
                    __('This will update address fields in all vendor codes for this vendor from their respective sources (Vendor Import Staging or Vendor Onboarding). Continue?'),
                    function() {
                        // Show progress indicator
                        frappe.show_alert({
                            message: __('Syncing addresses...'),
                            indicator: 'blue'
                        }, 3);
                        
                        frappe.call({
                            method: 'vms.vms_masters.doctype.company_vendor_code.corn_system_vendor_code.sync_single_vendor_addresses',
                            args: {
                                vendor_master_name: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message) {
                                    if (r.message.status === 'success') {
                                        frappe.show_alert({
                                            message: __(r.message.message),
                                            indicator: 'green'
                                        }, 5);
                                        
                                        // Show detailed message with companies updated
                                        if (r.message.companies && r.message.companies.length > 0) {
                                            frappe.msgprint({
                                                title: __('Address Sync Completed'),
                                                message: __('Updated addresses for the following companies:') + 
                                                         '<br><br><ul><li>' + 
                                                         r.message.companies.join('</li><li>') + 
                                                         '</li></ul>',
                                                indicator: 'green'
                                            });
                                        }
                                        
                                        // Reload the form to show updated data
                                        frm.reload_doc();
                                    } else if (r.message.status === 'info') {
                                        frappe.msgprint({
                                            title: __('Info'),
                                            message: __(r.message.message),
                                            indicator: 'blue'
                                        });
                                    } else {
                                        frappe.msgprint({
                                            title: __('Error'),
                                            message: __(r.message.message),
                                            indicator: 'red'
                                        });
                                    }
                                }
                            },
                            error: function(r) {
                                frappe.msgprint({
                                    title: __('Error'),
                                    message: __('Failed to sync addresses. Please check error logs.'),
                                    indicator: 'red'
                                });
                            }
                        });
                    }
                );
            }, __('Vendor Documents'));
            
            // Add button to trigger global sync for all vendors
            if (frappe.user.has_role(['System Manager', 'Administrator'])) {
                frm.add_custom_button(__('Sync All Vendors'), function() {
                    frappe.confirm(
                        __('This will sync addresses for ALL vendors in the system. This may take several minutes. Continue?'),
                        function() {
                            frappe.call({
                                method: 'vms.vms_masters.doctype.company_vendor_code.corn_system_vendor_code.trigger_address_sync',
                                callback: function(r) {
                                    if (r.message && r.message.status === 'success') {
                                        frappe.show_alert({
                                            message: __(r.message.message),
                                            indicator: 'green'
                                        }, 5);
                                        
                                        frappe.msgprint({
                                            title: __('Job Queued'),
                                            message: __('The address sync job has been queued and will run in the background. You will be notified once it completes. You can check the progress in the background jobs list.'),
                                            indicator: 'blue'
                                        });
                                    }
                                }
                            });
                        }
                    );
                }, __('Vendor Documents'));
            }
        }
    };