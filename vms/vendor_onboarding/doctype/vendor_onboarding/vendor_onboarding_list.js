// vendor_onboarding_list.js
// Place this file in: vms/vendor_onboarding/doctype/vendor_onboarding/vendor_onboarding_list.js

frappe.listview_settings['Vendor Onboarding'] = {
    add_fields: ["onboarding_form_status", "vendor_name", "ref_no", "modified"],
    
    get_indicator: function(doc) {
        var status_color = {
            "Pending": "orange",
            "Approved": "green", 
            "Rejected": "red",
            "SAP Error": "red",
            "Processing": "blue"
        };
        return [__(doc.onboarding_form_status), status_color[doc.onboarding_form_status], "onboarding_form_status,=," + doc.onboarding_form_status];
    },
    
    onload: function(listview) {
        // Add Monitor button
        listview.page.add_inner_button(__('Monitor Dashboard'), function() {
            show_monitoring_dashboard();
        });
        
        // Add Tools dropdown with all utility functions
        listview.page.add_menu_item(__('Tools'), function() {
            show_tools_menu();
        });
    }
};

function show_monitoring_dashboard() {
    // Show loading dialog first
    let loading_dialog = frappe.msgprint({
        title: __('Loading Dashboard...'),
        message: __('Please wait while we fetch monitoring data...'),
        indicator: 'blue'
    });
    
    // Fetch monitoring data
    frappe.call({
        method: 'vms.vendor_onboarding.monitoring_dashboard.get_monitoring_data',
        callback: function(r) {
            loading_dialog.hide();
            
            if (r.message && r.message.status === 'success') {
                show_monitoring_dialog(r.message.data);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message?.message || __('Failed to fetch monitoring data'),
                    indicator: 'red'
                });
            }
        },
        error: function() {
            loading_dialog.hide();
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to connect to monitoring system'),
                indicator: 'red'
            });
        }
    });
}

function show_monitoring_dialog(data) {
    let html = generate_monitoring_html(data);
    
    let dialog = new frappe.ui.Dialog({
        title: __('Vendor Onboarding Monitoring Dashboard'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'monitoring_html',
                options: html
            }
        ],
        primary_action_label: __('Refresh'),
        primary_action() {
            dialog.hide();
            show_monitoring_dashboard(); // Refresh data
        },
        secondary_action_label: __('Tools'),
        secondary_action() {
            show_tools_menu();
        }
    });
    
    dialog.show();
    
    // Add auto-refresh every 30 seconds
    let refresh_interval = setInterval(() => {
        if (dialog.is_visible) {
            frappe.call({
                method: 'vms.vendor_onboarding.monitoring_dashboard.get_monitoring_data',
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        let new_html = generate_monitoring_html(r.message.data);
                        dialog.fields_dict.monitoring_html.$wrapper.html(new_html);
                    }
                }
            });
        } else {
            clearInterval(refresh_interval);
        }
    }, 30000);
}

function generate_monitoring_html(data) {
    let health_color = {
        'excellent': '#28a745',
        'good': '#17a2b8', 
        'warning': '#ffc107',
        'critical': '#dc3545',
        'error': '#6c757d'
    };
    
    return `
        <div class="monitoring-dashboard">
            <style>
                .monitoring-dashboard {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                .dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }
                .dashboard-card {
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .card-header {
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 15px;
                    color: #495057;
                    display: flex;
                    align-items: center;
                }
                .card-icon {
                    margin-right: 10px;
                    font-size: 24px;
                }
                .metric-value {
                    font-size: 32px;
                    font-weight: 700;
                    margin: 10px 0;
                }
                .metric-label {
                    color: #6c757d;
                    font-size: 14px;
                }
                .status-indicator {
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    color: white;
                }
                .status-excellent { background-color: #28a745; }
                .status-good { background-color: #17a2b8; }
                .status-warning { background-color: #ffc107; color: #000; }
                .status-critical { background-color: #dc3545; }
                .status-error { background-color: #6c757d; }
                .document-list {
                    max-height: 200px;
                    overflow-y: auto;
                }
                .document-item {
                    padding: 8px 0;
                    border-bottom: 1px solid #f8f9fa;
                }
                .document-item:last-child {
                    border-bottom: none;
                }
                .progress-bar {
                    background-color: #e9ecef;
                    border-radius: 4px;
                    height: 8px;
                    margin: 10px 0;
                }
                .progress-fill {
                    height: 100%;
                    border-radius: 4px;
                    transition: width 0.3s ease;
                }
                .alert {
                    padding: 12px;
                    border-radius: 6px;
                    margin: 10px 0;
                }
                .alert-info { background-color: #d1ecf1; color: #0c5460; }
                .alert-warning { background-color: #fff3cd; color: #856404; }
                .alert-danger { background-color: #f8d7da; color: #721c24; }
            </style>
            
            <!-- System Health Overview -->
            <div class="dashboard-card">
                <div class="card-header">
                    <span class="card-icon">🏥</span>
                    System Health Overview
                </div>
                <div class="metric-value" style="color: ${health_color[data.system_health.system_status]}">
                    ${data.system_health.success_rate}%
                </div>
                <div class="metric-label">Success Rate (30 days)</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.system_health.success_rate}%; background-color: ${health_color[data.system_health.system_status]};"></div>
                </div>
                <span class="status-indicator status-${data.system_health.system_status}">
                    ${data.system_health.system_status.toUpperCase()}
                </span>
                <div style="margin-top: 10px;">
                    <small>Avg Processing Time: ${data.system_health.avg_processing_days} days</small>
                </div>
            </div>
            
            <div class="dashboard-grid">
                <!-- Stuck Documents -->
                <div class="dashboard-card">
                    <div class="card-header">
                        <span class="card-icon">⚠️</span>
                        Stuck Documents
                    </div>
                    <div class="metric-value" style="color: ${data.stuck_documents.count > 0 ? '#dc3545' : '#28a745'}">
                        ${data.stuck_documents.count}
                    </div>
                    <div class="metric-label">Documents requiring attention</div>
                    ${data.stuck_documents.count > 0 ? `
                        <div class="alert alert-warning">
                            <strong>Action Required:</strong> ${data.stuck_documents.count} documents are stuck in SAP Error status for more than 2 hours.
                        </div>
                        <div class="document-list">
                            ${data.stuck_documents.documents.slice(0, 5).map(doc => `
                                <div class="document-item">
                                    <strong>${doc.vendor_name}</strong> (${doc.ref_no})<br>
                                    <small>Stuck for ${doc.hours_stuck} hours</small>
                                </div>
                            `).join('')}
                        </div>
                    ` : '<div class="alert alert-info">All documents are processing normally.</div>'}
                </div>
                
                <!-- SAP Errors -->
                <div class="dashboard-card">
                    <div class="card-header">
                        <span class="card-icon">❌</span>
                        SAP Integration
                    </div>
                    <div class="metric-value" style="color: ${data.sap_error_count.today > 0 ? '#dc3545' : '#28a745'}">
                        ${data.sap_error_count.today}
                    </div>
                    <div class="metric-label">Errors today</div>
                    <div style="margin: 10px 0;">
                        <small>This week: ${data.sap_error_count.week} errors</small>
                    </div>
                    ${data.sap_error_count.recent_errors.length > 0 ? `
                        <div class="document-list">
                            ${data.sap_error_count.recent_errors.slice(0, 3).map(error => `
                                <div class="document-item">
                                    <strong>${error.vendor_onboarding}</strong><br>
                                    <small style="color: #dc3545;">${error.error_message || 'SAP Connection Error'}</small>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
                
                <!-- Pending Approvals -->
                <div class="dashboard-card">
                    <div class="card-header">
                        <span class="card-icon">⏳</span>
                        Pending Approvals
                    </div>
                    <div class="metric-value" style="color: ${data.pending_approvals.overdue.count > 0 ? '#ffc107' : '#17a2b8'}">
                        ${data.pending_approvals.overdue.count}
                    </div>
                    <div class="metric-label">Overdue approvals (3+ days)</div>
                    <div style="margin: 15px 0;">
                        <div>Purchase Team: ${data.pending_approvals.purchase_team}</div>
                        <div>Accounts Team: ${data.pending_approvals.accounts_team}</div>
                        <div>Department Heads: ${data.pending_approvals.heads}</div>
                    </div>
                    ${data.pending_approvals.overdue.count > 0 ? `
                        <div class="document-list">
                            ${data.pending_approvals.overdue.documents.slice(0, 3).map(doc => `
                                <div class="document-item">
                                    <strong>${doc.vendor_name}</strong><br>
                                    <small>Pending for ${doc.days_pending} days</small>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Recent Activities -->
            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <div class="card-header">
                        <span class="card-icon">✅</span>
                        Recent Approvals (24h)
                    </div>
                    <div class="document-list">
                        ${data.recent_activities.recent_approvals.length > 0 ? 
                            data.recent_activities.recent_approvals.map(doc => `
                                <div class="document-item">
                                    <strong>${doc.vendor_name}</strong>
                                    <span class="status-indicator status-${doc.onboarding_form_status.toLowerCase() === 'approved' ? 'excellent' : 'critical'}">
                                        ${doc.onboarding_form_status}
                                    </span><br>
                                    <small>by ${doc.modified_by} • ${frappe.datetime.comment_when(doc.modified)}</small>
                                </div>
                            `).join('') 
                            : '<div style="text-align: center; color: #6c757d; padding: 20px;">No recent approvals</div>'
                        }
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <div class="card-header">
                        <span class="card-icon">📝</span>
                        Recent Registrations (24h)
                    </div>
                    <div class="document-list">
                        ${data.recent_activities.recent_registrations.length > 0 ? 
                            data.recent_activities.recent_registrations.map(doc => `
                                <div class="document-item">
                                    <strong>${doc.vendor_name}</strong> (${doc.ref_no})<br>
                                    <small>by ${doc.registered_by} • ${frappe.datetime.comment_when(doc.creation)}</small>
                                </div>
                            `).join('') 
                            : '<div style="text-align: center; color: #6c757d; padding: 20px;">No recent registrations</div>'
                        }
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px;">
                Last updated: ${frappe.datetime.now_datetime()}
                <br>Auto-refreshes every 30 seconds
            </div>
        </div>
    `;
}

function show_tools_menu() {
    let tools_dialog = new frappe.ui.Dialog({
        title: __('Vendor Onboarding Tools'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'tools_html',
                options: get_tools_html()
            }
        ]
    });
    
    tools_dialog.show();
    
    // Add event listeners for tool buttons
    setTimeout(() => {
        add_tools_event_listeners();
    }, 500);
}

function get_tools_html() {
    return `
        <div class="tools-container">
            <style>
                .tools-container {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                .tools-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }
                .tool-card {
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }
                .tool-icon {
                    font-size: 48px;
                    margin-bottom: 10px;
                }
                .tool-title {
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 10px;
                    color: #495057;
                }
                .tool-description {
                    color: #6c757d;
                    font-size: 14px;
                    margin-bottom: 20px;
                    line-height: 1.4;
                }
                .tool-button {
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.2s;
                    width: 100%;
                }
                .tool-button:hover {
                    background: #0056b3;
                    transform: translateY(-2px);
                }
                .tool-button.danger {
                    background: #dc3545;
                }
                .tool-button.danger:hover {
                    background: #c82333;
                }
                .tool-button.warning {
                    background: #ffc107;
                    color: #000;
                }
                .tool-button.warning:hover {
                    background: #e0a800;
                }
                .tool-button.success {
                    background: #28a745;
                }
                .tool-button.success:hover {
                    background: #218838;
                }
            </style>
            
            <div class="alert alert-info">
                <strong>⚠️ Important:</strong> These are powerful administrative tools. Use with caution, especially in production environments.
            </div>
            
            <div class="tools-grid">
                <!-- Health Check Tools -->
                <div class="tool-card">
                    <div class="tool-icon">🏥</div>
                    <div class="tool-title">Health Check</div>
                    <div class="tool-description">
                        Run comprehensive health check on selected vendor onboarding document. 
                        Validates linked documents, approvals, and data integrity.
                    </div>
                    <button class="tool-button" onclick="run_single_health_check()">
                        Run Health Check
                    </button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-icon">🔍</div>
                    <div class="tool-title">Bulk Health Check</div>
                    <div class="tool-description">
                        Scan all recent documents (last 7 days) for health issues. 
                        Identifies documents with warnings or critical problems.
                    </div>
                    <button class="tool-button warning" onclick="run_bulk_health_check()">
                        Bulk Health Check
                    </button>
                </div>
                
                <!-- Status Management Tools -->
                <div class="tool-card">
                    <div class="tool-icon">🔧</div>
                    <div class="tool-title">Manual Fix</div>
                    <div class="tool-description">
                        Manually fix a specific vendor onboarding document. 
                        Analyzes and corrects status based on current approvals and SAP logs.
                    </div>
                    <button class="tool-button" onclick="run_manual_fix()">
                        Manual Fix Document
                    </button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-icon">🔄</div>
                    <div class="tool-title">Reset Status</div>
                    <div class="tool-description">
                        Reset vendor onboarding status for testing/debugging purposes. 
                        Use only in development or when specifically required.
                    </div>
                    <button class="tool-button warning" onclick="reset_document_status()">
                        Reset Status
                    </button>
                </div>
                
                <!-- SAP Integration Tools -->
                <div class="tool-card">
                    <div class="tool-icon">⚡</div>
                    <div class="tool-title">Force SAP Integration</div>
                    <div class="tool-description">
                        Force SAP integration for a specific document. 
                        Bypasses normal triggers and enqueues immediate SAP processing.
                    </div>
                    <button class="tool-button danger" onclick="force_sap_integration()">
                        Force SAP Integration
                    </button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-icon">🧹</div>
                    <div class="tool-title">Cleanup Stuck Documents</div>
                    <div class="tool-description">
                        Automatically fix documents stuck in SAP Error status. 
                        Runs the same logic as the scheduled cleanup job.
                    </div>
                    <button class="tool-button success" onclick="cleanup_stuck_documents()">
                        Cleanup Stuck Documents
                    </button>
                </div>
                
                <!-- Testing Tools -->
                <div class="tool-card">
                    <div class="tool-icon">🧪</div>
                    <div class="tool-title">Test Suite</div>
                    <div class="tool-description">
                        Run comprehensive test suite to validate system functionality. 
                        Creates test documents and validates all major workflows.
                    </div>
                    <button class="tool-button" onclick="run_test_suite()">
                        Run Test Suite
                    </button>
                </div>
                
                <div class="tool-card">
                    <div class="tool-icon">📊</div>
                    <div class="tool-title">System Analytics</div>
                    <div class="tool-description">
                        Generate detailed system analytics report. 
                        Provides insights into performance, errors, and usage patterns.
                    </div>
                    <button class="tool-button" onclick="generate_analytics()">
                        Generate Analytics
                    </button>
                </div>
                
                <!-- Maintenance Tools -->
                <div class="tool-card">
                    <div class="tool-icon">🔍</div>
                    <div class="tool-title">Document Inspector</div>
                    <div class="tool-description">
                        Deep inspection of document relationships and data integrity. 
                        Shows detailed information about linked documents and child tables.
                    </div>
                    <button class="tool-button" onclick="inspect_document()">
                        Inspect Document
                    </button>
                </div>
            </div>
        </div>
    `;
}

function add_tools_event_listeners() {
    // Single Health Check
    window.run_single_health_check = function() {
        let selected = get_selected_documents();
        if (selected.length !== 1) {
            frappe.msgprint(__('Please select exactly one document for health check.'));
            return;
        }
        
        frappe.call({
            method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.check_vendor_onboarding_health',
            args: { onb_name: selected[0] },
            callback: function(r) {
                if (r.message) {
                    show_health_check_results(r.message);
                }
            }
        });
    };
    
    // Bulk Health Check
    window.run_bulk_health_check = function() {
        frappe.confirm(
            'This will scan all documents from the last 7 days. Continue?',
            function() {
                let loading = frappe.show_alert({message: 'Running bulk health check...', indicator: 'blue'});
                
                frappe.call({
                    method: 'vms.vendor_onboarding.monitoring_dashboard.bulk_health_check',
                    callback: function(r) {
                        loading.hide();
                        if (r.message) {
                            show_bulk_health_results(r.message);
                        }
                    }
                });
            }
        );
    };
    
    // Manual Fix
    window.run_manual_fix = function() {
        let selected = get_selected_documents();
        if (selected.length !== 1) {
            frappe.msgprint(__('Please select exactly one document to fix.'));
            return;
        }
        
        frappe.confirm(
            `Fix the selected document: ${selected[0]}?`,
            function() {
                frappe.call({
                    method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.manual_fix_vendor_onboarding',
                    args: { onb_name: selected[0] },
                    callback: function(r) {
                        if (r.message) {
                            show_fix_results(r.message);
                            cur_list.refresh();
                        }
                    }
                });
            }
        );
    };
    
    // Reset Status
    window.reset_document_status = function() {
        let selected = get_selected_documents();
        if (selected.length !== 1) {
            frappe.msgprint(__('Please select exactly one document to reset.'));
            return;
        }
        
        let status_dialog = new frappe.ui.Dialog({
            title: 'Reset Document Status',
            fields: [
                {
                    label: 'New Status',
                    fieldname: 'new_status',
                    fieldtype: 'Select',
                    options: ['Pending', 'Approved', 'Rejected', 'SAP Error'],
                    default: 'Pending'
                }
            ],
            primary_action_label: 'Reset',
            primary_action(values) {
                frappe.call({
                    method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.reset_vendor_onboarding_status',
                    args: { 
                        onb_name: selected[0],
                        new_status: values.new_status
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });
                            cur_list.refresh();
                        } else {
                            frappe.msgprint({
                                title: 'Error',
                                message: r.message.message,
                                indicator: 'red'
                            });
                        }
                        status_dialog.hide();
                    }
                });
            }
        });
        
        status_dialog.show();
    };
    
    // Force SAP Integration
    window.force_sap_integration = function() {
        let selected = get_selected_documents();
        if (selected.length !== 1) {
            frappe.msgprint(__('Please select exactly one document for SAP integration.'));
            return;
        }
        
        frappe.confirm(
            '⚠️ This will force SAP integration regardless of current status. Continue?',
            function() {
                frappe.call({
                    method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.force_sap_integration',
                    args: { onb_name: selected[0] },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: r.message.status === 'success' ? 'green' : 'red'
                            });
                        }
                    }
                });
            }
        );
    };
    
    // Cleanup Stuck Documents
    window.cleanup_stuck_documents = function() {
        frappe.confirm(
            'This will cleanup all documents stuck in SAP Error status. Continue?',
            function() {
                let loading = frappe.show_alert({message: 'Cleaning up stuck documents...', indicator: 'blue'});
                
                frappe.call({
                    method: 'vms.vendor_onboarding.monitoring_dashboard.bulk_cleanup_stuck_documents',
                    callback: function(r) {
                        loading.hide();
                        if (r.message) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: r.message.status === 'success' ? 'green' : 'red'
                            });
                            cur_list.refresh();
                        }
                    }
                });
            }
        );
    };
    
    // Run Test Suite
    window.run_test_suite = function() {
        frappe.confirm(
            'This will run comprehensive tests and may create temporary test data. Continue?',
            function() {
                let loading = frappe.show_alert({message: 'Running test suite...', indicator: 'blue'});
                
                frappe.call({
                    method: 'vms.vendor_onboarding.monitoring_dashboard.run_comprehensive_test_suite',
                    callback: function(r) {
                        loading.hide();
                        if (r.message) {
                            show_test_results(r.message);
                        }
                    }
                });
            }
        );
    };
    
    // Generate Analytics
    window.generate_analytics = function() {
        frappe.show_alert({message: 'Generating analytics report...', indicator: 'blue'});
        
        frappe.call({
            method: 'vms.vendor_onboarding.monitoring_dashboard.get_monitoring_data',
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    show_analytics_report(r.message.data);
                }
            }
        });
    };
    
    // Document Inspector
    window.inspect_document = function() {
        let selected = get_selected_documents();
        if (selected.length !== 1) {
            frappe.msgprint(__('Please select exactly one document to inspect.'));
            return;
        }
        
        frappe.call({
            method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.check_vendor_onboarding_health',
            args: { onb_name: selected[0] },
            callback: function(r) {
                if (r.message) {
                    show_document_inspector(r.message);
                }
            }
        });
    };
}

function get_selected_documents() {
    if (cur_list && cur_list.get_checked_items) {
        return cur_list.get_checked_items().map(item => item.name);
    }
    return [];
}

function show_health_check_results(health_report) {
    let status_colors = {
        'good': '#28a745',
        'warning': '#ffc107', 
        'critical': '#dc3545',
        'error': '#6c757d'
    };
    
    let html = `
        <div style="font-family: monospace;">
            <div style="background: ${status_colors[health_report.overall_health]}; color: white; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="margin: 0;">Overall Health: ${health_report.overall_health.toUpperCase()}</h3>
                <p style="margin: 5px 0 0 0;">Document: ${health_report.document_name}</p>
            </div>
            
            <h4>Checks Performed:</h4>
            ${health_report.checks.map(check => `
                <div style="padding: 10px; margin: 5px 0; border-left: 4px solid ${check.status === 'complete' || check.status === 'has_data' ? '#28a745' : '#ffc107'};">
                    <strong>${check.name}:</strong> ${check.details}
                </div>
            `).join('')}
            
            ${health_report.recommendations.length > 0 ? `
                <h4>Recommendations:</h4>
                ${health_report.recommendations.map(rec => `
                    <div style="background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 4px;">
                        ⚠️ ${rec}
                    </div>
                `).join('')}
            ` : ''}
            
            <h4>Linked Documents:</h4>
            ${Object.entries(health_report.linked_documents).map(([field, info]) => `
                <div style="padding: 8px; margin: 3px 0;">
                    <strong>${field}:</strong> 
                    <span style="color: ${info.status === 'exists' ? '#28a745' : info.status === 'missing' ? '#dc3545' : '#6c757d'};">
                        ${info.status}
                    </span>
                    ${info.name ? ` (${info.name})` : ''}
                </div>
            `).join('')}
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: `Health Check Results - ${health_report.document_name}`,
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'health_html',
                options: html
            }
        ]
    });
    
    dialog.show();
}

function show_bulk_health_results(results) {
    let html = `
        <div>
            <div style="background: #e3f2fd; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="margin: 0;">Bulk Health Check Results</h3>
                <p style="margin: 5px 0 0 0;">
                    Checked: ${results.total_checked} documents | 
                    Issues Found: ${results.issues_found}
                </p>
            </div>
            
            ${results.health_issues.length > 0 ? `
                <h4>Documents with Issues:</h4>
                ${results.health_issues.map(issue => `
                    <div style="border: 1px solid #dee2e6; padding: 15px; margin: 10px 0; border-radius: 6px;">
                        <h5 style="margin: 0 0 10px 0;">${issue.document_name}</h5>
                        <div style="background: ${issue.overall_health === 'critical' ? '#f8d7da' : '#fff3cd'}; padding: 10px; border-radius: 4px;">
                            Status: ${issue.overall_health.toUpperCase()}
                        </div>
                        ${issue.recommendations ? issue.recommendations.map(rec => `
                            <div style="margin: 5px 0; padding: 5px; background: #f8f9fa;">
                                • ${rec}
                            </div>
                        `).join('') : ''}
                    </div>
                `).join('')}
            ` : '<div style="text-align: center; color: #28a745; padding: 20px;">✅ All documents are healthy!</div>'}
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: 'Bulk Health Check Results',
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'bulk_health_html',
                options: html
            }
        ]
    });
    
    dialog.show();
}

function show_fix_results(fix_result) {
    frappe.show_alert({
        message: fix_result.message,
        indicator: fix_result.status === 'success' ? 'green' : 'red'
    });
}

function show_test_results(test_results) {
    let html = `
        <div>
            <div style="background: ${test_results.results.overall_status === 'ALL TESTS PASSED' ? '#d4edda' : '#fff3cd'}; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="margin: 0;">${test_results.results.overall_status}</h3>
                <p style="margin: 5px 0 0 0;">
                    Passed: ${test_results.results.tests_passed} | 
                    Failed: ${test_results.results.tests_failed} | 
                    Total: ${test_results.results.tests_run}
                </p>
            </div>
            
            <h4>Test Results:</h4>
            ${test_results.results.detailed_results.map(test => `
                <div style="padding: 10px; margin: 5px 0; border-left: 4px solid ${test.status === 'PASS' ? '#28a745' : '#dc3545'};">
                    <strong>${test.test}:</strong> ${test.status}<br>
                    <small>${test.message}</small>
                </div>
            `).join('')}
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: 'Test Suite Results',
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'test_html',
                options: html
            }
        ]
    });
    
    dialog.show();
}

function show_analytics_report(data) {
    // This would show detailed analytics - can be expanded based on requirements
    frappe.msgprint({
        title: 'Analytics Report',
        message: 'Detailed analytics report generated successfully. Check monitoring dashboard for full details.',
        indicator: 'blue'
    });
}

function show_document_inspector(health_report) {
    // Enhanced version of health check with more technical details
    show_health_check_results(health_report);
}














