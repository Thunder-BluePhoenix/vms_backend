// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

frappe.ui.form.on("Existing Vendor Import", {
	refresh(frm) {
		// Add custom buttons
		add_custom_buttons(frm);
		
		// Auto-parse when file is uploaded
		if (frm.doc.csv_xl && !frm.doc.vendor_data) {
			setTimeout(() => {
				frm.save();
			}, 1000);
		}
		
		// Style the form
		style_form(frm);
		
		// Show field mapping if data exists
		if (frm.doc.field_mapping_html) {
			show_field_mapping_section(frm);
		}
		
		// Add help text
		add_help_text(frm);

        initialize_enhanced_features(frm);
	},
	
	csv_xl(frm) {
		if (frm.doc.csv_xl) {
			reset_form_data(frm);
			
			// Show loading message
			frm.dashboard.add_comment('Parsing uploaded file and generating field mapping...', 'blue', true);
			
			// Auto-save to trigger validation
			setTimeout(() => {
				frm.save().then(() => {
					frm.dashboard.clear_comment();
					frappe.show_alert({
						message: __('File parsed successfully. Please review field mapping.'),
						indicator: 'green'
					});
					
					// Scroll to field mapping section
					if (frm.doc.field_mapping_html) {
						setTimeout(() => {
							scroll_to_field_mapping();
						}, 500);
					}
				});
			}, 500);
		}
	},
	
	initiate(frm) {
		process_vendors(frm);
	},
	
	field_mapping(frm) {
		if (frm.doc.field_mapping && frm.doc.vendor_data) {
			// Re-validate data when field mapping changes
			setTimeout(() => {
				frm.save();
			}, 1000);
		}
	}
});

function add_custom_buttons(frm) {
	// Clear existing buttons
	frm.page.clear_actions_menu();
	
	// Download buttons group
	frm.add_custom_button(__('Field Mapping Template'), function() {
		download_field_mapping_template();
	}, __('Download'));
	
	frm.add_custom_button(__('Sample CSV Template'), function() {
		download_sample_template();
	}, __('Download'));
	
	if (frm.doc.vendor_data) {
		frm.add_custom_button(__('Processed Data (Excel)'), function() {
			download_processed_data(frm, 'all');
		}, __('Download'));
		
		frm.add_custom_button(__('Valid Records Only'), function() {
			download_processed_data(frm, 'valid');
		}, __('Download'));
		
		frm.add_custom_button(__('Invalid Records Only'), function() {
			download_processed_data(frm, 'invalid');
		}, __('Download'));
	}
	
	// Action buttons
	if (frm.doc.csv_xl && frm.doc.field_mapping && !frm.doc.existing_vendor_initialized) {
		frm.add_custom_button(__('Process Vendors'), function() {
			process_vendors(frm);
		}, __('Actions')).addClass('btn-primary');
		
		frm.add_custom_button(__('Re-validate Data'), function() {
			revalidate_data(frm);
		}, __('Actions')).addClass('btn-info');
	}
	
	if (frm.doc.existing_vendor_initialized) {
		frm.add_custom_button(__('Re-process'), function() {
			frappe.confirm(
				'Are you sure you want to re-process all vendors? This may create duplicates.',
				function() {
					process_vendors(frm);
				}
			);
		}, __('Actions')).addClass('btn-warning');
	}
	
	// Field mapping buttons
	if (frm.doc.csv_xl && frm.doc.vendor_data) {
		frm.add_custom_button(__('Reset Auto Mapping'), function() {
			reset_auto_mapping(frm);
		}, __('Mapping'));
		
		frm.add_custom_button(__('Clear All Mapping'), function() {
			clear_all_mapping(frm);
		}, __('Mapping'));
		
		frm.add_custom_button(__('Validate Mapping'), function() {
			validate_field_mapping(frm);
		}, __('Mapping'));
	}
}

function reset_form_data(frm) {
	frm.set_value('existing_vendor_initialized', 0);
	frm.set_value('vendor_data', '');
	frm.set_value('field_mapping', '');
	frm.set_value('success_fail_rate', '');
	frm.set_value('success_fail_rate_html', '');
	frm.set_value('vendor_html', '');
	frm.set_value('field_mapping_html', '');
}

function show_field_mapping_section(frm) {
	// Add field mapping section if it doesn't exist
	if (!frm.fields_dict.field_mapping_html) {
		// The HTML will be displayed in the field_mapping_html field
		frm.refresh_field('field_mapping_html');
	}
}

function scroll_to_field_mapping() {
	const mappingSection = document.querySelector('.field-mapping-container');
	if (mappingSection) {
		mappingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}
}

function process_vendors(frm) {
	if (!frm.doc.csv_xl) {
		frappe.msgprint(__('Please upload a CSV/Excel file first.'));
		return;
	}
	
	if (!frm.doc.vendor_data) {
		frappe.msgprint(__('Please save the form to parse the uploaded file first.'));
		return;
	}
	
	if (!frm.doc.field_mapping) {
		frappe.msgprint(__('Please configure field mapping first.'));
		return;
	}
	
	// Validate mapping before processing
	if (!validate_required_mapping(frm)) {
		return;
	}
	
	// Show progress dialog
	let progress_dialog = new frappe.ui.Dialog({
		title: __('Processing Vendors'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'progress_html',
				options: get_progress_html()
			}
		],
		primary_action_label: __('Cancel'),
		primary_action() {
			progress_dialog.hide();
		}
	});
	
	progress_dialog.show();
	
	// Call server method to process vendors
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.process_existing_vendors',
		args: {
			docname: frm.doc.name
		},
		callback: function(r) {
			progress_dialog.hide();
			
			if (r.message) {
				let results = r.message;
				show_results_dialog(results, frm);
			}
		},
		error: function(r) {
			progress_dialog.hide();
			frappe.msgprint({
				title: __('Error'),
				message: __('An error occurred while processing vendors. Please check the error log.'),
				indicator: 'red'
			});
		}
	});
}

function validate_required_mapping(frm) {
	try {
		const mapping = JSON.parse(frm.doc.field_mapping);
		const required_fields = ['vendor_name', 'vendor_code', 'company_code', 'state'];
		const mapped_fields = Object.values(mapping).filter(Boolean);
		
		const missing_required = required_fields.filter(field => !mapped_fields.includes(field));
		
		if (missing_required.length > 0) {
			frappe.msgprint({
				title: __('Required Fields Missing'),
				message: __('Please map the following required fields: ') + missing_required.join(', '),
				indicator: 'red'
			});
			return false;
		}
		
		return true;
	} catch (e) {
		frappe.msgprint(__('Invalid field mapping configuration.'));
		return false;
	}
}

function get_progress_html() {
	return `
		<div class="text-center">
			<div class="progress mb-4" style="height: 25px;">
				<div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
					 role="progressbar" style="width: 0%" id="import-progress-bar">
					<span id="progress-text">0%</span>
				</div>
			</div>
			
			<div class="row">
				<div class="col-md-3">
					<div class="card border-primary">
						<div class="card-body text-center">
							<h4 class="text-primary" id="total-count">0</h4>
							<small>Total Records</small>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card border-success">
						<div class="card-body text-center">
							<h4 class="text-success" id="success-count">0</h4>
							<small>Successful</small>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card border-danger">
						<div class="card-body text-center">
							<h4 class="text-danger" id="failed-count">0</h4>
							<small>Failed</small>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card border-info">
						<div class="card-body text-center">
							<h4 class="text-info" id="current-record">0</h4>
							<small>Current Record</small>
						</div>
					</div>
				</div>
			</div>
			
			<div class="mt-3">
				<p id="status-message">Initializing import process...</p>
				<div class="spinner-border text-primary" role="status">
					<span class="sr-only">Loading...</span>
				</div>
			</div>
		</div>
	`;
}

function show_results_dialog(results, frm) {
	let success_rate = results.total_processed > 0 ? 
		((results.successful / results.total_processed) * 100).toFixed(1) : 0;
	
	let results_dialog = new frappe.ui.Dialog({
		title: __('Import Results'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'results_html',
				options: generate_results_html(results)
			}
		],
		primary_action_label: __('Download Report'),
		primary_action() {
			download_processed_data(frm, 'all');
		},
		secondary_action_label: __('Close'),
		secondary_action() {
			results_dialog.hide();
			frm.reload_doc();
		}
	});
	
	results_dialog.show();
}

function generate_results_html(results) {
	let success_rate = results.total_processed > 0 ? 
		((results.successful / results.total_processed) * 100).toFixed(1) : 0;
	
	let html = `
		<div class="import-results">
			<div class="row mb-4">
				<div class="col-md-3 text-center">
					<div class="card border-primary">
						<div class="card-body">
							<h3 class="text-primary">${results.total_processed}</h3>
							<p class="mb-0">Total Processed</p>
						</div>
					</div>
				</div>
				<div class="col-md-3 text-center">
					<div class="card border-success">
						<div class="card-body">
							<h3 class="text-success">${results.successful}</h3>
							<p class="mb-0">Successful</p>
						</div>
					</div>
				</div>
				<div class="col-md-3 text-center">
					<div class="card border-danger">
						<div class="card-body">
							<h3 class="text-danger">${results.failed}</h3>
							<p class="mb-0">Failed</p>
						</div>
					</div>
				</div>
				<div class="col-md-3 text-center">
					<div class="card border-info">
						<div class="card-body">
							<h3 class="text-info">${success_rate}%</h3>
							<p class="mb-0">Success Rate</p>
						</div>
					</div>
				</div>
			</div>
			
			<div class="progress mb-3" style="height: 20px;">
				<div class="progress-bar bg-success" role="progressbar" 
					 style="width: ${success_rate}%" 
					 aria-valuenow="${success_rate}" 
					 aria-valuemin="0" 
					 aria-valuemax="100">
					${success_rate}%
				</div>
			</div>
	`;
	
	if (results.errors && results.errors.length > 0) {
		html += `
			<div class="card border-danger mt-3">
				<div class="card-header bg-danger text-white">
					<h6 class="mb-0">Errors (${results.errors.length})</h6>
				</div>
				<div class="card-body">
					<div style="max-height: 300px; overflow-y: auto;">
						<ul class="list-unstyled mb-0">
		`;
		
		results.errors.slice(0, 50).forEach(error => {
			html += `<li class="text-danger mb-1">• ${error}</li>`;
		});
		
		if (results.errors.length > 50) {
			html += `<li class="text-muted mb-1">... and ${results.errors.length - 50} more errors</li>`;
		}
		
		html += `
					</ul>
				</div>
			</div>
		`;
	}
	
	html += `</div>`;
	return html;
}

function download_processed_data(frm, data_type) {
	// Show loading indicator
	frappe.show_alert({
		message: __('Preparing download...'),
		indicator: 'blue'
	});
	
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.download_processed_data',
		args: {
			docname: frm.doc.name,
			data_type: data_type
		},
		callback: function(r) {
			if (r.message && r.message.file_url) {
				// Create download link
				const link = document.createElement('a');
				link.href = r.message.file_url;
				link.download = r.message.file_name;
				link.target = '_blank';
				
				// Trigger download
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
				
				frappe.show_alert({
					message: __('Download started: ') + r.message.file_name,
					indicator: 'green'
				});
			}
		},
		error: function(r) {
			frappe.show_alert({
				message: __('Failed to generate download file.'),
				indicator: 'red'
			});
		}
	});
}


function download_field_mapping_template() {
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.download_field_mapping_template',
		callback: function(r) {
			if (r.message && r.message.file_url) {
				window.open(r.message.file_url, '_blank');
				frappe.show_alert({
					message: __('Field mapping template downloaded'),
					indicator: 'green'
				});
			}
		}
	});
}

function download_sample_template() {
	// Create sample template data
	let sample_data = [{
		'C.Code': '2000',
		'Vendor Code': '10001',
		'Vendor Name': 'Sample Vendor Pvt. Ltd.',
		'State': 'Gujarat',
		'State Code': '6',
		'GSTN No': '24AACCD0267F1Z4',
		'PAN No': 'AACCD0267F',
		'Check': '10',
		'Vendor GST Classification': 'Registered',
		'Address01': 'Sample Address Line 1',
		'Address02': 'Sample Address Line 2',
		'Address03': 'Sample Address Line 3',
		'City': 'Ahmedabad',
		'Pincode': '380001',
		'Country': 'India',
		'Contact No': '9876543210',
		'Alternate No': '0260-1234567',
		'Email-Id': 'vendor@sample.com',
		'Primary Email': 'primary@sample.com',
		'Secondary Email': 'secondary@sample.com',
		'Purchase Group': 'PG01',
		'Purchase Organization': 'PO01',
		'Vendor Type': 'Local',
		'Terms of Payment': '30 Days',
		'Incoterm': 'FOB',
		'Bank Name': 'HDFC Bank',
		'IFSC Code': 'HDFC0001234',
		'Account Number': '123456789012',
		'Name of Account Holder': 'Sample Vendor Pvt Ltd',
		'Type of Account': 'Current'
	}];
	
	// Convert to CSV
	let csv_content = '';
	let headers = Object.keys(sample_data[0]);
	
	// Add headers
	csv_content += headers.join(',') + '\n';
	
	// Add sample row
	sample_data.forEach(row => {
		let values = headers.map(header => {
			let value = row[header] || '';
			// Escape commas and quotes
			if (value.toString().includes(',') || value.toString().includes('"')) {
				value = '"' + value.toString().replace(/"/g, '""') + '"';
			}
			return value;
		});
		csv_content += values.join(',') + '\n';
	});
	
	// Create and download file
	let blob = new Blob([csv_content], { type: 'text/csv' });
	let url = window.URL.createObjectURL(blob);
	let a = document.createElement('a');
	a.href = url;
	a.download = 'sample_vendor_import_template.csv';
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	window.URL.revokeObjectURL(url);
	
	frappe.show_alert({
		message: __('Sample template downloaded successfully'),
		indicator: 'green'
	});
}

function reset_auto_mapping(frm) {
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.get_auto_mapping',
		args: {
			docname: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				frm.set_value('field_mapping', JSON.stringify(r.message, null, 2));
				frm.save().then(() => {
					frappe.show_alert({
						message: __('Auto mapping applied successfully'),
						indicator: 'green'
					});
					frm.refresh();
				});
			}
		}
	});
}

function clear_all_mapping(frm) {
	frappe.confirm(
		'Are you sure you want to clear all field mappings?',
		function() {
			if (frm.doc.original_headers) {
				let headers = JSON.parse(frm.doc.original_headers);
				let empty_mapping = {};
				headers.forEach(header => {
					empty_mapping[header] = null;
				});
				
				frm.set_value('field_mapping', JSON.stringify(empty_mapping, null, 2));
				frm.save().then(() => {
					frappe.show_alert({
						message: __('All mappings cleared'),
						indicator: 'orange'
					});
					frm.refresh();
				});
			}
		}
	);
}

function validate_field_mapping(frm) {
	if (!frm.doc.field_mapping) {
		frappe.msgprint(__('No field mapping found.'));
		return;
	}
	
	try {
		const mapping = JSON.parse(frm.doc.field_mapping);
		const required_fields = ['vendor_name', 'vendor_code', 'company_code', 'state'];
		const mapped_fields = Object.values(mapping).filter(Boolean);
		
		let validation_results = {
			total_headers: Object.keys(mapping).length,
			mapped_headers: mapped_fields.length,
			unmapped_headers: Object.keys(mapping).length - mapped_fields.length,
			required_mapped: 0,
			required_missing: []
		};
		
		required_fields.forEach(field => {
			if (mapped_fields.includes(field)) {
				validation_results.required_mapped++;
			} else {
				validation_results.required_missing.push(field);
			}
		});
		
		// Show validation dialog
		let validation_dialog = new frappe.ui.Dialog({
			title: __('Field Mapping Validation'),
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'validation_html',
					options: generate_validation_html(validation_results)
				}
			],
			primary_action_label: __('Close'),
			primary_action() {
				validation_dialog.hide();
			}
		});
		
		validation_dialog.show();
		
	} catch (e) {
		frappe.msgprint(__('Invalid field mapping JSON format.'));
	}
}

function generate_validation_html(results) {
	let html = `
		<div class="validation-results">
			<div class="row mb-3">
				<div class="col-md-6">
					<div class="card border-info">
						<div class="card-body text-center">
							<h4 class="text-info">${results.mapped_headers}</h4>
							<small>Mapped Headers</small>
						</div>
					</div>
				</div>
				<div class="col-md-6">
					<div class="card border-warning">
						<div class="card-body text-center">
							<h4 class="text-warning">${results.unmapped_headers}</h4>
							<small>Unmapped Headers</small>
						</div>
					</div>
				</div>
			</div>
			
			<div class="row mb-3">
				<div class="col-md-6">
					<div class="card border-success">
						<div class="card-body text-center">
							<h4 class="text-success">${results.required_mapped}/4</h4>
							<small>Required Fields Mapped</small>
						</div>
					</div>
				</div>
				<div class="col-md-6">
					<div class="card border-danger">
						<div class="card-body text-center">
							<h4 class="text-danger">${results.required_missing.length}</h4>
							<small>Required Fields Missing</small>
						</div>
					</div>
				</div>
			</div>
	`;
	
	if (results.required_missing.length > 0) {
		html += `
			<div class="alert alert-danger">
				<h6>Missing Required Fields:</h6>
				<ul class="mb-0">
		`;
		results.required_missing.forEach(field => {
			html += `<li>${field}</li>`;
		});
		html += `
				</ul>
			</div>
		`;
	} else {
		html += `
			<div class="alert alert-success">
				<i class="fa fa-check-circle"></i> All required fields are mapped. You can proceed with processing.
			</div>
		`;
	}
	
	html += `</div>`;
	return html;
}


function revalidate_data(frm) {
	frm.dashboard.add_comment('Re-validating data with current field mapping...', 'blue', true);
	
	frm.save().then(() => {
		frm.dashboard.clear_comment();
		frappe.show_alert({
			message: __('Data re-validated successfully'),
			indicator: 'green'
		});
	});
}

function initialize_enhanced_features(frm) {
	// Initialize Chart.js if available
	if (typeof Chart !== 'undefined') {
		// Charts will be initialized by the HTML code
		console.log('Chart.js is available for enhanced visualizations');
	}
	
	// Initialize field mapping interactions
	setTimeout(() => {
		setup_field_mapping_interactions();
		setup_vendor_data_interactions();
	}, 1000);
}

function setup_field_mapping_interactions() {
	// Enhanced field mapping functions
	window.update_mapping_status = function(select) {
		const row = select.closest('tr');
		const statusBadge = row.querySelector('.mapping-status');
		
		if (select.value) {
			statusBadge.className = 'badge bg-success mapping-status';
			statusBadge.textContent = 'Mapped';
		} else {
			statusBadge.className = 'badge bg-warning mapping-status';
			statusBadge.textContent = 'Unmapped';
		}
		
		update_mapping_summary();
		update_mapping_progress();
	};
	
	window.update_mapping_summary = function() {
		const selects = document.querySelectorAll('.field-mapping-select');
		let mapped = 0, unmapped = 0;
		
		selects.forEach(select => {
			if (select.value) mapped++;
			else unmapped++;
		});
		
		// Update badges
		const mappedEl = document.querySelector('.mapped-count');
		const unmappedEl = document.querySelector('.unmapped-count');
		const totalEl = document.querySelector('.total-count');
		
		if (mappedEl) mappedEl.textContent = mapped;
		if (unmappedEl) unmappedEl.textContent = unmapped;
		if (totalEl) totalEl.textContent = mapped + unmapped;
	};
	
	window.update_mapping_progress = function() {
		const selects = document.querySelectorAll('.field-mapping-select');
		const mapped = Array.from(selects).filter(s => s.value).length;
		const total = selects.length;
		const percentage = total > 0 ? (mapped / total * 100) : 0;
		
		// Update progress bar in mapping stats
		const progressBar = document.querySelector('.mapping-stats-section .progress-bar');
		if (progressBar) {
			progressBar.style.width = percentage + '%';
			progressBar.textContent = percentage.toFixed(1) + '% Mapped';
		}
	};
	
	window.apply_auto_mapping = function() {
		if (!cur_frm) return;
		
		frappe.call({
			method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.get_auto_mapping',
			args: {
				docname: cur_frm.doc.name
			},
			callback: function(r) {
				if (r.message) {
					const mapping = r.message;
					document.querySelectorAll('.field-mapping-select').forEach(select => {
						const header = select.dataset.header;
						if (mapping[header]) {
							select.value = mapping[header];
							update_mapping_status(select);
						}
					});
					frappe.show_alert('Auto mapping applied successfully');
					update_mapping_progress();
				}
			}
		});
	};
	
	window.clear_all_mapping = function() {
		document.querySelectorAll('.field-mapping-select').forEach(select => {
			select.value = '';
			update_mapping_status(select);
		});
		frappe.show_alert('All mappings cleared');
		update_mapping_progress();
	};
	
	window.save_field_mapping = function() {
		if (!cur_frm) return;
		
		const mapping = {};
		document.querySelectorAll('.field-mapping-select').forEach(select => {
			mapping[select.dataset.header] = select.value;
		});
		
		cur_frm.set_value('field_mapping', JSON.stringify(mapping, null, 2));
		cur_frm.save().then(() => {
			frappe.show_alert('Field mapping saved successfully');
		});
	};
}

function setup_vendor_data_interactions() {
	// Enhanced vendor data functions
	window.highlight_vendor_row = function(rowId) {
		// Remove existing highlights
		document.querySelectorAll('.vendor-row').forEach(row => {
			row.classList.remove('table-warning');
		});
		
		// Highlight selected row
		const targetRow = document.querySelector(`[data-row="${rowId}"]`);
		if (targetRow) {
			targetRow.classList.add('table-warning');
			targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
		}
	};
	
	// Add click handlers to vendor rows
	document.querySelectorAll('.vendor-row').forEach(row => {
		row.addEventListener('click', function() {
			const rowId = this.dataset.row;
			highlight_vendor_row(rowId);
		});
	});
}



function add_help_text(frm) {
	if (!frm.doc.csv_xl) {
		frm.dashboard.add_comment(`
			<strong>Getting Started:</strong><br>
			1. Download the field mapping template to understand available fields<br>
			2. Prepare your CSV file with vendor data<br>
			3. Upload the CSV file using the "CSV/XL File" field<br>
			4. Review and adjust the automatic field mapping<br>
			5. Validate the data and process the import
		`, 'blue');
	} else if (frm.doc.csv_xl && !frm.doc.field_mapping) {
		frm.dashboard.add_comment(`
			<strong>Field Mapping Required:</strong><br>
			Please review and configure the field mapping below to proceed with validation and import.
		`, 'orange');
	} else if (frm.doc.field_mapping && !frm.doc.existing_vendor_initialized) {
		frm.dashboard.add_comment(`
			<strong>Ready to Process:</strong><br>
			Field mapping is configured. Review the validation results and click "Process Vendors" to start the import.
		`, 'green');
	}
}

function style_form(frm) {
	// Add custom CSS for better styling
	if (!$('#enhanced-vendor-import-styles').length) {
		$('<style id="enhanced-vendor-import-styles">')
			.text(`
				.enhanced-vendor-import .card {
					box-shadow: 0 2px 4px rgba(0,0,0,0.1);
					border: 1px solid #e3e6f0;
					margin-bottom: 1rem;
					border-radius: 8px;
				}
				
				.enhanced-vendor-import .card-header {
					background-color: #f8f9fa;
					border-bottom: 1px solid #e3e6f0;
					font-weight: 600;
					border-radius: 8px 8px 0 0;
				}
				
				.enhanced-vendor-import .table-responsive {
					max-height: 500px;
					overflow-y: auto;
				}
				
				.enhanced-vendor-import .badge {
					font-size: 0.75rem;
				}
				
				.enhanced-vendor-import .alert {
					border-left: 4px solid;
					margin-bottom: 1rem;
					border-radius: 4px;
				}
				
				.enhanced-vendor-import .spinner-border {
					width: 2rem;
					height: 2rem;
				}
				
				.import-results .card {
					transition: transform 0.2s;
					border-radius: 8px;
				}
				
				.import-results .card:hover {
					transform: translateY(-2px);
				}
				
				.field-mapping-container {
					margin: 20px 0;
					padding: 20px;
					background: #f8f9fa;
					border-radius: 10px;
					border: 1px solid #dee2e6;
				}
				
				.field-mapping-container .table {
					background: white;
					border-radius: 6px;
					overflow: hidden;
				}
				
				.field-mapping-container .form-control {
					border-radius: 4px;
					border: 1px solid #ced4da;
				}
				
				.field-mapping-container .form-control:focus {
					border-color: #80bdff;
					box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
				}
				
				.validation-results .card {
					border-radius: 6px;
					margin-bottom: 10px;
				}
				
				.btn-group-custom {
					margin: 5px 0;
				}
				
				.btn-group-custom .btn {
					margin-right: 5px;
					margin-bottom: 5px;
					border-radius: 4px;
				}
				
				.progress {
					border-radius: 10px;
					overflow: hidden;
				}
				
				.progress-bar {
					transition: width 0.6s ease;
				}
				
				.mapping-summary {
					padding: 10px;
					background: #e9ecef;
					border-radius: 6px;
					font-size: 0.9rem;
				}
				
				.mapping-summary .badge {
					margin-right: 8px;
					padding: 6px 10px;
				}
				
				@media (max-width: 768px) {
					.field-mapping-container {
						padding: 10px;
					}
					
					.btn-group-custom .btn {
						width: 100%;
						margin-bottom: 10px;
					}
				}
			`)
			.appendTo('head');
	}
	
	// Add class to form wrapper
	frm.wrapper.addClass('enhanced-vendor-import');
}

// Custom field validation
frappe.ui.form.on("Existing Vendor Import", {
	validate(frm) {
		if (!frm.doc.csv_xl) {
			frappe.validated = false;
			frappe.msgprint(__('Please upload a CSV/Excel file.'));
			return false;
		}
		
		// Check file extension
		let file_url = frm.doc.csv_xl;
		let file_extension = file_url.split('.').pop().toLowerCase();
		
		if (!['csv', 'xlsx', 'xls'].includes(file_extension)) {
			frappe.validated = false;
			frappe.msgprint(__('Please upload a valid CSV or Excel file.'));
			return false;
		}
		
		return true;
	}
});

// Global helper functions for field mapping interface
window.update_mapping_status = function(select) {
	const row = select.closest('tr');
	const statusBadge = row.querySelector('.mapping-status');
	
	if (select.value) {
		statusBadge.className = 'badge bg-success mapping-status';
		statusBadge.textContent = 'Mapped';
	} else {
		statusBadge.className = 'badge bg-warning mapping-status';
		statusBadge.textContent = 'Unmapped';
	}
	
	update_mapping_summary();
};

window.update_mapping_summary = function() {
	const selects = document.querySelectorAll('.field-mapping-select');
	let mapped = 0, unmapped = 0;
	
	selects.forEach(select => {
		if (select.value) mapped++;
		else unmapped++;
	});
	
	const mappedCountEl = document.querySelector('.mapped-count');
	const unmappedCountEl = document.querySelector('.unmapped-count');
	const totalCountEl = document.querySelector('.total-count');
	
	if (mappedCountEl) mappedCountEl.textContent = mapped;
	if (unmappedCountEl) unmappedCountEl.textContent = unmapped;
	if (totalCountEl) totalCountEl.textContent = mapped + unmapped;
};

window.apply_auto_mapping = function() {
	if (!cur_frm) return;
	
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.get_auto_mapping',
		args: {
			docname: cur_frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				const mapping = r.message;
				document.querySelectorAll('.field-mapping-select').forEach(select => {
					const header = select.dataset.header;
					if (mapping[header]) {
						select.value = mapping[header];
						update_mapping_status(select);
					}
				});
				frappe.show_alert('Auto mapping applied successfully');
			}
		}
	});
};

window.clear_all_mapping = function() {
	document.querySelectorAll('.field-mapping-select').forEach(select => {
		select.value = '';
		update_mapping_status(select);
	});
	frappe.show_alert('All mappings cleared');
};

window.save_field_mapping = function() {
	if (!cur_frm) return;
	
	const mapping = {};
	document.querySelectorAll('.field-mapping-select').forEach(select => {
		mapping[select.dataset.header] = select.value;
	});
	
	cur_frm.set_value('field_mapping', JSON.stringify(mapping, null, 2));
	cur_frm.save().then(() => {
		frappe.show_alert('Field mapping saved successfully');
	});
};

// Initialize when DOM is ready
$(document).ready(function() {
	// Auto-update mapping summary if elements exist
	setTimeout(function() {
		if (typeof update_mapping_summary === 'function') {
			update_mapping_summary();
		}
	}, 1000);
});


$(document).ready(function() {
	// Auto-update mapping summary if elements exist
	setTimeout(function() {
		if (typeof update_mapping_summary === 'function') {
			update_mapping_summary();
		}
		if (typeof update_mapping_progress === 'function') {
			update_mapping_progress();
		}
	}, 2000);
});

// Global download function accessible from HTML
window.download_processed_data = function(type) {
	if (cur_frm) {
		download_processed_data(cur_frm, type);
	}
};$(document).ready(function() {
	// Auto-update mapping summary if elements exist
	setTimeout(function() {
		if (typeof update_mapping_summary === 'function') {
			update_mapping_summary();
		}
		if (typeof update_mapping_progress === 'function') {
			update_mapping_progress();
		}
	}, 2000);
});

// Global download function accessible from HTML
window.download_processed_data = function(type) {
	if (cur_frm) {
		download_processed_data(cur_frm, type);
	}
};