
frappe.ui.form.on('Earth Invoice', {
    refresh: function(frm) {
        
        // Remove any workflow-related elements
        setTimeout(function() {
            $('.actions-btn-group').empty();
        }, 100);

        add_workflow_buttons(frm);
        show_workflow_status(frm);
        handle_readonly_state(frm);
        
    }
});


function add_workflow_buttons(frm) {
    if (!frm.doc.name || frm.doc.__islocal) return;
    
    const state = frm.doc.workflow_state;
    const roles = frappe.boot.user.roles;
    
    // Clear existing buttons
    frm.page.clear_actions();
    
    // UPDATED: Approve/Reject flow starts from Travel Desk only
    // Earth and Earth Upload cannot approve/reject

    if (state === 'Pending' && roles.includes('Nirav')) {
        add_approve_reject_buttons(frm, 'Approve By Nirav Sir');
    }

    if (state === 'Approve By Nirav Sir' && roles.includes('Travel Desk')) {
        add_approve_reject_buttons(frm, 'Approve By Travel Desk');
    }
    else if (state === 'Approve By Travel Desk' && roles.includes('Tyab')) {
        add_approve_reject_buttons(frm, 'Approve By Tyab Sir');
    }
    else if (state === 'Approve By Tyab Sir' && roles.includes('Panjikar')) {
        add_approve_reject_buttons(frm, 'Approve By Panjikar Sir');
    }
    else if (state === 'Approve By Panjikar Sir' && roles.includes('Accounts Team')) {
        check_company_access_and_add_buttons(frm);
    }
    else if (state === 'Rejected' && roles.includes('Earth') && !frm.doc.is_auto_rejected) {
        add_resubmit_button(frm);
    }
    
    // Add informational messages for Earth and Earth Upload users
    if (state === 'Pending') {
        if (roles.includes('Earth')) {
            frm.dashboard.add_comment(
                '<i class="fa fa-info-circle"></i> You can edit and upload documents. Approval flow will be handled by Travel Desk.',
                'blue',
                true
            );
        }
        else if (has_any_earth_upload_role(roles)) {
            const allowed_types = get_user_invoice_types_from_roles(roles);
            const types_text = allowed_types.length > 0 ? allowed_types.join(', ') : 'all types';
            frm.dashboard.add_comment(
                `<i class="fa fa-info-circle"></i> You can edit invoices for: <strong>${types_text}</strong>`,
                'blue',
                true
            );
        }
        
        else if (roles.includes('Nirav')) {
            frm.dashboard.add_comment(
                '<i class="fa fa-exclamation-triangle"></i> This invoice is ready for your approval/rejection.',
                'orange',
                true
            );
        }
    }
}

function has_any_earth_upload_role(roles) {
    return roles.some(role => role.startsWith('Earth Upload'));
}

function get_user_invoice_types_from_roles(roles) {
    const role_type_mapping = {
        'Hotel Booking': 'Earth Upload Hotel',
        'Bus Booking': 'Earth Upload Bus',
        'Domestic Air Booking': 'Earth Upload Domestic Air',
        'International Air Booking': 'Earth Upload International Air',
        'Railway Booking': 'Earth Upload Railway',
      
    };
    
    const types = [];
    roles.forEach(role => {
        if (role_type_mapping[role]) {
            types.push(role_type_mapping[role]);
        }
    });
    
    return types;
}

function add_approve_reject_buttons(frm, next_state) {
    
    frm.add_custom_button(__('Approve'), function() {
        approve_invoice(frm, next_state);
    }, __('Action')).addClass('btn-success'); 
    
    frm.add_custom_button(__('Reject'), function() {
        reject_invoice(frm);
    }, __('Action')).addClass('btn-danger'); 
}

function check_company_access_and_add_buttons(frm) {
    // For accounts team, check company access first
    frappe.call({
        method: 'vms.vms.doctype.earth_invoice.earth_invoice.user_has_company_access',
        args: {
            user: frappe.session.user,
            company: frm.doc.billing_company
        },
        callback: function(r) {
            if (r.message) {
                add_approve_reject_buttons(frm, 'Approved');
            } else {
                frm.dashboard.add_comment(
                    `<i class="fa fa-ban"></i> You don't have access to approve invoices for company: <strong>${frm.doc.billing_company}</strong>`,
                    'red',
                    true
                );
            }
        }
    });
}

function add_resubmit_button(frm) {
    frm.add_custom_button(__('Resubmit for Approval'), function() {
        resubmit_invoice(frm);
    }, __('Action')).addClass('btn-primary'); 
}


function approve_invoice(frm, next_state) {
    let approval_message = 'Are you sure you want to approve this invoice?';
    
   
    approval_message += `<br><br><strong>Note:</strong> This will also approve ALL other invoices from date <strong>${frm.doc.inv_date}</strong> at the same approval stage.`;
    
    frappe.confirm(
        __(approval_message),
        function() {
            frappe.call({
                method: 'vms.vms.doctype.earth_invoice.earth_invoice.approve_invoice',
                args: {
                    doc_name: frm.doc.name,
                    next_state: next_state
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        handle_group_approval(frm, next_state);
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            message: r.message?.message || 'Approval failed',
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}


function handle_group_approval(frm, next_state) {
    frappe.call({
        method: 'vms.vms.doctype.earth_invoice.earth_invoice.handle_group_approval',
        args: {
            approving_doc_name: frm.doc.name,
            inv_date: frm.doc.inv_date,
            current_workflow_state: frm.doc.workflow_state,
            approved_by: frappe.session.user,
            next_state: next_state
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                const affected_count = r.message.affected_invoices || 0;
                let success_message = 'Invoice approved successfully';
                
                if (affected_count > 0) {
                    success_message += `. ${affected_count} related invoices also auto-approved.`;
                }
                
                frappe.show_alert({
                    message: __(success_message),
                    indicator: 'green'
                });
                
                
                if (affected_count > 0) {
                    send_group_approval_notification(frm, affected_count, r.message.affected_invoice_names, next_state);
                }
                
                frm.reload_doc();
            } else {
                frappe.show_alert({
                    message: __('Invoice approved, but group approval may have failed'),
                    indicator: 'orange'
                });
                frm.reload_doc();
            }
        }
    });
}


function send_group_approval_notification(frm, affected_count, affected_names, next_state) {
    frappe.call({
        method: 'vms.vms.doctype.earth_invoice.earth_invoice.send_group_approval_email',
        args: {
            original_invoice: frm.doc.name,
            inv_date: frm.doc.inv_date,
            billing_company: frm.doc.billing_company || 'N/A',
            affected_invoices: affected_names || [],
            approved_by: frappe.session.user,
            next_state: next_state
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Group approval notification sent'),
                    indicator: 'green'
                });
            }
        }
    });
}

function reject_invoice(frm) {
    // Get list of previous approval levels for display
    const previous_levels = get_previous_approval_levels(frm.doc.workflow_state);
    
    let dialog = new frappe.ui.Dialog({
        title: __('Reject Invoice'),
        fields: [
            {
                fieldtype: 'Small Text',
                fieldname: 'rejection_remark',
                label: __('Rejection Reason'),
                reqd: 1
            },
            {
                fieldtype: 'HTML',
                options: `
                    <div class="alert alert-warning">
                        <strong>Warning:</strong> This will reject ALL invoices from date 
                        <strong>${frm.doc.inv_date}</strong> at the same approval stage.
                        <br><br>
                        <strong>Notifications will be sent to:</strong> ${previous_levels}
                    </div>
                `
            }
        ],
        primary_action: function() {
            const data = dialog.get_values();
            if (data.rejection_remark) {
                frappe.call({
                    method: 'vms.vms.doctype.earth_invoice.earth_invoice.reject_invoice',
                    args: {
                        doc_name: frm.doc.name,
                        rejection_remark: data.rejection_remark
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                            handle_group_rejection(frm, data.rejection_remark);
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                message: r.message?.message || 'Rejection failed',
                                indicator: 'red'
                            });
                        }
                    }
                    
                });
                dialog.hide();
            }
        },
        primary_action_label: __('Reject')
    });
    dialog.show();
}


function get_previous_approval_levels(current_state) {
    const level_hierarchy = {
        'Pending': 'None (First level)',
        'Approve By Nirav Sir': 'Earth Team',
        'Approve By Travel Desk': 'Earth Team, Nirav Sir', 
        'Approve By Tyab Sir': 'Earth Team, Nirav Sir, Travel Desk',
        'Approve By Panjikar Sir': 'Earth Team, Nirav Sir, Travel Desk, Tyab Sir',
        'Approved': 'Earth Team, Nirav Sir, Travel Desk, Tyab Sir, Panjikar Sir'
    };
    
    return level_hierarchy[current_state] || 'Previous approval levels';
}

function handle_group_rejection(frm, rejection_remark) {
    frappe.call({
        method: 'vms.vms.doctype.earth_invoice.earth_invoice.handle_group_rejection',
        args: {
            rejecting_doc_name: frm.doc.name,
            inv_date: frm.doc.inv_date,
            current_workflow_state: frm.doc.workflow_state,
            rejection_remark: rejection_remark,
            rejected_by: frappe.session.user
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                const affected_count = r.message.affected_invoices || 0;
                let success_message = 'Invoice rejected successfully';
                
                if (affected_count > 0) {
                    success_message += `. ${affected_count} related invoices also auto-rejected.`;
                }
                
                frappe.show_alert({
                    message: __(success_message),
                    indicator: 'green'
                });
                
                // Send group notification email to all approval levels
                if (affected_count > 0) {
                    send_group_rejection_notification(frm, affected_count, r.message.affected_invoice_names);
                }
                
                frm.reload_doc();
            } else {
                frappe.show_alert({
                    message: __('Invoice rejected, but group rejection may have failed'),
                    indicator: 'orange'
                });
                frm.reload_doc();
            }
        }
    });
}

// UPDATED: Send group rejection notification to previous approval levels only
function send_group_rejection_notification(frm, affected_count, affected_names) {
    frappe.call({
        method: 'vms.vms.doctype.earth_invoice.earth_invoice.send_group_rejection_email',
        args: {
            original_invoice: frm.doc.name,
            inv_date: frm.doc.inv_date,
            billing_company: frm.doc.billing_company || 'N/A',
            rejection_remark: frm.doc.rejection_remark,
            affected_invoices: affected_names || [],
            rejected_by: frappe.session.user,
            current_workflow_state: frm.doc.workflow_state
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Group rejection notification sent to previous approval levels'),
                    indicator: 'green'
                });
            }
        }
    });
}


function resubmit_invoice(frm) {
    frappe.confirm(
        __('Resubmit this invoice for approval?'),
        function() {
            frappe.call({
                method: 'vms.vms.doctype.earth_invoice.earth_invoice.resubmit_invoice',
                args: {
                    doc_name: frm.doc.name
                },
                callback: function(r) {
                    handle_response(r, 'Invoice resubmitted for approval', frm);
                }
            });
        }
    );
}

function handle_response(r, success_message, frm) {
    if (r.message && r.message.status === 'success') {
        frappe.show_alert({
            message: __(success_message),
            indicator: 'green'
        });
        frm.reload_doc();
    } else {
        frappe.msgprint({
            title: __('Error'),
            message: r.message?.message || 'Operation failed',
            indicator: 'red'
        });
    }
}

function show_workflow_status(frm) {
    if (!frm.doc.workflow_state) return;
    
    const state = frm.doc.workflow_state;
    let message = '';
    let color = 'blue';
    
    // Updated status messages to reflect new flow
    const state_info = {
        'Pending': 'Ready for Nirav Sir approval', 
        'Approve By Nirav Sir': 'Waiting for Travel Desk approval', 
        'Approve By Travel Desk': 'Waiting for Tyab Sir approval', 
        'Approve By Tyab Sir': 'Waiting for Panjikar Sir approval',
        'Approve By Panjikar Sir': 'Waiting for Accounts Team approval',
        'Approved': { msg: 'Invoice approved', color: 'green' },
        'Rejected': { msg: 'Invoice rejected', color: 'red' }
    };
    
    if (typeof state_info[state] === 'string') {
        message = state_info[state];
    } else if (state_info[state]) {
        message = state_info[state].msg;
        color = state_info[state].color;
    }
    
    if (message) {
        frm.dashboard.add_comment(`<i class="fa fa-info-circle"></i> ${message}`, color, true);
    }
    
    // Show rejection details
    if (state === 'Rejected' && frm.doc.rejection_remark) {
        let rejection_msg = `<strong>Reason:</strong> ${frm.doc.rejection_remark}`;
        
        if (frm.doc.is_auto_rejected) {
            rejection_msg += '<br><span style="color: orange;"><strong>Auto-rejected:</strong> This invoice is read-only</span>';
        }
        
        frm.dashboard.add_comment(rejection_msg, 'red', true);
    }
    
    // Show company access info for accounts team
    if (state === 'Approve By Panjikar Sir' && frappe.boot.user.roles.includes('Accounts Team')) {
        show_company_access_info(frm);
    }
}

function show_company_access_info(frm) {
    frappe.call({
        method: 'vms.vms.doctype.earth_invoice.earth_invoice.get_user_assigned_companies',
        args: {
            user: frappe.session.user
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                const companies = r.message;
                const has_access = companies.includes(frm.doc.billing_company);
                
                const access_msg = has_access ? 
                    `<i class="fa fa-check"></i> You can approve invoices for <strong>${frm.doc.billing_company}</strong>` :
                    `<i class="fa fa-times"></i> No access to approve for <strong>${frm.doc.billing_company}</strong>`;
                
                frm.dashboard.add_comment(access_msg, has_access ? 'green' : 'red', true);
                frm.dashboard.add_comment(`Your companies: <strong>${companies.join(', ')}</strong>`, 'blue', true);
            }
        }
    });
}

function handle_readonly_state(frm) {
    // Make auto-rejected invoices read-only
    if (frm.doc.workflow_state === 'Rejected' && frm.doc.is_auto_rejected) {
        frm.set_read_only();
        frm.dashboard.add_comment(
            '<i class="fa fa-lock"></i> This invoice was auto-rejected and cannot be edited',
            'orange',
            true
        );
    }
    
    // Handle permissions based on role and state
    const roles = frappe.boot.user.roles;
    const state = frm.doc.workflow_state;
    
    // Earth and Earth Upload users get informational messages instead of restrictions
    if (roles.includes('Earth') || roles.includes('Earth Upload')) {
        // They can edit in their allowed states, no additional restrictions needed
        return;
    }
}