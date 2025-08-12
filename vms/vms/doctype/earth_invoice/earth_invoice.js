

frappe.ui.form.on('Earth Invoice', {
    refresh: function(frm) {
       
        
        
        if (frm.doc.approval_status == "Pending" && !frm.doc.__islocal) {
            add_approval_actions(frm);
        }
        
    },
    
    before_save: function(frm) {
        
        if (!can_user_edit_document(frm)) {
            frappe.throw(__('You do not have permission to edit this document at current approval level'));
        }
    }
});

function hide_default_workflow_buttons(frm) {
    if (frm.doc.docstatus === 0) {
        frm.page.clear_actions_menu();
    }
}

function can_user_edit_document(frm) {
   
    if (frappe.user_roles.includes('Earth') && frm.is_new()) {
        return true;
    }

   
    if (frappe.user_roles.includes('Earth Upload') && 
        (frm.doc.workflow_state === 'Pending' || !frm.doc.workflow_state)) {
        return true;
    }
    
   
    const approval_roles = ['Travel Desk', 'Tyab', 'Panjikar', 'Accounts Team'];
    if (approval_roles.some(role => frappe.user_roles.includes(role))) {
        return false; // Read-only for approvers
    }
    
    // System Manager can always edit
    if (frappe.user_roles.includes('System Manager')) {
        return true;
    }
    
    return false;
}

function add_approval_actions(frm) {
    // Check if user can approve this specific document
    frappe.call({
        method: 'vms.APIs.approval_matrix.approval_matrix.check_user_can_approve',
        args: { docname: frm.doc.name },
        callback: function(r) {
            if (r.message) {
                // Use Frappe's built-in action system
                frm.page.add_action_icon("fa fa-check", function() {
                    approve_reject_action(frm, 'Approved');
                }, __("Approve"));
                
                frm.page.add_action_icon("fa fa-times", function() {
                    approve_reject_action(frm, 'Rejected');  
                }, __("Reject"));
                
                // Also add to menu
                frm.page.add_menu_item(__('Approve'), function() {
                    approve_reject_action(frm, 'Approved');
                });
                
                frm.page.add_menu_item(__('Reject'), function() {
                    approve_reject_action(frm, 'Rejected');
                });
                
                // Set primary action
                frm.page.set_primary_action(__('Approve'), function() {
                    approve_reject_action(frm, 'Approved');
                });
            }
        }
    });
}



function approve_reject_action(frm, action) {
    let dialog = new frappe.ui.Dialog({
        title: __('{0} Document', [action]),
        fields: [
            {
                fieldtype: 'Small Text',
                fieldname: 'comments',
                label: __('Comments'),
                reqd: action === 'Rejected' ? 1 : 0,
                description: action === 'Approved' ? 
                    __('Optional approval comments') : 
                    __('Please provide reason for rejection')
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: 'vms.APIs.approval_matrix.approval_matrix.process_single_approval',
                args: {
                    docname: frm.doc.name,
                    action: action,
                    comments: values.comments
                },
                btn: dialog.get_primary_btn(),
                freeze: true,
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frm.reload_doc();
                        frappe.show_alert({
                            message: __('{0} successfully', [action]),
                            indicator: 'green'
                        });
                        dialog.hide();
                        
                        // Redirect to list view after action
                        setTimeout(() => {
                            frappe.set_route('List', 'Earth Invoice');
                        }, 1500);
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            message: r.message?.message || __('An error occurred'),
                            indicator: 'red'
                        });
                    }
                }
            });
        },
        primary_action_label: __(action)
    });
    
    dialog.show();
}

function mark_ready_for_approval(frm) {
    frappe.confirm(__('Mark this document as ready for approval? This will start the approval process.'), 
        function() {
            frm.set_value('ready_for_approval', 1);
            frm.save();
        }
    );
}

function show_document_upload_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Upload Supporting Documents'),
        size: 'large',
        fields: [
            {
                fieldtype: 'Section Break',
                label: __('Required Documents')
            },
            {
                fieldtype: 'Attach',
                fieldname: 'invoice_copy',
                label: __('Invoice Copy'),
                reqd: 1
            },
            {
                fieldtype: 'Attach',
                fieldname: 'booking_confirmation',
                label: __('Booking Confirmation')
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Attach',
                fieldname: 'receipt',
                label: __('Payment Receipt')
            },
            {
                fieldtype: 'Attach',
                fieldname: 'additional_doc',
                label: __('Additional Document')
            },
            {
                fieldtype: 'Section Break',
                label: __('Upload Notes')
            },
            {
                fieldtype: 'Small Text',
                fieldname: 'upload_notes',
                label: __('Notes'),
                description: __('Any additional information about uploaded documents')
            }
        ],
        primary_action: function(values) {
            // Update the document with uploaded files
            if (values.invoice_copy) frm.set_value('invoice_copy', values.invoice_copy);
            if (values.booking_confirmation) frm.set_value('booking_confirmation', values.booking_confirmation);
            if (values.receipt) frm.set_value('payment_receipt', values.receipt);
            if (values.additional_doc) frm.set_value('additional_document', values.additional_doc);
            if (values.upload_notes) frm.set_value('upload_notes', values.upload_notes);
            
            frm.set_value('supporting_documents_uploaded', 1);
            frm.set_value('document_upload_date', frappe.datetime.now_datetime());
            
            frm.save();
            dialog.hide();
            
            frappe.show_alert({
                message: __('Documents uploaded successfully'),
                indicator: 'green'
            });
        },
        primary_action_label: __('Upload Documents')
    });
    
    dialog.show();
}