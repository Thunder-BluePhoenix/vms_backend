// vendor_import_staging_list.js
frappe.listview_settings['Vendor Import Staging'] = {
    add_fields: ["import_status", "processing_progress", "vendor_name", "validation_status"],
    
    get_indicator: function(doc) {
        if (doc.import_status === "Completed") {
            return [__("Completed"), "green", "import_status,=,Completed"];
        } else if (doc.import_status === "Processing") {
            return [__("Processing"), "orange", "import_status,=,Processing"];
        } else if (doc.import_status === "Failed") {
            return [__("Failed"), "red", "import_status,=,Failed"];
        } else if (doc.import_status === "Queued") {
            return [__("Queued"), "blue", "import_status,=,Queued"];
        } else {
            return [__("Pending"), "grey", "import_status,=,Pending"];
        }
    },

    onload: function(listview) {
        // 🔹 Button: Process Selected Records
        listview.page.add_inner_button(__('Create Vendor Masters'), function() {
            const selected_docs = listview.get_checked_items();

            if (!selected_docs.length) {
                frappe.msgprint(__('Please select records to process'));
                return;
            }

            // Filter processable records
            const processable_records = selected_docs.filter(doc => 
                doc.import_status === "Pending" && 
                doc.validation_status !== "Invalid"
            );

            if (!processable_records.length) {
                frappe.msgprint(__('No valid records selected. Only Pending records with valid status can be processed.'));
                return;
            }

            const invalid_count = selected_docs.length - processable_records.length;
            let confirmation_message = __('Process {0} staging records to Vendor Master?', [processable_records.length]);
            
            if (invalid_count > 0) {
                confirmation_message += `<br><br><small class="text-muted">${invalid_count} invalid/non-pending records will be skipped.</small>`;
            }
            
            confirmation_message += '<br><br><strong>This will:</strong><ul><li>Create/update Vendor Master records</li><li>Create Company Vendor Code documents</li><li>Create Company Details records</li><li>Set up Multiple Company Data</li><li>Create Payment Details</li><li>Process via background jobs in batches of 50</li></ul>';
            
            frappe.confirm(
                confirmation_message,
                function() {
                    initiate_bulk_vendor_creation(processable_records);
                }
            );
        }, __('Vendor Processing'));

        // 🔹 Button: Process All Pending
        listview.page.add_inner_button(__('Process All Pending'), function() {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Vendor Import Staging',
                    filters: {
                        import_status: 'Pending',
                        validation_status: ['!=', 'Invalid']
                    },
                    fields: ['name', 'vendor_name', 'import_status', 'validation_status'],
                    limit_page_length: 0
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        let message = `Found ${r.message.length} pending records ready for processing.<br><br>`;
                        message += '<strong>This will process ALL pending valid records in background jobs.</strong>';
                        
                        frappe.confirm(message, function() {
                            initiate_bulk_vendor_creation(r.message);
                        });
                    } else {
                        frappe.msgprint(__('No pending records found to process'));
                    }
                }
            });
        }, __('Vendor Processing'));

        // 🔹 Button: Monitor Processing
        listview.page.add_inner_button(__('Monitor Processing'), function() {
            show_processing_monitor();
        }, __('Vendor Processing'));
    }
};


function initiate_bulk_vendor_creation(records) {
    /**
     * Initiate bulk vendor master creation with background jobs
     */
    const record_names = records.map(record => record.name);
    
    // Show progress dialog
    const progress_dialog = new frappe.ui.Dialog({
        title: __('Creating Vendor Masters'),
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
            batch_size: 50
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
                
                // Refresh current page
                setTimeout(() => {
                    location.reload();
                }, 2000);
                
            } else {
                const error_message = r.message ? r.message.error : 'Unknown error occurred';
                frappe.msgprint({
                    title: __('Processing Failed'),
                    message: error_message,
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            progress_dialog.hide();
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to initiate processing: {0}', [err.message || 'Unknown error']),
                indicator: 'red'
            });
        }
    });
}

function get_processing_progress_html(processed, total, status_message) {
    /**
     * Generate HTML for processing progress display
     */
    const percentage = total > 0 ? Math.round((processed / total) * 100) : 0;
    
    return `
        <div class="processing-progress-container">
            <div class="progress-stats">
                <div class="row">
                    <div class="col-md-4">
                        <div class="stat-box bg-primary">
                            <div class="stat-number">${total}</div>
                            <div class="stat-label">Total Records</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-box bg-success">
                            <div class="stat-number">${processed}</div>
                            <div class="stat-label">Processed</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-box bg-info">
                            <div class="stat-number">${total - processed}</div>
                            <div class="stat-label">Remaining</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="progress-bar-container">
                <div class="progress" style="height: 25px; margin: 20px 0;">
                    <div class="progress-bar bg-success progress-bar-striped progress-bar-animated" 
                         role="progressbar" 
                         style="width: ${percentage}%" 
                         aria-valuenow="${percentage}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        ${percentage}%
                    </div>
                </div>
            </div>
            
            <div class="status-message">
                <p class="text-center text-muted">${status_message}</p>
            </div>
        </div>
        
        <style>
            .processing-progress-container {
                padding: 20px;
            }
            
            .stat-box {
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                color: white;
                margin-bottom: 10px;
            }
            
            .stat-number {
                font-size: 2rem;
                font-weight: bold;
            }
            
            .stat-label {
                font-size: 0.9rem;
                opacity: 0.9;
            }
            
            .progress-bar-container {
                margin: 20px 0;
            }
            
            .status-message {
                margin-top: 10px;
            }
        </style>
    `;
}

function show_processing_monitor(total_records = null) {
    /**
     * Show processing monitor dialog
     */
    const monitor_dialog = new frappe.ui.Dialog({
        title: __('Processing Monitor'),
        size: 'large',
        fields: [
            {
                fieldname: 'monitor_html',
                fieldtype: 'HTML',
                options: get_monitor_html()
            }
        ]
    });
    
    monitor_dialog.show();
    
    // Auto-refresh monitor every 5 seconds
    const refresh_interval = setInterval(() => {
        if (monitor_dialog.is_visible) {
            refresh_monitor(monitor_dialog);
        } else {
            clearInterval(refresh_interval);
        }
    }, 5000);
}

function get_monitor_html() {
    /**
     * Generate monitoring HTML
     */
    return `
        <div id="processing-monitor">
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <p class="mt-3">Loading processing status...</p>
            </div>
        </div>
        
        <style>
            #processing-monitor {
                min-height: 300px;
                padding: 20px;
            }
            
            .status-card {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            .status-success { border-left: 4px solid #28a745; }
            .status-processing { border-left: 4px solid #ffc107; }
            .status-failed { border-left: 4px solid #dc3545; }
            .status-queued { border-left: 4px solid #007bff; }
        </style>
    `;
}

function refresh_monitor(dialog) {
    /**
     * Refresh processing monitor data
     */
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_processing_status',
        callback: function(r) {
            if (r.message) {
                const monitor_html = generate_monitor_status_html(r.message);
                dialog.fields_dict.monitor_html.$wrapper.html(monitor_html);
            }
        }
    });
}

function generate_monitor_status_html(status_data) {
    /**
     * Generate HTML for monitor status display
     */
    return `
        <div class="processing-status">
            <h5>Background Job Status</h5>
            
            <div class="row">
                <div class="col-md-3">
                    <div class="status-card status-success">
                        <h6>Completed</h6>
                        <h3>${status_data.completed || 0}</h3>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="status-card status-processing">
                        <h6>Processing</h6>
                        <h3>${status_data.processing || 0}</h3>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="status-card status-queued">
                        <h6>Queued</h6>
                        <h3>${status_data.queued || 0}</h3>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="status-card status-failed">
                        <h6>Failed</h6>
                        <h3>${status_data.failed || 0}</h3>
                    </div>
                </div>
            </div>
            
            ${status_data.recent_jobs ? generate_recent_jobs_html(status_data.recent_jobs) : ''}
        </div>
    `;
}

function generate_recent_jobs_html(recent_jobs) {
    /**
     * Generate HTML for recent jobs display
     */
    let jobs_html = '<div class="recent-jobs"><h6>Recent Background Jobs</h6><div class="table-responsive"><table class="table table-sm">';
    jobs_html += '<thead><tr><th>Job Name</th><th>Status</th><th>Progress</th><th>Started</th></tr></thead><tbody>';
    
    recent_jobs.forEach(job => {
        jobs_html += `
            <tr>
                <td>${job.job_name}</td>
                <td><span class="badge badge-${get_job_status_color(job.status)}">${job.status}</span></td>
                <td>${job.progress || 'N/A'}</td>
                <td>${job.started_at || 'N/A'}</td>
            </tr>
        `;
    });
    
    jobs_html += '</tbody></table></div></div>';
    return jobs_html;
}

function get_job_status_color(status) {
    const status_colors = {
        'completed': 'success',
        'processing': 'warning',
        'queued': 'info',
        'failed': 'danger',
        'cancelled': 'secondary'
    };
    return status_colors[status.toLowerCase()] || 'secondary';
}