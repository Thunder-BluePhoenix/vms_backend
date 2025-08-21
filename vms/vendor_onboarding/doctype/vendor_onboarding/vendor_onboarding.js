// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Vendor Onboarding", {
// 	refresh(frm) {....&& frm.doc.mandatory_data_filled

// 	},
// });
frappe.ui.form.on('Vendor Onboarding', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && !frm.doc.data_sent_to_sap) {
            frm.add_custom_button(__('Send to SAP'), function() {
                // Show confirmation dialog with details
                frappe.confirm(
                    __('Are you sure you want to send this vendor data to SAP?<br><br><small>This will process all company and GST data for this vendor.</small>'),
                    function() {
                        // User confirmed, proceed with API call
                        send_to_sap_enhanced(frm);
                    }
                );
            }).addClass('btn-primary');
        }

        if (!frm.doc.__islocal && frm.doc.name) {
            render_sap_validation_display(frm);
        }
        
        // Add manual validation button
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Refresh SAP Validation'), function() {
                refresh_sap_validation_display(frm);
            }, __('Actions'));
            
            // Add quick validation status button
            frm.add_custom_button(__('Quick Validation Check'), function() {
                quick_validation_check(frm);
            }, __('Actions'));
            frm.add_custom_button(__('Detailed Validation Report'), function() {
                show_detailed_validation_report(frm);
            }, __('Actions'));
        }
        
        
        // Add validation indicator to form header
        add_validation_indicator(frm);
        
        // Hide the empty HTML field since we're rendering dynamically
        // hide_html_field(frm);
    },
    onload: function(frm) {
        // Listen for real-time updates
        frappe.realtime.on("vendor_onboarding_updated", function(data) {
            if (data.name === frm.doc.name) {
                frm.refresh();
            }
        });
    },
    
    after_save: function(frm) {
        // Re-render validation display after save
        setTimeout(() => {
            render_sap_validation_display(frm);
        }, 500);
        // frm.refresh();
    },
    
    // Trigger re-render when key fields change
    mandatory_data_filled: function(frm) {
        render_sap_validation_display(frm);
    }
});

function send_to_sap_enhanced(frm) {
    // Get reference to the button for disabling during API call
    let btn = $('.btn-primary:contains("Send to SAP")');
    
    frappe.call({
        method: 'vms.APIs.sap.sap.send_vendor_to_sap_via_front',
        args: {
            doc_name: frm.doc.name
        },
        btn: btn, // This disables the button during the call
        freeze: true, // Shows loading overlay
        freeze_message: __('Sending vendor data to SAP...<br><small>This may take a few minutes</small>'), // Custom loading message
        callback: function(r) {
            if (r.message) {
                handle_sap_response(r.message, frm);
            } else {
                // No response received
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('No response received from SAP integration. Please check the logs and try again.')
                });
            }
        },
        error: function(error) {
            // Handle network or server errors
            console.error('SAP API Error:', error);
            
            let error_message = 'Failed to send data to SAP. ';
            
            // Try to extract meaningful error message
            if (error.responseJSON && error.responseJSON.message) {
                error_message += error.responseJSON.message;
            } else if (error.responseText) {
                error_message += 'Server error occurred.';
            } else {
                error_message += 'Network error occurred. Please check your connection and try again.';
            }
            
            frappe.msgprint({
                title: __('Network Error'),
                indicator: 'red',
                message: __(error_message)
            });
        }
    });
}

function handle_sap_response(response, frm) {
    console.log('SAP Response:', response);
    
    const status = response.status;
    const message = response.message;
    const details = response.details || {};
    
    // Extract SAP-specific metrics
    const successful_calls = response.successful_sap_calls || details.successful_sap_calls || 0;
    const failed_calls = response.failed_sap_calls || details.failed_sap_calls || 0;
    const connection_errors = response.connection_errors || details.connection_errors || 0;
    const success_rate = response.success_rate || details.success_rate || 0;
    
    switch (status) {
        case 'success':
            // Complete success - all SAP calls succeeded
            frappe.show_alert({
                message: __('✅ Success: All data sent to SAP successfully'),
                indicator: 'green'
            });
            
            // Show detailed success message
            let success_details = `
                <div style="margin-bottom: 15px;">
                    <strong>✅ SAP Integration Completed Successfully!</strong>
                </div>
                <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>📊 Processing Summary:</strong><br>
                    • Companies Processed: ${details.companies_processed || response.companies_processed || 0}<br>
                    • GST Entries Processed: ${details.gst_rows_processed || response.gst_rows_processed || 0}<br>
                    • Successful SAP Calls: ${successful_calls}<br>
                    • Success Rate: ${success_rate.toFixed(1)}%<br>
                    • Vendor: ${details.vendor_name || 'Unknown'}
                </div>
                <small style="color: #666;">The form will be refreshed to show the updated status.</small>
            `;
            
            frappe.msgprint({
                title: __('SAP Integration Success'),
                indicator: 'green',
                message: success_details
            });
            
            // Refresh the form to show updated status
            setTimeout(() => {
                frm.reload_doc();
            }, 2000);
            
            break;
            
        case 'partial_success':
            // Partial success - some SAP calls succeeded, some failed
            frappe.show_alert({
                message: __('⚠️ Partial Success: Some data sent to SAP'),
                indicator: 'orange'
            });
            
            let partial_details = `
                <div style="margin-bottom: 15px;">
                    <strong>⚠️ SAP Integration Partially Completed</strong>
                </div>
                <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>📊 Processing Summary:</strong><br>
                    • Companies Processed: ${details.companies_processed || response.companies_processed || 0}<br>
                    • GST Entries Processed: ${details.gst_rows_processed || response.gst_rows_processed || 0}<br>
                    • Successful SAP Calls: ${successful_calls}<br>
                    • Failed SAP Calls: ${failed_calls}<br>
                    • Success Rate: ${success_rate.toFixed(1)}%
                </div>
                <div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>⚠️ Issues Found:</strong><br>
                    ${connection_errors > 0 ? `• Connection errors: ${connection_errors} (Check SAP server)<br>` : ''}
                    • Some entries failed to process in SAP<br>
                    • Check the VMS SAP Logs and Error Logs for detailed error information
                </div>
                <small style="color: #666;">The form will be refreshed to show the updated status.</small>
            `;
            
            frappe.msgprint({
                title: __('SAP Integration Partial Success'),
                indicator: 'orange',
                message: partial_details
            });
            
            // Refresh the form
            setTimeout(() => {
                frm.reload_doc();
            }, 2000);
            
            break;
            
        case 'error':
            // Error case - SAP integration failed
            let error_details = `
                <div style="margin-bottom: 15px;">
                    <strong>❌ SAP Integration Failed</strong>
                </div>
                <div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>Error Details:</strong><br>
                    ${message}
                </div>
            `;
            
            // Add specific error information based on error types
            if (connection_errors > 0) {
                error_details += `
                    <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>🔌 Connection Issues Detected:</strong><br>
                        • SAP server appears to be unreachable (${connection_errors} connection errors)<br>
                        • Check if SAP server is running on the configured host/port<br>
                        • Verify network connectivity to SAP server<br>
                        • Contact IT team to check SAP server status
                    </div>
                `;
            } else if (details.error_type === 'validation_error') {
                error_details += `
                    <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>🔍 Data Validation Issues:</strong><br>
                        Please ensure all required fields are completed and conditions are met before trying again.
                    </div>
                `;
            } else if (details.error_type === 'permission_error') {
                error_details += `
                    <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>🔐 Permission Issues:</strong><br>
                        Please contact your system administrator for the required permissions.
                    </div>
                `;
            } else {
                error_details += `
                    <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>🔧 Next Steps:</strong><br>
                        • Check the VMS SAP Logs and Error Logs for detailed information<br>
                        • Verify SAP server connectivity and credentials<br>
                        • Ensure all required vendor data is complete<br>
                        • Contact IT support if the issue persists
                    </div>
                `;
            }
            
            // Add processing summary if any attempts were made
            if (response.companies_processed || response.gst_rows_processed) {
                error_details += `
                    <div style="background-color: #e2e3e5; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>📊 Processing Summary:</strong><br>
                        • Companies Processed: ${response.companies_processed || 0}<br>
                        • GST Entries Processed: ${response.gst_rows_processed || 0}<br>
                        • Successful SAP Calls: ${successful_calls}<br>
                        • Failed SAP Calls: ${failed_calls}<br>
                        ${connection_errors > 0 ? `• Connection Errors: ${connection_errors}<br>` : ''}
                    </div>
                `;
            }
            
            frappe.msgprint({
                title: __('SAP Integration Failed'),
                indicator: 'red',
                message: error_details
            });
            
            break;
            
        case 'warning':
            // Warning case (unexpected response)
            frappe.show_alert({
                message: __('⚠️ Warning: Unexpected response from SAP'),
                indicator: 'orange'
            });
            
            frappe.msgprint({
                title: __('SAP Integration Warning'),
                indicator: 'orange',
                message: `
                    <div style="margin-bottom: 15px;">
                        <strong>⚠️ Unexpected Response</strong>
                    </div>
                    <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        ${message}
                    </div>
                    <small>Please check the logs for more information and contact support if needed.</small>
                `
            });
            
            break;
            
        default:
            // Unknown status
            frappe.msgprint({
                title: __('Unknown Response'),
                indicator: 'red',
                message: __('Received unknown response status from SAP integration. Please check the logs.')
            });
    }
}

function render_sap_validation_display(frm) {
    if (!frm.doc.name || frm.doc.__islocal) return;
    
    // Get validation data from backend
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_onboarding.onboarding_sap_validation.get_complete_validation_data',
        args: {
            onb_ref: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                // Generate and inject comprehensive HTML
                inject_comprehensive_validation_html(frm, r.message.validation_data);
                
                // Update form indicators
                update_validation_indicator(frm, r.message.validation_data.validation_passed);
            } else {
                console.error('Failed to get validation data:', r.message);
                inject_error_html(frm, r.message ? r.message.message : 'Unknown error');
            }
        }
    });
}

// Function to inject HTML at the correct position (with or above sap_validation_html field)
function inject_comprehensive_validation_html(frm, validation_data) {
    // Remove any existing validation display
    frm.page.wrapper.find('.sap-validation-container').remove();
    
    let html_content = validation_data.validation_passed ? 
        generate_comprehensive_success_html(validation_data) : 
        generate_comprehensive_error_html(validation_data);
    
    // Find the correct position - prioritize sap_validation_html field, fallback to mandatory_data_for_sap
    let target_field = frm.get_field('sap_validation_html') || frm.get_field('mandatory_data_for_sap');
    
    if (target_field && target_field.$wrapper) {
        // Position above the target field
        target_field.$wrapper.before(html_content);
    } else {
        // Fallback: add to form body
        frm.fields_dict.purchasing_data_tab ? 
            frm.fields_dict.purchasing_data_tab.$wrapper.append(html_content) :
            frm.page.body.append(html_content);
    }
    
    // Add all interactive elements
    add_comprehensive_validation_interactions(frm, validation_data);
}

// Generate comprehensive success HTML
function generate_comprehensive_success_html(validation_data) {
    return `
        <div class="sap-validation-container" style="margin: 20px 0;">
            <div style="border: 2px solid #10b981; border-radius: 12px; padding: 24px; background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.15);">
                
                <!-- Header Section -->
                <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #d1fae5;">
                    <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 32px; box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);">
                        ✓
                    </div>
                    <div style="flex: 1;">
                        <h2 style="margin: 0; color: #065f46; font-size: 24px; font-weight: 700;">✅ SAP Validation Successful</h2>
                        <p style="margin: 8px 0 0 0; color: #047857; font-size: 16px;">All mandatory data validated and ready for SAP integration</p>
                        <div style="margin-top: 12px; display: flex; gap: 12px; flex-wrap: wrap;">
                            <span style="background: #dcfce7; color: #166534; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                                🚀 Ready for SAP Integration
                            </span>
                            <span style="background: #e0e7ff; color: #4338ca; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                                ${validation_data.companies_count} Companies Processed
                            </span>
                            <span style="background: #fef3c7; color: #d97706; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                                ${validation_data.vendor_type} Vendor
                            </span>
                        </div>
                        <div style="margin-top: 8px; color: #6b7280; font-size: 12px;">
                            Last validated: ${new Date(validation_data.timestamp).toLocaleString()}
                        </div>
                    </div>
                </div>
                
                <!-- Success Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px;">
                    <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #d1fae5; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 48px; height: 48px; background: #dbeafe; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                <svg width="24" height="24" fill="none" stroke="#2563eb" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                            </div>
                            <h4 style="margin: 0; color: #065f46; font-size: 16px; font-weight: 600;">Validation Status</h4>
                        </div>
                        <div style="color: #047857; font-size: 14px; line-height: 1.5;">
                            ✅ All mandatory fields complete<br>
                            ✅ Banking details verified<br>
                            ✅ Document references valid
                        </div>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #d1fae5; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 48px; height: 48px; background: #dcfce7; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                <svg width="24" height="24" fill="none" stroke="#16a34a" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                                </svg>
                            </div>
                            <h4 style="margin: 0; color: #065f46; font-size: 16px; font-weight: 600;">Data Summary</h4>
                        </div>
                        <div style="color: #047857; font-size: 14px; line-height: 1.5;">
                            <strong>Vendor Type:</strong> ${validation_data.vendor_type}<br>
                            <strong>Companies:</strong> ${validation_data.companies_count} processed<br>
                            <strong>Fields Validated:</strong> ${validation_data.total_fields_validated || 'All required'} fields
                        </div>
                    </div>
                </div>
                
                <!-- Next Steps -->
                <div style="background: #f8fafc; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb;">
                    <h4 style="margin: 0 0 12px 0; color: #374151; font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                        🎯 Next Steps
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
                        <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: white; border-radius: 8px;">
                            <span style="width: 32px; height: 32px; background: #3b82f6; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600;">1</span>
                            <span style="font-size: 14px; color: #374151;">Data ready for SAP transmission</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: white; border-radius: 8px;">
                            <span style="width: 32px; height: 32px; background: #3b82f6; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600;">2</span>
                            <span style="font-size: 14px; color: #374151;">Proceed with onboarding workflow</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: white; border-radius: 8px;">
                            <span style="width: 32px; height: 32px; background: #3b82f6; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600;">3</span>
                            <span style="font-size: 14px; color: #374151;">Monitor SAP integration status</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Generate comprehensive error HTML with ALL validation data
function generate_comprehensive_error_html(validation_data) {
    // Parse and categorize ALL missing fields
    let field_categories = categorize_missing_fields(validation_data.missing_fields_summary);
    let total_errors = validation_data.total_missing_count || 0;
    
    // Generate category sections
    let categories_html = '';
    Object.keys(field_categories).forEach(category => {
        if (field_categories[category].length > 0) {
            categories_html += generate_field_category_html(category, field_categories[category]);
        }
    });
    
    return `
        <div class="sap-validation-container" style="margin: 20px 0;">
            <div style="border: 2px solid #ef4444; border-radius: 12px; padding: 24px; background: linear-gradient(135deg, #fef2f2 0%, #fef2f2 100%); box-shadow: 0 8px 25px rgba(239, 68, 68, 0.15);">
                
                <!-- Header Section -->
                <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #fecaca;">
                    <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 32px; box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3);">
                        !
                    </div>
                    <div style="flex: 1;">
                        <h2 style="margin: 0; color: #991b1b; font-size: 24px; font-weight: 700;">❌ SAP Validation Failed</h2>
                        <p style="margin: 8px 0 0 0; color: #dc2626; font-size: 16px;">${total_errors} mandatory fields require immediate attention</p>
                        <div style="margin-top: 12px; display: flex; gap: 12px; flex-wrap: wrap;">
                            <span style="background: #fee2e2; color: #991b1b; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                                🔧 Action Required
                            </span>
                            <span style="background: #fef3c7; color: #d97706; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                                ${validation_data.companies_count} Companies
                            </span>
                            <span style="background: #e0e7ff; color: #4338ca; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                                ${validation_data.vendor_type} Vendor
                            </span>
                        </div>
                        <div style="margin-top: 8px; color: #6b7280; font-size: 12px;">
                            Last validation: ${new Date(validation_data.timestamp).toLocaleString()}
                        </div>
                    </div>
                </div>
                
                <!-- Error Summary Metrics -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
                    <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #fecaca; text-align: center;">
                        <div style="width: 48px; height: 48px; background: #fee2e2; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px;">
                            <svg width="24" height="24" fill="none" stroke="#dc2626" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z"></path>
                            </svg>
                        </div>
                        <div style="font-size: 13px; color: #991b1b; margin-bottom: 4px; font-weight: 600;">Total Errors</div>
                        <div style="font-weight: 700; color: #dc2626; font-size: 20px;">${total_errors}</div>
                    </div>
                    
                    <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #fecaca; text-align: center;">
                        <div style="width: 48px; height: 48px; background: #fee2e2; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px;">
                            <svg width="24" height="24" fill="none" stroke="#dc2626" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                            </svg>
                        </div>
                        <div style="font-size: 13px; color: #991b1b; margin-bottom: 4px; font-weight: 600;">Categories</div>
                        <div style="font-weight: 700; color: #dc2626; font-size: 20px;">${Object.keys(field_categories).filter(cat => field_categories[cat].length > 0).length}</div>
                    </div>
                    
                    <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #fecaca; text-align: center;">
                        <div style="width: 48px; height: 48px; background: #fee2e2; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px;">
                            <svg width="24" height="24" fill="none" stroke="#dc2626" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <div style="font-size: 13px; color: #991b1b; margin-bottom: 4px; font-weight: 600;">Priority</div>
                        <div style="font-weight: 700; color: #dc2626; font-size: 16px;">High</div>
                    </div>
                </div>
                
                <!-- Comprehensive Missing Fields by Category -->
                <div style="margin-bottom: 24px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h3 style="margin: 0; color: #991b1b; font-size: 18px; font-weight: 700;">
                            🔍 Missing Required Fields (${total_errors} total)
                        </h3>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-xs btn-secondary sap-collapse-all" style="font-size: 11px;">
                                Collapse All
                            </button>
                            <button class="btn btn-xs btn-secondary sap-expand-all" style="font-size: 11px;">
                                Expand All
                            </button>
                        </div>
                    </div>
                    
                    <div class="sap-categories-container">
                        ${categories_html}
                    </div>
                </div>
                
                <!-- Resolution Steps -->
                <div style="background: #f8fafc; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb;">
                    <h4 style="margin: 0 0 16px 0; color: #374151; font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                        🛠️ Resolution Guide
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                        <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                                <span style="width: 28px; height: 28px; background: #3b82f6; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;">1</span>
                                <h5 style="margin: 0; color: #374151; font-size: 14px; font-weight: 600;">Complete Missing Fields</h5>
                            </div>
                            <p style="margin: 0; font-size: 12px; color: #6b7280; line-height: 1.4;">
                                Navigate to each source document and fill in the required fields. Use the doctype references above to locate each field.
                            </p>
                        </div>
                        
                        <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #10b981;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                                <span style="width: 28px; height: 28px; background: #10b981; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;">2</span>
                                <h5 style="margin: 0; color: #374151; font-size: 14px; font-weight: 600;">Verify Banking Details</h5>
                            </div>
                            <p style="margin: 0; font-size: 12px; color: #6b7280; line-height: 1.4;">
                                Ensure all banking information is complete and accurate. For international vendors, check both beneficiary and intermediate bank details.
                            </p>
                        </div>
                        
                        <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                                <span style="width: 28px; height: 28px; background: #f59e0b; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;">3</span>
                                <h5 style="margin: 0; color: #374151; font-size: 14px; font-weight: 600;">Save & Re-validate</h5>
                            </div>
                            <p style="margin: 0; font-size: 12px; color: #6b7280; line-height: 1.4;">
                                Save this document to trigger automatic re-validation. The display will update when all requirements are met.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Function to categorize missing fields into logical groups
function categorize_missing_fields(missing_fields_list) {
    let categories = {
        "Company & Organization": [],
        "Vendor Master Data": [],
        "Address & Contact Information": [],
        "Banking & Payment Details": [],
        "International Banking": [],
        "Tax & Legal Information": [],
        "Purchase & Account Settings": [],
        "Other SAP Fields": []
    };
    
    // Field categorization mapping with more comprehensive coverage
    let field_category_map = {
        // Company & Organization
        "company code": "Company & Organization",
        "company master": "Company & Organization",
        "purchase organization": "Company & Organization",
        "purchase group": "Company & Organization",
        
        // Vendor Master Data
        "vendor name": "Vendor Master Data",
        "vendor master": "Vendor Master Data",
        "mobile number": "Vendor Master Data",
        "search term": "Vendor Master Data",
        "vendor type": "Vendor Master Data",
        
        // Address & Contact
        "address": "Address & Contact Information",
        "city": "Address & Contact Information",
        "state": "Address & Contact Information",
        "pincode": "Address & Contact Information",
        "pin code": "Address & Contact Information",
        "country": "Address & Contact Information",
        "email": "Address & Contact Information",
        "telephone": "Address & Contact Information",
        "contact": "Address & Contact Information",
        
        // Banking & Payment Details
        "bank": "Banking & Payment Details",
        "ifsc": "Banking & Payment Details",
        "account number": "Banking & Payment Details",
        "account holder": "Banking & Payment Details",
        "payment details": "Banking & Payment Details",
        "currency": "Banking & Payment Details",
        
        // International Banking
        "beneficiary": "International Banking",
        "intermediate": "International Banking",
        "swift": "International Banking",
        "iban": "International Banking",
        "international bank": "International Banking",
        
        // Tax & Legal
        "gst": "Tax & Legal Information",
        "pan": "Tax & Legal Information",
        "tax": "Tax & Legal Information",
        
        // Purchase & Account Settings
        "reconciliation": "Purchase & Account Settings",
        "account group": "Purchase & Account Settings",
        "terms of payment": "Purchase & Account Settings",
        "incoterm": "Purchase & Account Settings"
    };
    
    // Categorize each missing field
    missing_fields_list.forEach(field => {
        if (!field || !field.trim()) return;
        
        let category = "Other SAP Fields";
        let field_lower = field.toLowerCase();
        
        // Find the best matching category
        for (let keyword in field_category_map) {
            if (field_lower.includes(keyword)) {
                category = field_category_map[keyword];
                break;
            }
        }
        
        categories[category].push(field);
    });
    
    return categories;
}

// Generate HTML for a specific field category
function generate_field_category_html(category, fields) {
    let categoryId = category.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
    let categoryColors = {
        "Company & Organization": { bg: "#dbeafe", border: "#2563eb", text: "#1e40af" },
        "Vendor Master Data": { bg: "#dcfce7", border: "#16a34a", text: "#15803d" },
        "Address & Contact Information": { bg: "#fef3c7", border: "#d97706", text: "#b45309" },
        "Banking & Payment Details": { bg: "#fee2e2", border: "#dc2626", text: "#b91c1c" },
        "International Banking": { bg: "#fce7f3", border: "#be185d", text: "#a21caf" },
        "Tax & Legal Information": { bg: "#e0e7ff", border: "#4f46e5", text: "#4338ca" },
        "Purchase & Account Settings": { bg: "#f3e8ff", border: "#7c3aed", text: "#6d28d9" },
        "Other SAP Fields": { bg: "#f1f5f9", border: "#64748b", text: "#475569" }
    };
    
    let colors = categoryColors[category] || categoryColors["Other SAP Fields"];
    
    return `
        <div class="sap-category-section" data-category="${categoryId}" style="margin-bottom: 16px; border: 1px solid ${colors.border}; border-radius: 8px; overflow: hidden;">
            <div class="sap-category-header" style="background: ${colors.bg}; padding: 12px 16px; cursor: pointer; display: flex; justify-content: space-between; align-items: center;" onclick="toggleCategory('${categoryId}')">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="width: 24px; height: 24px; background: ${colors.border}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;">
                        ${fields.length}
                    </span>
                    <h4 style="margin: 0; color: ${colors.text}; font-size: 14px; font-weight: 600;">${category}</h4>
                </div>
                <svg class="sap-category-arrow" width="16" height="16" fill="none" stroke="${colors.text}" viewBox="0 0 24 24" style="transition: transform 0.2s;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </div>
            <div class="sap-category-content" data-category-content="${categoryId}" style="background: white;">
                ${generateFieldItemsHtml(fields, colors)}
            </div>
        </div>
    `;
}

// Generate HTML for individual field items within a category
function generateFieldItemsHtml(fields, colors) {
    return fields.map(field => {
        let fieldName = field.split("(")[0].trim();
        let doctype = field.includes("(") ? field.split("(")[1].replace(")", "").trim() : "";
        
        return `
            <div class="sap-field-item" style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#f8fafc'" onmouseout="this.style.backgroundColor='white'">
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: #111827; font-size: 13px; margin-bottom: 2px;">${fieldName}</div>
                    ${doctype ? `
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 11px; color: #6b7280;">Source:</span>
                            <span style="background: ${colors.bg}; color: ${colors.text}; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 500;">${doctype}</span>
                        </div>
                    ` : ''}
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: 600;">
                        Required
                    </span>
                    ${doctype ? `
                        <button class="btn btn-xs btn-outline-primary sap-navigate-field" data-doctype="${doctype}" style="font-size: 10px; padding: 2px 8px;" onclick="navigateToDoctype('${doctype}')">
                            Go to
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('') + (fields.length === 0 ? '<div style="padding: 16px; text-align: center; color: #6b7280; font-style: italic;">No fields in this category</div>' : '');
}

// Position validation display correctly
function position_validation_display(frm) {
    // Ensure the validation display appears in the right location
    setTimeout(() => {
        let html_field = frm.get_field('sap_validation_html');
        if (html_field && html_field.$wrapper) {
            // Hide the actual HTML field label and content since we're rendering above it
            html_field.$wrapper.find('.control-label').hide();
            html_field.$wrapper.find('.control-input').hide();
        }
    }, 100);
}

// Enhanced interactive elements
function add_comprehensive_validation_interactions(frm, validation_data) {
    // Add global functions for category interactions
    window.toggleCategory = function(categoryId) {
        let content = document.querySelector(`[data-category-content="${categoryId}"]`);
        let arrow = document.querySelector(`[data-category="${categoryId}"] .sap-category-arrow`);
        
        if (content && arrow) {
            if (content.style.display === 'none') {
                content.style.display = 'block';
                arrow.style.transform = 'rotate(0deg)';
            } else {
                content.style.display = 'none';
                arrow.style.transform = 'rotate(-90deg)';
            }
        }
    };
    
    window.navigateToDoctype = function(doctype) {
        frappe.set_route('List', doctype);
    };
    
    // Collapse/Expand all functionality
    frm.page.wrapper.find('.sap-collapse-all').off('click').on('click', function() {
        frm.page.wrapper.find('.sap-category-content').hide();
        frm.page.wrapper.find('.sap-category-arrow').css('transform', 'rotate(-90deg)');
    });
    
    frm.page.wrapper.find('.sap-expand-all').off('click').on('click', function() {
        frm.page.wrapper.find('.sap-category-content').show();
        frm.page.wrapper.find('.sap-category-arrow').css('transform', 'rotate(0deg)');
    });
    
    // Detailed validation report
    window.show_detailed_validation_report = function(frm) {
        let html = generate_detailed_report_html(validation_data);
        
        let dialog = new frappe.ui.Dialog({
            title: __('Detailed SAP Validation Report'),
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'report_html',
                    options: html
                }
            ],
            primary_action_label: validation_data.validation_passed ? __('Close') : __('Fix Issues'),
            primary_action: function() {
                dialog.hide();
                if (!validation_data.validation_passed) {
                    // Scroll to validation section
                    scroll_to_validation_section(frm);
                }
            }
        });
        
        dialog.show();
    };
}

// Generate detailed report HTML for dialog
function generate_detailed_report_html(validation_data) {
    if (validation_data.validation_passed) {
        return `
            <div style="text-align: center; padding: 40px;">
                <div style="width: 80px; height: 80px; background: #10b981; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; color: white; font-size: 32px;">✓</div>
                <h2 style="color: #065f46; margin-bottom: 16px;">SAP Validation Complete</h2>
                <p style="color: #047857; font-size: 16px; margin-bottom: 24px;">All ${validation_data.total_fields_validated || 'required'} fields have been validated successfully.</p>
                <div style="background: #f0fdf4; border: 1px solid #d1fae5; border-radius: 8px; padding: 20px;">
                    <h4 style="color: #065f46; margin-bottom: 12px;">Validation Summary</h4>
                    <div style="text-align: left; color: #047857;">
                        <p><strong>Vendor Type:</strong> ${validation_data.vendor_type}</p>
                        <p><strong>Companies Processed:</strong> ${validation_data.companies_count}</p>
                        <p><strong>Banking Validation:</strong> ✅ Passed</p>
                        <p><strong>Status:</strong> Ready for SAP Integration</p>
                    </div>
                </div>
            </div>
        `;
    } else {
        let field_categories = categorize_missing_fields(validation_data.missing_fields_summary);
        let categories_html = '';
        
        Object.keys(field_categories).forEach(category => {
            if (field_categories[category].length > 0) {
                categories_html += `
                    <div style="margin-bottom: 20px;">
                        <h4 style="color: #991b1b; margin-bottom: 8px; font-size: 14px;">${category} (${field_categories[category].length} fields)</h4>
                        <div style="background: white; border-radius: 6px; border: 1px solid #fecaca;">
                            ${field_categories[category].map(field => {
                                let fieldName = field.split("(")[0].trim();
                                let doctype = field.includes("(") ? field.split("(")[1].replace(")", "").trim() : "";
                                return `
                                    <div style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <div style="font-weight: 500; font-size: 12px;">${fieldName}</div>
                                            ${doctype ? `<div style="font-size: 10px; color: #6b7280;">Source: ${doctype}</div>` : ''}
                                        </div>
                                        <span style="background: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 8px; font-size: 9px;">Required</span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            }
        });
        
        return `
            <div style="padding: 20px;">
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="width: 60px; height: 60px; background: #ef4444; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; color: white; font-size: 24px;">!</div>
                    <h2 style="color: #991b1b; margin-bottom: 8px;">SAP Validation Report</h2>
                    <p style="color: #dc2626;">${validation_data.total_missing_count} fields require attention across ${Object.keys(field_categories).filter(cat => field_categories[cat].length > 0).length} categories</p>
                </div>
                
                <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                    <h4 style="color: #991b1b; margin-bottom: 12px;">Summary</h4>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; font-size: 13px;">
                        <div><strong>Vendor Type:</strong> ${validation_data.vendor_type}</div>
                        <div><strong>Companies:</strong> ${validation_data.companies_count}</div>
                        <div><strong>Total Errors:</strong> ${validation_data.total_missing_count}</div>
                        <div><strong>Categories:</strong> ${Object.keys(field_categories).filter(cat => field_categories[cat].length > 0).length}</div>
                    </div>
                </div>
                
                <h3 style="color: #991b1b; margin-bottom: 16px; font-size: 16px;">Missing Fields by Category</h3>
                ${categories_html}
            </div>
        `;
    }
}

// Function to refresh validation with loading state
function refresh_sap_validation_display(frm) {
    // Show loading state
    frm.page.wrapper.find('.sap-validation-container').remove();
    
    let loading_html = `
        <div class="sap-validation-container" style="margin: 20px 0;">
            <div style="border: 2px solid #3b82f6; border-radius: 12px; padding: 24px; background: #eff6ff; text-align: center;">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem; margin-bottom: 16px;"></div>
                <h3 style="color: #1d4ed8; margin-bottom: 8px;">Refreshing SAP Validation</h3>
                <p style="margin: 0; color: #3730a3;">Please wait while we validate all mandatory fields...</p>
            </div>
        </div>
    `;
    
    // Position at correct location
    let target_field = frm.get_field('sap_validation_html') || frm.get_field('mandatory_data_for_sap');
    if (target_field && target_field.$wrapper) {
        target_field.$wrapper.before(loading_html);
    }
    
    // Re-render after validation
    setTimeout(() => {
        render_sap_validation_display(frm);
        frappe.show_alert({
            message: __('SAP validation refreshed'),
            indicator: 'blue'
        }, 3);
    }, 1500);
}

// Helper function to scroll to validation section
function scroll_to_validation_section(frm) {
    let validation_container = frm.page.wrapper.find('.sap-validation-container');
    if (validation_container.length > 0) {
        validation_container[0].scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
        
        // Add highlight effect
        validation_container.animate({
            backgroundColor: '#fef3c7'
        }, 500).animate({
            backgroundColor: 'transparent'
        }, 1000);
    }
}

// Add validation indicator to form header
function add_validation_indicator(frm) {
    if (frm.doc.mandatory_data_filled === 1) {
        frm.page.set_indicator(__('SAP Ready'), 'green');
    } else if (frm.doc.mandatory_data_filled === 0) {
        frm.page.set_indicator(__('SAP Validation Pending'), 'red');
    }
}

// Update validation indicator
function update_validation_indicator(frm, validation_status) {
    frm.page.clear_indicator();
    
    if (validation_status) {
        frm.page.set_indicator(__('SAP Ready'), 'green');
        frappe.show_alert({
            message: __('✅ SAP validation successful'),
            indicator: 'green'
        }, 3);
    } else {
        frm.page.set_indicator(__('SAP Validation Failed'), 'red');
        frappe.show_alert({
            message: __('❌ SAP validation failed - check details below'),
            indicator: 'red'
        }, 4);
    }
}

// Auto-trigger validation on key field changes
frappe.ui.form.on('Vendor Onboarding', {
    ref_no: function(frm) {
        if (!frm.doc.__islocal) {
            setTimeout(() => render_sap_validation_display(frm), 1000);
        }
    },
    
    payment_detail: function(frm) {
        if (!frm.doc.__islocal) {
            setTimeout(() => render_sap_validation_display(frm), 1000);
        }
    },
    
    purchase_organization: function(frm) {
        if (!frm.doc.__islocal) {
            setTimeout(() => render_sap_validation_display(frm), 1000);
        }
    },
    
    account_group: function(frm) {
        if (!frm.doc.__islocal) {
            setTimeout(() => render_sap_validation_display(frm), 1000);
        }
    }
});

// Debug function for console
window.debug_sap_validation = function(frm) {
    console.log('Current form doc:', frm.doc);
    console.log('Mandatory data filled:', frm.doc.mandatory_data_filled);
    render_sap_validation_display(frm);
};





















// Quick validation check without updating HTML
function quick_validation_check(frm) {
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_onboarding.onboarding_sap_validation.get_validation_summary',
        args: {
            onb_ref: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                show_validation_summary_dialog(r.message.summary);
            }
        }
    });
}

// Show validation summary in a dialog
function show_validation_summary_dialog(summary) {
    let html = `
        <div style="padding: 20px;">
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                <div style="width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; ${summary.validation_passed ? 'background: #10b981; color: white;' : 'background: #ef4444; color: white;'}">
                    ${summary.validation_passed ? '✓' : '!'}
                </div>
                <div>
                    <h3 style="margin: 0; color: ${summary.validation_passed ? '#065f46' : '#991b1b'};">
                        ${summary.validation_passed ? 'Validation Successful' : 'Validation Failed'}
                    </h3>
                    <p style="margin: 5px 0 0 0; color: #6b7280;">
                        ${summary.validation_passed ? 'Ready for SAP integration' : `${summary.error_count} fields need attention`}
                    </p>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 8px;">
                    <div style="font-size: 12px; color: #6b7280; margin-bottom: 5px;">Vendor Type</div>
                    <div style="font-weight: 600; color: #374151;">${summary.vendor_type}</div>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 8px;">
                    <div style="font-size: 12px; color: #6b7280; margin-bottom: 5px;">Companies</div>
                    <div style="font-weight: 600; color: #374151;">${summary.companies_count}</div>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 8px;">
                    <div style="font-size: 12px; color: #6b7280; margin-bottom: 5px;">Status</div>
                    <div style="font-weight: 600; color: ${summary.validation_passed ? '#065f46' : '#991b1b'};">
                        ${summary.validation_passed ? 'Ready' : `${summary.error_count} errors`}
                    </div>
                </div>
            </div>
    `;
    
    if (!summary.validation_passed && summary.missing_fields.length > 0) {
        html += `
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #991b1b; font-size: 14px;">Top Missing Fields:</h4>
                <ul style="margin: 0; padding-left: 20px; color: #7f1d1d;">
        `;
        
        summary.missing_fields.forEach(field => {
            let fieldName = field.split('(')[0].trim();
            html += `<li style="margin-bottom: 5px; font-size: 13px;">${fieldName}</li>`;
        });
        
        html += `
                </ul>
                <p style="margin: 10px 0 0 0; font-size: 12px; color: #991b1b; font-style: italic;">
                    Check "Mandatory Data For SAP" field for complete details
                </p>
            </div>
        `;
    }
    
    html += '</div>';
    
    let dialog = new frappe.ui.Dialog({
        title: __('SAP Validation Summary'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'summary_html',
                options: html
            }
        ],
        primary_action_label: summary.validation_passed ? __('Close') : __('Fix Issues'),
        primary_action: function() {
            dialog.hide();
            if (!summary.validation_passed) {
                // Scroll to validation section
                scroll_to_validation(cur_frm);
            }
        }
    });
    
    dialog.show();
}


// Scroll to validation section
function scroll_to_validation(frm) {
    let validation_field = frm.get_field('sap_validation_html');
    if (validation_field && validation_field.$wrapper && validation_field.$wrapper[0]) {
        validation_field.$wrapper[0].scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
        
        // Add a subtle highlight effect
        validation_field.$wrapper.animate({
            backgroundColor: '#fef3c7'
        }, 500).animate({
            backgroundColor: 'transparent'
        }, 1000);
    }
}