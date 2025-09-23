function process_selected_to_vendor_master(listview) {
    /**
     * MAIN FUNCTION: Process selected staging records to Vendor Master via background jobs
     * This is the primary workflow button in Vendor Import Staging list view
     */
    
    const selected = listview.get_checked_items();
    if (selected.length === 0) {
        frappe.msgprint(__('Please select staging records to process to Vendor Master'));
        return;
    }
    
    // First, check if selected records are ready for import
    check_import_readiness_and_proceed(selected, listview);
}

function check_import_readiness_and_proceed(selected_records, listview) {
    /**
     * Check if selected records are ready for import and show confirmation
     */
    
    const record_names = selected_records.map(record => record.name);
    
    // Show checking dialog
    const check_dialog = new frappe.ui.Dialog({
        title: __('Checking Import Readiness'),
        size: 'small',
        fields: [
            {
                fieldname: 'checking_html',
                fieldtype: 'HTML',
                options: `
                    <div class="text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="sr-only">Loading...</span>
                        </div>
                        <p class="mt-3">Checking ${selected_records.length} records for import readiness...</p>
                    </div>
                `
            }
        ]
    });
    
    check_dialog.show();
    
    // Call API to check readiness
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.check_import_readiness',
        args: {
            record_names: record_names
        },
        callback: function(r) {
            check_dialog.hide();
            
            if (r.message && r.message.status === 'success') {
                show_readiness_confirmation(r.message.results, listview);
            } else {
                frappe.msgprint({
                    title: __('Readiness Check Failed'),
                    message: r.message ? r.message.error : __('Unknown error occurred'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_readiness_confirmation(readiness_results, listview) {
    /**
     * Show confirmation dialog with readiness results
     */
    
    const { ready_records, not_ready_records, summary } = readiness_results;
    
    let confirmation_html = `
        <div class="import-readiness-summary">
            <div class="row mb-3">
                <div class="col-md-4 text-center">
                    <div class="stat-card bg-primary text-white">
                        <div class="stat-number">${summary.total}</div>
                        <div class="stat-label">Total Selected</div>
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <div class="stat-card bg-success text-white">
                        <div class="stat-number">${summary.ready}</div>
                        <div class="stat-label">Ready</div>
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <div class="stat-card bg-warning text-white">
                        <div class="stat-number">${summary.not_ready}</div>
                        <div class="stat-label">Not Ready</div>
                    </div>
                </div>
            </div>
    `;
    
    if (summary.ready > 0) {
        confirmation_html += `
            <div class="ready-records mb-3">
                <h6 class="text-success"><i class="fa fa-check-circle"></i> Ready Records (${summary.ready})</h6>
                <div class="ready-list" style="max-height: 150px; overflow-y: auto;">
        `;
        
        ready_records.slice(0, 10).forEach(record => {
            confirmation_html += `
                <div class="record-item">
                    <small><strong>${record.vendor_name}</strong> (${record.vendor_code}) - ${record.validation_status}</small>
                </div>
            `;
        });
        
        if (ready_records.length > 10) {
            confirmation_html += `<div class="text-muted"><small>... and ${ready_records.length - 10} more</small></div>`;
        }
        
        confirmation_html += `</div></div>`;
    }
    
    if (summary.not_ready > 0) {
        confirmation_html += `
            <div class="not-ready-records mb-3">
                <h6 class="text-warning"><i class="fa fa-exclamation-triangle"></i> Not Ready Records (${summary.not_ready})</h6>
                <div class="not-ready-list" style="max-height: 150px; overflow-y: auto;">
        `;
        
        not_ready_records.slice(0, 5).forEach(record => {
            confirmation_html += `
                <div class="record-item">
                    <small><strong>${record.vendor_name || record.name}</strong> - <span class="text-danger">${record.not_ready_reason}</span></small>
                </div>
            `;
        });
        
        if (not_ready_records.length > 5) {
            confirmation_html += `<div class="text-muted"><small>... and ${not_ready_records.length - 5} more</small></div>`;
        }
        
        confirmation_html += `</div></div>`;
    }
    
    confirmation_html += `
            <div class="alert alert-info">
                <strong>This will:</strong>
                <ul class="mb-0">
                    <li>Create/update Vendor Master records</li>
                    <li>Create Company Vendor Code documents with proper references</li>
                    <li>Populate multiple company data</li>
                    <li>Process via background jobs in batches</li>
                </ul>
            </div>
        </div>
        
        <style>
            .import-readiness-summary .stat-card {
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            .import-readiness-summary .stat-number {
                font-size: 1.5rem;
                font-weight: bold;
            }
            .import-readiness-summary .stat-label {
                font-size: 0.8rem;
            }
            .import-readiness-summary .record-item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
        </style>
    `;
    
    const confirmation_dialog = new frappe.ui.Dialog({
        title: __('Confirm Import to Vendor Master'),
        size: 'large',
        fields: [
            {
                fieldname: 'confirmation_html',
                fieldtype: 'HTML',
                options: confirmation_html
            }
        ],
        primary_action_label: summary.ready > 0 ? __('Process {0} Ready Records', [summary.ready]) : __('Close'),
        primary_action: function() {
            if (summary.ready > 0) {
                confirmation_dialog.hide();
                const ready_record_names = ready_records.map(r => r.name);
                initiate_batch_processing(ready_record_names, listview);
            } else {
                confirmation_dialog.hide();
            }
        }
    });
    
    // Add secondary action to process all anyway
    if (summary.not_ready > 0) {
        confirmation_dialog.set_secondary_action_label(__('Process All Anyway'));
        confirmation_dialog.set_secondary_action(function() {
            confirmation_dialog.hide();
            const all_record_names = [...ready_records, ...not_ready_records].map(r => r.name);
            initiate_batch_processing(all_record_names, listview);
        });
    }
    
    confirmation_dialog.show();
}

function initiate_batch_processing(record_names, listview) {
    /**
     * Initiate background job processing for selected records
     */
    
    // Show progress dialog
    const progress_dialog = new frappe.ui.Dialog({
        title: __('Initiating Vendor Master Creation'),
        size: 'large',
        fields: [
            {
                fieldname: 'progress_html',
                fieldtype: 'HTML',
                options: get_processing_progress_html(0, record_names.length, 'Initiating background jobs...')
            }
        ]
    });
    
    progress_dialog.show();
    
    // Call background job API
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_bulk_staging_to_vendor_master',
        args: {
            record_names: record_names,
            batch_size: 50  // Process in batches of 50
        },
        freeze: true,
        freeze_message: __('Initiating background processing...'),
        callback: function(r) {
            progress_dialog.hide();
            
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Background processing initiated for {0} records', [r.message.total_records]),
                    indicator: 'green'
                });
                
                // Show skipped records if any
                if (r.message.skipped_records && r.message.skipped_records.length > 0) {
                    show_skipped_records_info(r.message.skipped_records);
                }
                
                // Show monitoring dialog
                show_processing_monitor(r.message.total_records);
                
                // Refresh the list
                listview.refresh();
                
            } else {
                frappe.msgprint({
                    title: __('Processing Failed'),
                    message: r.message ? r.message.error : __('Unknown error occurred'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_skipped_records_info(skipped_records) {
    /**
     * Show information about skipped records
     */
    
    let skipped_html = `
        <div class="skipped-records-info">
            <h6>Skipped Records (${skipped_records.length})</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Record</th>
                            <th>Status</th>
                            <th>Validation</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    skipped_records.forEach(record => {
        skipped_html += `
            <tr>
                <td><small>${record.name}</small></td>
                <td><span class="badge badge-warning">${record.status}</span></td>
                <td><span class="badge badge-secondary">${record.validation}</span></td>
            </tr>
        `;
    });
    
    skipped_html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    const skipped_dialog = new frappe.ui.Dialog({
        title: __('Skipped Records Information'),
        size: 'large',
        fields: [
            {
                fieldname: 'skipped_html',
                fieldtype: 'HTML',
                options: skipped_html
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            skipped_dialog.hide();
        }
    });
    
    skipped_dialog.show();
}    
// vendor_import_staging.js
// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vendor Import Staging', {
    refresh(frm) {
        // Add custom buttons based on document status
        add_custom_buttons(frm);
        
        // Add realtime updates for processing status
        setup_realtime_updates(frm);
        
        // Color code based on status
        color_code_form(frm);
        
        // Auto refresh if processing
        if (frm.doc.import_status === 'Processing') {
            setup_auto_refresh(frm);
        }
    },
    
    import_source(frm) {
        // Load source document information when import source is selected
        if (frm.doc.import_source) {
            load_import_source_info(frm);
        }
    },
    
    import_status(frm) {
        // Update form appearance when status changes
        color_code_form(frm);
        
        // Show completion message
        if (frm.doc.import_status === 'Completed') {
            frappe.show_alert({
                message: __('Vendor import completed successfully'),
                indicator: 'green'
            });
        }
    }
});

function add_custom_buttons(frm) {
    // Clear existing buttons
    frm.page.clear_actions_menu();
    
    // Process to Vendor Master button
    if (frm.doc.import_status === 'Pending' && frm.doc.validation_status !== 'Invalid') {
        frm.add_custom_button(__('Process to Vendor Master'), function() {
            process_to_vendor_master(frm);
        }).addClass('btn-primary');
    }
    
    // Retry processing button
    if (frm.doc.import_status === 'Failed') {
        frm.add_custom_button(__('Retry Processing'), function() {
            retry_processing(frm);
        }).addClass('btn-warning');
    }
    
    // View related vendor button
    if (frm.doc.import_status === 'Completed') {
        frm.add_custom_button(__('View Vendor Master'), function() {
            view_related_vendor(frm);
        }).addClass('btn-secondary');
    }
    
    // Validation and quality buttons
    frm.add_custom_button(__('Re-validate Data'), function() {
        revalidate_staging_data(frm);
    }, __('Actions'));
    
    frm.add_custom_button(__('View Error Log'), function() {
        view_error_log(frm);
    }, __('Actions'));
    
    if (frappe.user.has_role(['System Manager', 'Vendor Manager'])) {
        frm.add_custom_button(__('Health Check'), function() {
            run_health_check(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('Batch Statistics'), function() {
            show_batch_statistics(frm);
        }, __('Actions'));
    }
}

function setup_realtime_updates(frm) {
    // Listen for realtime updates on processing status
    frappe.realtime.on('vendor_staging_update', (data) => {
        if (data.docname === frm.doc.name) {
            // Update progress
            if (data.progress !== undefined) {
                frm.set_value('processing_progress', data.progress);
            }
            
            // Update status
            if (data.status) {
                frm.set_value('import_status', data.status);
            }
            
            // Show notification
            if (data.message) {
                frappe.show_alert({
                    message: data.message,
                    indicator: data.indicator || 'blue'
                });
            }
            
            frm.refresh();
        }
    });
}

function color_code_form(frm) {
    // Remove existing status classes
    frm.page.main.removeClass('status-pending status-processing status-completed status-failed');
    
    // Add status-based class
    const status_class = `status-${frm.doc.import_status.toLowerCase().replace(' ', '-')}`;
    frm.page.main.addClass(status_class);
    
    // Update indicator
    const indicators = {
        'Pending': 'orange',
        'Queued': 'blue', 
        'Processing': 'yellow',
        'Completed': 'green',
        'Failed': 'red',
        'Partially Completed': 'purple'
    };
    
    frm.dashboard.add_indicator(
        __(frm.doc.import_status),
        indicators[frm.doc.import_status] || 'gray'
    );
}

function setup_auto_refresh(frm) {
    // Auto refresh every 30 seconds while processing
    if (frm.doc.import_status === 'Processing') {
        setTimeout(() => {
            if (frm.doc.import_status === 'Processing') {
                frm.reload_doc();
            }
        }, 30000);
    }
}

function load_import_source_info(frm) {
    if (!frm.doc.import_source) return;
    
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Existing Vendor Import',
            filters: { name: frm.doc.import_source },
            fieldname: ['vendor_data', 'success_fail_rate', 'field_mapping']
        },
        callback: function(r) {
            if (r.message) {
                // Show import source statistics
                const stats = JSON.parse(r.message.success_fail_rate || '{}');
                frm.set_value('total_records', stats.total_records || 0);
                
                frappe.show_alert({
                    message: __('Import source loaded: {0} total records', [stats.total_records || 0]),
                    indicator: 'blue'
                });
            }
        }
    });
}

function process_to_vendor_master(frm) {
    frappe.confirm(
        __('This will create/update a Vendor Master record. Continue?'),
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_single_staging_record',
                args: {
                    docname: frm.doc.name
                },
                freeze: true,
                freeze_message: __('Processing vendor record...'),
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Vendor master created/updated successfully'),
                            indicator: 'green'
                        });
                        
                        frm.reload_doc();
                        
                        // Show option to view created vendor
                        if (r.message.vendor_name) {
                            frappe.msgprint({
                                title: __('Success'),
                                message: __('Vendor Master "{0}" has been created/updated.', [r.message.vendor_name]),
                                primary_action: {
                                    label: __('View Vendor Master'),
                                    action: function() {
                                        frappe.set_route('Form', 'Vendor Master', r.message.vendor_name);
                                    }
                                }
                            });
                        }
                    } else {
                        frappe.msgprint({
                            title: __('Processing Failed'),
                            message: r.message ? r.message.error : __('Unknown error occurred'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function retry_processing(frm) {
    frappe.confirm(
        __('This will retry processing this failed record. Continue?'),
        function() {
            // Reset status and attempt processing again
            frm.set_value('import_status', 'Pending');
            frm.set_value('import_attempts', (frm.doc.import_attempts || 0));
            
            frm.save().then(() => {
                process_to_vendor_master(frm);
            });
        }
    );
}

function view_related_vendor(frm) {
    // Find and open related vendor master
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Vendor Master',
            filters: {
                // vendor_code: frm.doc.vendor_code,
                // company_code: frm.doc.c_code
                office_email_primary:frm.doc.primary_email
            },
            fields: ['name', 'vendor_name']
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                const vendor = r.message[0];
                frappe.set_route('Form', 'Vendor Master', vendor.name);
            } else {
                frappe.msgprint(__('Related vendor master not found'));
            }
        }
    });
}

function revalidate_staging_data(frm) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.revalidate_staging_record',
        args: {
            docname: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Re-validating data...'),
        callback: function(r) {
            if (r.message) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __('Data validation completed'),
                    indicator: 'blue'
                });
            }
        }
    });
}

function view_error_log(frm) {
    if (!frm.doc.error_log) {
        frappe.msgprint(__('No error log available'));
        return;
    }
    
    const dialog = new frappe.ui.Dialog({
        title: __('Error Log - {0}', [frm.doc.name]),
        size: 'large',
        fields: [
            {
                fieldname: 'error_details',
                fieldtype: 'Code',
                label: __('Error Details'),
                default: frm.doc.error_log,
                read_only: 1
            }
        ]
    });
    
    dialog.show();
}

function run_health_check(frm) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.health_check_staging_records',
        freeze: true,
        freeze_message: __('Running health check...'),
        callback: function(r) {
            if (r.message && !r.message.error) {
                show_health_check_results(r.message);
            } else {
                frappe.msgprint({
                    title: __('Health Check Failed'),
                    message: r.message ? r.message.error : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_health_check_results(results) {
    let html = `
        <div class="health-check-results">
            <h5>Health Check Results</h5>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-number">${results.orphaned_records}</div>
                        <div class="stat-label">Orphaned Records</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-number">${results.stuck_records}</div>
                        <div class="stat-label">Stuck Records</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-number">${results.validation_issues.length}</div>
                        <div class="stat-label">Validation Issues</div>
                    </div>
                </div>
            </div>
            
            <div class="recommendations mt-3">
                <h6>Recommendations:</h6>
                <ul>
                    ${results.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
        </div>
        
        <style>
            .health-check-results .stat-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
                border: 1px solid #dee2e6;
            }
            .health-check-results .stat-number {
                font-size: 2rem;
                font-weight: bold;
                color: #495057;
            }
            .health-check-results .stat-label {
                color: #6c757d;
                margin-top: 5px;
            }
        </style>
    `;
    
    const dialog = new frappe.ui.Dialog({
        title: __('Health Check Results'),
        size: 'large',
        fields: [
            {
                fieldname: 'results_html',
                fieldtype: 'HTML',
                options: html
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function show_batch_statistics(frm) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_staging_statistics',
        callback: function(r) {
            if (r.message && !r.message.error) {
                display_batch_statistics(r.message);
            } else {
                frappe.msgprint(__('Error loading statistics'));
            }
        }
    });
}

function display_batch_statistics(stats) {
    // Prepare HTML for statistics display
    let statusTableHTML = '<table class="table table-bordered"><thead><tr><th>Import Status</th><th>Validation Status</th><th>Count</th></tr></thead><tbody>';
    
    stats.status_stats.forEach(stat => {
        statusTableHTML += `<tr>
            <td>${stat.import_status || 'N/A'}</td>
            <td>${stat.validation_status || 'N/A'}</td>
            <td>${stat.count}</td>
        </tr>`;
    });
    statusTableHTML += '</tbody></table>';
    
    let batchTableHTML = '<table class="table table-bordered"><thead><tr><th>Batch ID</th><th>Total</th><th>Completed</th><th>Failed</th><th>Pending</th></tr></thead><tbody>';
    
    stats.batch_stats.forEach(batch => {
        batchTableHTML += `<tr>
            <td>${batch.batch_id}</td>
            <td>${batch.total_records}</td>
            <td><span class="badge badge-success">${batch.completed}</span></td>
            <td><span class="badge badge-danger">${batch.failed}</span></td>
            <td><span class="badge badge-warning">${batch.pending}</span></td>
        </tr>`;
    });
    batchTableHTML += '</tbody></table>';
    
    const dialog = new frappe.ui.Dialog({
        title: __('Staging Import Statistics'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'total_summary',
                fieldtype: 'HTML',
                options: `<div class="alert alert-info"><strong>Total Records:</strong> ${stats.total_records}</div>`
            },
            {
                fieldname: 'status_stats',
                fieldtype: 'HTML',
                label: __('Status Statistics'),
                options: statusTableHTML
            },
            {
                fieldname: 'batch_stats', 
                fieldtype: 'HTML',
                label: __('Batch Statistics'),
                options: batchTableHTML
            }
        ]
    });
    
    dialog.show();
}

// List View Customizations - CORRECTED BUTTON PLACEMENT
frappe.listview_settings['Vendor Import Staging'] = {
    add_fields: ["import_status", "validation_status", "processing_progress", "batch_id"],
    
    get_indicator: function(doc) {
        const status_colors = {
            "Pending": "orange",
            "Queued": "blue",
            "Processing": "yellow", 
            "Completed": "green",
            "Failed": "red",
            "Partially Completed": "purple"
        };
        
        return [__(doc.import_status), status_colors[doc.import_status] || "gray"];
    },
    
    onload: function(listview) {
        // MAIN PROCESSING BUTTON - This is the key button for background job processing
        listview.page.add_primary_action(__('Process to Vendor Master'), function() {
            process_selected_to_vendor_master(listview);
        });
        
        // Add bulk actions
        add_bulk_actions(listview);
        
        // Add filter shortcuts
        add_filter_shortcuts(listview);
        
        // Auto refresh list if there are processing records
        setup_list_auto_refresh(listview);
    },
    
    formatters: {
        processing_progress: function(value) {
            if (!value) return '';
            
            const progress_class = value >= 100 ? 'progress-bar-success' : 
                                 value >= 50 ? 'progress-bar-info' : 'progress-bar-warning';
            
            return `<div class="progress" style="margin: 0; height: 10px;">
                <div class="progress-bar ${progress_class}" style="width: ${value}%"></div>
            </div> <small>${value}%</small>`;
        },
        
        batch_id: function(value) {
            if (!value) return '';
            return `<span class="badge badge-info">${value}</span>`;
        }
    }
};

function process_selected_to_vendor_master(listview) {
    /**
     * MAIN FUNCTION: Process selected staging records to Vendor Master via background jobs
     * This is the primary workflow button in Vendor Import Staging list view
     */
    
    const selected = listview.get_checked_items();
    if (selected.length === 0) {
        frappe.msgprint(__('Please select staging records to process to Vendor Master'));
        return;
    }
    
    // Filter only valid records that can be processed
    const processable_records = selected.filter(record => 
        record.import_status === 'Pending' && 
        record.validation_status !== 'Invalid'
    );
    
    if (processable_records.length === 0) {
        frappe.msgprint(__('No processable records selected. Only Pending records with Valid status can be processed.'));
        return;
    }
    
    // Show confirmation dialog with details
    const invalid_count = selected.length - processable_records.length;
    let confirmation_message = __('Process {0} staging records to Vendor Master?', [processable_records.length]);
    
    if (invalid_count > 0) {
        confirmation_message += `<br><br><small class="text-muted">${invalid_count} invalid/non-pending records will be skipped.</small>`;
    }
    
    confirmation_message += '<br><br><strong>This will:</strong><ul><li>Create/update Vendor Master records</li><li>Create Company Vendor Code documents</li><li>Populate multiple company data with proper references</li><li>Process via background jobs in batches</li></ul>';
    
    frappe.confirm(
        confirmation_message,
        function() {
            initiate_batch_processing(processable_records, listview);
        }
    );
}

function initiate_batch_processing(records, listview) {
    /**
     * Initiate background job processing for selected records
     */
    
    const record_names = records.map(record => record.name);
    
    // Show progress dialog
    const progress_dialog = new frappe.ui.Dialog({
        title: __('Processing Staging Records'),
        size: 'large',
        fields: [
            {
                fieldname: 'progress_html',
                fieldtype: 'HTML',
                options: get_processing_progress_html(0, records.length, 'Initiating background jobs...')
            }
        ]
    });
    
    progress_dialog.show();
    
    // Call background job API
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_bulk_staging_to_vendor_master',
        args: {
            record_names: record_names,
            batch_size: 50  // Process in batches of 50
        },
        freeze: true,
        freeze_message: __('Initiating background processing...'),
        callback: function(r) {
            progress_dialog.hide();
            
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Background processing initiated for {0} records', [records.length]),
                    indicator: 'green'
                });
                
                // Show monitoring dialog
                show_processing_monitor(records.length);
                
                // Refresh the list
                listview.refresh();
                
            } else {
                frappe.msgprint({
                    title: __('Processing Failed'),
                    message: r.message ? r.message.error : __('Unknown error occurred'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_processing_monitor(total_records) {
    /**
     * Show real-time processing monitor dialog
     */
    
    const monitor_dialog = new frappe.ui.Dialog({
        title: __('Processing Monitor'),
        size: 'large',
        fields: [
            {
                fieldname: 'monitor_html',
                fieldtype: 'HTML',
                options: get_monitor_html(total_records, 0, 0, 0, 0)
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            monitor_dialog.hide();
        }
    });
    
    monitor_dialog.show();
    
    // Set up real-time updates
    let update_interval = setInterval(() => {
        update_processing_stats(monitor_dialog, total_records, () => {
            clearInterval(update_interval);
        });
    }, 5000); // Update every 5 seconds
    
    // Clear interval when dialog is closed
    monitor_dialog.$wrapper.on('hidden.bs.modal', function() {
        clearInterval(update_interval);
    });
}

function update_processing_stats(dialog, total_records, complete_callback) {
    /**
     * Update processing statistics in monitor dialog
     */
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_processing_stats',
        args: {
            total_expected: total_records
        },
        callback: function(r) {
            if (r.message) {
                const stats = r.message;
                dialog.set_values({
                    monitor_html: get_monitor_html(
                        total_records, 
                        stats.completed || 0, 
                        stats.failed || 0, 
                        stats.processing || 0,
                        stats.queued || 0
                    )
                });
                
                // Check if processing is complete
                if ((stats.completed + stats.failed) >= total_records) {
                    complete_callback();
                    
                    frappe.show_alert({
                        message: __('Processing complete: {0} successful, {1} failed', [stats.completed, stats.failed]),
                        indicator: stats.failed > 0 ? 'orange' : 'green'
                    });
                }
            }
        }
    });
}

function get_processing_progress_html(current, total, message) {
    const progress_percent = total > 0 ? (current / total) * 100 : 0;
    
    return `
        <div class="processing-progress">
            <div class="progress mb-3" style="height: 25px;">
                <div class="progress-bar progress-bar-info progress-bar-striped active" 
                     style="width: ${progress_percent}%">
                    ${progress_percent.toFixed(1)}%
                </div>
            </div>
            <div class="text-center">
                <h5>${current} of ${total} records</h5>
                <p class="text-muted">${message}</p>
            </div>
        </div>
    `;
}

function get_monitor_html(total, completed, failed, processing, queued) {
    const pending = total - completed - failed - processing - queued;
    const success_rate = total > 0 ? ((completed / total) * 100).toFixed(1) : 0;
    const completion_rate = total > 0 ? (((completed + failed) / total) * 100).toFixed(1) : 0;
    
    return `
        <div class="processing-monitor">
            <div class="row mb-4">
                <div class="col-md-2 text-center">
                    <div class="stat-card bg-primary text-white">
                        <div class="stat-number">${total}</div>
                        <div class="stat-label">Total Records</div>
                    </div>
                </div>
                <div class="col-md-2 text-center">
                    <div class="stat-card bg-success text-white">
                        <div class="stat-number">${completed}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                </div>
                <div class="col-md-2 text-center">
                    <div class="stat-card bg-danger text-white">
                        <div class="stat-number">${failed}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                </div>
                <div class="col-md-2 text-center">
                    <div class="stat-card bg-info text-white">
                        <div class="stat-number">${processing}</div>
                        <div class="stat-label">Processing</div>
                    </div>
                </div>
                <div class="col-md-2 text-center">
                    <div class="stat-card bg-secondary text-white">
                        <div class="stat-number">${queued}</div>
                        <div class="stat-label">Queued</div>
                    </div>
                </div>
                <div class="col-md-2 text-center">
                    <div class="stat-card bg-warning text-white">
                        <div class="stat-number">${pending}</div>
                        <div class="stat-label">Pending</div>
                    </div>
                </div>
            </div>
            
            <div class="progress mb-3" style="height: 20px;">
                <div class="progress-bar bg-success" style="width: ${(completed/total)*100}%" title="Completed"></div>
                <div class="progress-bar bg-danger" style="width: ${(failed/total)*100}%" title="Failed"></div>
                <div class="progress-bar bg-info" style="width: ${(processing/total)*100}%" title="Processing"></div>
                <div class="progress-bar bg-secondary" style="width: ${(queued/total)*100}%" title="Queued"></div>
            </div>
            
            <div class="text-center">
                <h5>Success Rate: ${success_rate}% | Completion: ${completion_rate}%</h5>
                <p class="text-muted">
                    ${processing + queued > 0 ? 
                        'Background jobs are processing records to Vendor Master...' : 
                        'Processing complete!'
                    }
                </p>
            </div>
            
            ${processing + queued > 0 ? `
                <div class="text-center mt-3">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="sr-only">Processing...</span>
                    </div>
                    <small class="text-muted ml-2">Auto-refreshing every 5 seconds</small>
                </div>
            ` : ''}
        </div>
        
        <style>
            .processing-monitor .stat-card {
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            .processing-monitor .stat-number {
                font-size: 1.5rem;
                font-weight: bold;
            }
            .processing-monitor .stat-label {
                font-size: 0.8rem;
            }
        </style>
    `;
}

function add_bulk_actions(listview) {
    // Retry failed records
    listview.page.add_action_item(__('Retry Failed Records'), function() {
        const selected = listview.get_checked_items();
        if (selected.length === 0) {
            frappe.msgprint(__('Please select failed records to retry'));
            return;
        }
        
        const failed_records = selected.filter(record => record.import_status === 'Failed');
        if (failed_records.length === 0) {
            frappe.msgprint(__('No failed records selected'));
            return;
        }
        
        retry_failed_staging_records(failed_records, listview);
    });
    
    // Bulk validation
    listview.page.add_action_item(__('Re-validate Selected'), function() {
        const selected = listview.get_checked_items();
        if (selected.length === 0) {
            frappe.msgprint(__('Please select records to validate'));
            return;
        }
        
        revalidate_bulk_staging_records(selected);
    });
    
    // Health check
    listview.page.add_action_item(__('System Health Check'), function() {
        run_health_check();
    });
}

function retry_failed_staging_records(failed_records, listview) {
    const record_names = failed_records.map(record => record.name);
    
    frappe.confirm(
        __('Retry processing for {0} failed records?<br><br>This will reset their status and attempt processing again.', [failed_records.length]),
        function() {
            // Reset status to Pending
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'Vendor Import Staging',
                    name: record_names,
                    fieldname: {
                        'import_status': 'Pending',
                        'error_log': ''
                    }
                },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.show_alert({
                            message: __('Reset {0} records for retry', [record_names.length]),
                            indicator: 'blue'
                        });
                        
                        listview.refresh();
                        
                        // Automatically start processing the reset records
                        setTimeout(() => {
                            initiate_batch_processing(record_names, listview);
                        }, 1000);
                    }
                }
            });
        }
    );
}

function revalidate_bulk_staging_records(selected_records) {
    const record_names = selected_records.map(record => record.name);
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.revalidate_bulk_staging_records',
        args: {
            record_names: record_names
        },
        freeze: true,
        freeze_message: __('Re-validating {0} records...', [record_names.length]),
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Bulk validation completed for {0} records', [record_names.length]),
                    indicator: 'blue'
                });
                
                cur_list.refresh();
            }
        }
    });
}

function run_health_check() {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.health_check_staging_records',
        freeze: true,
        freeze_message: __('Running health check...'),
        callback: function(r) {
            if (r.message && !r.message.error) {
                show_health_check_results(r.message);
            } else {
                frappe.msgprint({
                    title: __('Health Check Failed'),
                    message: r.message ? r.message.error : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_health_check_results(results) {
    let html = `
        <div class="health-check-results">
            <h5>System Health Check Results</h5>
            
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card ${results.orphaned_records > 0 ? 'bg-warning' : 'bg-success'} text-white text-center">
                        <div class="stat-number">${results.orphaned_records}</div>
                        <div class="stat-label">Orphaned Records</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card ${results.stuck_records > 0 ? 'bg-danger' : 'bg-success'} text-white text-center">
                        <div class="stat-number">${results.stuck_records}</div>
                        <div class="stat-label">Stuck Records</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card ${results.validation_issues.length > 0 ? 'bg-warning' : 'bg-success'} text-white text-center">
                        <div class="stat-number">${results.validation_issues.length}</div>
                        <div class="stat-label">Validation Issues</div>
                    </div>
                </div>
            </div>
            
            <div class="recommendations">
                <h6><i class="fa fa-lightbulb-o"></i> Recommendations:</h6>
                <ul class="list-group">
                    ${results.recommendations.map(rec => `<li class="list-group-item">${rec}</li>`).join('')}
                </ul>
            </div>
        </div>
        
        <style>
            .health-check-results .stat-card {
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            .health-check-results .stat-number {
                font-size: 2rem;
                font-weight: bold;
            }
            .health-check-results .stat-label {
                font-size: 0.9rem;
                margin-top: 5px;
            }
            .health-check-results .list-group-item {
                border: none;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }
        </style>
    `;
    
    const dialog = new frappe.ui.Dialog({
        title: __('System Health Check Results'),
        size: 'large',
        fields: [
            {
                fieldname: 'results_html',
                fieldtype: 'HTML',
                options: html
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function add_filter_shortcuts(listview) {
    // Quick filter buttons
    listview.page.add_inner_button(__('Pending Records'), function() {
        listview.filter_area.add([[listview.doctype, 'import_status', '=', 'Pending']]);
    });
    
    listview.page.add_inner_button(__('Failed Records'), function() {
        listview.filter_area.add([[listview.doctype, 'import_status', '=', 'Failed']]);
    });
    
    listview.page.add_inner_button(__('Processing Records'), function() {
        listview.filter_area.add([[listview.doctype, 'import_status', '=', 'Processing']]);
    });
    
    listview.page.add_inner_button(__('Invalid Records'), function() {
        listview.filter_area.add([[listview.doctype, 'validation_status', '=', 'Invalid']]);
    });
    
    listview.page.add_inner_button(__('Clear Filters'), function() {
        listview.filter_area.clear();
    });
}

function setup_list_auto_refresh(listview) {
    // Check if there are processing records
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Vendor Import Staging',
            filters: {'import_status': ['in', ['Processing', 'Queued']]}
        },
        callback: function(r) {
            if (r.message > 0) {
                // Auto refresh every 30 seconds if there are processing records
                setTimeout(() => {
                    if (cur_list && cur_list.doctype === 'Vendor Import Staging') {
                        cur_list.refresh();
                        setup_list_auto_refresh(listview);
                    }
                }, 30000);
                
                // Show processing indicator in list
                if (!listview.$page.find('.processing-indicator').length) {
                    listview.$page.find('.page-title').after(`
                        <div class="processing-indicator">
                            <span class="indicator blue">
                                <i class="fa fa-refresh fa-spin"></i>
                                Processing ${r.message} records
                            </span>
                        </div>
                    `);
                }
            } else {
                // Remove processing indicator
                listview.$page.find('.processing-indicator').remove();
            }
        }
    });
}

// Custom CSS for staging form
frappe.ui.form.on('Vendor Import Staging', {
    onload: function(frm) {
        // Add custom CSS
        if (!$('head').find('#vendor-staging-css').length) {
            $('<style id="vendor-staging-css">')
                .text(`
                    .status-pending .form-header { border-left: 4px solid #ff9800; }
                    .status-queued .form-header { border-left: 4px solid #2196f3; }
                    .status-processing .form-header { border-left: 4px solid #03a9f4; animation: pulse 2s infinite; }
                    .status-completed .form-header { border-left: 4px solid #4caf50; }
                    .status-failed .form-header { border-left: 4px solid #f44336; }
                    
                    @keyframes pulse {
                        0% { border-left-color: #03a9f4; }
                        50% { border-left-color: #81d4fa; }
                        100% { border-left-color: #03a9f4; }
                    }
                    
                    .vendor-staging-progress {
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 6px;
                        margin: 10px 0;
                    }
                    
                    .validation-status-valid { color: #28a745; font-weight: bold; }
                    .validation-status-warning { color: #ffc107; font-weight: bold; }
                    .validation-status-invalid { color: #dc3545; font-weight: bold; }
                    
                    .processing-indicator {
                        position: fixed;
                        top: 60px;
                        right: 20px;
                        z-index: 1000;
                        background: white;
                        padding: 10px 15px;
                        border-radius: 5px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        border: 1px solid #dee2e6;
                    }
                `)
                .appendTo('head');
        }
    }
});

function add_bulk_actions(listview) {
    // Bulk process to vendor master
    listview.page.add_action_item(__('Process Selected to Vendor Master'), function() {
        const selected = listview.get_checked_items();
        if (selected.length === 0) {
            frappe.msgprint(__('Please select records to process'));
            return;
        }
        
        frappe.confirm(
            __('Process {0} selected records to Vendor Master?', [selected.length]),
            function() {
                process_bulk_staging_records(selected);
            }
        );
    });
    
    // Bulk retry failed records
    listview.page.add_action_item(__('Retry Failed Records'), function() {
        const selected = listview.get_checked_items();
        if (selected.length === 0) {
            frappe.msgprint(__('Please select failed records to retry'));
            return;
        }
        
        retry_bulk_staging_records(selected);
    });
    
    // Bulk validation
    listview.page.add_action_item(__('Re-validate Selected'), function() {
        const selected = listview.get_checked_items();
        if (selected.length === 0) {
            frappe.msgprint(__('Please select records to validate'));
            return;
        }
        
        revalidate_bulk_staging_records(selected);
    });
}

function add_filter_shortcuts(listview) {
    // Quick filter buttons
    listview.page.add_inner_button(__('Pending Records'), function() {
        listview.filter_area.add([[listview.doctype, 'import_status', '=', 'Pending']]);
    });
    
    listview.page.add_inner_button(__('Failed Records'), function() {
        listview.filter_area.add([[listview.doctype, 'import_status', '=', 'Failed']]);
    });
    
    listview.page.add_inner_button(__('Processing Records'), function() {
        listview.filter_area.add([[listview.doctype, 'import_status', '=', 'Processing']]);
    });
    
    listview.page.add_inner_button(__('Invalid Records'), function() {
        listview.filter_area.add([[listview.doctype, 'validation_status', '=', 'Invalid']]);
    });
}

function setup_list_auto_refresh(listview) {
    // Check if there are processing records
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Vendor Import Staging',
            filters: {'import_status': 'Processing'}
        },
        callback: function(r) {
            if (r.message > 0) {
                // Auto refresh every 60 seconds if there are processing records
                setTimeout(() => {
                    listview.refresh();
                    setup_list_auto_refresh(listview);
                }, 60000);
            }
        }
    });
}

function process_bulk_staging_records(selected_records) {
    const record_names = selected_records.map(record => record.name);
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_bulk_staging_records',
        args: {
            record_names: record_names
        },
        freeze: true,
        freeze_message: __('Processing {0} records...', [record_names.length]),
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Bulk processing initiated for {0} records', [record_names.length]),
                    indicator: 'blue'
                });
                
                // Refresh the list view
                cur_list.refresh();
            }
        }
    });
}

function retry_bulk_staging_records(selected_records) {
    const failed_records = selected_records.filter(record => record.import_status === 'Failed');
    
    if (failed_records.length === 0) {
        frappe.msgprint(__('No failed records selected'));
        return;
    }
    
    const record_names = failed_records.map(record => record.name);
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.retry_bulk_staging_records', 
        args: {
            record_names: record_names
        },
        freeze: true,
        freeze_message: __('Retrying {0} failed records...', [record_names.length]),
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Retry initiated for {0} records', [record_names.length]),
                    indicator: 'orange'
                });
                
                cur_list.refresh();
            }
        }
    });
}

function revalidate_bulk_staging_records(selected_records) {
    const record_names = selected_records.map(record => record.name);
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.revalidate_bulk_staging_records',
        args: {
            record_names: record_names
        },
        freeze: true,
        freeze_message: __('Re-validating {0} records...', [record_names.length]),
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Bulk validation completed for {0} records', [record_names.length]),
                    indicator: 'blue'
                });
                
                cur_list.refresh();
            }
        }
    });
}

// Custom CSS for staging form
frappe.ui.form.on('Vendor Import Staging', {
    onload: function(frm) {
        // Add custom CSS
        if (!$('head').find('#vendor-staging-css').length) {
            $('<style id="vendor-staging-css">')
                .text(`
                    .status-pending .form-header { border-left: 4px solid #ff9800; }
                    .status-processing .form-header { border-left: 4px solid #2196f3; }
                    .status-completed .form-header { border-left: 4px solid #4caf50; }
                    .status-failed .form-header { border-left: 4px solid #f44336; }
                    
                    .vendor-staging-progress {
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 6px;
                        margin: 10px 0;
                    }
                    
                    .validation-status-valid { color: #28a745; }
                    .validation-status-warning { color: #ffc107; }
                    .validation-status-invalid { color: #dc3545; }
                `)
                .appendTo('head');
        }
    }
});