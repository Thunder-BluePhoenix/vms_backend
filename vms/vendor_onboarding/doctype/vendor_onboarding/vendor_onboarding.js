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

