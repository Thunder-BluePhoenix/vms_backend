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

        if (!frm.is_new()) {
            // Add Tools dropdown menu
            add_tools_buttons(frm);
            
            // Add status indicators
            add_status_indicators(frm);
            
            // Add real-time status updates
            setup_realtime_updates(frm);
        }
        
        
        // Add validation indicator to form header
        add_validation_indicator(frm);
        
        // Hide the empty HTML field since we're rendering dynamically
        // hide_html_field(frm);
    },
    onload: function(frm) {
        // Listen for real-time updates
        setup_field_properties(frm);
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
    onboarding_form_status: function(frm) {
        // Update form styling based on status
        update_form_styling(frm);
        add_status_indicators(frm);
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


// vendor_onboarding.js - Fixed version with proper error handling
// Place this file in: vms/vendor_onboarding/doctype/vendor_onboarding/vendor_onboarding.js

// frappe.ui.form.on('Vendor Onboarding', {
//     refresh: function(frm) {
//         if (!frm.is_new()) {
//             // Add Tools dropdown menu
//             add_tools_buttons(frm);
            
//             // Add status indicators
//             add_status_indicators(frm);
            
//             // Add real-time status updates
//             setup_realtime_updates(frm);
//         }
//     },
    
//     onload: function(frm) {
//         // Set field properties and validations
//         setup_field_properties(frm);
//     },
    
//     onboarding_form_status: function(frm) {
//         // Update form styling based on status
//         update_form_styling(frm);
        
//         // Update status indicator (this will replace the old one)
//         add_status_indicators(frm);
//     }
// });

function add_tools_buttons(frm) {
    // Health Check - What it does: Analyzes document completeness, linked documents, approvals, and SAP status
    frm.add_custom_button(__('Health Check'), function() {
        run_health_check(frm);
    }, __('Tools'));
    
    // Manual Fix - What it does: Automatically corrects status based on approvals and SAP logs
    frm.add_custom_button(__('Manual Fix'), function() {
        run_manual_fix(frm);
    }, __('Tools'));
    
    // Document Inspector - What it does: Shows detailed technical information about the document
    frm.add_custom_button(__('Document Inspector'), function() {
        show_document_inspector(frm);
    }, __('Tools'));
    
    // Force SAP Integration - What it does: Manually triggers SAP integration bypassing normal conditions
    if (frm.doc.onboarding_form_status === 'SAP Error' || 
        (frm.doc.purchase_team_undertaking && frm.doc.accounts_team_undertaking && 
         frm.doc.purchase_head_undertaking && frm.doc.accounts_head_undertaking)) {
        frm.add_custom_button(__('Force SAP Integration'), function() {
            force_sap_integration(frm);
        }, __('Tools'));
    }
    
    // View SAP Logs - What it does: Opens filtered list of SAP logs for this document
    frm.add_custom_button(__('View SAP Logs'), function() {
        view_sap_logs(frm);
    }, __('Tools'));
    
    // Reset Status (only for development/testing) - What it does: Resets document status for testing
    if (frappe.boot.developer_mode) {
        frm.add_custom_button(__('Reset Status'), function() {
            reset_status(frm);
        }, __('Tools'));
    }
}

function add_status_indicators(frm) {
    if (frm.doc.onboarding_form_status) {
        let status_field = frm.get_field('onboarding_form_status');
        if (status_field && status_field.$wrapper) {
            // Remove any existing status indicators first
            status_field.$wrapper.find('.status-indicator-wrapper').remove();
            
            // Add new status indicator
            let status_html = get_status_indicator_html(frm.doc.onboarding_form_status);
            status_field.$wrapper.append(status_html);
        }
    }
}

function setup_realtime_updates(frm) {
    frappe.realtime.on('vendor_onboarding_update', function(data) {
        if (data.name === frm.doc.name) {
            frappe.show_alert({
                message: `Document updated: ${data.message}`,
                indicator: 'blue'
            });
            frm.reload_doc();
        }
    });
    
    frappe.realtime.on('sap_integration_update', function(data) {
        if (data.vendor_onboarding === frm.doc.name) {
            frappe.show_alert({
                message: `SAP Integration: ${data.status}`,
                indicator: data.status === 'success' ? 'green' : 'red'
            });
            frm.reload_doc();
        }
    });
}

function setup_field_properties(frm) {
    frm.set_df_property('onboarding_form_status', 'description', 
        'Current status of the onboarding process. Updated automatically based on approvals.');
        
    frm.set_df_property('data_sent_to_sap', 'description',
        'Indicates whether data has been successfully sent to SAP system.');
}

function update_form_styling(frm) {
    let status = frm.doc.onboarding_form_status;
    let colors = {
        'Pending': '#ffc107',
        'Approved': '#28a745',
        'Rejected': '#dc3545',
        'SAP Error': '#fd7e14',
        'Processing': '#17a2b8'
    };
    
    if (colors[status]) {
        frm.page.set_indicator(status, colors[status].replace('#', ''));
    }
}

function run_health_check(frm) {
    let loading = frappe.show_alert({
        message: 'Running health check...',
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.check_vendor_onboarding_health',
        args: {
            onb_name: frm.doc.name
        },
        callback: function(r) {
            loading.hide();
            if (r.message) {
                show_health_check_dialog(r.message);
            } else {
                frappe.msgprint('No health check data received');
            }
        },
        error: function(err) {
            loading.hide();
            frappe.msgprint({
                title: 'Error',
                message: 'Failed to run health check: ' + (err.message || 'Unknown error'),
                indicator: 'red'
            });
        }
    });
}

function run_manual_fix(frm) {
    frappe.confirm(
        `This will analyze and fix any issues with document <strong>${frm.doc.name}</strong>. Continue?`,
        function() {
            let loading = frappe.show_alert({
                message: 'Running manual fix...',
                indicator: 'orange'
            });
            
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.manual_fix_vendor_onboarding',
                args: {
                    onb_name: frm.doc.name
                },
                callback: function(r) {
                    loading.hide();
                    if (r.message) {
                        show_fix_result_dialog(r.message);
                        if (r.message.status === 'success') {
                            frm.reload_doc();
                        }
                    } else {
                        frappe.msgprint('No response received from manual fix');
                    }
                },
                error: function(err) {
                    loading.hide();
                    frappe.msgprint({
                        title: 'Error',
                        message: 'Manual fix failed: ' + (err.message || 'Unknown error'),
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

function force_sap_integration(frm) {
    frappe.confirm(
        'Warning: This will force SAP integration regardless of current status. This action should only be used when normal SAP processing has failed. Continue?',
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.force_sap_integration',
                args: {
                    onb_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: r.message.status === 'success' ? 'green' : 'red'
                        });
                        
                        if (r.message.status === 'success') {
                            frappe.show_alert({
                                message: 'SAP integration has been queued. Check back in a few minutes.',
                                indicator: 'blue'
                            });
                        }
                    }
                },
                error: function(err) {
                    frappe.msgprint({
                        title: 'Error',
                        message: 'Force SAP integration failed: ' + (err.message || 'Unknown error'),
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

function reset_status(frm) {
    let status_dialog = new frappe.ui.Dialog({
        title: 'Reset Document Status',
        fields: [
            {
                label: 'New Status',
                fieldname: 'new_status',
                fieldtype: 'Select',
                options: ['Pending', 'Approved', 'Rejected', 'SAP Error'],
                reqd: 1,
                default: 'Pending',
                description: 'Select the new status for this document'
            },
            {
                fieldtype: 'HTML',
                options: `<div class="alert alert-warning">
                    <strong>Warning:</strong> This is a development tool. Use only for testing purposes.
                    Resetting status may cause inconsistencies in production data.
                </div>`
            }
        ],
        primary_action_label: 'Reset Status',
        primary_action(values) {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.reset_vendor_onboarding_status',
                args: {
                    onb_name: frm.doc.name,
                    new_status: values.new_status
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: 'Error',
                            message: r.message ? r.message.message : 'Reset failed',
                            indicator: 'red'
                        });
                    }
                    status_dialog.hide();
                }
            });
        }
    });
    
    status_dialog.show();
}

function show_document_inspector(frm) {
    let loading = frappe.show_alert({
        message: 'Inspecting document...',
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.check_vendor_onboarding_health',
        args: {
            onb_name: frm.doc.name
        },
        callback: function(r) {
            loading.hide();
            if (r.message) {
                show_document_inspector_dialog(frm, r.message);
            } else {
                frappe.msgprint('No inspection data received');
            }
        },
        error: function(err) {
            loading.hide();
            frappe.msgprint({
                title: 'Error',
                message: 'Document inspection failed: ' + (err.message || 'Unknown error'),
                indicator: 'red'
            });
        }
    });
}

function view_sap_logs(frm) {
    frappe.route_options = {
        "vendor_onboarding": frm.doc.name
    };
    frappe.set_route("List", "VMS SAP Logs");
}

function show_health_check_dialog(health_report) {
    // Ensure health_report has all required properties with defaults
    health_report = health_report || {};
    health_report.overall_health = health_report.overall_health || 'unknown';
    health_report.document_name = health_report.document_name || 'Unknown';
    health_report.current_status = health_report.current_status || 'Unknown';
    health_report.checks = health_report.checks || [];
    health_report.linked_documents = health_report.linked_documents || {};
    health_report.sap_status = health_report.sap_status || {};
    health_report.recommendations = health_report.recommendations || [];
    
    let status_colors = {
        'good': '#28a745',
        'warning': '#ffc107',
        'critical': '#dc3545',
        'error': '#6c757d',
        'unknown': '#6c757d'
    };
    
    let html = `
        <div class="health-check-report">
            <style>
                .health-check-report {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                .health-header {
                    background: ${status_colors[health_report.overall_health]};
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                }
                .health-header h3 {
                    margin: 0;
                    font-size: 24px;
                }
                .health-header p {
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }
                .check-item {
                    display: flex;
                    align-items: center;
                    padding: 12px;
                    margin: 8px 0;
                    border-radius: 6px;
                    border-left: 4px solid #28a745;
                }
                .check-item.warning {
                    border-left-color: #ffc107;
                    background-color: #fff3cd;
                }
                .check-item.error {
                    border-left-color: #dc3545;
                    background-color: #f8d7da;
                }
                .check-icon {
                    font-size: 20px;
                    margin-right: 12px;
                }
                .check-content {
                    flex: 1;
                }
                .check-name {
                    font-weight: 600;
                    margin-bottom: 4px;
                }
                .check-details {
                    color: #6c757d;
                    font-size: 14px;
                }
                .linked-docs {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 12px;
                    margin-top: 20px;
                }
                .doc-card {
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 12px;
                    text-align: center;
                }
                .doc-status {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                .doc-status.exists {
                    background: #d4edda;
                    color: #155724;
                }
                .doc-status.missing {
                    background: #f8d7da;
                    color: #721c24;
                }
                .doc-status.not_set {
                    background: #e2e3e5;
                    color: #383d41;
                }
                .recommendations {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 20px;
                }
                .sap-status {
                    background: #f8f9fa;
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 20px;
                }
            </style>
            
            <div class="health-header">
                <h3>${health_report.overall_health.toUpperCase()} HEALTH</h3>
                <p>Document: ${health_report.document_name}</p>
                <p>Current Status: ${health_report.current_status}</p>
            </div>
            
            <h4>System Checks</h4>
            ${health_report.checks.length > 0 ? health_report.checks.map(check => {
                let isHealthy = check.status === 'complete' || check.status === 'has_data';
                let isWarning = check.status === 'pending' || check.status === 'incomplete' || check.status === 'empty';
                return `
                    <div class="check-item ${isWarning ? 'warning' : isHealthy ? '' : 'error'}">
                        <div class="check-icon">
                            ${isHealthy ? '✅' : isWarning ? '⚠️' : '❌'}
                        </div>
                        <div class="check-content">
                            <div class="check-name">${check.name || 'Unknown Check'}</div>
                            <div class="check-details">${check.details || 'No details available'}</div>
                        </div>
                    </div>
                `;
            }).join('') : '<p>No checks performed</p>'}
            
            <h4>Linked Documents</h4>
            <div class="linked-docs">
                ${Object.keys(health_report.linked_documents).length > 0 ? Object.entries(health_report.linked_documents).map(([field, info]) => `
                    <div class="doc-card">
                        <div style="font-weight: 600; margin-bottom: 8px;">
                            ${field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        <div class="doc-status ${info.status || 'not_set'}">${info.status || 'not_set'}</div>
                        ${info.name ? `<div style="font-size: 12px; margin-top: 4px; color: #6c757d;">${info.name}</div>` : ''}
                        ${info.modified ? `<div style="font-size: 11px; margin-top: 2px; color: #6c757d;">Modified: ${info.modified}</div>` : ''}
                    </div>
                `).join('') : '<p>No linked documents found</p>'}
            </div>
            
            ${Object.keys(health_report.sap_status).length > 0 ? `
                <div class="sap-status">
                    <h4>SAP Integration Status</h4>
                    ${Object.entries(health_report.sap_status).map(([status, info]) => `
                        <div style="margin: 8px 0;">
                            <strong>${status}:</strong> ${info.count || 0} attempts
                            ${info.last_attempt ? `<br><small>Last: ${info.last_attempt}</small>` : ''}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            ${health_report.recommendations.length > 0 ? `
                <div class="recommendations">
                    <h4 style="margin-top: 0;">Recommendations</h4>
                    ${health_report.recommendations.map(rec => `
                        <div style="margin: 8px 0;">• ${rec}</div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: `Health Check - ${health_report.document_name}`,
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'health_html',
                options: html
            }
        ],
        primary_action_label: 'Run Fix',
        primary_action() {
            dialog.hide();
            if (health_report.overall_health !== 'good') {
                run_manual_fix_from_health_check(health_report.document_name);
            } else {
                frappe.msgprint('Document is healthy. No fix needed.');
            }
        }
    });
    
    dialog.show();
}

function show_fix_result_dialog(fix_result) {
    fix_result = fix_result || {};
    let icon = fix_result.status === 'success' ? '✅' : '❌';
    let color = fix_result.status === 'success' ? '#28a745' : '#dc3545';
    
    let html = `
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 48px; margin-bottom: 20px;">${icon}</div>
            <h3 style="color: ${color}; margin-bottom: 15px;">
                ${fix_result.status === 'success' ? 'Fix Applied Successfully' : 'Fix Failed'}
            </h3>
            <p style="font-size: 16px; margin-bottom: 20px;">${fix_result.message || 'No message provided'}</p>
            
            ${fix_result.new_status ? `
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <strong>New Status:</strong> ${fix_result.new_status}<br>
                    ${fix_result.sap_success_count !== undefined ? `<strong>SAP Success Count:</strong> ${fix_result.sap_success_count}<br>` : ''}
                    ${fix_result.sap_error_count !== undefined ? `<strong>SAP Error Count:</strong> ${fix_result.sap_error_count}` : ''}
                </div>
            ` : ''}
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: 'Manual Fix Results',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'fix_html',
                options: html
            }
        ],
        primary_action_label: 'OK',
        primary_action() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function show_document_inspector_dialog(frm, health_report) {
    health_report = health_report || {};
    health_report.linked_documents = health_report.linked_documents || {};
    
    let html = `
        <div class="document-inspector">
            <style>
                .document-inspector {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                .inspector-section {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    margin: 15px 0;
                    overflow: hidden;
                }
                .inspector-header {
                    background: #f8f9fa;
                    padding: 12px 15px;
                    font-weight: 600;
                    border-bottom: 1px solid #dee2e6;
                }
                .inspector-content {
                    padding: 15px;
                }
                .field-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 10px;
                }
                .field-item {
                    background: #f8f9fa;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                }
                .field-label {
                    font-weight: 600;
                    color: #495057;
                }
                .field-value {
                    color: #6c757d;
                    margin-top: 2px;
                }
                .child-table {
                    overflow-x: auto;
                }
                .child-table table {
                    width: 100%;
                    font-size: 12px;
                    border-collapse: collapse;
                }
                .child-table th,
                .child-table td {
                    padding: 8px;
                    border: 1px solid #dee2e6;
                    text-align: left;
                }
                .child-table th {
                    background: #f8f9fa;
                    font-weight: 600;
                }
            </style>
            
            <div class="inspector-section">
                <div class="inspector-header">Document Information</div>
                <div class="inspector-content">
                    <div class="field-grid">
                        <div class="field-item">
                            <div class="field-label">Document Name</div>
                            <div class="field-value">${frm.doc.name || 'Not Available'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Reference No</div>
                            <div class="field-value">${frm.doc.ref_no || 'Not Set'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Vendor Name</div>
                            <div class="field-value">${frm.doc.vendor_name || 'Not Set'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Current Status</div>
                            <div class="field-value">${frm.doc.onboarding_form_status || 'Not Set'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Created</div>
                            <div class="field-value">${frm.doc.creation ? frappe.datetime.str_to_user(frm.doc.creation) : 'Not Available'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Last Modified</div>
                            <div class="field-value">${frm.doc.modified ? frappe.datetime.str_to_user(frm.doc.modified) : 'Not Available'}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="inspector-section">
                <div class="inspector-header">Approval Status</div>
                <div class="inspector-content">
                    <div class="field-grid">
                        <div class="field-item">
                            <div class="field-label">Purchase Team</div>
                            <div class="field-value">${frm.doc.purchase_team_undertaking ? '✅ Approved' : '⏳ Pending'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Purchase Head</div>
                            <div class="field-value">${frm.doc.purchase_head_undertaking ? '✅ Approved' : '⏳ Pending'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Accounts Team</div>
                            <div class="field-value">${frm.doc.accounts_team_undertaking ? '✅ Approved' : '⏳ Pending'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Accounts Head</div>
                            <div class="field-value">${frm.doc.accounts_head_undertaking ? '✅ Approved' : '⏳ Pending'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">Mandatory Data</div>
                            <div class="field-value">${frm.doc.mandatory_data_filled ? '✅ Complete' : '❌ Incomplete'}</div>
                        </div>
                        <div class="field-item">
                            <div class="field-label">SAP Integration</div>
                            <div class="field-value">${frm.doc.data_sent_to_sap ? '✅ Completed' : '⏳ Pending'}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="inspector-section">
                <div class="inspector-header">Linked Documents Status</div>
                <div class="inspector-content">
                    <div class="field-grid">
                        ${Object.keys(health_report.linked_documents).length > 0 ? Object.entries(health_report.linked_documents).map(([field, info]) => `
                            <div class="field-item">
                                <div class="field-label">${field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                                <div class="field-value">
                                    <span style="color: ${info.status === 'exists' ? '#28a745' : info.status === 'missing' ? '#dc3545' : '#6c757d'}">
                                        ${info.status === 'exists' ? '✅ Exists' : info.status === 'missing' ? '❌ Missing' : '⚪ Not Set'}
                                    </span>
                                    ${info.name ? `<br><small>${info.name}</small>` : ''}
                                </div>
                            </div>
                        `).join('') : '<div class="field-item"><div class="field-label">No linked documents information available</div></div>'}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: `Document Inspector - ${frm.doc.name}`,
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'inspector_html',
                options: html
            }
        ],
        primary_action_label: 'Run Health Check',
        primary_action() {
            dialog.hide();
            run_health_check(frm);
        }
    });
    
    dialog.show();
}

function run_manual_fix_from_health_check(document_name) {
    frappe.confirm(
        `Run manual fix on document ${document_name}?`,
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.manual_fix_vendor_onboarding',
                args: {
                    onb_name: document_name
                },
                callback: function(r) {
                    if (r.message) {
                        show_fix_result_dialog(r.message);
                        cur_frm.reload_doc();
                    }
                }
            });
        }
    );
}

function get_status_indicator_html(status) {
    let indicators = {
        'Pending': { color: '#ffc107', icon: '⏳' },
        'Approved': { color: '#28a745', icon: '✅' },
        'Rejected': { color: '#dc3545', icon: '❌' },
        'SAP Error': { color: '#fd7e14', icon: '⚠️' },
        'Processing': { color: '#17a2b8', icon: '🔄' }
    };
    
    let indicator = indicators[status] || { color: '#6c757d', icon: '❓' };
    
    return `
        <div class="status-indicator-wrapper" style="margin-top: 8px;">
            <span style="
                display: inline-block;
                background: ${indicator.color};
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            ">
                ${indicator.icon} ${status}
            </span>
        </div>
    `;
}