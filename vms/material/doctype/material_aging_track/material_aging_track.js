// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Aging Track', {
	refresh: function(frm) {
		// Add custom buttons to the form
		add_view_buttons(frm);
		
		// Add color coding for aging status
		add_aging_status_indicator(frm);
	},
	
	onload: function(frm) {
		// Set up any field properties or filters
		setup_field_properties(frm);
	}
});

function add_view_buttons(frm) {
	// Clear existing custom buttons
	frm.clear_custom_buttons();
	
	// Button 1: View Material Master
	if (frm.doc.material_master_id) {
		frm.add_custom_button(__('View Material Master'), function() {
			frappe.set_route('Form', 'Material Master', frm.doc.material_master_id);
		}, __('Quick Access'));
	}
	
	// Button 2: View Requestor Master
	if (frm.doc.requestor_id) {
		frm.add_custom_button(__('View Requestor Master'), function() {
			frappe.set_route('Form', 'Requestor Master', frm.doc.requestor_id);
		}, __('Quick Access'));
	}
	
	// Button 3: View ERP to SAP MO Log
	if (frm.doc.erp_to_sap_mo_log) {
		frm.add_custom_button(__('View ERP to SAP Log'), function() {
			frappe.set_route('Form', 'MO SAP Logs', frm.doc.erp_to_sap_mo_log);
		}, __('Quick Access'));
	}
	
	// Button 4: View SAP to ERP MO Log
	if (frm.doc.sap_to_erp_mo_log) {
		frm.add_custom_button(__('View SAP to ERP Log'), function() {
			frappe.set_route('Form', 'MO SAP Logs', frm.doc.sap_to_erp_mo_log);
		}, __('Quick Access'));
	}
	
	// Add refresh button to update aging metrics
	frm.add_custom_button(__('Refresh Aging Metrics'), function() {
		refresh_aging_metrics(frm);
	}, __('Actions'));
	
	// Add button to view all related documents
	if (frm.doc.material_master_id || frm.doc.requestor_id || 
	    frm.doc.erp_to_sap_mo_log || frm.doc.sap_to_erp_mo_log) {
		frm.add_custom_button(__('View All Documents'), function() {
			view_all_documents(frm);
		}, __('Actions'));
	}
	
	// Add button to view aging analytics
	frm.add_custom_button(__('View Aging Analytics'), function() {
		show_aging_analytics(frm);
	}, __('Reports'));
}

function add_aging_status_indicator(frm) {
	if (!frm.doc.aging_status) return;
	
	// Add color indicator based on aging status
	let indicator_color = 'blue';
	let indicator_text = frm.doc.aging_status;
	
	switch(frm.doc.aging_status) {
		case 'New (0-30 days)':
			indicator_color = 'green';
			break;
		case 'Recent (31-90 days)':
			indicator_color = 'blue';
			break;
		case 'Established (91-180 days)':
			indicator_color = 'orange';
			break;
		case 'Long Term (180+ days)':
			indicator_color = 'yellow';
			break;
	}
	
	frm.dashboard.set_headline_alert(
		`<div class="form-message ${indicator_color}">
			<strong>${indicator_text}</strong> - ${frm.doc.days_since_creation || 0} days since creation
		</div>`
	);
}

function setup_field_properties(frm) {
	// Make datetime fields read-only as they're auto-populated
	frm.set_df_property('material_master_creation_dt', 'read_only', 1);
	frm.set_df_property('requestor_creation_dt', 'read_only', 1);
	frm.set_df_property('sap_mo_log_creation_e_s', 'read_only', 1);
	frm.set_df_property('sap_mo_log_creation_s_e', 'read_only', 1);
	
	// Make calculated fields read-only
	frm.set_df_property('days_since_creation', 'read_only', 1);
	frm.set_df_property('aging_status', 'read_only', 1);
	frm.set_df_property('mat_onboard_duration', 'read_only', 1);
	frm.set_df_property('req_to_mat_duration', 'read_only', 1);
	frm.set_df_property('mat_onboard_duration_e_s', 'read_only', 1);
	frm.set_df_property('mat_onboard_duration_s_e', 'read_only', 1);
}

function refresh_aging_metrics(frm) {
	if (!frm.doc.material_master_id) {
		frappe.msgprint({
			title: __('Material Master Required'),
			message: __('Please link a Material Master to refresh aging metrics'),
			indicator: 'red'
		});
		return;
	}
	
	frappe.call({
		method: 'vms.material.doctype.material_aging_track.material_aging_track.create_or_update_aging_tracker_from_requestor',
		args: {
			req_id: frm.doc.requestor_id
		},
		freeze: true,
		freeze_message: __('Updating aging metrics...'),
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
		size: 'large',
		fields: [
			{
				fieldname: 'html_content',
				fieldtype: 'HTML'
			}
		]
	});
	
	let html = '<div style="padding: 15px;">';
	html += '<h4 style="margin-bottom: 15px;">Linked Documents</h4>';
	
	// Material Master
	if (frm.doc.material_master_id) {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px;">
				<strong>Material Master</strong>
				<br/>
				<span style="color: #888;">${frm.doc.material_master_id}</span>
				<br/>
				<button class="btn btn-primary btn-sm" style="margin-top: 8px;" 
					onclick="frappe.set_route('Form', 'Material Master', '${frm.doc.material_master_id}')">
					Open Material Master
				</button>
				${frm.doc.material_master_creation_dt ? 
					`<br/><small style="color: #666;">Created: ${frappe.datetime.str_to_user(frm.doc.material_master_creation_dt)}</small>` 
					: ''}
			</div>
		`;
	} else {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9f9f9;">
				<strong>Material Master</strong>
				<br/>
				<span style="color: #888;">Not linked</span>
			</div>
		`;
	}
	
	// Requestor Master
	if (frm.doc.requestor_id) {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px;">
				<strong>Requestor Master</strong>
				<br/>
				<span style="color: #888;">${frm.doc.requestor_id}</span>
				<br/>
				<button class="btn btn-default btn-sm" style="margin-top: 8px;" 
					onclick="frappe.set_route('Form', 'Requestor Master', '${frm.doc.requestor_id}')">
					Open Requestor Master
				</button>
				${frm.doc.requestor_creation_dt ? 
					`<br/><small style="color: #666;">Created: ${frappe.datetime.str_to_user(frm.doc.requestor_creation_dt)}</small>` 
					: ''}
			</div>
		`;
	} else {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9f9f9;">
				<strong>Requestor Master</strong>
				<br/>
				<span style="color: #888;">Not linked</span>
			</div>
		`;
	}
	
	// ERP to SAP MO Log
	if (frm.doc.erp_to_sap_mo_log) {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px;">
				<strong>ERP to SAP MO Log</strong>
				<br/>
				<span style="color: #888;">${frm.doc.erp_to_sap_mo_log}</span>
				<br/>
				<button class="btn btn-default btn-sm" style="margin-top: 8px;" 
					onclick="frappe.set_route('Form', 'MO SAP Logs', '${frm.doc.erp_to_sap_mo_log}')">
					Open ERP to SAP Log
				</button>
				${frm.doc.sap_mo_log_creation_e_s ? 
					`<br/><small style="color: #666;">Created: ${frappe.datetime.str_to_user(frm.doc.sap_mo_log_creation_e_s)}</small>` 
					: ''}
			</div>
		`;
	} else {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9f9f9;">
				<strong>ERP to SAP MO Log</strong>
				<br/>
				<span style="color: #888;">Not created yet</span>
			</div>
		`;
	}
	
	// SAP to ERP MO Log
	if (frm.doc.sap_to_erp_mo_log) {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px;">
				<strong>SAP to ERP MO Log</strong>
				<br/>
				<span style="color: #888;">${frm.doc.sap_to_erp_mo_log}</span>
				<br/>
				<button class="btn btn-default btn-sm" style="margin-top: 8px;" 
					onclick="frappe.set_route('Form', 'MO SAP Logs', '${frm.doc.sap_to_erp_mo_log}')">
					Open SAP to ERP Log
				</button>
				${frm.doc.sap_mo_log_creation_s_e ? 
					`<br/><small style="color: #666;">Created: ${frappe.datetime.str_to_user(frm.doc.sap_mo_log_creation_s_e)}</small>` 
					: ''}
			</div>
		`;
	} else {
		html += `
			<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9f9f9;">
				<strong>SAP to ERP MO Log</strong>
				<br/>
				<span style="color: #888;">Not created yet</span>
			</div>
		`;
	}
	
	html += '</div>';
	
	dialog.fields_dict.html_content.$wrapper.html(html);
	dialog.show();
}

function show_aging_analytics(frm) {
	let dialog = new frappe.ui.Dialog({
		title: __('Material Aging Analytics'),
		size: 'large',
		fields: [
			{
				fieldname: 'html_content',
				fieldtype: 'HTML'
			}
		]
	});
	
	let html = '<div style="padding: 20px;">';
	html += '<h4 style="margin-bottom: 20px; color: #36414c;">Material Onboarding Timeline</h4>';
	
	// Summary card
	html += `
		<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
		            padding: 20px; border-radius: 8px; color: white; margin-bottom: 20px;">
			<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
				<div>
					<div style="font-size: 12px; opacity: 0.9;">Total Days Since Creation</div>
					<div style="font-size: 28px; font-weight: bold;">${frm.doc.days_since_creation || 0}</div>
				</div>
				<div>
					<div style="font-size: 12px; opacity: 0.9;">Aging Status</div>
					<div style="font-size: 20px; font-weight: bold;">${frm.doc.aging_status || 'N/A'}</div>
				</div>
			</div>
		</div>
	`;
	
	// Duration metrics
	html += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">';
	
	// MAT Onboard Duration
	html += `
		<div style="padding: 15px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9fafb;">
			<div style="font-size: 12px; color: #6c757d; margin-bottom: 5px;">MAT Onboard Duration</div>
			<div style="font-size: 24px; font-weight: bold; color: #36414c;">
				${format_duration_custom(frm.doc.mat_onboard_duration)}
			</div>
		</div>
	`;
	
	// REQ to MAT Duration
	html += `
		<div style="padding: 15px; border: 1px solid #d1d8dd; border-radius: 5px; background: #f9fafb;">
			<div style="font-size: 12px; color: #6c757d; margin-bottom: 5px;">REQ to MAT Duration</div>
			<div style="font-size: 24px; font-weight: bold; color: #36414c;">
				${format_duration_custom(frm.doc.req_to_mat_duration)}
			</div>
		</div>
	`;
	
	// ERP to SAP Duration
	html += `
		<div style="padding: 15px; border: 1px solid #d1d8dd; border-radius: 5px; background: #fff8e1;">
			<div style="font-size: 12px; color: #6c757d; margin-bottom: 5px;">MAT Onboard Duration (ERP to SAP)</div>
			<div style="font-size: 24px; font-weight: bold; color: #f57c00;">
				${format_duration_custom(frm.doc.mat_onboard_duration_e_s)}
			</div>
		</div>
	`;
	
	// SAP to ERP Duration
	html += `
		<div style="padding: 15px; border: 1px solid #d1d8dd; border-radius: 5px; background: #e3f2fd;">
			<div style="font-size: 12px; color: #6c757d; margin-bottom: 5px;">MAT Onboard Duration (SAP to ERP)</div>
			<div style="font-size: 24px; font-weight: bold; color: #1976d2;">
				${format_duration_custom(frm.doc.mat_onboard_duration_s_e)}
			</div>
		</div>
	`;
	
	html += '</div>';
	
	// Timeline visualization
	html += '<h5 style="margin: 20px 0 15px 0; color: #36414c;">Process Timeline</h5>';
	html += '<div style="position: relative; padding: 20px 0;">';
	
	// Timeline items
	const timeline_items = [
		{
			label: 'Requestor Created',
			datetime: frm.doc.requestor_creation_dt,
			color: '#28a745'
		},
		{
			label: 'Material Master Created',
			datetime: frm.doc.material_master_creation_dt,
			color: '#007bff'
		},
		{
			label: 'ERP to SAP Log Created',
			datetime: frm.doc.sap_mo_log_creation_e_s,
			color: '#ffc107'
		},
		{
			label: 'SAP to ERP Log Created',
			datetime: frm.doc.sap_mo_log_creation_s_e,
			color: '#17a2b8'
		}
	];
	
	timeline_items.forEach((item, index) => {
		if (item.datetime) {
			html += `
				<div style="display: flex; align-items: center; margin-bottom: 20px;">
					<div style="width: 16px; height: 16px; border-radius: 50%; 
					            background: ${item.color}; margin-right: 15px; 
					            flex-shrink: 0; border: 3px solid white; 
					            box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>
					<div style="flex-grow: 1;">
						<div style="font-weight: 600; color: #36414c;">${item.label}</div>
						<div style="font-size: 13px; color: #6c757d;">
							${frappe.datetime.str_to_user(item.datetime)}
						</div>
					</div>
				</div>
			`;
		} else {
			html += `
				<div style="display: flex; align-items: center; margin-bottom: 20px; opacity: 0.4;">
					<div style="width: 16px; height: 16px; border-radius: 50%; 
					            background: #d1d8dd; margin-right: 15px; 
					            flex-shrink: 0;"></div>
					<div style="flex-grow: 1;">
						<div style="font-weight: 600; color: #6c757d;">${item.label}</div>
						<div style="font-size: 13px; color: #adb5bd;">Not yet created</div>
					</div>
				</div>
			`;
		}
	});
	
	html += '</div>';
	html += '</div>';
	
	dialog.fields_dict.html_content.$wrapper.html(html);
	dialog.show();
}

// Helper function to format duration
function format_duration_custom(seconds) {
	if (!seconds || seconds <= 0) return '0s';
	
	const days = Math.floor(seconds / 86400);
	const hours = Math.floor((seconds % 86400) / 3600);
	const minutes = Math.floor((seconds % 3600) / 60);
	const secs = Math.floor(seconds % 60);
	
	let parts = [];
	if (days > 0) parts.push(`${days}d`);
	if (hours > 0) parts.push(`${hours}h`);
	if (minutes > 0) parts.push(`${minutes}m`);
	if (secs > 0 && days === 0) parts.push(`${secs}s`);
	
	return parts.length > 0 ? parts.join(' ') : '0s';
}