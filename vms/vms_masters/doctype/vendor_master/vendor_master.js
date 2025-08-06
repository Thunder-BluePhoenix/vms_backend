frappe.ui.form.on('Vendor Master', {
    refresh: function(frm) {
        // Add custom buttons for document management
        if (!frm.is_new()) {
            // View Document History button
            frm.add_custom_button(__('View History'), function() {
                frappe.call({
                    method: 'vms.vendor_onboarding.vendor_document_management.get_vendor_document_history',
                    args: {
                        vendor_master_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            show_document_history(r.message);
                        }
                    }
                });
            }, __('Vendor Documents'));
            
            // Sync from Latest Onboarding button
            if (frm.doc.vendor_onb_records && frm.doc.vendor_onb_records.length > 0) {
                frm.add_custom_button(__('Sync from Latest'), function() {
                    // Find the latest onboarding
                    let latest = frm.doc.vendor_onb_records[frm.doc.vendor_onb_records.length - 1];
                    
                    frappe.confirm(
                        __('This will sync documents from onboarding {0}. Continue?', [latest.vendor_onboarding_no]),
                        function() {
                            frappe.call({
                                method: 'vms.vendor_onboarding.vendor_document_management.sync_vendor_documents_on_approval',
                                args: {
                                    vendor_onboarding_name: latest.vendor_onboarding_no
                                },
                                callback: function(r) {
                                    if (r.message && r.message.status === 'success') {
                                        frappe.msgprint(__('Documents synced successfully'));
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    );
                }, __('Vendor Documents'));
            }
        }
    }
});

function show_document_history(data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Vendor Document History'),
        size: 'large'
    });
    
    let html = `
        <div class="vendor-doc-history">
            <h5>Current Documents</h5>
            <table class="table table-bordered">
                <tr>
                    <td><strong>Bank Details:</strong></td>
                    <td>${data.current_documents.bank_details || 'Not Set'}</td>
                </tr>
                <tr>
                    <td><strong>Document Details:</strong></td>
                    <td>${data.current_documents.document_details || 'Not Set'}</td>
                </tr>
                <tr>
                    <td><strong>Manufacturing Details:</strong></td>
                    <td>${data.current_documents.manufacturing_details || 'Not Set'}</td>
                </tr>
            </table>
            
            <h5 class="mt-3">Onboarding History</h5>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Onboarding ID</th>
                        <th>Status</th>
                        <th>Current</th>
                        <th>Synced Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>`;
    
    data.onboarding_history.forEach(function(record) {
        html += `
            <tr>
                <td>${frappe.datetime.str_to_user(record.date)}</td>
                <td><a href="/app/vendor-onboarding/${record.onboarding_id}">${record.onboarding_id}</a></td>
                <td>${record.status}</td>
                <td>${record.is_current ? '<span class="badge badge-success">Yes</span>' : 'No'}</td>
                <td>${record.synced_date ? frappe.datetime.str_to_user(record.synced_date) : '-'}</td>
                <td>
                    <button class="btn btn-xs btn-primary" 
                        onclick="restore_from_onboarding('${record.onboarding_id}')">
                        Restore
                    </button>
                </td>
            </tr>`;
    });
    
    html += `
                </tbody>
            </table>
        </div>`;
    
    dialog.$body.html(html);
    dialog.show();
}

// Global function for restore button
window.restore_from_onboarding = function(onboarding_id) {
    frappe.confirm(
        __('Restore documents from this onboarding?'),
        function() {
            frappe.call({
                method: 'vms.vendor_onboarding.vendor_document_management.restore_from_onboarding',
                args: {
                    vendor_master_name: cur_frm.doc.name,
                    onboarding_name: onboarding_id
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.msgprint(__('Documents restored successfully'));
                        cur_frm.reload_doc();
                        $('.modal').modal('hide');
                    }
                }
            });
        }
    );
};