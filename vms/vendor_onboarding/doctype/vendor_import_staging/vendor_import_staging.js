// vendor_import_staging.js - FIXED VERSION (No Errors)
frappe.ui.form.on('Vendor Import Staging', {
    refresh: function(frm) {
        setup_custom_buttons(frm);
        setup_status_indicators(frm);
        setup_realtime_updates(frm);
        setup_auto_refresh(frm);
        color_code_form(frm);
        load_import_source_info(frm);
        
        // Add custom actions in the toolbar
        if (frm.doc.import_status === 'Failed' && frappe.user.has_role(['System Manager', 'Vendor Manager'])) {
            frm.add_custom_button(__('Reset & Retry'), function() {
                reset_and_retry_record(frm);
            }).addClass('btn-warning');
        }
        
        // Add validation check button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Validate Data'), function() {
                validate_staging_record(frm);
            }, __('Actions'));
        }
        
        // Show related documents
        if (frm.doc.import_status === 'Completed') {
            setup_related_documents_section(frm);
        }


        // add_comprehensive_form_buttons(frm);
        
        // // Add document creation preview
        // add_document_creation_preview(frm);
        
        // // Add real-time comprehensive validation
        // setup_comprehensive_validation_indicators(frm);
    },
    
    import_status: function(frm) {
        setup_status_indicators(frm);
        setup_auto_refresh(frm);
        
        if (frm.doc.import_status === 'Processing') {
            // Start progress monitoring
            monitor_processing_progress(frm);
        }
    },
    
    vendor_name: function(frm) {
        if (frm.doc.vendor_name && !frm.doc.title) {
            frm.set_value('title', `${frm.doc.vendor_name} - ${frm.doc.vendor_code || 'Pending'}`);
        }
    },
    
    vendor_code: function(frm) {
        if (frm.doc.vendor_name && frm.doc.vendor_code) {
            frm.set_value('title', `${frm.doc.vendor_name} - ${frm.doc.vendor_code}`);
        }
    },
    
    onload: function(frm) {
        // Set up form layout and styling (FIXED)
        setup_form_layout(frm);
        
        // Add help information
        if (frm.is_new()) {
            frm.dashboard.add_comment(`
                <strong>New Staging Record:</strong><br>
                This record will be used to stage vendor data before creating the final Vendor Master.
                Fill in the required fields and validate before processing.
            `, 'blue');
        }
    }
});

function setup_custom_buttons(frm) {
    // Clear existing custom buttons
    frm.clear_custom_buttons();
    
    // Main processing button
    if (frm.doc.import_status === 'Pending' && frm.doc.validation_status !== 'Invalid') {
        frm.add_custom_button(__('Process to Vendor Master'), function() {
            process_to_vendor_master(frm);
        }).addClass('btn-primary');
    }
    
    // Retry button for failed records
    if (frm.doc.import_status === 'Failed') {
        frm.add_custom_button(__('Retry Processing'), function() {
            retry_processing(frm);
        }).addClass('btn-warning');
    }
    
    // View related documents - GROUPED TOGETHER
    if (frm.doc.import_status === 'Completed') {
        frm.add_custom_button(__('View Vendor Master'), function() {
            view_related_vendor(frm);
        }, __('View Documents')).addClass('btn-secondary');
        
        frm.add_custom_button(__('View Company Details'), function() {
            view_related_company_details(frm);
        }, __('View Documents')).addClass('btn-info');
        
        frm.add_custom_button(__('View Vendor Codes'), function() {
            view_related_vendor_codes(frm);
        }, __('View Documents')).addClass('btn-success');
        
        frm.add_custom_button(__('View Bank Details'), function() {
            view_related_bank_details(frm);
        }, __('View Documents')).addClass('btn-warning');
    }
    
    // Validation and quality buttons
    frm.add_custom_button(__('Re-validate Data'), function() {
        revalidate_staging_data(frm);
    }, __('Data Quality'));
    
    frm.add_custom_button(__('View Error Log'), function() {
        view_error_log(frm);
    }, __('Data Quality'));
    
    frm.add_custom_button(__('Data Completeness Check'), function() {
        check_data_completeness(frm);
    }, __('Data Quality'));
    
    // System admin functions
    if (frappe.user.has_role(['System Manager', 'Vendor Manager'])) {
        frm.add_custom_button(__('Health Check'), function() {
            run_single_record_health_check(frm);
        }, __('System'));
        
        frm.add_custom_button(__('Export Record Data'), function() {
            export_record_data(frm);
        }, __('System'));
        
        if (frm.doc.batch_id) {
            frm.add_custom_button(__('View Batch Statistics'), function() {
                show_batch_statistics(frm);
            }, __('System'));
        }
    }
}

function setup_status_indicators(frm) {
    // FIXED: Use methods that actually exist
    
    // Add status-based indicator
    const indicators = {
        'Pending': 'orange',
        'Queued': 'blue',
        'Processing': 'yellow',
        'Completed': 'green',
        'Failed': 'red',
        'Partially Completed': 'purple'
    };
    
    // Only call methods that exist
    if (frm.dashboard && frm.dashboard.add_indicator) {
        frm.dashboard.add_indicator(
            __(frm.doc.import_status || 'Unknown'),
            indicators[frm.doc.import_status] || 'gray'
        );
    }
    
    // Add processing progress if relevant
    if (frm.doc.processing_progress && frm.doc.processing_progress > 0) {
        const progress_html = `
            <div class="progress" style="height: 25px; margin: 10px 0;">
                <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" 
                     style="width: ${frm.doc.processing_progress}%">
                    ${frm.doc.processing_progress}%
                </div>
            </div>
        `;
        
        if (frm.dashboard && frm.dashboard.add_section) {
            frm.dashboard.add_section(progress_html);
        }
    }
    
    // Add validation status
    if (frm.doc.validation_status) {
        const validation_colors = {
            'Valid': 'green',
            'Invalid': 'red',
            'Warning': 'orange',
            'Pending': 'blue'
        };
        
        if (frm.dashboard && frm.dashboard.add_indicator) {
            frm.dashboard.add_indicator(
                __(`Validation: ${frm.doc.validation_status}`),
                validation_colors[frm.doc.validation_status] || 'gray'
            );
        }
    }
    
    // Add summary statistics
    if (frm.doc.total_records || frm.doc.processed_records || frm.doc.failed_records) {
        const summary_html = `
            <div class="row">
                <div class="col-md-4 text-center">
                    <div class="card-body">
                        <h5 class="text-primary">${frm.doc.total_records || 0}</h5>
                        <small>Total Records</small>
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <div class="card-body">
                        <h5 class="text-success">${frm.doc.processed_records || 0}</h5>
                        <small>Processed</small>
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <div class="card-body">
                        <h5 class="text-danger">${frm.doc.failed_records || 0}</h5>
                        <small>Failed</small>
                    </div>
                </div>
            </div>
        `;
        
        if (frm.dashboard && frm.dashboard.add_section) {
            frm.dashboard.add_section(summary_html);
        }
    }
}

function setup_realtime_updates(frm) {
    // Listen for realtime updates on processing status
    if (frm.doc.name && !frm.is_new()) {
        frappe.realtime.on(`vendor_staging_update_${frm.doc.name}`, (data) => {
            console.log('Received realtime update:', data);
            
            // Update progress
            if (data.progress !== undefined) {
                frm.set_value('processing_progress', data.progress);
            }
            
            // Update status
            if (data.status && data.status !== frm.doc.import_status) {
                frm.set_value('import_status', data.status);
                
                // Show notification
                frappe.show_alert({
                    message: __('Status updated to: {0}', [data.status]),
                    indicator: data.status === 'Completed' ? 'green' : 
                              data.status === 'Failed' ? 'red' : 'blue'
                });
            }
            
            // Update error log if provided
            if (data.error_log) {
                frm.set_value('error_log', data.error_log);
            }
            
            frm.refresh();
        });
    }
}

function setup_auto_refresh(frm) {
    // Auto refresh every 30 seconds while processing
    if (frm.doc.import_status === 'Processing' || frm.doc.import_status === 'Queued') {
        setTimeout(() => {
            if (frm.doc.import_status === 'Processing' || frm.doc.import_status === 'Queued') {
                frm.reload_doc();
            }
        }, 30000);
    }
}

function color_code_form(frm) {
    // Remove existing status classes
    frm.page.main.removeClass('status-pending status-processing status-completed status-failed status-queued');
    
    // Add status-based class
    const status_class = `status-${frm.doc.import_status?.toLowerCase().replace(' ', '-') || 'pending'}`;
    frm.page.main.addClass(status_class);
    
    // Add CSS for status-based styling
    if (!$('#staging-status-styles').length) {
        $('<style id="staging-status-styles">')
            .text(`
                .status-pending { border-left: 4px solid #ffc107; }
                .status-queued { border-left: 4px solid #007bff; }
                .status-processing { border-left: 4px solid #fd7e14; }
                .status-completed { border-left: 4px solid #28a745; }
                .status-failed { border-left: 4px solid #dc3545; }
                .status-partially-completed { border-left: 4px solid #6f42c1; }
                
                .staging-progress-bar {
                    height: 20px;
                    border-radius: 10px;
                    margin: 10px 0;
                }
                
                .staging-stat-card {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 5px;
                    background: white;
                }
                
                .staging-error-log {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 10px;
                    font-family: monospace;
                    font-size: 0.9rem;
                    max-height: 300px;
                    overflow-y: auto;
                }
            `)
            .appendTo('head');
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
                try {
                    const stats = JSON.parse(r.message.success_fail_rate || '{}');
                    if (stats.total_records) {
                        frm.set_value('total_records', stats.total_records);
                    }
                    
                    // Show import source info
                    if (frm.dashboard && frm.dashboard.add_comment) {
                        frm.dashboard.add_comment(
                            `<strong>Import Source:</strong> ${frm.doc.import_source}<br>
                             <strong>Total Records:</strong> ${stats.total_records || 0}<br>
                             <strong>Valid Records:</strong> ${stats.valid_records || 0}`,
                            'blue'
                        );
                    }
                } catch (e) {
                    console.log('Error parsing import source stats:', e);
                }
            }
        }
    });
}

function setup_form_layout(frm) {
    // FIXED: Check if methods exist before calling
    
    // Add custom styling and layout improvements
    if (frm.fields_dict.error_log && frm.fields_dict.error_log.wrapper) {
        $(frm.fields_dict.error_log.wrapper).addClass('staging-error-log-wrapper');
    }
    
    // Enhance progress field display
    if (frm.fields_dict.processing_progress && frm.fields_dict.processing_progress.wrapper) {
        $(frm.fields_dict.processing_progress.wrapper).addClass('staging-progress-wrapper');
    }
    
    // Group related fields visually (check if elements exist first)
    if ($('.frappe-control[data-fieldname="processing_progress"]').length) {
        $('.frappe-control[data-fieldname="processing_progress"]').addClass('staging-stat-card');
    }
    if ($('.frappe-control[data-fieldname="validation_status"]').length) {
        $('.frappe-control[data-fieldname="validation_status"]').addClass('staging-stat-card');
    }
}

function process_to_vendor_master(frm) {
    // Validate before processing
    if (!frm.doc.vendor_name || !frm.doc.vendor_code || !frm.doc.c_code) {
        frappe.msgprint({
            title: __('Validation Required'),
            message: __('Please ensure Vendor Name, Vendor Code, and Company Code are filled before processing.'),
            indicator: 'red'
        });
        return;
    }
    
    frappe.confirm(
        __('This will create/update a Vendor Master record and all related documents. Continue?'),
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
                                message: __('Vendor Master "{0}" has been created/updated.<br><br>Would you like to view it now?', [r.message.vendor_name]),
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
        __('This will retry processing this failed record. Any previous errors will be cleared. Continue?'),
        function() {
            // Reset status and attempt processing again
            frm.set_value('import_status', 'Pending');
            frm.set_value('error_log', '');
            frm.set_value('failed_records', 0);
            frm.set_value('processing_progress', 0);
            frm.set_value('import_attempts', (frm.doc.import_attempts || 0) + 1);
            
            frm.save().then(() => {
                process_to_vendor_master(frm);
            });
        }
    );
}

function reset_and_retry_record(frm) {
    frappe.prompt([
        {
            label: 'Fix Missing Master Data',
            fieldname: 'fix_master_data',
            fieldtype: 'Check',
            description: 'Attempt to create missing Company Master records'
        },
        {
            label: 'Skip Strict Validation',
            fieldname: 'skip_validation',
            fieldtype: 'Check',
            description: 'Process even with minor validation issues'
        }
    ], function(values) {
        frappe.call({
            method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.retry_failed_records_with_options',
            args: {
                record_names: [frm.doc.name],
                options: values
            },
            freeze: true,
            freeze_message: __('Resetting and retrying...'),
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: __('Record reset and retry initiated'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Reset Failed'),
                        message: r.message ? r.message.error : __('Unknown error'),
                        indicator: 'red'
                    });
                }
            }
        });
    }, __('Reset & Retry Options'), __('Reset & Retry'));
}

function view_related_vendor(frm) {
    if (!frm.doc.vendor_name && !frm.doc.primary_email) {
        frappe.msgprint(__('Vendor name or email required to find related vendor'));
        return;
    }
    
    // Search for vendor master by multiple criteria
    const filters = {};
    if (frm.doc.primary_email) {
        filters.office_email_primary = frm.doc.primary_email;
    } else if (frm.doc.vendor_name) {
        filters.vendor_name = frm.doc.vendor_name;
    }
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Vendor Master',
            filters: filters,
            fields: ['name', 'vendor_name'],
            limit: 1
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

function view_related_company_details(frm) {
    if (!frm.doc.vendor_name) {
        frappe.msgprint(__('Vendor name required to find company details'));
        return;
    }
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Vendor Onboarding Company Details',
            filters: {
                vendor_name: frm.doc.vendor_name
            },
            fields: ['name', 'company_name'],
            limit: 1
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                const company_details = r.message[0];
                frappe.set_route('Form', 'Vendor Onboarding Company Details', company_details.name);
            } else {
                frappe.msgprint(__('Related company details not found'));
            }
        }
    });
}

function view_related_vendor_codes(frm) {
    if (!frm.doc.c_code) {
        frappe.msgprint(__('Company code required to find vendor codes'));
        return;
    }
    
    // Find company master first
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Company Master',
            filters: { company_code: frm.doc.c_code },
            fieldname: ['name']
        },
        callback: function(r) {
            if (r.message && r.message.name) {
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Company Vendor Code',
                        filters: {
                            company_name: r.message.name
                        },
                        fields: ['name'],
                        limit: 1
                    },
                    callback: function(r2) {
                        if (r2.message && r2.message.length > 0) {
                            frappe.set_route('Form', 'Company Vendor Code', r2.message[0].name);
                        } else {
                            frappe.msgprint(__('Related vendor codes not found'));
                        }
                    }
                });
            } else {
                frappe.msgprint(__('Company Master not found for this company code'));
            }
        }
    });
}

function view_related_bank_details(frm) {
    // Find vendor master first, then bank details
    if (!frm.doc.vendor_name && !frm.doc.primary_email) {
        frappe.msgprint(__('Vendor name or email required to find bank details'));
        return;
    }
    
    const filters = {};
    if (frm.doc.primary_email) {
        filters.office_email_primary = frm.doc.primary_email;
    } else if (frm.doc.vendor_name) {
        filters.vendor_name = frm.doc.vendor_name;
    }
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Vendor Master',
            filters: filters,
            fields: ['name'],
            limit: 1
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                const vendor_master = r.message[0].name;
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Vendor Bank Details',
                        filters: {
                            ref_no: vendor_master
                        },
                        fields: ['name'],
                        limit: 1
                    },
                    callback: function(r2) {
                        if (r2.message && r2.message.length > 0) {
                            frappe.set_route('Form', 'Vendor Bank Details', r2.message[0].name);
                        } else {
                            frappe.msgprint(__('Related bank details not found'));
                        }
                    }
                });
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
            if (r.message && r.message.status === 'success') {
                frm.reload_doc();
                frappe.show_alert({
                    message: __('Data validation completed'),
                    indicator: 'blue'
                });
                
                if (r.message.validation_status) {
                    frappe.msgprint({
                        title: __('Validation Results'),
                        message: __('Validation Status: {0}', [r.message.validation_status]),
                        indicator: r.message.validation_status === 'Valid' ? 'green' : 'orange'
                    });
                }
            } else {
                frappe.msgprint({
                    title: __('Validation Failed'),
                    message: r.message ? r.message.error : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function validate_staging_record(frm) {
    if (frm.is_dirty()) {
        frappe.msgprint(__('Please save the document before validating'));
        return;
    }
    
    revalidate_staging_data(frm);
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
                read_only: 1,
                options: {
                    mode: 'text',
                    theme: 'github'
                }
            },
            {
                fieldname: 'copy_errors',
                fieldtype: 'Button',
                label: __('Copy to Clipboard'),
                click: function() {
                    if (navigator.clipboard) {
                        navigator.clipboard.writeText(frm.doc.error_log);
                        frappe.show_alert({
                            message: __('Error log copied to clipboard'),
                            indicator: 'green'
                        });
                    } else {
                        // Fallback for older browsers
                        frappe.show_alert({
                            message: __('Copy functionality not available in this browser'),
                            indicator: 'orange'
                        });
                    }
                }
            }
        ]
    });
    
    dialog.show();
}

function check_data_completeness(frm) {
    const required_fields = ['vendor_name', 'vendor_code', 'c_code'];
    const recommended_fields = ['gstn_no', 'pan_no', 'primary_email', 'contact_no'];
    
    let completeness_html = '<h5>Data Completeness Report</h5>';
    
    // Check required fields
    completeness_html += '<h6>Required Fields</h6><ul>';
    required_fields.forEach(field => {
        const value = frm.doc[field];
        const status = value ? '✓' : '✗';
        const color = value ? 'green' : 'red';
        completeness_html += `<li style="color: ${color}">${status} ${__(field.replace('_', ' ').toUpperCase())}</li>`;
    });
    completeness_html += '</ul>';
    
    // Check recommended fields
    completeness_html += '<h6>Recommended Fields</h6><ul>';
    recommended_fields.forEach(field => {
        const value = frm.doc[field];
        const status = value ? '✓' : '○';
        const color = value ? 'green' : 'orange';
        completeness_html += `<li style="color: ${color}">${status} ${__(field.replace('_', ' ').toUpperCase())}</li>`;
    });
    completeness_html += '</ul>';
    
    // Calculate completeness percentage
    const total_fields = required_fields.length + recommended_fields.length;
    const filled_fields = [...required_fields, ...recommended_fields].filter(field => frm.doc[field]).length;
    const completeness_percentage = Math.round((filled_fields / total_fields) * 100);
    
    completeness_html += `<div class="alert alert-info">
        <strong>Overall Completeness: ${completeness_percentage}%</strong><br>
        <div class="progress staging-progress-bar">
            <div class="progress-bar bg-info" style="width: ${completeness_percentage}%"></div>
        </div>
    </div>`;
    
    const dialog = new frappe.ui.Dialog({
        title: __('Data Completeness Check'),
        size: 'medium',
        fields: [
            {
                fieldname: 'completeness_report',
                fieldtype: 'HTML',
                options: completeness_html
            }
        ]
    });
    
    dialog.show();
}

function run_single_record_health_check(frm) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.single_record_health_check',
        args: {
            docname: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Running health check...'),
        callback: function(r) {
            if (r.message && !r.message.error) {
                show_health_check_results(r.message, frm);
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

function show_health_check_results(health_data, frm) {
    let health_html = `<h5>Health Check Results for ${frm.doc.name}</h5>`;
    
    // Overall status
    const status_color = health_data.overall_status === 'Healthy' ? 'success' : 
                        health_data.overall_status === 'Warning' ? 'warning' : 'danger';
    
    health_html += `<div class="alert alert-${status_color}">
        <strong>Overall Status: ${health_data.overall_status}</strong>
    </div>`;
    
    // Individual checks
    if (health_data.checks) {
        health_html += '<h6>Individual Checks</h6><ul>';
        Object.keys(health_data.checks).forEach(check => {
            const result = health_data.checks[check];
            const status = result.passed ? '✓' : '✗';
            const color = result.passed ? 'green' : 'red';
            health_html += `<li style="color: ${color}">${status} ${check}: ${result.message}</li>`;
        });
        health_html += '</ul>';
    }
    
    // Recommendations
    if (health_data.recommendations && health_data.recommendations.length > 0) {
        health_html += '<h6>Recommendations</h6><ul>';
        health_data.recommendations.forEach(rec => {
            health_html += `<li class="text-warning">• ${rec}</li>`;
        });
        health_html += '</ul>';
    }
    
    const dialog = new frappe.ui.Dialog({
        title: __('Health Check Results'),
        size: 'large',
        fields: [
            {
                fieldname: 'health_results',
                fieldtype: 'HTML',
                options: health_html
            }
        ]
    });
    
    dialog.show();
}

function export_record_data(frm) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.export_single_record_data',
        args: {
            docname: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                // Download the exported file
                window.open(r.message.file_url, '_blank');
                frappe.show_alert({
                    message: __('Record data exported successfully'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Export Failed'),
                    message: r.message ? r.message.error : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_batch_statistics(frm) {
    if (!frm.doc.batch_id) {
        frappe.msgprint(__('No batch ID available'));
        return;
    }
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_batch_statistics',
        args: {
            batch_id: frm.doc.batch_id
        },
        callback: function(r) {
            if (r.message) {
                show_batch_statistics_dialog(r.message);
            }
        }
    });
}

function show_batch_statistics_dialog(batch_data) {
    let batch_html = `
        <h5>Batch Statistics: ${batch_data.batch_id}</h5>
        
        <div class="row">
            <div class="col-md-3 text-center">
                <div class="staging-stat-card">
                    <h4 class="text-info">${batch_data.total_records}</h4>
                    <small>Total Records</small>
                </div>
            </div>
            <div class="col-md-3 text-center">
                <div class="staging-stat-card">
                    <h4 class="text-success">${batch_data.completed_records}</h4>
                    <small>Completed</small>
                </div>
            </div>
            <div class="col-md-3 text-center">
                <div class="staging-stat-card">
                    <h4 class="text-warning">${batch_data.processing_records}</h4>
                    <small>Processing</small>
                </div>
            </div>
            <div class="col-md-3 text-center">
                <div class="staging-stat-card">
                    <h4 class="text-danger">${batch_data.failed_records}</h4>
                    <small>Failed</small>
                </div>
            </div>
        </div>
        
        <div class="progress staging-progress-bar">
            <div class="progress-bar bg-success" style="width: ${batch_data.completion_percentage}%">
                ${batch_data.completion_percentage}% Complete
            </div>
        </div>
    `;
    
    // Add recent records from this batch
    if (batch_data.sample_records && batch_data.sample_records.length > 0) {
        batch_html += `
            <h6>Sample Records from This Batch</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Record</th>
                            <th>Vendor Name</th>
                            <th>Status</th>
                            <th>Progress</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        batch_data.sample_records.forEach(record => {
            const status_color = {
                'Completed': 'success',
                'Processing': 'warning', 
                'Failed': 'danger',
                'Pending': 'secondary'
            }[record.import_status] || 'secondary';
            
            batch_html += `
                <tr>
                    <td><a href="#Form/Vendor Import Staging/${record.name}">${record.name}</a></td>
                    <td>${record.vendor_name || 'N/A'}</td>
                    <td><span class="badge badge-${status_color}">${record.import_status}</span></td>
                    <td>${record.processing_progress || 0}%</td>
                </tr>
            `;
        });
        
        batch_html += '</tbody></table></div>';
    }
    
    const dialog = new frappe.ui.Dialog({
        title: __('Batch Statistics'),
        size: 'large',
        fields: [
            {
                fieldname: 'batch_stats',
                fieldtype: 'HTML',
                options: batch_html
            }
        ]
    });
    
    dialog.show();
}

function setup_related_documents_section(frm) {
    // Add a section to show related documents created
    if (frm.doc.import_status === 'Completed') {
        let related_docs_html = `
            <div class="card">
                <div class="card-header">
                    <h6><i class="fa fa-link"></i> Related Documents Created</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <button class="btn btn-sm btn-outline-primary" onclick="frappe.ui.form.get_open_form().events.view_related_vendor()">
                                <i class="fa fa-user"></i> View Vendor Master
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-sm btn-outline-info" onclick="frappe.ui.form.get_open_form().events.view_related_company_details()">
                                <i class="fa fa-building"></i> View Company Details
                            </button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <button class="btn btn-sm btn-outline-success" onclick="frappe.ui.form.get_open_form().events.view_related_vendor_codes()">
                                <i class="fa fa-code"></i> View Vendor Codes
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-sm btn-outline-warning" onclick="frappe.ui.form.get_open_form().events.view_related_bank_details()">
                                <i class="fa fa-university"></i> View Bank Details
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        if (frm.dashboard && frm.dashboard.add_section) {
            frm.dashboard.add_section(related_docs_html);
        }
    }
}

function monitor_processing_progress(frm) {
    // Monitor processing progress with periodic updates
    let monitoring_interval = setInterval(() => {
        if (frm.doc.import_status !== 'Processing') {
            clearInterval(monitoring_interval);
            return;
        }
        
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Vendor Import Staging',
                filters: { name: frm.doc.name },
                fieldname: ['processing_progress', 'import_status', 'error_log']
            },
            callback: function(r) {
                if (r.message) {
                    // Update progress without triggering save
                    frm.doc.processing_progress = r.message.processing_progress;
                    frm.doc.import_status = r.message.import_status;
                    if (r.message.error_log) {
                        frm.doc.error_log = r.message.error_log;
                    }
                    
                    frm.refresh();
                    
                    // Stop monitoring if no longer processing
                    if (r.message.import_status !== 'Processing') {
                        clearInterval(monitoring_interval);
                        
                        // Show completion notification
                        frappe.show_alert({
                            message: __('Processing completed with status: {0}', [r.message.import_status]),
                            indicator: r.message.import_status === 'Completed' ? 'green' : 'red'
                        });
                    }
                }
            }
        });
    }, 10000); // Check every 10 seconds
}




function add_comprehensive_form_buttons(frm) {
    if (!frm.doc.__islocal) {
        // 🔹 Comprehensive Record Check
        frm.add_custom_button(__('Comprehensive Validation'), function() {
            run_comprehensive_record_check(frm);
        }, __('Data Quality'));
        
        // 🔹 Document Creation Preview
        frm.add_custom_button(__('Document Creation Preview'), function() {
            show_document_creation_preview(frm);
        }, __('Data Quality'));
        
        // 🔹 Complete Integrity Report
        frm.add_custom_button(__('Complete Integrity Report'), function() {
            generate_complete_integrity_report(frm);
        }, __('Data Quality'));
    }
}

function run_comprehensive_record_check(frm) {
    const check_dialog = new frappe.ui.Dialog({
        title: __('Comprehensive Record Validation'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'validation_results',
                fieldtype: 'HTML',
                options: generate_loading_html('Running comprehensive validation of all document creation paths...')
            }
        ]
    });
    
    check_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_stage_inspect.single_record_comprehensive_check',
        args: {
            docname: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                const results_html = generate_comprehensive_record_results_html(r.message);
                check_dialog.fields_dict.validation_results.$wrapper.html(results_html);
                
                // Add processing button if record is ready
                if (r.message.processing_readiness && r.message.processing_readiness.ready) {
                    check_dialog.$wrapper.find('.modal-footer').prepend(`
                        <button class="btn btn-success btn-process-record">
                            Process to Vendor Master
                        </button>
                    `);
                    
                    check_dialog.$wrapper.find('.btn-process-record').click(function() {
                        check_dialog.hide();
                        process_single_record_comprehensive(frm);
                    });
                }
            }
        }
    });
}

function generate_comprehensive_record_results_html(results) {
    const validation = results.validation_results;
    const readiness = results.processing_readiness;
    const preview = results.document_creation_preview;
    
    let html = `
        <div class="comprehensive-record-results">
            <!-- Overall Status -->
            <div class="alert alert-${validation.overall_status === 'Valid' ? 'success' : 'danger'}">
                <h5>
                    <i class="fa fa-${validation.overall_status === 'Valid' ? 'check-circle' : 'times-circle'}"></i>
                    Record Status: ${validation.overall_status}
                </h5>
                <p><strong>Vendor:</strong> ${results.vendor_name} | <strong>Company:</strong> ${results.company_code}</p>
            </div>
            
            <!-- Processing Readiness -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card border-${readiness.ready ? 'success' : 'danger'}">
                        <div class="card-body text-center">
                            <h3 class="text-${readiness.ready ? 'success' : 'danger'}">
                                ${readiness.ready ? '✅' : '❌'}
                            </h3>
                            <p>${readiness.ready ? 'Ready for Processing' : 'Not Ready'}</p>
                            <small>Confidence: ${readiness.confidence_level}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card border-info">
                        <div class="card-body text-center">
                            <h3 class="text-info">${preview.estimated_records}</h3>
                            <p>Estimated Documents</p>
                            <small>${preview.main_documents.length} main + ${preview.child_tables.length} child tables</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Document Creation Preview -->
            <div class="card mb-4">
                <div class="card-header">
                    <h6><i class="fa fa-file-alt"></i> Document Creation Preview</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Main Documents</h6>
                            <ul class="list-group">
    `;
    
    preview.main_documents.forEach(doc => {
        html += `
            <li class="list-group-item">
                <strong>${doc.doctype}</strong>
                <br><small class="text-muted">
                    ${Object.keys(doc.key_fields).map(field => 
                        `${field}: ${doc.key_fields[field] || 'Not set'}`
                    ).join(', ')}
                </small>
            </li>
        `;
    });
    
    html += `
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Child Tables</h6>
                            <ul class="list-group">
    `;
    
    preview.child_tables.forEach(child => {
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <strong>${child.child_table}</strong>
                    <br><small class="text-muted">in ${child.parent_doctype}</small>
                </div>
                <span class="badge badge-primary badge-pill">${child.records_count}</span>
            </li>
        `;
    });
    
    html += `
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Validation Details -->
            ${generate_validation_details_html(validation)}
        </div>
    `;
    
    return html;
}

function generate_validation_details_html(validation) {
    let html = '<div class="validation-details">';
    
    // Critical errors
    if (validation.critical_errors && validation.critical_errors.length > 0) {
        html += `
            <div class="card border-danger mb-3">
                <div class="card-header bg-danger text-white">
                    <h6 class="mb-0">Critical Errors (${validation.critical_errors.length})</h6>
                </div>
                <div class="card-body">
                    <ul class="mb-0">
                        ${validation.critical_errors.map(error => `<li class="text-danger">${error}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Missing masters
    if (validation.missing_masters && Object.keys(validation.missing_masters).length > 0) {
        html += `
            <div class="card border-warning mb-3">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0">Missing Master Data</h6>
                </div>
                <div class="card-body">
                    ${Object.keys(validation.missing_masters).map(doctype => {
                        const items = Array.from(validation.missing_masters[doctype]);
                        return `<p><strong>${doctype}:</strong> ${items.join(', ')}</p>`;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    // Recommendations
    if (validation.recommendations && validation.recommendations.length > 0) {
        html += `
            <div class="card border-primary">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0">Recommendations</h6>
                </div>
                <div class="card-body">
                    <ul class="mb-0">
                        ${validation.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// Export comprehensive results
function generate_complete_integrity_report(frm) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_stage_inspect.single_record_comprehensive_check',
        args: {
            docname: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                // Create downloadable report
                const report_data = {
                    record: frm.doc.name,
                    vendor_name: frm.doc.vendor_name,
                    validation_results: r.message.validation_results,
                    processing_readiness: r.message.processing_readiness,
                    document_preview: r.message.document_creation_preview,
                    generated_at: new Date().toISOString()
                };
                
                // Download as JSON
                download_json_report(report_data, `integrity_report_${frm.doc.name}.json`);
                
                frappe.msgprint({
                    title: 'Report Generated',
                    message: 'Complete integrity report has been downloaded.',
                    indicator: 'green'
                });
            }
        }
    });
}

function download_json_report(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

console.log('📊 Comprehensive Data Integrity UI System loaded successfully!');



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



// ###########################3Yet to be Added below#############################################


function add_document_analysis_buttons(listview) {
    // 🔹 Document Creation Analysis
    listview.page.add_inner_button(__('Document Creation Analysis'), function() {
        show_document_creation_analysis(listview);
    }, __('Document Analysis'));

    // 🔹 Estimated Documents Report
    listview.page.add_inner_button(__('Estimated Documents'), function() {
        show_estimated_documents_report(listview);
    }, __('Document Analysis'));
}

function add_missing_masters_buttons(listview) {
    // 🔹 Missing Masters Report
    listview.page.add_inner_button(__('Missing Masters Report'), function() {
        show_missing_masters_breakdown(listview);
    }, __('Missing Masters'));

    // 🔹 Create Missing Masters
    listview.page.add_inner_button(__('Create Missing Masters'), function() {
        initiate_missing_masters_creation(listview);
    }, __('Missing Masters'));

    // 🔹 Master Data Health Check
    listview.page.add_inner_button(__('Master Data Health'), function() {
        run_master_data_health_check(listview);
    }, __('Missing Masters'));
}

function add_enhanced_processing_buttons(listview) {
    // 🔹 Smart Batch Processing
    listview.page.add_inner_button(__('Smart Batch Process'), function() {
        initiate_smart_batch_processing(listview);
    }, __('Enhanced Processing'));

    // 🔹 Process Valid Records Only
    listview.page.add_inner_button(__('Process Valid Only'), function() {
        process_only_valid_records(listview);
    }, __('Enhanced Processing'));

    // 🔹 Batch Validation
    listview.page.add_inner_button(__('Batch Validation'), function() {
        run_batch_validation(listview);
    }, __('Enhanced Processing'));
}

function show_document_creation_analysis(listview) {
    const analysis_dialog = new frappe.ui.Dialog({
        title: __('Document Creation Impact Analysis'),
        size: 'large',
        fields: [
            {
                fieldname: 'analysis_content',
                fieldtype: 'HTML',
                options: generate_loading_html('Analyzing document creation patterns across all staging records...')
            }
        ]
    });
    
    analysis_dialog.show();
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.get_document_creation_analysis',
        callback: function(r) {
            if (r.message) {
                const analysis_html = generate_document_analysis_html(r.message);
                analysis_dialog.fields_dict.analysis_content.$wrapper.html(analysis_html);
            } else {
                analysis_dialog.fields_dict.analysis_content.$wrapper.html(
                    '<div class="alert alert-info">No analysis data available at this time.</div>'
                );
            }
        },
        error: function(r) {
            show_error_dialog('Analysis Failed', r.message || 'Failed to generate document creation analysis');
            analysis_dialog.hide();
        }
    });
}

function generate_document_analysis_html(analysis_data) {
    return `
        <div class="document-analysis-results">
            <div class="alert alert-info">
                <h5><i class="fa fa-chart-bar"></i> Document Creation Analysis</h5>
                <p>Analysis of document creation impact across staging records</p>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-4">
                    <div class="card bg-primary text-white">
                        <div class="card-body text-center">
                            <h3>${analysis_data.total_staging_records || 0}</h3>
                            <p>Staging Records</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-success text-white">
                        <div class="card-body text-center">
                            <h3>${analysis_data.estimated_documents || 0}</h3>
                            <p>Estimated Documents</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-warning text-white">
                        <div class="card-body text-center">
                            <h3>${analysis_data.validation_required || 0}</h3>
                            <p>Need Validation</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="alert alert-secondary">
                <h6>Document Types to be Created:</h6>
                <ul class="mb-0">
                    <li><strong>Vendor Master:</strong> 1 per valid record</li>
                    <li><strong>Company Vendor Code:</strong> 1 per valid record</li>
                    <li><strong>Vendor Onboarding Company Details:</strong> 1 per valid record</li>
                    <li><strong>Vendor Bank Details:</strong> 1 per record with bank information</li>
                    <li><strong>Child Tables:</strong> Multiple company data, vendor types, banking details</li>
                </ul>
            </div>
        </div>
    `;
}

function show_estimated_documents_report(listview) {
    frappe.msgprint({
        title: __('Estimated Documents Report'),
        message: `
            <div class="estimated-documents-info">
                <h6>Document Creation Estimates</h6>
                <p>Based on current staging records, the system will create:</p>
                <ul>
                    <li><strong>Main Documents:</strong> ~4 per staging record</li>
                    <li><strong>Child Table Entries:</strong> ~6 per staging record</li>
                    <li><strong>Total Estimated:</strong> ~10 database records per staging record</li>
                </ul>
                <div class="alert alert-info mt-3">
                    <small><i class="fa fa-info-circle"></i> Actual counts depend on data completeness and validation results.</small>
                </div>
            </div>
        `,
        indicator: 'blue'
    });
}

function initiate_missing_masters_creation(listview) {
    frappe.msgprint({
        title: __('Create Missing Masters'),
        message: `
            <div class="missing-masters-creation">
                <p>This feature will help you create missing master data records.</p>
                <div class="alert alert-warning">
                    <strong>Note:</strong> This is a placeholder for the missing masters creation workflow.
                    You can implement specific master creation dialogs here.
                </div>
            </div>
        `,
        indicator: 'orange'
    });
}

function run_master_data_health_check(listview) {
    const health_dialog = new frappe.ui.Dialog({
        title: __('Master Data Health Check'),
        size: 'large',
        fields: [
            {
                fieldname: 'health_content',
                fieldtype: 'HTML',
                options: generate_loading_html('Checking master data health across all linked doctypes...')
            }
        ]
    });
    
    health_dialog.show();
    
    // Simulate health check - replace with actual API call
    setTimeout(() => {
        health_dialog.fields_dict.health_content.$wrapper.html(`
            <div class="master-data-health">
                <div class="alert alert-success">
                    <h5><i class="fa fa-check-circle"></i> Master Data Health Check</h5>
                    <p>Checking connectivity and availability of all master data...</p>
                </div>
                
                <div class="health-checklist">
                    <h6>Master Data Status:</h6>
                    <ul class="list-group">
                        <li class="list-group-item d-flex justify-content-between">
                            <span>Company Master</span>
                            <span class="badge badge-success">Available</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between">
                            <span>State Master</span>
                            <span class="badge badge-success">Available</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between">
                            <span>Currency Master</span>
                            <span class="badge badge-success">Available</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between">
                            <span>Bank Master</span>
                            <span class="badge badge-warning">Some Missing</span>
                        </li>
                    </ul>
                </div>
            </div>
        `);
    }, 2000);
}

function initiate_smart_batch_processing(listview) {
    frappe.msgprint({
        title: __('Smart Batch Processing'),
        message: `
            <div class="smart-batch-info">
                <h6>Smart Batch Processing Features:</h6>
                <ul>
                    <li>Automatic validation before processing</li>
                    <li>Error handling and recovery</li>
                    <li>Progress tracking and reporting</li>
                    <li>Rollback capability for failed batches</li>
                </ul>
                <div class="alert alert-info mt-3">
                    <small>This will be implemented with your existing batch processing logic.</small>
                </div>
            </div>
        `,
        indicator: 'blue'
    });
}

function process_only_valid_records(listview) {
    frappe.confirm(
        __('This will process only records with "Valid" validation status. Continue?'),
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.process_valid_records_only',
                freeze: true,
                freeze_message: __('Processing valid records...'),
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Processing Results'),
                            message: `Processed ${r.message.processed_count || 0} valid records successfully.`,
                            indicator: 'green'
                        });
                        listview.refresh();
                    }
                }
            });
        }
    );
}

// function run_batch_validation(listview) {
//     const batch_dialog = new frappe.ui.Dialog({
//         title: __('Batch Validation'),
//         fields: [
//             {
//                 fieldname: 'batch_size',
//                 fieldtype: 'Int',
//                 label: 'Batch Size',
//                 default: 100,
//                 description: 'Number of records to validate in one batch'
//             },
//             {
//                 fieldname: 'validation_type',
//                 fieldtype: 'Select',
//                 label: 'Validation Type',
//                 options: '\nBasic\nComprehensive\nLink Fields Only',
//                 default: 'Basic'
//             }
//         ],
//         primary_action_label: __('Start Validation'),
//         primary_action: function() {
//             const values = batch_dialog.get_values();
            
//             frappe.call({
//                 method: 'vms.vendor_onboarding.doctype.vendor_import_staging.vendor_import_staging.run_batch_validation',
//                 args: {
//                     batch_size: values.batch_size,
//                     validation_type: values.validation_type
//                 },
//                 freeze: true,
//                 freeze_message: __('Running batch validation...'),
//                 callback: function(r) {
//                     batch_dialog.hide();
//                     if (r.message) {
//                         frappe.msgprint({
//                             title: __('Batch Validation Complete'),
//                             message: `
//                                 <div>
//                                     <p><strong>Validation Results:</strong></p>
//                                     <ul>
//                                         <li>Processed: ${r.message.processed || 0} records</li>
//                                         <li>Valid: ${r.message.valid || 0} records</li>
//                                         <li>Invalid: ${r.message.invalid || 0} records</li>
//                                     </ul>
//                                 </div>
//                             `,
//                             indicator: 'green'
//                         });
//                         listview.refresh();
//                     }
//                 }
//             });
//         }
//     });
    
//     batch_dialog.show();
// }
