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

    // Custom actions menu
    onload: function(listview) {
        // 🔹 Button: Create Vendor Masters (Process Selected Records)
        listview.page.add_inner_button(__('Create Vendor Masters'), function() {
            const selected_docs = listview.get_checked_items();
            
            if (!selected_docs.length) {
                frappe.msgprint(__('Please select records to process'));
                return;
            }

            // Filter processable records
            const processable_records = selected_docs.filter(doc => 
                doc.import_status === "Pending" && 
                doc.validation_status === "Valid"
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

        // 🔹 Button: Process All Pending Records
        listview.page.add_inner_button(__('Process All Pending'), function() {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Vendor Import Staging',
                    filters: {
                        import_status: 'Pending',
                        validation_status: 'Valid'
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

        // 🔹 Button: Retry Failed Records
        listview.page.add_inner_button(__('Retry Failed Records'), function() {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Vendor Import Staging',
                    filters: {
                        import_status: 'Failed'
                    },
                    fields: ['name', 'vendor_name', 'error_log'],
                    limit_page_length: 0
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        show_retry_failed_dialog(r.message);
                    } else {
                        frappe.msgprint({
                            title: __('No Failed Records'),
                            message: __('No failed records found to retry.'),
                            indicator: 'blue'
                        });
                    }
                }
            });
        }, __('Vendor Processing'));

        // 🔹 Button: Monitor Processing
        listview.page.add_inner_button(__('Monitor Processing'), function() {
            show_processing_monitor();
        }, __('Vendor Processing'));

        // 🔹 Button: System Health Check
        listview.page.add_inner_button(__('Health Check'), function() {
            show_system_health_check();
        }, __('System Health'));

        // 🔹 Button: Data Integrity Check
        listview.page.add_inner_button(__('Data Integrity Check'), function() {
            show_data_integrity_check();
        }, __('System Health'));

        // 🔹 Button: Master Data Validation
        listview.page.add_inner_button(__('Master Data Validation'), function() {
            show_master_data_validation();
        }, __('System Health'));

        listview.page.add_inner_button(__('Bulk Revalidate'), function() {
            
            frappe.confirm(
                'This will revalidate all records where import status is not "Queued", "Processing", or "Completed". Do you want to continue?',
                function() {
                    // User confirmed
                    frappe.call({
                        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.bulk_revalidate_staging_records',
                        args: {},
                        freeze: true,
                        freeze_message: __('Starting bulk revalidation...'),
                        callback: function(r) {
                            if (r.message && r.message.status === 'success') {
                                listview.refresh();
                            }
                        }
                    });
                }
            );
            
        }, __('Vendor Processing'));
        
        // Optional: Add button for selected records only
        listview.page.add_inner_button(__('Revalidate Selected'), function() {
            let selected = listview.get_checked_items();
            
            if (selected.length === 0) {
                frappe.msgprint(__('Please select at least one record'));
                return;
            }
            
            // Filter selected items based on import_status
            let eligible_docs = [];
            let ineligible_count = 0;
            
            selected.forEach(item => {
                if (!['Queued', 'Processing', 'Completed'].includes(item.import_status)) {
                    eligible_docs.push(item.name);
                } else {
                    ineligible_count++;
                }
            });
            
            if (eligible_docs.length === 0) {
                frappe.msgprint({
                    message: 'None of the selected records are eligible for revalidation. Records with status "Queued", "Processing", or "Completed" cannot be revalidated.',
                    indicator: 'orange'
                });
                return;
            }
            
            let message = `Revalidate ${eligible_docs.length} selected record(s)?`;
            if (ineligible_count > 0) {
                message += `<br><br><small class="text-muted">${ineligible_count} record(s) will be skipped (Queued/Processing/Completed)</small>`;
            }
            
            frappe.confirm(
                message,
                function() {
                    frappe.call({
                        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.bulk_revalidate_staging_records',
                        args: {
                            docnames: eligible_docs
                        },
                        freeze: true,
                        freeze_message: __('Starting revalidation...'),
                        callback: function(r) {
                            if (r.message && r.message.status === 'success') {
                                listview.clear_checked_items();
                                listview.refresh();
                            }
                        }
                    });
                }
            );
            
        }, __('Vendor Processing'));



        // add_comprehensive_integrity_buttons(listview);
        
        // Add document creation analysis
        // add_document_analysis_buttons(listview);
        
        // // Add missing masters management
        // add_missing_masters_buttons(listview);
        
        // // Enhanced processing buttons
        // add_enhanced_processing_buttons(listview);
    }
};

function show_retry_failed_dialog(failed_records) {
    /**
     * Show dialog for retrying failed records with error details
     */
    
    // Group errors by type for better analysis
    const error_groups = {};
    failed_records.forEach(record => {
        const error_key = get_error_category(record.error_log);
        if (!error_groups[error_key]) {
            error_groups[error_key] = [];
        }
        error_groups[error_key].push(record);
    });

    let error_summary_html = '<div class="failed-records-summary">';
    error_summary_html += '<h5>Failed Records Summary</h5>';
    error_summary_html += '<div class="row">';
    error_summary_html += `<div class="col-md-12"><strong>Total Failed Records: ${failed_records.length}</strong></div>`;
    error_summary_html += '</div><br>';

    // Show error categories
    error_summary_html += '<h6>Error Categories:</h6>';
    Object.keys(error_groups).forEach(error_type => {
        const count = error_groups[error_type].length;
        error_summary_html += `<div class="error-category">`;
        error_summary_html += `<span class="badge badge-danger">${count}</span> ${error_type}`;
        error_summary_html += `</div>`;
    });

    error_summary_html += '<br><div class="table-responsive">';
    error_summary_html += '<table class="table table-sm table-striped">';
    error_summary_html += '<thead><tr><th>Record</th><th>Vendor Name</th><th>Error</th></tr></thead><tbody>';
    
    failed_records.slice(0, 10).forEach(record => {
        const short_error = record.error_log ? record.error_log.substring(0, 80) + '...' : 'No error details';
        error_summary_html += `<tr>`;
        error_summary_html += `<td><code>${record.name}</code></td>`;
        error_summary_html += `<td>${record.vendor_name || 'N/A'}</td>`;
        error_summary_html += `<td><small class="text-muted">${short_error}</small></td>`;
        error_summary_html += `</tr>`;
    });

    if (failed_records.length > 10) {
        error_summary_html += `<tr><td colspan="3" class="text-center text-muted">... and ${failed_records.length - 10} more records</td></tr>`;
    }

    error_summary_html += '</tbody></table></div></div>';

    const retry_dialog = new frappe.ui.Dialog({
        title: __('Retry Failed Records'),
        size: 'large',
        fields: [
            {
                fieldname: 'failed_summary',
                fieldtype: 'HTML',
                options: error_summary_html
            },
            {
                fieldname: 'retry_options_section',
                fieldtype: 'Section Break',
                label: __('Retry Options')
            },
            {
                fieldname: 'fix_master_data',
                fieldtype: 'Check',
                label: __('Auto-fix missing master data'),
                description: __('Attempt to create missing Company Master records')
            },
            {
                fieldname: 'skip_validation',
                fieldtype: 'Check',
                label: __('Skip strict validation'),
                description: __('Process records even with minor validation issues')
            },
            {
                fieldname: 'batch_size',
                fieldtype: 'Int',
                label: __('Batch Size'),
                default: 25,
                description: __('Smaller batch size for problematic records')
            }
        ],
        primary_action: function() {
            const values = retry_dialog.get_values();
            retry_failed_records(failed_records, values);
            retry_dialog.hide();
        },
        primary_action_label: __('Retry All Failed Records')
    });

    retry_dialog.show();
}

function get_error_category(error_log) {
    /**
     * Categorize error messages for better grouping
     */
    if (!error_log) return 'Unknown Error';
    
    const error_lower = error_log.toLowerCase();
    
    if (error_lower.includes('company master') || error_lower.includes('company') && error_lower.includes('not found')) {
        return 'Missing Company Master';
    } else if (error_lower.includes('vendor name') && error_lower.includes('required')) {
        return 'Missing Vendor Name';
    } else if (error_lower.includes('validation') || error_lower.includes('invalid')) {
        return 'Validation Error';
    } else if (error_lower.includes('permission') || error_lower.includes('access')) {
        return 'Permission Error';
    } else if (error_lower.includes('duplicate') || error_lower.includes('exists')) {
        return 'Duplicate Data';
    } else if (error_lower.includes('timeout') || error_lower.includes('connection')) {
        return 'System/Network Issue';
    } else {
        return 'Other Error';
    }
}

function retry_failed_records(failed_records, options) {
    /**
     * Retry processing failed records with specified options
     */
    
    const progress_dialog = new frappe.ui.Dialog({
        title: __('Retrying Failed Records'),
        size: 'large',
        fields: [
            {
                fieldname: 'retry_progress',
                fieldtype: 'HTML',
                options: get_processing_progress_html(0, failed_records.length, 'Preparing to retry failed records...')
            }
        ]
    });
    
    progress_dialog.show();
    
    const record_names = failed_records.map(r => r.name);
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.retry_failed_records_with_options',
        args: {
            record_names: record_names,
            options: options
        },
        freeze: true,
        freeze_message: __('Initiating retry process...'),
        callback: function(r) {
            progress_dialog.hide();
            
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Retry process initiated for {0} records', [r.message.total_records]),
                    indicator: 'green'
                });
                
                // Show monitoring dialog
                show_processing_monitor(r.message.total_records);
                
                // Refresh the list
                setTimeout(() => {
                    location.reload();
                }, 2000);
                
            } else {
                const error_message = r.message ? r.message.error : 'Unknown error occurred';
                frappe.msgprint({
                    title: __('Retry Failed'),
                    message: error_message,
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            progress_dialog.hide();
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to initiate retry: {0}', [err.message || 'Unknown error']),
                indicator: 'red'
            });
        }
    });
}

// function show_system_health_check() {
//     /**
//      * Show comprehensive system health check dialog
//      */
    
//     const health_dialog = new frappe.ui.Dialog({
//         title: __('System Health Check'),
//         size: 'large',
//         fields: [
//             {
//                 fieldname: 'health_status',
//                 fieldtype: 'HTML',
//                 options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Performing system health check...</p></div>'
//             }
//         ]
//     });
    
//     health_dialog.show();
    
//     // Perform health check
//     frappe.call({
//         method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.comprehensive_health_check',
//         callback: function(r) {
//             if (r.message) {
//                 const health_html = generate_health_check_html(r.message);
//                 health_dialog.fields_dict.health_status.$wrapper.html(health_html);
//             }
//         }
//     });
// }

// function generate_health_check_html(health_data) {
//     /**
//      * Generate HTML for health check display
//      */
    
//     const overall_status = health_data.overall_health || 'Unknown';
//     const status_color = {
//         'Healthy': 'success',
//         'Warning': 'warning', 
//         'Critical': 'danger',
//         'Unknown': 'secondary'
//     }[overall_status] || 'secondary';
    
//     let html = `
//         <div class="health-check-results">
//             <div class="card">
//                 <div class="card-header bg-${status_color} text-white">
//                     <h5 class="mb-0">
//                         <i class="fa fa-heartbeat"></i> Overall System Health: 
//                         <span class="badge badge-light text-${status_color}">${overall_status}</span>
//                     </h5>
//                 </div>
//                 <div class="card-body">
//     `;
    
//     // System components health
//     if (health_data.components) {
//         html += '<h6>System Components</h6>';
//         html += '<div class="row">';
        
//         Object.keys(health_data.components).forEach(component => {
//             const comp_data = health_data.components[component];
//             const comp_status = comp_data.status || 'Unknown';
//             const comp_color = comp_status === 'Healthy' ? 'success' : comp_status === 'Warning' ? 'warning' : 'danger';
            
//             html += `
//                 <div class="col-md-4 mb-3">
//                     <div class="card border-${comp_color}">
//                         <div class="card-body text-center">
//                             <h6 class="text-${comp_color}">${component}</h6>
//                             <span class="badge badge-${comp_color}">${comp_status}</span>
//                             ${comp_data.details ? `<br><small class="text-muted">${comp_data.details}</small>` : ''}
//                         </div>
//                     </div>
//                 </div>
//             `;
//         });
        
//         html += '</div>';
//     }
    
//     // Data integrity results
//     if (health_data.data_integrity) {
//         html += '<h6>Data Integrity</h6>';
//         html += '<div class="table-responsive">';
//         html += '<table class="table table-sm">';
//         html += '<thead><tr><th>Check</th><th>Result</th><th>Details</th></tr></thead><tbody>';
        
//         Object.keys(health_data.data_integrity).forEach(check => {
//             const check_data = health_data.data_integrity[check];
//             const status_badge = check_data.passed ? 'success' : 'danger';
//             const status_text = check_data.passed ? 'Passed' : 'Failed';
            
//             html += `
//                 <tr>
//                     <td>${check}</td>
//                     <td><span class="badge badge-${status_badge}">${status_text}</span></td>
//                     <td><small>${check_data.message || 'N/A'}</small></td>
//                 </tr>
//             `;
//         });
        
//         html += '</tbody></table></div>';
//     }
    
//     // Master data validation
//     if (health_data.master_data_validation) {
//         html += '<h6>Master Data Validation</h6>';
//         html += '<div class="row">';
        
//         Object.keys(health_data.master_data_validation).forEach(doctype => {
//             const validation_data = health_data.master_data_validation[doctype];
            
//             html += `
//                 <div class="col-md-6 mb-3">
//                     <div class="card">
//                         <div class="card-body">
//                             <h6>${doctype}</h6>
//                             <div class="progress mb-2" style="height: 20px;">
//                                 <div class="progress-bar bg-success" style="width: ${validation_data.valid_percentage}%">
//                                     ${validation_data.valid_percentage}% Valid
//                                 </div>
//                             </div>
//                             <small>
//                                 Valid: ${validation_data.valid_count} | 
//                                 Invalid: ${validation_data.invalid_count} | 
//                                 Total: ${validation_data.total_count}
//                             </small>
//                             ${validation_data.missing_references ? `<br><small class="text-warning">Missing References: ${validation_data.missing_references}</small>` : ''}
//                         </div>
//                     </div>
//                 </div>
//             `;
//         });
        
//         html += '</div>';
//     }
    
//     // Recommendations
//     if (health_data.recommendations && health_data.recommendations.length > 0) {
//         html += '<h6>Recommendations</h6>';
//         html += '<ul class="list-group">';
        
//         health_data.recommendations.forEach(recommendation => {
//             html += `<li class="list-group-item list-group-item-warning">${recommendation}</li>`;
//         });
        
//         html += '</ul>';
//     }
    
//     html += `
//                 </div>
//             </div>
//         </div>
        
//         <style>
//             .health-check-results .card {
//                 margin-bottom: 10px;
//             }
            
//             .progress {
//                 border-radius: 10px;
//             }
//         </style>
//     `;
    
//     return html;
// }

// function show_data_integrity_check() {
//     /**
//      * Show data integrity check focusing on link field validation
//      */
    
//     const integrity_dialog = new frappe.ui.Dialog({
//         title: __('Data Integrity Check'),
//         size: 'large',
//         fields: [
//             {
//                 fieldname: 'integrity_status',
//                 fieldtype: 'HTML',
//                 options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Checking data integrity...</p></div>'
//             }
//         ]
//     });
    
//     integrity_dialog.show();
    
//     frappe.call({
//         method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.check_data_integrity',
//         callback: function(r) {
//             if (r.message) {
//                 const integrity_html = generate_data_integrity_html(r.message);
//                 integrity_dialog.fields_dict.integrity_status.$wrapper.html(integrity_html);
//             }
//         }
//     });
// }

// function generate_data_integrity_html(integrity_data) {
//     /**
//      * Generate HTML for data integrity check results
//      */
    
//     let html = `
//         <div class="data-integrity-results">
//             <h5>Link Field Validation Results</h5>
//     `;
    
//     // Missing Company Masters
//     if (integrity_data.missing_company_masters) {
//         html += `
//             <div class="card border-warning mb-3">
//                 <div class="card-header bg-warning text-dark">
//                     <h6><i class="fa fa-exclamation-triangle"></i> Missing Company Masters</h6>
//                 </div>
//                 <div class="card-body">
//                     <p>Found <strong>${integrity_data.missing_company_masters.length}</strong> staging records referencing non-existent Company Masters:</p>
//                     <div class="table-responsive">
//                         <table class="table table-sm">
//                             <thead><tr><th>Company Code</th><th>Referenced By Records</th><th>Action</th></tr></thead>
//                             <tbody>
//         `;
        
//         Object.keys(integrity_data.missing_company_masters).forEach(company_code => {
//             const count = integrity_data.missing_company_masters[company_code];
//             html += `
//                 <tr>
//                     <td><code>${company_code}</code></td>
//                     <td><span class="badge badge-secondary">${count} records</span></td>
//                     <td><button class="btn btn-sm btn-primary" onclick="create_missing_company_master('${company_code}')">Create Master</button></td>
//                 </tr>
//             `;
//         });
        
//         html += '</tbody></table></div></div></div>';
//     }
    
//     // Invalid links summary
//     if (integrity_data.invalid_links) {
//         html += `
//             <div class="card border-danger mb-3">
//                 <div class="card-header bg-danger text-white">
//                     <h6><i class="fa fa-times-circle"></i> Invalid Link References</h6>
//                 </div>
//                 <div class="card-body">
//         `;
        
//         Object.keys(integrity_data.invalid_links).forEach(doctype => {
//             const invalid_count = integrity_data.invalid_links[doctype];
//             html += `
//                 <div class="mb-2">
//                     <strong>${doctype}:</strong> 
//                     <span class="badge badge-danger">${invalid_count} invalid references</span>
//                 </div>
//             `;
//         });
        
//         html += '</div></div>';
//     }
    
//     // Data completeness
//     if (integrity_data.completeness) {
//         html += `
//             <div class="card border-info mb-3">
//                 <div class="card-header bg-info text-white">
//                     <h6><i class="fa fa-chart-bar"></i> Data Completeness</h6>
//                 </div>
//                 <div class="card-body">
//                     <div class="row">
//         `;
        
//         Object.keys(integrity_data.completeness).forEach(field => {
//             const completeness = integrity_data.completeness[field];
//             html += `
//                 <div class="col-md-4 mb-3">
//                     <div class="text-center">
//                         <div class="progress" style="height: 25px;">
//                             <div class="progress-bar" style="width: ${completeness.percentage}%">
//                                 ${completeness.percentage}%
//                             </div>
//                         </div>
//                         <small>${field}</small><br>
//                         <small class="text-muted">${completeness.filled}/${completeness.total}</small>
//                     </div>
//                 </div>
//             `;
//         });
        
//         html += '</div></div></div>';
//     }
    
//     html += '</div>';
    
//     return html;
// }

// function show_master_data_validation() {
//     /**
//      * Show master data validation and auto-fix options
//      */
    
//     const master_dialog = new frappe.ui.Dialog({
//         title: __('Master Data Validation'),
//         size: 'large',
//         fields: [
//             {
//                 fieldname: 'validation_status',
//                 fieldtype: 'HTML',
//                 options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Validating master data...</p></div>'
//             }
//         ]
//     });
    
//     master_dialog.show();
    
//     frappe.call({
//         method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.validate_master_data_completeness',
//         callback: function(r) {
//             if (r.message) {
//                 const validation_html = generate_master_validation_html(r.message);
//                 master_dialog.fields_dict.validation_status.$wrapper.html(validation_html);
//             }
//         }
//     });
// }

// function generate_master_validation_html(validation_data) {
//     /**
//      * Generate HTML for master data validation results
//      */
    
//     let html = `
//         <div class="master-validation-results">
//             <div class="card">
//                 <div class="card-header">
//                     <h5>Master Data Validation Summary</h5>
//                 </div>
//                 <div class="card-body">
//     `;
    
//     // Summary statistics
//     if (validation_data.summary) {
//         html += '<div class="row mb-4">';
//         Object.keys(validation_data.summary).forEach(key => {
//             const value = validation_data.summary[key];
//             const color = key.includes('missing') ? 'danger' : key.includes('valid') ? 'success' : 'info';
            
//             html += `
//                 <div class="col-md-3 text-center">
//                     <div class="card border-${color}">
//                         <div class="card-body">
//                             <h4 class="text-${color}">${value}</h4>
//                             <small>${key.replace(/_/g, ' ').toUpperCase()}</small>
//                         </div>
//                     </div>
//                 </div>
//             `;
//         });
//         html += '</div>';
//     }
    
//     // Missing master data details
//     if (validation_data.missing_masters) {
//         html += '<h6>Missing Master Data</h6>';
//         html += '<div class="accordion" id="missingMastersAccordion">';
        
//         Object.keys(validation_data.missing_masters).forEach((doctype, index) => {
//             const missing_items = validation_data.missing_masters[doctype];
            
//             html += `
//                 <div class="card">
//                     <div class="card-header">
//                         <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapse${index}">
//                             ${doctype} (${missing_items.length} missing)
//                         </button>
//                     </div>
//                     <div id="collapse${index}" class="collapse" data-parent="#missingMastersAccordion">
//                         <div class="card-body">
//                             <div class="table-responsive">
//                                 <table class="table table-sm">
//                                     <thead><tr><th>Missing Value</th><th>Referenced By</th><th>Action</th></tr></thead>
//                                     <tbody>
//             `;
            
//             missing_items.slice(0, 10).forEach(item => {
//                 html += `
//                     <tr>
//                         <td><code>${item.value}</code></td>
//                         <td><span class="badge badge-secondary">${item.count} records</span></td>
//                         <td><button class="btn btn-sm btn-success" onclick="auto_create_master('${doctype}', '${item.value}')">Auto Create</button></td>
//                     </tr>
//                 `;
//             });
            
//             if (missing_items.length > 10) {
//                 html += `<tr><td colspan="3" class="text-center text-muted">... and ${missing_items.length - 10} more items</td></tr>`;
//             }
            
//             html += '</tbody></table></div></div></div></div>';
//         });
        
//         html += '</div>';
//     }
    
//     html += `
//                     <div class="mt-3">
//                         <button class="btn btn-primary" onclick="auto_fix_all_masters()">
//                             <i class="fa fa-magic"></i> Auto-Fix All Missing Masters
//                         </button>
//                         <button class="btn btn-secondary ml-2" onclick="export_master_data_report()">
//                             <i class="fa fa-download"></i> Export Report
//                         </button>
//                     </div>
//                 </div>
//             </div>
//         </div>
//     `;
    
//     return html;
// }

// Global helper functions for master data management
// window.create_missing_company_master = function(company_code) {
//     frappe.prompt([
//         {
//             label: 'Company Name',
//             fieldname: 'company_name',
//             fieldtype: 'Data',
//             reqd: 1,
//             default: company_code
//         },
//         {
//             label: 'Company Short Form',
//             fieldname: 'company_short_form', 
//             fieldtype: 'Data'
//         }
//     ], function(values) {
//         frappe.call({
//             method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.create_company_master',
//             args: {
//                 company_code: company_code,
//                 company_name: values.company_name,
//                 company_short_form: values.company_short_form
//             },
//             callback: function(r) {
//                 if (r.message.status === 'success') {
//                     frappe.show_alert({
//                         message: __('Company Master created successfully'),
//                         indicator: 'green'
//                     });
//                     setTimeout(() => location.reload(), 1000);
//                 } else {
//                     frappe.msgprint({
//                         title: __('Error'),
//                         message: r.message.error,
//                         indicator: 'red'
//                     });
//                 }
//             }
//         });
//     }, __('Create Company Master'), __('Create'));
// };

// window.auto_create_master = function(doctype, value) {
//     frappe.call({
//         method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.auto_create_master_data',
//         args: {
//             doctype: doctype,
//             value: value
//         },
//         callback: function(r) {
//             if (r.message.status === 'success') {
//                 frappe.show_alert({
//                     message: __('Master data created successfully'),
//                     indicator: 'green'
//                 });
//             } else {
//                 frappe.msgprint({
//                     title: __('Error'),
//                     message: r.message.error,
//                     indicator: 'red'
//                 });
//             }
//         }
//     });
// };

// window.auto_fix_all_masters = function() {
//     frappe.confirm(
//         __('This will automatically create all missing master data. Are you sure?'),
//         function() {
//             frappe.call({
//                 method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.auto_fix_all_master_data',
//                 freeze: true,
//                 freeze_message: __('Creating missing master data...'),
//                 callback: function(r) {
//                     if (r.message.status === 'success') {
//                         frappe.show_alert({
//                             message: __('Created {0} master records', [r.message.created_count]),
//                             indicator: 'green'
//                         });
//                         setTimeout(() => location.reload(), 2000);
//                     } else {
//                         frappe.msgprint({
//                             title: __('Error'),
//                             message: r.message.error,
//                             indicator: 'red'
//                         });
//                     }
//                 }
//             });
//         }
//     );
// };

// window.export_master_data_report = function() {
//     frappe.call({
//         method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.export_master_data_validation_report',
//         callback: function(r) {
//             if (r.message.status === 'success') {
//                 // Download the generated report
//                 window.open(r.message.file_url, '_blank');
//             } else {
//                 frappe.msgprint({
//                     title: __('Export Failed'),
//                     message: r.message.error,
//                     indicator: 'red'
//                 });
//             }
//         }
//     });
// };

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





function add_comprehensive_integrity_buttons(listview) {
    // 🔹 Comprehensive Data Integrity Check
    listview.page.add_inner_button(__('Comprehensive Integrity Check'), function() {
        run_comprehensive_integrity_check(listview);
    }, __('Data Integrity'));

    // 🔹 Document Creation Analysis
    listview.page.add_inner_button(__('Document Creation Analysis'), function() {
        show_document_creation_analysis(listview);
    }, __('Data Integrity'));

    // 🔹 Missing Masters Breakdown
    listview.page.add_inner_button(__('Missing Masters Report'), function() {
        show_missing_masters_breakdown(listview);
    }, __('Data Integrity'));
}

function run_comprehensive_integrity_check(listview) {
    const integrity_dialog = new frappe.ui.Dialog({
        title: __('Comprehensive Data Integrity Check'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'integrity_status',
                fieldtype: 'HTML',
                options: generate_loading_html('Running comprehensive analysis of all documents and child tables...')
            }
        ]
    });
    
    integrity_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_stage_inspect.comprehensive_data_integrity_check',
        freeze: true,
        freeze_message: __('Analyzing complete document ecosystem...'),
        callback: function(r) {
            if (r.message) {
                const integrity_html = generate_comprehensive_integrity_html(r.message);
                integrity_dialog.fields_dict.integrity_status.$wrapper.html(integrity_html);
                
                // Add action buttons based on results
                add_comprehensive_action_buttons(integrity_dialog, r.message, listview);
            }
        },
        error: function(r) {
            integrity_dialog.fields_dict.integrity_status.$wrapper.html(
                `<div class="alert alert-danger">
                    <h5>Analysis Failed</h5>
                    <p>Error: ${r.message || 'Unknown error occurred during comprehensive analysis'}</p>
                </div>`
            );
        }
    });
}

function generate_comprehensive_integrity_html(integrity_data) {
    const status = integrity_data.overall_status;
    const status_color = get_comprehensive_status_color(status);
    
    let html = `
        <div class="comprehensive-integrity-results">
            <!-- System Health Overview -->
            <div class="card border-${status_color} mb-4">
                <div class="card-header bg-${status_color} text-white">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h4 class="mb-0">
                                <i class="fa fa-shield-alt"></i>
                                Complete System Integrity: <span class="badge badge-light text-${status_color}">${status}</span>
                            </h4>
                            <small>Analyzed ${integrity_data.total_records} staging records and their complete document creation paths</small>
                        </div>
                        <div class="col-md-4 text-right">
                            <div class="integrity-score-display">
                                <div class="score-circle bg-white text-${status_color}">
                                    ${Math.round(((integrity_data.validation_summary.valid_records / integrity_data.total_records) * 100) || 0)}%
                                </div>
                                <small class="text-white">System Health</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-md-3">
                            <div class="metric-card bg-primary">
                                <div class="metric-number">${integrity_data.total_records}</div>
                                <div class="metric-label">Total Records</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card bg-success">
                                <div class="metric-number">${integrity_data.validation_summary.valid_records}</div>
                                <div class="metric-label">Ready for Processing</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card bg-warning">
                                <div class="metric-number">${integrity_data.validation_summary.warning_records}</div>
                                <div class="metric-label">Have Warnings</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card bg-danger">
                                <div class="metric-number">${integrity_data.validation_summary.invalid_records}</div>
                                <div class="metric-label">Have Critical Errors</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Document Creation Impact Analysis -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0"><i class="fa fa-file-alt"></i> Document Creation Impact</h6>
                        </div>
                        <div class="card-body">
                            ${generate_document_impact_html(integrity_data.document_integrity_analysis)}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-warning text-dark">
                            <h6 class="mb-0"><i class="fa fa-table"></i> Child Table Issues</h6>
                        </div>
                        <div class="card-body">
                            ${generate_child_table_issues_html(integrity_data.child_table_issues)}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Missing Masters Analysis -->
            <div class="card mb-4">
                <div class="card-header bg-secondary text-white">
                    <h6 class="mb-0"><i class="fa fa-exclamation-triangle"></i> Missing Master Data Analysis</h6>
                </div>
                <div class="card-body">
                    ${generate_missing_masters_analysis_html(integrity_data.missing_masters_analysis)}
                </div>
            </div>
            
            <!-- System Recommendations -->
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0"><i class="fa fa-lightbulb"></i> System Recommendations</h6>
                </div>
                <div class="card-body">
                    ${generate_system_recommendations_html(integrity_data.recommendations)}
                </div>
            </div>
        </div>
        
        <style>
            .comprehensive-integrity-results .metric-card {
                padding: 20px;
                border-radius: 10px;
                color: white;
                margin-bottom: 15px;
                text-align: center;
            }
            
            .metric-number {
                font-size: 2.5rem;
                font-weight: bold;
                line-height: 1;
            }
            
            .metric-label {
                font-size: 0.9rem;
                margin-top: 8px;
            }
            
            .score-circle {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                font-weight: bold;
                margin: 0 auto;
            }
            
            .integrity-score-display {
                text-align: center;
            }
            
            .document-impact-chart {
                margin: 10px 0;
                padding: 8px;
                border-left: 4px solid #007bff;
                background: #f8f9fa;
                border-radius: 4px;
            }
            
            .missing-masters-item {
                margin: 8px 0;
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: #f8f9fa;
            }
            
            .priority-high { border-left: 4px solid #dc3545; }
            .priority-medium { border-left: 4px solid #ffc107; }
            .priority-low { border-left: 4px solid #28a745; }
        </style>
    `;
    
    return html;
}

function generate_document_impact_html(document_analysis) {
    if (!document_analysis || Object.keys(document_analysis).length === 0) {
        return '<div class="alert alert-success">✅ No document integrity issues detected</div>';
    }
    
    let html = '<div class="document-impact-analysis">';
    
    Object.keys(document_analysis).forEach(doctype => {
        const issue_count = document_analysis[doctype];
        const severity = issue_count > 10 ? 'danger' : issue_count > 5 ? 'warning' : 'info';
        
        html += `
            <div class="document-impact-chart">
                <div class="d-flex justify-content-between align-items-center">
                    <strong>${doctype}</strong>
                    <span class="badge badge-${severity}">${issue_count} issues</span>
                </div>
                <div class="progress mt-2" style="height: 8px;">
                    <div class="progress-bar bg-${severity}" style="width: ${Math.min(100, (issue_count / 20) * 100)}%"></div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function generate_child_table_issues_html(child_table_issues) {
    if (!child_table_issues || Object.keys(child_table_issues).length === 0) {
        return '<div class="alert alert-success">✅ No child table issues detected</div>';
    }
    
    let html = '<ul class="list-group">';
    
    Object.keys(child_table_issues).forEach(table_name => {
        const issue_count = child_table_issues[table_name];
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                ${table_name}
                <span class="badge badge-warning badge-pill">${issue_count}</span>
            </li>
        `;
    });
    
    html += '</ul>';
    return html;
}

function generate_missing_masters_analysis_html(missing_masters) {
    if (!missing_masters || Object.keys(missing_masters).length === 0) {
        return '<div class="alert alert-success">✅ No missing master data detected</div>';
    }
    
    let html = '<div class="missing-masters-analysis">';
    
    Object.keys(missing_masters).forEach(doctype => {
        const items = missing_masters[doctype];
        const total_items = Object.keys(items).length;
        const total_references = Object.values(items).reduce((sum, count) => sum + count, 0);
        
        // Determine priority
        let priority_class = 'priority-low';
        let priority_text = 'Low';
        if (total_references >= 50) {
            priority_class = 'priority-high';
            priority_text = 'High';
        } else if (total_references >= 10) {
            priority_class = 'priority-medium';
            priority_text = 'Medium';
        }
        
        html += `
            <div class="missing-masters-item ${priority_class}">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <h6 class="mb-1">${doctype}</h6>
                        <small class="text-muted">${total_items} missing items</small>
                    </div>
                    <div class="col-md-3 text-center">
                        <span class="badge badge-${priority_text === 'High' ? 'danger' : priority_text === 'Medium' ? 'warning' : 'success'}">
                            ${priority_text} Priority
                        </span>
                    </div>
                    <div class="col-md-3 text-right">
                        <strong>${total_references} records affected</strong>
                    </div>
                </div>
                <div class="mt-2">
                    <small class="text-muted">
                        Missing: ${Object.keys(items).slice(0, 3).join(', ')}${total_items > 3 ? ` and ${total_items - 3} more` : ''}
                    </small>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function generate_system_recommendations_html(recommendations) {
    if (!recommendations || recommendations.length === 0) {
        return '<div class="alert alert-info">No specific recommendations at this time.</div>';
    }
    
    let html = '<ul class="recommendations-list">';
    
    recommendations.forEach(rec => {
        let rec_class = 'list-group-item-info';
        if (rec.includes('🔴') || rec.includes('CRITICAL')) rec_class = 'list-group-item-danger';
        else if (rec.includes('⚠️') || rec.includes('WARNING')) rec_class = 'list-group-item-warning';
        else if (rec.includes('✅')) rec_class = 'list-group-item-success';
        
        html += `<li class="list-group-item ${rec_class}">${rec}</li>`;
    });
    
    html += '</ul>';
    return html;
}

function show_document_creation_analysis(listview) {
    const analysis_dialog = new frappe.ui.Dialog({
        title: __('Document Creation Impact Analysis'),
        size: 'large',
        fields: [
            {
                fieldname: 'analysis_content',
                fieldtype: 'HTML',
                options: generate_loading_html('Analyzing document creation patterns...')
            }
        ]
    });
    
    analysis_dialog.show();
    
    // Simulate comprehensive document analysis
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_stage_inspect.comprehensive_data_integrity_check',
        callback: function(r) {
            if (r.message) {
                const analysis_html = generate_document_creation_analysis_html(r.message);
                analysis_dialog.fields_dict.analysis_content.$wrapper.html(analysis_html);
            }
        }
    });
}

function generate_document_creation_analysis_html(integrity_data) {
    // Calculate estimated document creation impact
    const total_records = integrity_data.total_records;
    const valid_records = integrity_data.validation_summary.valid_records;
    
    // Estimate documents per record (based on typical creation pattern)
    const estimated_docs_per_record = {
        "Vendor Master": 1,
        "Company Vendor Code": 1,
        "Vendor Onboarding Company Details": 1,
        "Vendor Bank Details": 0.8,  // Not all records have bank details
        "Multiple Company Data (child)": 1,
        "Vendor Code Child (child)": 1,
        "Banker Details (child)": 0.8,
        "International Bank Details (child)": 0.3
    };
    
    let html = `
        <div class="document-creation-analysis">
            <div class="alert alert-info">
                <h5><i class="fa fa-info-circle"></i> Document Creation Impact Analysis</h5>
                <p>Based on ${total_records} staging records, here's the estimated document creation impact:</p>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card border-success">
                        <div class="card-body text-center">
                            <h2 class="text-success">${valid_records}</h2>
                            <p class="card-text">Records Ready for Processing</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card border-primary">
                        <div class="card-body text-center">
                            <h2 class="text-primary">${Object.values(estimated_docs_per_record).reduce((sum, factor) => sum + (valid_records * factor), 0).toFixed(0)}</h2>
                            <p class="card-text">Estimated Total Documents</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <h6>Document Creation Breakdown:</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Document Type</th>
                            <th>Category</th>
                            <th>Estimated Count</th>
                            <th>Creation Factor</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    Object.keys(estimated_docs_per_record).forEach(doctype => {
        const factor = estimated_docs_per_record[doctype];
        const estimated_count = Math.round(valid_records * factor);
        const category = doctype.includes('child') ? 'Child Table' : 'Main Document';
        
        html += `
            <tr>
                <td><strong>${doctype}</strong></td>
                <td><span class="badge badge-${category === 'Main Document' ? 'primary' : 'secondary'}">${category}</span></td>
                <td>${estimated_count}</td>
                <td>${(factor * 100).toFixed(0)}%</td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
            
            <div class="alert alert-warning mt-3">
                <h6><i class="fa fa-exclamation-triangle"></i> Important Notes:</h6>
                <ul class="mb-0">
                    <li>Document counts are estimates based on data completeness patterns</li>
                    <li>Actual creation depends on data availability in each staging record</li>
                    <li>Child table records are created within parent documents</li>
                    <li>Failed validations will block entire document creation chains</li>
                </ul>
            </div>
        </div>
    `;
    
    return html;
}

function show_missing_masters_breakdown(listview) {
    const masters_dialog = new frappe.ui.Dialog({
        title: __('Missing Masters Breakdown & Action Plan'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'masters_content',
                fieldtype: 'HTML',
                options: generate_loading_html('Analyzing missing master data across all document types...')
            }
        ]
    });
    
    masters_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_stage_inspect.get_missing_masters_breakdown',
        callback: function(r) {
            if (r.message) {
                const masters_html = generate_missing_masters_breakdown_html(r.message);
                masters_dialog.fields_dict.masters_content.$wrapper.html(masters_html);
                
                // Add action buttons for creating missing masters
                add_missing_masters_action_buttons(masters_dialog, r.message);
            }
        }
    });
}

function generate_missing_masters_breakdown_html(breakdown_data) {
    let html = `
        <div class="missing-masters-breakdown">
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="summary-card bg-warning">
                        <h3>${breakdown_data.summary.total_doctypes_affected}</h3>
                        <p>DocTypes Affected</p>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="summary-card bg-danger">
                        <h3>${breakdown_data.summary.total_missing_records}</h3>
                        <p>Missing Master Records</p>
                    </div>
                </div>
            </div>
            
            <h5>Priority Action Plan</h5>
            <div class="priority-actions mb-4">
    `;
    
    if (breakdown_data.priority_actions && breakdown_data.priority_actions.length > 0) {
        breakdown_data.priority_actions.forEach(action => {
            const priority_color = action.priority === 'High' ? 'danger' : action.priority === 'Medium' ? 'warning' : 'success';
            
            html += `
                <div class="card border-${priority_color} mb-3">
                    <div class="card-header bg-${priority_color} text-white">
                        <div class="row align-items-center">
                            <div class="col-md-8">
                                <h6 class="mb-0">${action.doctype}</h6>
                                <small>${action.impact}</small>
                            </div>
                            <div class="col-md-4 text-right">
                                <span class="badge badge-light">${action.priority} Priority</span>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <p><strong>Action:</strong> ${action.action}</p>
                        <div class="missing-items-preview">
                            <strong>Sample Missing Items:</strong>
                            <ul class="mb-0">
                                ${action.missing_items.map(item => `<li><code>${item}</code></li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        });
    } else {
        html += '<div class="alert alert-success">✅ No missing masters detected!</div>';
    }
    
    html += `
            </div>
            
            <h5>Detailed Breakdown</h5>
            <div class="detailed-breakdown">
    `;
    
    if (breakdown_data.detailed_breakdown) {
        Object.keys(breakdown_data.detailed_breakdown).forEach(doctype => {
            const details = breakdown_data.detailed_breakdown[doctype];
            const priority_color = details.priority === 'High' ? 'danger' : details.priority === 'Medium' ? 'warning' : 'success';
            
            html += `
                <div class="card mb-3">
                    <div class="card-header">
                        <div class="row align-items-center">
                            <div class="col-md-6">
                                <h6 class="mb-0">${doctype}</h6>
                            </div>
                            <div class="col-md-2 text-center">
                                <span class="badge badge-${priority_color}">${details.priority}</span>
                            </div>
                            <div class="col-md-2 text-center">
                                <strong>${details.total_missing}</strong><br>
                                <small>Missing Items</small>
                            </div>
                            <div class="col-md-2 text-center">
                                <strong>${details.total_references}</strong><br>
                                <small>References</small>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="missing-items-details">
                            <h6>Missing Items:</h6>
                            <div class="row">
                                ${Object.keys(details.missing_items).map(item => `
                                    <div class="col-md-6">
                                        <span class="badge badge-secondary">${item}</span>
                                        <small class="text-muted">(${details.missing_items[item]} refs)</small>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
    }
    
    html += `
            </div>
        </div>
        
        <style>
            .summary-card {
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                color: white;
                margin-bottom: 15px;
            }
            
            .summary-card h3 {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .missing-items-preview ul,
            .missing-items-details .row {
                max-height: 200px;
                overflow-y: auto;
            }
            
            .missing-items-details .col-md-6 {
                margin-bottom: 8px;
            }
        </style>
    `;
    
    return html;
}

// Helper functions

function show_error_dialog(title, error_message) {
    const error_dialog = new frappe.ui.Dialog({
        title: title,
        fields: [
            {
                fieldname: 'error_content',
                fieldtype: 'HTML',
                options: `
                    <div class="alert alert-danger">
                        <h5><i class="fa fa-exclamation-triangle"></i> ${title}</h5>
                        <p>${error_message}</p>
                        <hr>
                        <small class="text-muted">If this error persists, please contact your system administrator.</small>
                    </div>
                `
            }
        ]
    });
    error_dialog.show();
}


function get_comprehensive_status_color(status) {
    const colors = {
        'Excellent': 'success',
        'Good': 'success',
        'Healthy': 'success',
        'Warning': 'warning',
        'Critical': 'danger',
        'Error': 'danger',
        'Invalid': 'danger',
        'Valid': 'success'
    };
    return colors[status] || 'secondary';
}

function generate_loading_html(message) {
    return `
        <div class="text-center p-4">
            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                <span class="sr-only">Loading...</span>
            </div>
            <p class="text-muted">${message}</p>
            <div class="progress mt-3" style="height: 8px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
            </div>
        </div>
    `;
}
function add_comprehensive_action_buttons(dialog, integrity_data, listview) {
    // Add buttons based on integrity results
    if (integrity_data.validation_summary.valid_records > 0) {
        dialog.$wrapper.find('.modal-footer').prepend(`
            <button class="btn btn-success btn-process-valid">
                Process ${integrity_data.validation_summary.valid_records} Valid Records
            </button>
        `);
        
        dialog.$wrapper.find('.btn-process-valid').click(function() {
            dialog.hide();
            initiate_bulk_processing_from_integrity_check(integrity_data, listview);
        });
    }
    
    if (Object.keys(integrity_data.missing_masters_analysis || {}).length > 0) {
        dialog.$wrapper.find('.modal-footer').prepend(`
            <button class="btn btn-warning btn-create-masters">
                Create Missing Masters
            </button>
        `);
        
        dialog.$wrapper.find('.btn-create-masters').click(function() {
            dialog.hide();
            show_missing_masters_breakdown(listview);
        });
    }
}






// =============================================================================
// CONSOLIDATED HEALTH CHECK SYSTEM JAVASCRIPT FUNCTIONS
// =============================================================================

// Main Health Check Function
function show_system_health_check() {
    const health_dialog = new frappe.ui.Dialog({
        title: __('System Health Check'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'health_status',
                fieldtype: 'HTML',
                options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Performing comprehensive system health check...</p></div>'
            }
        ],
        primary_action_label: __('Refresh Check'),
        primary_action(values) {
            show_system_health_check();
        }
    });
    
    health_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.comprehensive_health_check',
        callback: function(r) {
            if (r.message) {
                const health_html = generate_enhanced_health_check_html(r.message);
                health_dialog.fields_dict.health_status.$wrapper.html(health_html);
            }
        },
        error: function(err) {
            health_dialog.fields_dict.health_status.$wrapper.html(
                '<div class="alert alert-danger">Error performing health check: ' + err.message + '</div>'
            );
        }
    });
}

// Generate HTML for Health Check Display
function generate_enhanced_health_check_html(health_data) {
    const overall_status = health_data.overall_health || 'Unknown';
    const health_score = health_data.health_score || 0;
    const status_color = {
        'Healthy': 'success',
        'Warning': 'warning', 
        'Critical': 'danger',
        'Unknown': 'secondary'
    }[overall_status] || 'secondary';
    
    let html = `
        <div class="enhanced-health-check-results">
            <div class="card">
                <div class="card-header bg-${status_color} text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">
                            <i class="fa fa-heartbeat"></i> System Health: 
                            <span class="badge badge-light text-${status_color}">${overall_status}</span>
                        </h5>
                        <div class="health-score">
                            <div class="progress" style="width: 100px; height: 25px;">
                                <div class="progress-bar bg-light" style="width: ${health_score}%">
                                    <span class="text-dark font-weight-bold">${health_score}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card-body">
    `;
    
    // Validation Summary
    if (health_data.validation_summary) {
        const vs = health_data.validation_summary;
        html += `
            <div class="row mb-4">
                <div class="col-12">
                    <h6><i class="fa fa-check-circle"></i> Validation Summary</h6>
                    <div class="row">
                        <div class="col-md-3 text-center">
                            <div class="card border-info">
                                <div class="card-body">
                                    <h4 class="text-info">${vs.total_records}</h4>
                                    <small>TOTAL RECORDS</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 text-center">
                            <div class="card border-success">
                                <div class="card-body">
                                    <h4 class="text-success">${vs.valid_records}</h4>
                                    <small>VALID RECORDS</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 text-center">
                            <div class="card border-warning">
                                <div class="card-body">
                                    <h4 class="text-warning">${vs.warning_records}</h4>
                                    <small>WARNING RECORDS</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 text-center">
                            <div class="card border-danger">
                                <div class="card-body">
                                    <h4 class="text-danger">${vs.invalid_records}</h4>
                                    <small>INVALID RECORDS</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // System Components
    if (health_data.components) {
        html += '<h6><i class="fa fa-server"></i> System Components</h6>';
        html += '<div class="row mb-4">';
        
        Object.keys(health_data.components).forEach(component => {
            const comp_data = health_data.components[component];
            const comp_status = comp_data.status || 'Unknown';
            const comp_color = comp_status === 'Healthy' ? 'success' : comp_status === 'Warning' ? 'warning' : 'danger';
            
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card border-${comp_color}">
                        <div class="card-body text-center">
                            <h6 class="text-${comp_color}">${component}</h6>
                            <span class="badge badge-${comp_color}">${comp_status}</span>
                            ${comp_data.details ? `<br><small class="text-muted mt-1 d-block">${comp_data.details}</small>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    // Data Integrity Results
    if (health_data.data_integrity) {
        html += '<h6><i class="fa fa-database"></i> Data Integrity Validation</h6>';
        html += '<div class="table-responsive mb-4">';
        html += '<table class="table table-sm">';
        html += '<thead><tr><th>Validation Check</th><th>Status</th><th>Details</th><th>Actions</th></tr></thead><tbody>';
        
        Object.keys(health_data.data_integrity).forEach(check => {
            const check_data = health_data.data_integrity[check];
            const status_badge = check_data.passed ? 'success' : 'danger';
            const status_text = check_data.passed ? 'Passed' : 'Failed';
            
            html += `
                <tr>
                    <td><strong>${check}</strong></td>
                    <td><span class="badge badge-${status_badge}">${status_text}</span></td>
                    <td><small>${check_data.message || 'N/A'}</small>`;
            
            if (check_data.details && Array.isArray(check_data.details)) {
                html += `<br><small class="text-muted">Sample issues: ${check_data.details.slice(0, 2).join('; ')}...</small>`;
            }
            
            if (check_data.total_errors) {
                html += `<br><small class="text-danger">Total errors: ${check_data.total_errors}</small>`;
            }
            
            if (check_data.total_warnings) {
                html += `<br><small class="text-warning">Total warnings: ${check_data.total_warnings}</small>`;
            }
            
            html += '</td><td>';
            
            if (check === 'Missing Masters' && !check_data.passed) {
                html += '<button class="btn btn-sm btn-primary" onclick="show_master_creation_wizard()">Create Masters</button>';
            } else if (check === 'Format Validation' && !check_data.passed) {
                html += '<button class="btn btn-sm btn-info" onclick="show_format_validation_details()">View Details</button>';
            }
            
            html += '</td></tr>';
        });
        
        html += '</tbody></table></div>';
    }
    
    // Master Data Validation
    if (health_data.master_data_validation) {
        html += '<h6><i class="fa fa-sitemap"></i> Master Data Validation</h6>';
        html += '<div class="row mb-4">';
        
        Object.keys(health_data.master_data_validation).forEach(doctype => {
            const validation_data = health_data.master_data_validation[doctype];
            const percentage = validation_data.valid_percentage || 0;
            const color = percentage >= 90 ? 'success' : percentage >= 70 ? 'warning' : 'danger';
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card border-${color}">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="mb-0">${doctype}</h6>
                                <span class="badge badge-${color}">${percentage}%</span>
                            </div>
                            <div class="progress mb-2" style="height: 8px;">
                                <div class="progress-bar bg-${color}" style="width: ${percentage}%"></div>
                            </div>
                            <div class="row text-center">
                                <div class="col-4">
                                    <small class="text-success">Valid<br><strong>${validation_data.valid_count || 0}</strong></small>
                                </div>
                                <div class="col-4">
                                    <small class="text-danger">Invalid<br><strong>${validation_data.invalid_count || 0}</strong></small>
                                </div>
                                <div class="col-4">
                                    <small class="text-info">Total<br><strong>${validation_data.total_count || 0}</strong></small>
                                </div>
                            </div>
                            ${validation_data.missing_references > 0 ? `
                                <div class="mt-2">
                                    <button class="btn btn-sm btn-outline-primary btn-block" 
                                            onclick="create_masters_for_doctype('${doctype}')">
                                        Create ${validation_data.missing_references} Missing Records
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    // Recommendations
    if (health_data.recommendations && health_data.recommendations.length > 0) {
        html += '<h6><i class="fa fa-lightbulb-o"></i> Recommendations & Quick Actions</h6>';
        html += '<div class="list-group mb-4">';
        
        health_data.recommendations.forEach((recommendation, index) => {
            html += `<div class="list-group-item list-group-item-warning d-flex justify-content-between align-items-center">
                        <span>${recommendation}</span>`;
            
            if (recommendation.includes('Create missing master data')) {
                html += '<button class="btn btn-sm btn-success" onclick="bulk_create_all_missing_masters()">Auto-Create All</button>';
            } else if (recommendation.includes('Fix') && recommendation.includes('validation errors')) {
                html += '<button class="btn btn-sm btn-info" onclick="show_validation_error_details()">View Errors</button>';
            } else if (recommendation.includes('Reset') && recommendation.includes('stuck processing')) {
                html += '<button class="btn btn-sm btn-warning" onclick="reset_stuck_records()">Reset Records</button>';
            }
            
            html += '</div>';
        });
        
        html += '</div>';
    }
    
    // Quick Actions
    html += `
        <div class="card bg-light">
            <div class="card-body">
                <h6><i class="fa fa-bolt"></i> Quick Actions</h6>
                <div class="btn-group-vertical btn-block" role="group">
                    <button type="button" class="btn btn-primary mb-2" onclick="show_data_integrity_check()">
                        <i class="fa fa-search"></i> Detailed Data Integrity Check
                    </button>
                    <button type="button" class="btn btn-info mb-2" onclick="show_master_data_validation()">
                        <i class="fa fa-sitemap"></i> Master Data Validation
                    </button>
                    <button type="button" class="btn btn-success mb-2" onclick="show_bulk_master_creation()">
                        <i class="fa fa-plus-circle"></i> Bulk Create Missing Masters
                    </button>
                    <button type="button" class="btn btn-warning" onclick="run_validation_fix_wizard()">
                        <i class="fa fa-magic"></i> Validation Fix Wizard
                    </button>
                </div>
            </div>
        </div>
    `;
    
    html += `
                </div>
            </div>
        </div>
        <style>
            .enhanced-health-check-results .card { margin-bottom: 10px; }
            .health-score .progress { border-radius: 15px; }
            .health-score .progress-bar { border-radius: 15px; }
            .list-group-item { border-left: 4px solid #ffc107; }
            .btn-group-vertical .btn { text-align: left; }
        </style>
    `;
    
    return html;
}

// Data Integrity Check Functions
function show_data_integrity_check() {
    const integrity_dialog = new frappe.ui.Dialog({
        title: __('Data Integrity Check'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'integrity_status',
                fieldtype: 'HTML',
                options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Performing comprehensive data integrity check...</p></div>'
            }
        ],
        primary_action_label: __('Export Report'),
        primary_action(values) {
            export_data_integrity_report();
        }
    });
    
    integrity_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.check_data_integrity',
        callback: function(r) {
            if (r.message) {
                const integrity_html = generate_enhanced_data_integrity_html(r.message);
                integrity_dialog.fields_dict.integrity_status.$wrapper.html(integrity_html);
            }
        }
    });
}

function generate_enhanced_data_integrity_html(integrity_data) {
    let html = `
        <div class="enhanced-data-integrity-results">
            <h5><i class="fa fa-shield"></i> Comprehensive Data Integrity Analysis</h5>
    `;
    
    // Format validation errors
    if (integrity_data.format_validation && integrity_data.format_validation.total_errors > 0) {
        html += `
            <div class="card border-danger mb-3">
                <div class="card-header bg-danger text-white">
                    <h6><i class="fa fa-exclamation-circle"></i> Format Validation Errors</h6>
                </div>
                <div class="card-body">
                    <p>Found <strong>${integrity_data.format_validation.total_errors}</strong> format validation errors:</p>
                    <div class="alert alert-light">
                        <h6>Sample Errors:</h6>
                        <ul class="mb-0">
                            ${integrity_data.format_validation.sample_errors.map(error => `<li><code>${error}</code></li>`).join('')}
                        </ul>
                    </div>
                    <button class="btn btn-info" onclick="show_format_validation_details()">View All Format Errors</button>
                </div>
            </div>
        `;
    }
    
    // Missing Company Masters
    if (integrity_data.missing_company_masters && Object.keys(integrity_data.missing_company_masters).length > 0) {
        html += `
            <div class="card border-warning mb-3">
                <div class="card-header bg-warning text-dark">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6><i class="fa fa-building"></i> Missing Company Masters</h6>
                        <button class="btn btn-sm btn-success" onclick="bulk_create_company_masters()">
                            <i class="fa fa-plus"></i> Create All
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <p>Found <strong>${Object.keys(integrity_data.missing_company_masters).length}</strong> missing Company Master records:</p>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead><tr><th>Company Code</th><th>Referenced By</th><th>Action</th></tr></thead>
                            <tbody>
        `;
        
        Object.keys(integrity_data.missing_company_masters).forEach(company_code => {
            const count = integrity_data.missing_company_masters[company_code];
            html += `
                <tr>
                    <td><code class="bg-light px-2 py-1">${company_code}</code></td>
                    <td><span class="badge badge-secondary">${count} records</span></td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="create_company_master_with_form('${company_code}')">
                            <i class="fa fa-plus"></i> Create
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div></div></div>';
    }
    
    // Missing masters detail
    if (integrity_data.missing_masters_detail && Object.keys(integrity_data.missing_masters_detail).length > 0) {
        html += `
            <div class="card border-info mb-3">
                <div class="card-header bg-info text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6><i class="fa fa-sitemap"></i> All Missing Master Data</h6>
                        <button class="btn btn-sm btn-light" onclick="bulk_create_all_missing_masters()">
                            <i class="fa fa-magic"></i> Auto-Create All
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="accordion" id="missingMastersAccordion">
        `;
        
        Object.keys(integrity_data.missing_masters_detail).forEach((doctype, index) => {
            const missing_items = integrity_data.missing_masters_detail[doctype];
            const item_count = missing_items.length;
            
            html += `
                <div class="card">
                    <div class="card-header">
                        <button class="btn btn-link text-left" type="button" data-toggle="collapse" 
                                data-target="#collapse${index}" aria-expanded="false">
                            <i class="fa fa-chevron-right"></i> ${doctype} 
                            <span class="badge badge-warning ml-2">${item_count} missing</span>
                        </button>
                    </div>
                    <div id="collapse${index}" class="collapse" data-parent="#missingMastersAccordion">
                        <div class="card-body">
                            <div class="row mb-3">
                                <div class="col-6">
                                    <button class="btn btn-success btn-sm" onclick="bulk_create_masters_for_doctype('${doctype}')">
                                        <i class="fa fa-plus-circle"></i> Create All ${item_count} Records
                                    </button>
                                </div>
                                <div class="col-6 text-right">
                                    <button class="btn btn-info btn-sm" onclick="download_master_template('${doctype}')">
                                        <i class="fa fa-download"></i> Download Template
                                    </button>
                                </div>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-sm table-striped">
                                    <thead><tr><th>Missing Value</th><th>Action</th></tr></thead>
                                    <tbody>
            `;
            
            missing_items.slice(0, 20).forEach(item => {
                html += `
                    <tr>
                        <td><code class="bg-light px-2 py-1">${item}</code></td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="create_single_master('${doctype}', '${item}')">
                                <i class="fa fa-plus"></i> Create
                            </button>
                        </td>
                    </tr>
                `;
            });
            
            if (missing_items.length > 20) {
                html += `<tr><td colspan="2" class="text-center text-muted">... and ${missing_items.length - 20} more items</td></tr>`;
            }
            
            html += '</tbody></table></div></div></div></div>';
        });
        
        html += '</div></div></div>';
    }
    
    // Data completeness
    if (integrity_data.completeness) {
        html += `
            <div class="card border-info mb-3">
                <div class="card-header bg-info text-white">
                    <h6><i class="fa fa-chart-bar"></i> Data Completeness Analysis</h6>
                </div>
                <div class="card-body">
                    <div class="row">
        `;
        
        Object.keys(integrity_data.completeness).forEach(field => {
            const completeness = integrity_data.completeness[field];
            const percentage = completeness.percentage || 0;
            const color = percentage >= 90 ? 'success' : percentage >= 70 ? 'warning' : 'danger';
            
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card border-${color}">
                        <div class="card-body text-center">
                            <h6 class="text-${color}">${field.replace(/_/g, ' ').toUpperCase()}</h6>
                            <div class="progress mb-2" style="height: 25px;">
                                <div class="progress-bar bg-${color}" style="width: ${percentage}%">
                                    <span class="text-white font-weight-bold">${percentage}%</span>
                                </div>
                            </div>
                            <small class="text-muted">${completeness.filled}/${completeness.total} records</small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div></div></div>';
    }
    
    html += '</div>';
    return html;
}

// Master Data Validation Functions
function show_master_data_validation() {
    const master_dialog = new frappe.ui.Dialog({
        title: __('Master Data Validation'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'validation_status',
                fieldtype: 'HTML',
                options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Validating master data...</p></div>'
            }
        ],
        primary_action_label: __('Export Report'),
        primary_action(values) {
            export_master_data_report();
        }
    });
    
    master_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.validate_master_data_completeness',
        callback: function(r) {
            if (r.message) {
                const validation_html = generate_enhanced_master_validation_html(r.message);
                master_dialog.fields_dict.validation_status.$wrapper.html(validation_html);
            }
        }
    });
}

function generate_enhanced_master_validation_html(validation_data) {
    let html = `
        <div class="enhanced-master-validation-results">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fa fa-sitemap"></i> Master Data Validation Dashboard</h5>
                </div>
                <div class="card-body">
    `;
    
    // Summary statistics
    if (validation_data.summary) {
        html += '<div class="row mb-4">';
        const summary_items = [
            {key: 'total_records', label: 'Total Records', icon: 'fa-database', color: 'primary'},
            {key: 'pending_records', label: 'Pending Records', icon: 'fa-clock-o', color: 'warning'},
            {key: 'failed_records', label: 'Failed Records', icon: 'fa-times', color: 'danger'},
            {key: 'completed_records', label: 'Completed Records', icon: 'fa-check', color: 'success'}
        ];
        
        summary_items.forEach(item => {
            const value = validation_data.summary[item.key] || 0;
            html += `
                <div class="col-md-3 text-center">
                    <div class="card border-${item.color}">
                        <div class="card-body">
                            <i class="fa ${item.icon} fa-2x text-${item.color} mb-2"></i>
                            <h4 class="text-${item.color}">${value}</h4>
                            <small class="text-muted">${item.label.toUpperCase()}</small>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Master data statistics
    if (validation_data.doctype_stats) {
        html += '<h6><i class="fa fa-bar-chart"></i> Master Data Completeness by Type</h6>';
        html += '<div class="row mb-4">';
        
        Object.keys(validation_data.doctype_stats).forEach(doctype => {
            const stats = validation_data.doctype_stats[doctype];
            const percentage = stats.valid_percentage || 0;
            const color = percentage >= 90 ? 'success' : percentage >= 70 ? 'warning' : 'danger';
            
            html += `
                <div class="col-lg-6 col-xl-4 mb-3">
                    <div class="card border-${color} h-100">
                        <div class="card-header bg-${color} text-white d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">${doctype}</h6>
                            <span class="badge badge-light text-${color}">${percentage}%</span>
                        </div>
                        <div class="card-body">
                            <div class="progress mb-3" style="height: 10px;">
                                <div class="progress-bar bg-${color}" style="width: ${percentage}%"></div>
                            </div>
                            
                            <div class="row text-center mb-3">
                                <div class="col-4">
                                    <div class="border-right">
                                        <div class="text-success font-weight-bold">${stats.valid_count}</div>
                                        <small class="text-muted">Valid</small>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="border-right">
                                        <div class="text-danger font-weight-bold">${stats.invalid_count}</div>
                                        <small class="text-muted">Invalid</small>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="text-primary font-weight-bold">${stats.total_count}</div>
                                    <small class="text-muted">Total</small>
                                </div>
                            </div>
                            
                            ${stats.missing_references > 0 ? `
                                <button class="btn btn-${color} btn-sm btn-block" 
                                        onclick="create_masters_for_doctype('${doctype}', ${stats.missing_references})">
                                    <i class="fa fa-plus-circle"></i> Create ${stats.missing_references} Missing
                                </button>
                            ` : `
                                <div class="text-center text-success">
                                    <i class="fa fa-check-circle"></i> All references valid
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    // Missing master data details
    if (validation_data.missing_masters && Object.keys(validation_data.missing_masters).length > 0) {
        html += `
            <div class="card border-warning mb-4">
                <div class="card-header bg-warning text-dark">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6><i class="fa fa-exclamation-triangle"></i> Missing Master Data Details</h6>
                        <div>
                            <button class="btn btn-sm btn-success mr-2" onclick="bulk_create_all_missing_masters()">
                                <i class="fa fa-magic"></i> Auto-Create All
                            </button>
                            <button class="btn btn-sm btn-info" onclick="download_all_master_templates()">
                                <i class="fa fa-download"></i> Download Templates
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="accordion" id="missingMastersDetailAccordion">
        `;
        
        Object.keys(validation_data.missing_masters).forEach((doctype, index) => {
            const missing_items = validation_data.missing_masters[doctype];
            
            html += `
                <div class="card">
                    <div class="card-header">
                        <button class="btn btn-link text-left" type="button" data-toggle="collapse" 
                                data-target="#detailCollapse${index}" aria-expanded="false">
                            <i class="fa fa-chevron-right"></i> ${doctype} 
                            <span class="badge badge-danger ml-2">${missing_items.length} missing</span>
                        </button>
                    </div>
                    <div id="detailCollapse${index}" class="collapse" data-parent="#missingMastersDetailAccordion">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <div>
                                    <button class="btn btn-success btn-sm mr-2" onclick="bulk_create_masters_for_doctype('${doctype}')">
                                        <i class="fa fa-plus-circle"></i> Create All ${missing_items.length}
                                    </button>
                                    <button class="btn btn-info btn-sm" onclick="download_master_template('${doctype}')">
                                        <i class="fa fa-download"></i> Template
                                    </button>
                                </div>
                                <small class="text-muted">Click individual create buttons for custom data</small>
                            </div>
                            
                            <div class="table-responsive">
                                <table class="table table-sm table-hover">
                                    <thead class="thead-light">
                                        <tr><th>Missing Value</th><th>Referenced By</th><th>Action</th></tr>
                                    </thead>
                                    <tbody>
            `;
            
            missing_items.slice(0, 15).forEach(item => {
                html += `
                    <tr>
                        <td><code class="bg-light px-2 py-1">${item.value}</code></td>
                        <td><span class="badge badge-secondary">${item.count} records</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="create_master_with_form('${doctype}', '${item.value}')">
                                <i class="fa fa-plus"></i> Create
                            </button>
                        </td>
                    </tr>
                `;
            });
            
            if (missing_items.length > 15) {
                html += `<tr><td colspan="3" class="text-center text-muted">... and ${missing_items.length - 15} more items</td></tr>`;
            }
            
            html += '</tbody></table></div></div></div></div>';
        });
        
        html += '</div></div></div>';
    }
    
    html += '</div></div></div>';
    return html;
}

// Master Creation Functions
function create_master_with_form(doctype, value) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_master_creation_template',
        args: { doctype: doctype },
        callback: function(r) {
            if (r.message) {
                show_master_creation_form(doctype, value, r.message);
            }
        }
    });
}

function show_master_creation_form(doctype, value, template) {
    const fields = [
        {
            fieldname: 'master_info',
            fieldtype: 'HTML',
            options: `<div class="alert alert-info">Creating <strong>${doctype}</strong> with primary value: <code>${value}</code></div>`
        }
    ];
    
    // Add required fields
    template.required_fields.forEach(field => {
        if (field !== 'name') {
            fields.push({
                fieldname: field,
                fieldtype: template.field_types[field] || 'Data',
                label: field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                reqd: 1,
                default: field.includes('code') || field.includes('name') ? value : ''
            });
        }
    });
    
    // Add optional fields
    template.optional_fields.forEach(field => {
        fields.push({
            fieldname: field,
            fieldtype: template.field_types[field] || 'Data',
            label: field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        });
    });
    
    const creation_dialog = new frappe.ui.Dialog({
        title: __('Create {0}', [doctype]),
        fields: fields,
        size: 'large',
        primary_action_label: __('Create'),
        primary_action(values) {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.create_missing_master',
                args: {
                    doctype: doctype,
                    value: value,
                    additional_data: JSON.stringify(values)
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                        creation_dialog.hide();
                        show_system_health_check();
                    } else {
                        frappe.show_alert({
                            message: r.message ? r.message.message : 'Error creating master',
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    });
    
    creation_dialog.show();
}

function bulk_create_all_missing_masters() {
    frappe.confirm(
        'This will automatically create all missing master data records. Continue?',
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.check_data_integrity',
                callback: function(r) {
                    if (r.message && r.message.missing_masters_detail) {
                        frappe.call({
                            method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.bulk_create_missing_masters',
                            args: {
                                missing_masters_json: JSON.stringify(r.message.missing_masters_detail)
                            },
                            callback: function(bulk_result) {
                                if (bulk_result.message) {
                                    const result = bulk_result.message;
                                    frappe.show_alert({
                                        message: `Created ${result.success_count} masters successfully. ${result.failure_count} failed.`,
                                        indicator: result.failure_count > 0 ? 'orange' : 'green'
                                    });
                                    
                                    if (result.failure_count > 0) {
                                        console.log('Failed creations:', result.results.filter(r => !r.success));
                                    }
                                    
                                    show_system_health_check();
                                }
                            }
                        });
                    }
                }
            });
        }
    );
}

function create_masters_for_doctype(doctype, missing_count) {
    frappe.confirm(
        `Create ${missing_count || 'all'} missing ${doctype} records?`,
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.check_data_integrity',
                callback: function(r) {
                    if (r.message && r.message.missing_masters_detail && r.message.missing_masters_detail[doctype]) {
                        const missing_values = r.message.missing_masters_detail[doctype];
                        const masters_to_create = {};
                        masters_to_create[doctype] = missing_values;
                        
                        frappe.call({
                            method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.bulk_create_missing_masters',
                            args: {
                                missing_masters_json: JSON.stringify(masters_to_create)
                            },
                            callback: function(bulk_result) {
                                if (bulk_result.message) {
                                    const result = bulk_result.message;
                                    frappe.show_alert({
                                        message: `${doctype}: Created ${result.success_count} masters. ${result.failure_count} failed.`,
                                        indicator: result.failure_count > 0 ? 'orange' : 'green'
                                    });
                                    
                                    show_system_health_check();
                                }
                            }
                        });
                    }
                }
            });
        }
    );
}

function bulk_create_masters_for_doctype(doctype) {
    create_masters_for_doctype(doctype);
}

function create_single_master(doctype, value) {
    create_master_with_form(doctype, value);
}

function create_company_master_with_form(company_code) {
    create_master_with_form('Company Master', company_code);
}

function bulk_create_company_masters() {
    create_masters_for_doctype('Company Master');
}

// Validation Detail Functions
function show_format_validation_details() {
    const format_dialog = new frappe.ui.Dialog({
        title: __('Format Validation Details'),
        size: 'large',
        fields: [
            {
                fieldname: 'format_details',
                fieldtype: 'HTML',
                options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Loading format validation details...</p></div>'
            }
        ]
    });
    
    format_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.perform_comprehensive_validation_check',
        callback: function(r) {
            if (r.message && r.message.data_integrity && r.message.data_integrity['Format Validation']) {
                const format_data = r.message.data_integrity['Format Validation'];
                let html = `
                    <div class="format-validation-details">
                        <h5>Format Validation Errors</h5>
                `;
                
                if (format_data.details && format_data.details.length > 0) {
                    html += `
                        <div class="alert alert-warning">
                            <strong>Total Errors:</strong> ${format_data.total_errors || format_data.details.length}
                        </div>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead><tr><th>#</th><th>Error Description</th></tr></thead>
                                <tbody>
                    `;
                    
                    format_data.details.forEach((error, index) => {
                        html += `<tr><td>${index + 1}</td><td><code>${error}</code></td></tr>`;
                    });
                    
                    html += '</tbody></table></div>';
                } else {
                    html += '<div class="alert alert-success">No format validation errors found.</div>';
                }
                
                html += '</div>';
                format_dialog.fields_dict.format_details.$wrapper.html(html);
            }
        }
    });
}

function show_validation_error_details() {
    const error_dialog = new frappe.ui.Dialog({
        title: __('Validation Error Details'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'error_details',
                fieldtype: 'HTML',
                options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Loading validation error details...</p></div>'
            }
        ]
    });
    
    error_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.perform_comprehensive_validation_check',
        callback: function(r) {
            if (r.message) {
                let html = `
                    <div class="validation-error-details">
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <div class="card border-danger">
                                    <div class="card-body text-center">
                                        <h4 class="text-danger">${r.message.critical_issues || 0}</h4>
                                        <small>Critical Issues</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card border-warning">
                                    <div class="card-body text-center">
                                        <h4 class="text-warning">${r.message.warning_issues || 0}</h4>
                                        <small>Warning Issues</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card border-success">
                                    <div class="card-body text-center">
                                        <h4 class="text-success">${r.message.validation_summary.valid_records || 0}</h4>
                                        <small>Valid Records</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card border-info">
                                    <div class="card-body text-center">
                                        <h4 class="text-info">${r.message.validation_summary.total_records || 0}</h4>
                                        <small>Total Records</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                `;
                
                // Show data integrity details
                if (r.message.data_integrity) {
                    Object.keys(r.message.data_integrity).forEach(check => {
                        const check_data = r.message.data_integrity[check];
                        const status_color = check_data.passed ? 'success' : 'danger';
                        
                        html += `
                            <div class="card border-${status_color} mb-3">
                                <div class="card-header bg-${status_color} text-white">
                                    <h6>${check}</h6>
                                </div>
                                <div class="card-body">
                                    <p>${check_data.message}</p>
                                    ${check_data.details && Array.isArray(check_data.details) ? 
                                        `<div class="alert alert-light">
                                            <h6>Sample Issues:</h6>
                                            <ul>${check_data.details.slice(0, 10).map(detail => `<li><code>${detail}</code></li>`).join('')}</ul>
                                        </div>` : ''}
                                </div>
                            </div>
                        `;
                    });
                }
                
                html += '</div>';
                error_dialog.fields_dict.error_details.$wrapper.html(html);
            }
        }
    });
}

// Wizard Functions
function show_master_creation_wizard() {
    const wizard_dialog = new frappe.ui.Dialog({
        title: __('Master Data Creation Wizard'),
        size: 'large',
        fields: [
            {
                fieldname: 'wizard_step',
                fieldtype: 'HTML',
                options: `
                    <div class="master-creation-wizard">
                        <h5>Choose Master Data Creation Method</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-body text-center">
                                        <i class="fa fa-magic fa-3x text-primary mb-3"></i>
                                        <h6>Auto-Create All</h6>
                                        <p class="text-muted">Automatically create all missing master data with default values</p>
                                        <button class="btn btn-primary" onclick="auto_create_all_wizard()">Start Auto-Create</button>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-body text-center">
                                        <i class="fa fa-edit fa-3x text-info mb-3"></i>
                                        <h6>Manual Creation</h6>
                                        <p class="text-muted">Create master data with custom values using forms</p>
                                        <button class="btn btn-info" onclick="manual_create_wizard()">Start Manual Creation</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            }
        ]
    });
    
    wizard_dialog.show();
}

function auto_create_all_wizard() {
    bulk_create_all_missing_masters();
}

function manual_create_wizard() {
    show_bulk_master_creation();
}

function run_validation_fix_wizard() {
    const fix_wizard = new frappe.ui.Dialog({
        title: __('Validation Fix Wizard'),
        size: 'large',
        fields: [
            {
                fieldname: 'fix_options',
                fieldtype: 'HTML',
                options: `
                    <div class="validation-fix-wizard">
                        <h5>Validation Fix Options</h5>
                        <div class="list-group">
                            <div class="list-group-item">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Fix Format Errors</h6>
                                    <button class="btn btn-sm btn-primary" onclick="fix_format_errors()">Fix Now</button>
                                </div>
                                <p class="mb-1">Fix GST, PAN, and email format issues automatically</p>
                            </div>
                            
                            <div class="list-group-item">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Create Missing Masters</h6>
                                    <button class="btn btn-sm btn-success" onclick="bulk_create_all_missing_masters()">Create All</button>
                                </div>
                                <p class="mb-1">Create all missing master data records</p>
                            </div>
                            
                            <div class="list-group-item">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Reset Stuck Records</h6>
                                    <button class="btn btn-sm btn-warning" onclick="reset_stuck_records()">Reset</button>
                                </div>
                                <p class="mb-1">Reset records stuck in processing status</p>
                            </div>
                            
                            <div class="list-group-item">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Re-validate All Records</h6>
                                    <button class="btn btn-sm btn-info" onclick="revalidate_all_records()">Re-validate</button>
                                </div>
                                <p class="mb-1">Run validation on all staging records</p>
                            </div>
                        </div>
                    </div>
                `
            }
        ]
    });
    
    fix_wizard.show();
}

function show_bulk_master_creation() {
    const bulk_dialog = new frappe.ui.Dialog({
        title: __('Bulk Master Data Creation'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'bulk_creation',
                fieldtype: 'HTML',
                options: '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Loading missing masters...</p></div>'
            }
        ],
        primary_action_label: __('Create Selected'),
        primary_action(values) {
            const selected = get_selected_masters_for_creation();
            if (selected && Object.keys(selected).length > 0) {
                frappe.call({
                    method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.bulk_create_missing_masters',
                    args: {
                        missing_masters_json: JSON.stringify(selected)
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: `Created ${r.message.success_count} masters successfully`,
                                indicator: 'green'
                            });
                            bulk_dialog.hide();
                            show_system_health_check();
                        }
                    }
                });
            }
        }
    });
    
    bulk_dialog.show();
    
    // Load missing masters
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.check_data_integrity',
        callback: function(r) {
            if (r.message && r.message.missing_masters_detail) {
                const html = generate_bulk_creation_html(r.message.missing_masters_detail);
                bulk_dialog.fields_dict.bulk_creation.$wrapper.html(html);
            }
        }
    });
}

function generate_bulk_creation_html(missing_masters) {
    let html = `
        <div class="bulk-master-creation">
            <h5>Select Masters to Create</h5>
    `;
    
    Object.keys(missing_masters).forEach((doctype, index) => {
        const missing_items = missing_masters[doctype];
        
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <label class="mb-0">
                            <input type="checkbox" id="doctype_${index}" onchange="toggle_doctype_selection('${doctype}', this.checked)"> 
                            <strong>${doctype}</strong> (${missing_items.length} items)
                        </label>
                        <button class="btn btn-sm btn-outline-primary" onclick="select_all_for_doctype('${doctype}')">Select All</button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row" id="items_${doctype}">
        `;
        
        missing_items.slice(0, 20).forEach((item, itemIndex) => {
            html += `
                <div class="col-md-4 mb-2">
                    <label class="mb-0">
                        <input type="checkbox" class="master-item" data-doctype="${doctype}" data-value="${item}">
                        <code>${item}</code>
                    </label>
                </div>
            `;
        });
        
        if (missing_items.length > 20) {
            html += `<div class="col-12"><small class="text-muted">... and ${missing_items.length - 20} more items</small></div>`;
        }
        
        html += '</div></div></div>';
    });
    
    html += '</div>';
    return html;
}

// Utility Functions
function get_selected_masters_for_creation() {
    const selected = {};
    document.querySelectorAll('.master-item:checked').forEach(checkbox => {
        const doctype = checkbox.dataset.doctype;
        const value = checkbox.dataset.value;
        
        if (!selected[doctype]) {
            selected[doctype] = [];
        }
        selected[doctype].push(value);
    });
    
    return selected;
}

function toggle_doctype_selection(doctype, checked) {
    document.querySelectorAll(`.master-item[data-doctype="${doctype}"]`).forEach(checkbox => {
        checkbox.checked = checked;
    });
}

function select_all_for_doctype(doctype) {
    toggle_doctype_selection(doctype, true);
}

// Fix and Action Functions
function fix_format_errors() {
    frappe.confirm(
        'This will attempt to auto-fix format errors (trim whitespace, standardize formats). Continue?',
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.auto_fix_format_errors',
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: `Fixed ${r.message.fixed_count || 0} format errors`,
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    );
}

function reset_stuck_records() {
    frappe.confirm(
        'Reset all records stuck in processing status?',
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.reset_stuck_processing_records',
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: `Reset ${r.message.reset_count || 0} stuck records`,
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    );
}

function revalidate_all_records() {
    frappe.confirm(
        'Re-validate all staging records? This may take a while.',
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.revalidate_all_staging_records',
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: `Re-validated ${r.message.processed_count || 0} records`,
                            indicator: 'green'
                        });
                        show_system_health_check();
                    }
                }
            });
        }
    );
}

// Template and Export Functions
function download_master_template(doctype) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_master_creation_template',
        args: { doctype: doctype },
        callback: function(r) {
            if (r.message) {
                const template = r.message;
                let csv_content = "data:text/csv;charset=utf-8,";
                
                // Add headers
                const headers = [...template.required_fields, ...template.optional_fields];
                csv_content += headers.join(',') + '\n';
                
                // Add sample row
                csv_content += headers.map(h => `sample_${h}`).join(',') + '\n';
                
                const encoded_uri = encodeURI(csv_content);
                const link = document.createElement("a");
                link.setAttribute("href", encoded_uri);
                link.setAttribute("download", `${doctype}_template.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        }
    });
}

function download_all_master_templates() {
    const master_types = ['Company Master', 'State Master', 'City Master', 'Country Master', 'Bank Master', 'Currency Master'];
    
    master_types.forEach((doctype, index) => {
        setTimeout(() => download_master_template(doctype), index * 500);
    });
}

function export_data_integrity_report() {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.export_data_integrity_report',
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: 'Data integrity report exported successfully',
                    indicator: 'green'
                });
            }
        }
    });
}

function export_master_data_report() {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.export_master_data_report',
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: 'Master data report exported successfully',
                    indicator: 'green'
                });
            }
        }
    });
}