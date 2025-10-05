// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vendor Aging Tracker', {
    refresh: function(frm) {
        // Add custom buttons
        add_custom_buttons(frm);
        
        // Add visual indicators for aging status
        add_aging_indicators(frm);
        
        // Refresh aging calculations button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Refresh Aging Data'), function() {
                refresh_aging_data(frm);
            }, __('Actions'));
        }
        
        // View all Purchase Orders button
        if (frm.doc.vendor_code && !frm.is_new()) {
            frm.add_custom_button(__('View All Purchase Orders'), function() {
                view_all_purchase_orders(frm);
            }, __('View'));
        }
        
        // View Vendor Onboarding button
        if (frm.doc.vendor_onboarding_link) {
            frm.add_custom_button(__('View Vendor Onboarding'), function() {
                frappe.set_route('Form', 'Vendor Onboarding', frm.doc.vendor_onboarding_link);
            }, __('View'));
        }
        
        // View SAP Log button
        if (frm.doc.sap_log_reference) {
            frm.add_custom_button(__('View SAP Log'), function() {
                frappe.set_route('Form', 'VMS SAP Logs', frm.doc.sap_log_reference);
            }, __('View'));
        }
    },
    
    vendor_code: function(frm) {
        // Auto-fetch vendor details when vendor code changes
        if (frm.doc.vendor_code && frm.is_new()) {
            fetch_vendor_details(frm);
        }
    }
});

frappe.ui.form.on('Vendor Aging PO Details', {
    purchase_order: function(frm, cdt, cdn) {
        // Auto-fetch PO details when PO is selected
        let row = locals[cdt][cdn];
        if (row.purchase_order) {
            fetch_po_details(frm, cdt, cdn);
        }
    }
});

function add_custom_buttons(frm) {
    // Dashboard button
    if (!frm.is_new()) {
        frm.add_custom_button(__('Aging Dashboard'), function() {
            show_aging_dashboard();
        }, __('Reports'));
    }
    
    // Export aging report button
    if (!frm.is_new()) {
        frm.add_custom_button(__('Export Aging Report'), function() {
            export_aging_report(frm);
        }, __('Reports'));
    }
}

function add_aging_indicators(frm) {
    // Add color indicators based on aging status
    if (frm.doc.vendor_aging_status) {
        let color = get_aging_color(frm.doc.vendor_aging_status);
        frm.set_df_property('vendor_aging_status', 'description', 
            `<span style="color: ${color}; font-weight: bold;">● ${frm.doc.vendor_aging_status}</span>`);
    }
    
    // Add indicators for PO aging in child table
    if (frm.doc.purchase_order_details) {
        frm.doc.purchase_order_details.forEach(po => {
            if (po.days_since_po > 60) {
                frappe.model.set_value(po.doctype, po.name, 'po_aging_status', 'Very Old (60+ days)');
            }
        });
    }
}

function get_aging_color(status) {
    const color_map = {
        'New (0-30 days)': '#28a745',
        'Recent (31-90 days)': '#17a2b8',
        'Established (91-180 days)': '#ffc107',
        'Long Term (180+ days)': '#dc3545'
    };
    return color_map[status] || '#6c757d';
}

function refresh_aging_data(frm) {
    frappe.call({
        method: 'vms.vms.doctype.vendor_aging_tracker.vendor_aging_tracker.refresh_all_aging_trackers',
        callback: function(r) {
            frm.reload_doc();
            frappe.show_alert({
                message: __('Aging data refreshed successfully'),
                indicator: 'green'
            });
        }
    });
}

function view_all_purchase_orders(frm) {
    frappe.route_options = {
        'vendor_code': frm.doc.vendor_code
    };
    frappe.set_route('List', 'Purchase Order');
}

function fetch_vendor_details(frm) {
    // Fetch vendor details from SAP logs or Vendor Onboarding
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'VMS SAP Logs',
            filters: {
                'total_transaction': ['like', `%${frm.doc.vendor_code}%`],
                'status': 'Success'
            },
            fields: ['name', 'vendor_onboarding_link', 'total_transaction'],
            limit: 1
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let sap_log = r.message[0];
                frm.set_value('sap_log_reference', sap_log.name);
                
                if (sap_log.total_transaction) {
                    try {
                        let transaction_data = JSON.parse(sap_log.total_transaction);
                        let request_details = transaction_data.request_details || {};
                        let payload = request_details.payload || {};
                        
                        frm.set_value('vendor_name', payload.Name1);
                        frm.set_value('company_code', request_details.company_name);
                        frm.set_value('sap_client_code', request_details.sap_client_code);
                        frm.set_value('gst_number', request_details.gst_number);
                        
                        if (transaction_data.transaction_summary) {
                            frm.set_value('vendor_creation_date', 
                                transaction_data.transaction_summary.timestamp);
                        }
                    } catch (e) {
                        console.error('Error parsing transaction data:', e);
                    }
                }
                
                if (sap_log.vendor_onboarding_link) {
                    frm.set_value('vendor_onboarding_link', sap_log.vendor_onboarding_link);
                }
            }
        }
    });
}

function fetch_po_details(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Purchase Order',
            name: row.purchase_order
        },
        callback: function(r) {
            if (r.message) {
                let po = r.message;
                frappe.model.set_value(cdt, cdn, 'po_number', po.po_number);
                frappe.model.set_value(cdt, cdn, 'po_date', po.po_date);
                frappe.model.set_value(cdt, cdn, 'po_status', po.vendor_status);
                frappe.model.set_value(cdt, cdn, 'po_value', po.total_value_of_po__so);
                frappe.model.set_value(cdt, cdn, 'delivery_date', po.delivery_date);
            }
        }
    });
}

function show_aging_dashboard() {
    frappe.call({
        method: 'vms.vms.doctype.vendor_aging_tracker.vendor_aging_tracker.get_vendor_aging_dashboard_data',
        callback: function(r) {
            if (r.message) {
                show_dashboard_dialog(r.message);
            }
        }
    });
}

function show_dashboard_dialog(data) {
    let html = `
        <div class="aging-dashboard">
            <h4>Vendor Aging Dashboard</h4>
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5>${data.total_vendors}</h5>
                            <p>Total Vendors</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 style="color: #28a745;">${data.active_vendors}</h5>
                            <p>Active Vendors</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 style="color: #dc3545;">${data.inactive_vendors}</h5>
                            <p>Inactive Vendors</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5>${data.total_purchase_orders}</h5>
                            <p>Total POs</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <h5 class="mt-4">Aging Categories</h5>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (let [category, count] of Object.entries(data.aging_categories)) {
        html += `
            <tr>
                <td>${category}</td>
                <td>${count}</td>
            </tr>
        `;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: __('Vendor Aging Dashboard'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'dashboard_html',
                options: html
            }
        ],
        size: 'large'
    });
    
    dialog.show();
}

function export_aging_report(frm) {
    frappe.call({
        method: 'frappe.desk.reportview.export_query',
        args: {
            doctype: 'Vendor Aging Tracker',
            file_format_type: 'Excel',
            filters: {}
        },
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Report exported successfully'),
                    indicator: 'green'
                });
            }
        }
    });
}