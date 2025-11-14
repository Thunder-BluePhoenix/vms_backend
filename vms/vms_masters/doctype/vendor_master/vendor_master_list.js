frappe.listview_settings['Vendor Master'] = {
    onload(listview) {
        listview.page.add_inner_button(__('Process Imported Vendors'), function() {
            frappe.confirm(
                'This will process all imported vendors (create users & send emails) in background. Continue?',
                function() {
                    // On yes
                    frappe.call({
                        method: 'vms.utils.bulk_vendor_user_creation.start_bulk_vendor_processing',
                        callback: function(r) {
                            if (r.message.status === 'success') {
                                frappe.show_alert({
                                    message: r.message.message,
                                    indicator: 'green'
                                }, 5);
                            } else if (r.message.status === 'info') {
                                frappe.show_alert({
                                    message: r.message.message,
                                    indicator: 'blue'
                                }, 3);
                            } else {
                                frappe.msgprint(r.message.message);
                            }
                        }
                    });
                }
            );
        }, __('Vendor CODE Actions'));
        
    
        frappe.call({
            method: 'frappe.client.get_count',
            args: {
                doctype: 'Vendor Master',
                filters: {
                    via_data_import: 1,
                    user_create: 0,
                    is_blocked: 0
                }
            },
            callback: function(r) {
                if (r.message > 0) {
                    listview.page.set_indicator(__('Pending Users: ' + r.message), 'orange');
                }
            }
        });
        listview.page.add_menu_item(__('Danger'), function() {
            let selected = listview.get_checked_items();

            if (!selected.length) {
                frappe.msgprint(__('Please select at least one Vendor Master.'));
                return;
            }

            // Build a list of vendors
            let vendor_names = selected.map(row => row.name).join(", ");

            // Friendly dialog box
            frappe.prompt(
                [
                    {
                        fieldname: 'confirm_text',
                        label: 'Type DELETE to confirm',
                        fieldtype: 'Data',
                        reqd: 1
                    }
                ],
                (values) => {
                    if (values.confirm_text !== "DELETE") {
                        frappe.msgprint(__('Action cancelled. You must type DELETE to confirm.'));
                        return;
                    }

                    // Call Danger API for each vendor
                    frappe.call({
                        method: "vms.vms_masters.doctype.vendor_master.vendor_master.danger_action_bulk", // update path
                        args: { vendor_name: vendor_names },
                        freeze: true,
                        freeze_message: __('Deleting selected vendors...'),
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.show_alert({
                                    message: __('Vendors deleted successfully'),
                                    indicator: 'red'
                                });
                                listview.refresh();
                            }
                        }
                    });
                },
                __('⚠️ Confirm Danger Delete'),
                __('Delete')
            );
        });


          // Add bulk action for syncing multiple vendors at once   
        listview.page.add_inner_button(__('Sync Selected Vendors Addresses'), function() {
            let selected = listview.get_checked_items();
            
            if (selected.length === 0) {
                frappe.msgprint(__('Please select at least one vendor'));
                return;
            }
            
            frappe.confirm(
                __('Sync addresses for {0} selected vendor(s)?', [selected.length]),
                function() {
                    frappe.show_alert({
                        message: __('Syncing addresses for {0} vendor(s)...', [selected.length]),
                        indicator: 'blue'
                    }, 3);
                    
                    sync_multiple_vendors(selected, listview);
                }
            );
        },__('Vendor CODE Actions'));
        
        // Add button for syncing all vendors (Admin only)
        if (frappe.user.has_role(['System Manager', 'Administrator'])) {
            listview.page.add_inner_button(__('Sync All Vendors'), function() {
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
                                        message: __('The address sync job has been queued and will run in the background.'),
                                        indicator: 'blue'
                                    });
                                }
                            }
                        });
                    }
                );
            }, __('Vendor CODE Actions'));
        }
    },
    
    // Add indicator for vendors with multiple companies
    // get_indicator: function(doc) {
    //     if (doc.multiple_company_data && doc.multiple_company_data.length > 0) {
    //         return [__("Multi-Company"), "blue", "multiple_company_data,>,0"];
    //     }
    // }
};





// File: vms/vms/doctype/vendor_master/vendor_master_list.js
// function sync_vcode_addresses(listview) {


function sync_multiple_vendors(selected_vendors, listview) {
    let completed = 0;
    let total = selected_vendors.length;
    let results = {
        success: [],
        failed: [],
        no_changes: []
    };
    
    // Create progress dialog
    let progress = frappe.show_progress(
        __('Syncing Addresses'), 
        0, 
        total,
        __('Processing vendors...')
    );
    
    // Process each vendor sequentially
    process_vendor(0);
    
    function process_vendor(index) {
        if (index >= total) {
            // All done - show summary
            progress.hide();
            show_sync_summary(results, total);
            listview.refresh();
            return;
        }
        
        let vendor = selected_vendors[index];
        
        frappe.call({
            method: 'vms.vms_masters.doctype.company_vendor_code.corn_system_vendor_code.sync_single_vendor_addresses',
            args: {
                vendor_master_name: vendor.name
            },
            callback: function(r) {
                completed++;
                progress.percent = (completed / total) * 100;
                progress.set_message(__('Processing {0} of {1}', [completed, total]));
                
                if (r.message) {
                    if (r.message.status === 'success') {
                        results.success.push({
                            name: vendor.name,
                            companies: r.message.companies || []
                        });
                    } else if (r.message.status === 'info') {
                        results.no_changes.push(vendor.name);
                    } else {
                        results.failed.push({
                            name: vendor.name,
                            error: r.message.message
                        });
                    }
                }
                
                // Process next vendor
                process_vendor(index + 1);
            },
            error: function(r) {
                completed++;
                results.failed.push({
                    name: vendor.name,
                    error: 'Request failed'
                });
                progress.percent = (completed / total) * 100;
                
                // Process next vendor even on error
                process_vendor(index + 1);
            }
        });
    }
}

function show_sync_summary(results, total) {
    let message = '<div style="font-family: monospace;">';
    
    message += '<h4>Address Sync Summary</h4>';
    message += '<table class="table table-bordered" style="margin-top: 10px;">';
    message += '<tr><th>Status</th><th>Count</th></tr>';
    message += `<tr><td><span class="indicator-pill green">Success</span></td><td>${results.success.length}</td></tr>`;
    message += `<tr><td><span class="indicator-pill blue">No Changes</span></td><td>${results.no_changes.length}</td></tr>`;
    message += `<tr><td><span class="indicator-pill red">Failed</span></td><td>${results.failed.length}</td></tr>`;
    message += `<tr><th>Total</th><th>${total}</th></tr>`;
    message += '</table>';
    
    // Show successful vendors
    if (results.success.length > 0) {
        message += '<h5 style="margin-top: 20px;">Successfully Updated:</h5>';
        message += '<ul>';
        results.success.forEach(function(item) {
            message += `<li><strong>${item.name}</strong>`;
            if (item.companies.length > 0) {
                message += ` (${item.companies.join(', ')})`;
            }
            message += '</li>';
        });
        message += '</ul>';
    }
    
    // Show failed vendors
    if (results.failed.length > 0) {
        message += '<h5 style="margin-top: 20px; color: red;">Failed:</h5>';
        message += '<ul>';
        results.failed.forEach(function(item) {
            message += `<li><strong>${item.name}</strong>: ${item.error}</li>`;
        });
        message += '</ul>';
    }
    
    message += '</div>';
    
    frappe.msgprint({
        title: __('Bulk Address Sync Completed'),
        message: message,
        indicator: results.failed.length > 0 ? 'orange' : 'green',
        wide: true
    });
}