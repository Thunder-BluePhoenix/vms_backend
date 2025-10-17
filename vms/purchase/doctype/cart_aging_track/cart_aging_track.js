// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cart Aging Track', {
	refresh: function(frm) {
		// Add custom buttons to the form
		add_view_buttons(frm);
	}
});

function add_view_buttons(frm) {
	// Clear existing custom buttons
	frm.clear_custom_buttons();
	
	// Button 1: View Cart Details
	if (frm.doc.cart_id) {
		frm.add_custom_button(__('View Cart Details'), function() {
			frappe.set_route('Form', 'Cart Details', frm.doc.cart_id);
		}, __('Quick Access'));
	}
	
	// Button 2: View PR (ERP)
	if (frm.doc.pr_erp_link) {
		frm.add_custom_button(__('View PR (ERP)'), function() {
			frappe.set_route('Form', 'Purchase Requisition Webform', frm.doc.pr_erp_link);
		}, __('Quick Access'));
	}
	
	// Button 3: View SAP PR
	if (frm.doc.pr_sap_link) {
		frm.add_custom_button(__('View SAP PR'), function() {
			frappe.set_route('Form', 'Purchase Requisition Form', frm.doc.pr_sap_link);
		}, __('Quick Access'));
	}
	
	// Add refresh button to update aging metrics
	frm.add_custom_button(__('Refresh Aging Metrics'), function() {
		refresh_aging_metrics(frm);
	}, __('Actions'));
	
	// Add button to view all related documents in tabs
	if (frm.doc.cart_id || frm.doc.pr_erp_link || frm.doc.pr_sap_link) {
		frm.add_custom_button(__('View All Documents'), function() {
			view_all_documents(frm);
		}, __('Actions'));
	}
}

function refresh_aging_metrics(frm) {
	frappe.call({
		method: 'vms.purchase.doctype.cart_aging_track.cart_aging_track.create_or_update_cart_aging_track',
		args: {
			cart_id: frm.doc.cart_id
		},
		callback: function(r) {
			if (r.message && r.message.status === 'success') {
				frappe.show_alert({
					message: __('Aging metrics updated successfully'),
					indicator: 'green'
				});
				frm.reload_doc();
			} else {
				frappe.show_alert({
					message: __('Failed to update aging metrics'),
					indicator: 'red'
				});
			}
		}
	});
}

function view_all_documents(frm) {
	// Create a dialog showing all linked documents with buttons
	let dialog = new frappe.ui.Dialog({
		title: __('View Linked Documents'),
		fields: [
			{
				fieldname: 'html_content',
				fieldtype: 'HTML'
			}
		]
	});
	
	let html = '<div style="padding: 15px;">';
	html += '<h4 style="margin-bottom: 15px;">Linked Documents</h4>';
	
	// Cart Details
	if (frm.doc.cart_id) {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px;">
				<strong>Cart Details</strong>
				<br/>
				<span style="color: #888;">${frm.doc.cart_id}</span>
				<br/>
				<button class="btn btn-primary btn-sm" style="margin-top: 8px;" 
					onclick="frappe.set_route('Form', 'Cart Details', '${frm.doc.cart_id}')">
					Open Cart Details
				</button>
				${frm.doc.cart_creation_datetime ? 
					`<br/><small style="color: #666;">Created: ${frappe.datetime.str_to_user(frm.doc.cart_creation_datetime)}</small>` 
					: ''}
			</div>
		`;
	} else {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9f9f9;">
				<strong>Cart Details</strong>
				<br/>
				<span style="color: #888;">Not linked</span>
			</div>
		`;
	}
	
	// PR ERP
	if (frm.doc.pr_erp_link) {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px;">
				<strong>Purchase Requisition (ERP)</strong>
				<br/>
				<span style="color: #888;">${frm.doc.pr_erp_link}</span>
				<br/>
				<button class="btn btn-default btn-sm" style="margin-top: 8px;" 
					onclick="frappe.set_route('Form', 'Purchase Requisition Webform', '${frm.doc.pr_erp_link}')">
					Open PR (ERP)
				</button>
				${frm.doc.pr_creation_datetime ? 
					`<br/><small style="color: #666;">Created: ${frappe.datetime.str_to_user(frm.doc.pr_creation_datetime)}</small>` 
					: ''}
			</div>
		`;
	} else {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9f9f9;">
				<strong>Purchase Requisition (ERP)</strong>
				<br/>
				<span style="color: #888;">Not created yet</span>
			</div>
		`;
	}
	
	// SAP PR
	if (frm.doc.pr_sap_link) {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px;">
				<strong>SAP Purchase Requisition</strong>
				<br/>
				<span style="color: #888;">${frm.doc.pr_sap_link}</span>
				<br/>
				<button class="btn btn-default btn-sm" style="margin-top: 8px;" 
					onclick="frappe.set_route('Form', 'Purchase Requisition Form', '${frm.doc.pr_sap_link}')">
					Open SAP PR
				</button>
				${frm.doc.sap_pr_creation_datetime ? 
					`<br/><small style="color: #666;">Created: ${frappe.datetime.str_to_user(frm.doc.sap_pr_creation_datetime)}</small>` 
					: ''}
			</div>
		`;
	} else {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9f9f9;">
				<strong>SAP Purchase Requisition</strong>
				<br/>
				<span style="color: #888;">Not created yet</span>
			</div>
		`;
	}
	
	html += '</div>';
	
	dialog.fields_dict.html_content.$wrapper.html(html);
	dialog.show();
}

// Helper function to format duration
function format_duration_custom(seconds) {
	if (!seconds || seconds <= 0) return '0 seconds';
	
	const days = Math.floor(seconds / 86400);
	const hours = Math.floor((seconds % 86400) / 3600);
	const minutes = Math.floor((seconds % 3600) / 60);
	
	let parts = [];
	if (days > 0) parts.push(`${days} day${days > 1 ? 's' : ''}`);
	if (hours > 0) parts.push(`${hours} hour${hours > 1 ? 's' : ''}`);
	if (minutes > 0) parts.push(`${minutes} minute${minutes > 1 ? 's' : ''}`);
	
	return parts.length > 0 ? parts.join(', ') : '0 seconds';
}