// Enhanced existing_vendor_import.js
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

		// Initialize enhanced features
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
		
		frm.add_custom_button(__('Preview Import'), function() {
			preview_import(frm);
		}, __('Actions')).addClass('btn-secondary');
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
	// The HTML will be displayed in the field_mapping_html field
	frm.refresh_field('field_mapping_html');
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
				
				// Refresh form to show updated status
				frm.reload_doc();
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
	let mapping = {};
	try {
		mapping = JSON.parse(frm.doc.field_mapping || '{}');
	} catch(e) {
		frappe.msgprint(__('Invalid field mapping format.'));
		return false;
	}
	
	// Check for required fields
	let requiredFields = ['vendor_name'];
	let missingFields = [];
	
	let mappedFields = Object.values(mapping).filter(v => v);
	
	for (let field of requiredFields) {
		if (!mappedFields.includes(field)) {
			missingFields.push(field);
		}
	}
	
	if (missingFields.length > 0) {
		frappe.msgprint({
			title: __('Missing Required Mappings'),
			message: __('Please map the following required fields: ') + missingFields.join(', '),
			indicator: 'orange'
		});
		return false;
	}
	
	return true;
}

function show_results_dialog(results, frm) {
	let html = `
		<div class="import-results">
			<div class="row">
				<div class="col-md-6">
					<div class="card border-success">
						<div class="card-header bg-success text-white">
							<h6 class="mb-0"><i class="fa fa-check-circle"></i> Import Summary</h6>
						</div>
						<div class="card-body">
							<div class="row text-center">
								<div class="col-6">
									<h4 class="text-primary">${results.total_processed}</h4>
									<small>Total Processed</small>
								</div>
								<div class="col-6">
									<h4 class="text-success">${results.vendors_created}</h4>
									<small>Vendors Created</small>
								</div>
							</div>
						</div>
					</div>
				</div>
				<div class="col-md-6">
					<div class="card border-info">
						<div class="card-header bg-info text-white">
							<h6 class="mb-0"><i class="fa fa-building"></i> Company Codes</h6>
						</div>
						<div class="card-body">
							<div class="row text-center">
								<div class="col-6">
									<h4 class="text-success">${results.company_codes_created}</h4>
									<small>Created</small>
								</div>
								<div class="col-6">
									<h4 class="text-warning">${results.company_codes_updated}</h4>
									<small>Updated</small>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
	`;
	
	if (results.errors && results.errors.length > 0) {
		html += `
			<div class="card border-danger mt-3">
				<div class="card-header bg-danger text-white">
					<h6 class="mb-0"><i class="fa fa-exclamation-triangle"></i> Errors (${results.errors.length})</h6>
				</div>
				<div class="card-body" style="max-height: 200px; overflow-y: auto;">
		`;
		
		results.errors.forEach(error => {
			html += `<div class="alert alert-danger py-1 mb-1"><small>${error}</small></div>`;
		});
		
		html += '</div></div>';
	}
	
	if (results.warnings && results.warnings.length > 0) {
		html += `
			<div class="card border-warning mt-3">
				<div class="card-header bg-warning text-dark">
					<h6 class="mb-0"><i class="fa fa-exclamation-triangle"></i> Warnings (${results.warnings.length})</h6>
				</div>
				<div class="card-body" style="max-height: 200px; overflow-y: auto;">
		`;
		
		results.warnings.forEach(warning => {
			html += `<div class="alert alert-warning py-1 mb-1"><small>${warning}</small></div>`;
		});
		
		html += '</div></div>';
	}
	
	html += '</div>';
	
	let results_dialog = new frappe.ui.Dialog({
		title: __('Import Results'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'results_html',
				options: html
			}
		],
		primary_action_label: __('Download Report'),
		primary_action() {
			download_processed_data(frm, 'all');
		},
		secondary_action_label: __('Close'),
		secondary_action() {
			results_dialog.hide();
		}
	});
	
	results_dialog.show();
}

function get_progress_html() {
	return `
		<div class="progress-container text-center">
			<div class="spinner-border text-primary mb-3" role="status">
				<span class="sr-only">Loading...</span>
			</div>
			<h5>Processing Vendor Import</h5>
			<p class="text-muted">Please wait while we process your vendor data...</p>
			
			<div class="progress-steps mt-4">
				<div class="step active">
					<i class="fa fa-check-circle"></i> Validating Data
				</div>
				<div class="step">
					<i class="fa fa-cog fa-spin"></i> Creating Vendors
				</div>
				<div class="step">
					<i class="fa fa-clock"></i> Linking Companies
				</div>
				<div class="step">
					<i class="fa fa-clock"></i> Finalizing
				</div>
			</div>
		</div>
		
		<style>
			.progress-steps {
				display: flex;
				justify-content: space-between;
				margin-top: 20px;
			}
			
			.step {
				text-align: center;
				flex: 1;
				padding: 10px;
				border-radius: 6px;
				margin: 0 5px;
				background: #f8f9fa;
				border: 1px solid #dee2e6;
			}
			
			.step.active {
				background: #e3f2fd;
				border-color: #2196f3;
				color: #1976d2;
			}
			
			.step i {
				display: block;
				font-size: 1.2rem;
				margin-bottom: 5px;
			}
		</style>
	`;
}

function download_processed_data(frm, data_type) {
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.download_processed_data',
		args: {
			docname: frm.doc.name,
			data_type: data_type
		},
		callback: function(r) {
			if (r.message) {
				// Open download link
				window.open(r.message.file_url, '_blank');
				frappe.show_alert({
					message: __('Download started: ') + r.message.file_name,
					indicator: 'green'
				});
			}
		}
	});
}

function download_field_mapping_template() {
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.download_field_mapping_template',
		callback: function(r) {
			if (r.message) {
				window.open(r.message.file_url, '_blank');
				frappe.show_alert({
					message: __('Template downloaded successfully'),
					indicator: 'green'
				});
			}
		}
	});
}

function download_sample_template() {
	// Generate sample CSV data
	let sample_data = [{
		'Vendor Name': 'Sample Vendor Pvt Ltd.',
		'Vendor Code': '10001',
		'C.Code': '2000',
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
			let headers = [];
			try {
				headers = JSON.parse(frm.doc.original_headers || '[]');
			} catch(e) {
				headers = [];
			}
			
			// Create empty mapping object
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
	);
}

function validate_field_mapping(frm) {
	if (!frm.doc.field_mapping) {
		frappe.msgprint(__('No field mapping to validate.'));
		return;
	}
	
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.validate_import_data',
		args: {
			docname: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				let results = r.message;
				
				let message = `
					<div class="validation-summary">
						<h6>Validation Results:</h6>
						<ul>
							<li><strong>Total Records:</strong> ${results.total_records}</li>
							<li><strong>Valid Records:</strong> <span class="text-success">${results.valid_records}</span></li>
							<li><strong>Invalid Records:</strong> <span class="text-danger">${results.invalid_records}</span></li>
							<li><strong>Errors:</strong> <span class="text-danger">${results.errors ? results.errors.length : 0}</span></li>
							<li><strong>Warnings:</strong> <span class="text-warning">${results.warnings ? results.warnings.length : 0}</span></li>
						</ul>
					</div>
				`;
				
				frappe.msgprint({
					title: __('Validation Complete'),
					message: message,
					indicator: results.errors && results.errors.length > 0 ? 'red' : 'green'
				});
				
				// Refresh to show updated validation results
				frm.refresh();
			}
		}
	});
}

function revalidate_data(frm) {
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.validate_import_data',
		args: {
			docname: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				frappe.show_alert({
					message: __('Data re-validated successfully'),
					indicator: 'green'
				});
				frm.reload_doc();
			}
		}
	});
}

function preview_import(frm) {
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.get_vendor_import_preview',
		args: {
			docname: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.preview_data) {
				show_preview_dialog(r.message, frm);
			}
		}
	});
}

function show_preview_dialog(preview_data, frm) {
	let html = '<div class="preview-container">';
	
	// Summary
	html += `
		<div class="preview-summary mb-3">
			<div class="row">
				<div class="col-md-4">
					<div class="text-center">
						<h4 class="text-primary">${preview_data.total_records}</h4>
						<small>Total Records</small>
					</div>
				</div>
				<div class="col-md-4">
					<div class="text-center">
						<h4 class="text-success">${preview_data.mapped_fields}</h4>
						<small>Mapped Fields</small>
					</div>
				</div>
				<div class="col-md-4">
					<div class="text-center">
						<h4 class="text-info">5</h4>
						<small>Preview Records</small>
					</div>
				</div>
			</div>
		</div>
	`;
	
	// Preview table
	if (preview_data.preview_data && preview_data.preview_data.length > 0) {
		let firstRow = preview_data.preview_data[0];
		let fields = Object.keys(firstRow).filter(key => !key.startsWith('_'));
		
		html += `
			<div class="table-responsive">
				<table class="table table-bordered table-striped">
					<thead class="table-dark">
						<tr>
							<th>Row</th>
		`;
		
		fields.forEach(field => {
			html += `<th>${field.replace(/_/g, ' ').toUpperCase()}</th>`;
		});
		
		html += '</tr></thead><tbody>';
		
		preview_data.preview_data.forEach(row => {
			html += `<tr><td><span class="badge bg-secondary">${row._row_number}</span></td>`;
			fields.forEach(field => {
				let value = row[field] || 'N/A';
				html += `<td>${value}</td>`;
			});
			html += '</tr>';
		});
		
		html += '</tbody></table></div>';
	}
	
	html += '</div>';
	
	let preview_dialog = new frappe.ui.Dialog({
		title: __('Import Preview'),
		size: 'extra-large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'preview_html',
				options: html
			}
		],
		primary_action_label: __('Proceed with Import'),
		primary_action() {
			preview_dialog.hide();
			process_vendors(frm);
		}
	});
	
	preview_dialog.show();
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

function initialize_enhanced_features(frm) {
	// Add Chart.js for validation charts
	if (typeof Chart === 'undefined') {
		frappe.require('https://cdn.jsdelivr.net/npm/chart.js', () => {
			console.log('Chart.js loaded for vendor import visualizations');
		});
	}
	
	// Add export functionality
	if (frm.doc.vendor_data) {
		add_export_functionality(frm);
	}
	
	// Add real-time validation
	if (frm.doc.field_mapping && frm.doc.vendor_data) {
		setup_realtime_validation(frm);
	}
}

function add_export_functionality(frm) {
	// Add export menu to the form
	if (!frm.page.menu.find('[data-label="Export Data"]').length) {
		frm.page.add_menu_item(__('Export Data'), function() {
			show_export_dialog(frm);
		});
	}
}

function show_export_dialog(frm) {
	let export_dialog = new frappe.ui.Dialog({
		title: __('Export Options'),
		fields: [
			{
				fieldtype: 'Select',
				fieldname: 'export_type',
				label: 'Export Type',
				options: [
					'All Records',
					'Valid Records Only',
					'Invalid Records Only',
					'Field Mapping Template'
				],
				default: 'All Records'
			},
			{
				fieldtype: 'Select',
				fieldname: 'export_format',
				label: 'Format',
				options: ['Excel', 'CSV'],
				default: 'Excel'
			},
			{
				fieldtype: 'Check',
				fieldname: 'include_validation',
				label: 'Include Validation Results',
				default: 1
			}
		],
		primary_action_label: __('Export'),
		primary_action(values) {
			export_dialog.hide();
			
			if (values.export_type === 'Field Mapping Template') {
				download_field_mapping_template();
			} else {
				let data_type = values.export_type.toLowerCase().includes('valid') ? 'valid' : 
							   values.export_type.toLowerCase().includes('invalid') ? 'invalid' : 'all';
				download_processed_data(frm, data_type);
			}
		}
	});
	
	export_dialog.show();
}

function setup_realtime_validation(frm) {
	// Add real-time field mapping validation
	frappe.realtime.on('vendor_import_progress', function(data) {
		if (data.docname === frm.doc.name) {
			update_progress_indicator(data);
		}
	});
}

function update_progress_indicator(data) {
	// Update any progress indicators based on real-time data
	if (data.status === 'processing') {
		$('.progress-bar').css('width', data.percentage + '%');
	}
}

// Enhanced validation functions
function validate_csv_structure(frm) {
	if (!frm.doc.vendor_data) {
		return false;
	}
	
	try {
		let data = JSON.parse(frm.doc.vendor_data);
		return data && data.length > 0;
	} catch(e) {
		return false;
	}
}

function get_mapping_completeness(frm) {
	if (!frm.doc.field_mapping) {
		return 0;
	}
	
	try {
		let mapping = JSON.parse(frm.doc.field_mapping);
		let total = Object.keys(mapping).length;
		let mapped = Object.values(mapping).filter(v => v).length;
		return total > 0 ? (mapped / total * 100) : 0;
	} catch(e) {
		return 0;
	}
}

// Advanced features
function show_duplicate_analysis(frm) {
	frappe.call({
		method: 'vms.vendor_onboarding.doctype.existing_vendor_import.existing_vendor_import.get_import_summary',
		args: {
			docname: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				show_analytics_dialog(r.message);
			}
		}
	});
}

function show_analytics_dialog(summary) {
	let html = `
		<div class="analytics-container">
			<div class="row">
				<div class="col-md-6">
					<h6>Data Distribution</h6>
					<div class="analytics-item">
						<strong>Companies:</strong> ${summary.companies.length}
						<div class="small text-muted">${summary.companies.join(', ')}</div>
					</div>
					<div class="analytics-item">
						<strong>States:</strong> ${summary.states.length}
						<div class="small text-muted">${summary.states.join(', ')}</div>
					</div>
				</div>
				<div class="col-md-6">
					<h6>Field Mapping</h6>
					<div class="progress mb-2">
						<div class="progress-bar bg-success" style="width: ${summary.field_mapping_percentage}%">
							${summary.field_mapping_percentage.toFixed(1)}%
						</div>
					</div>
					<div class="analytics-item">
						<strong>Mapped Fields:</strong> ${summary.mapped_fields}
					</div>
					<div class="analytics-item">
						<strong>Unmapped Fields:</strong> ${summary.unmapped_fields}
					</div>
				</div>
			</div>
		</div>
		
		<style>
			.analytics-item {
				margin-bottom: 10px;
				padding: 8px;
				background: #f8f9fa;
				border-radius: 4px;
			}
		</style>
	`;
	
	let analytics_dialog = new frappe.ui.Dialog({
		title: __('Import Analytics'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'analytics_html',
				options: html
			}
		]
	});
	
	analytics_dialog.show();
}

// Custom field validation
frappe.ui.form.on("Existing Vendor Import", {
	validate(frm) {
		if (!frm.doc.csv_xl) {
			frappe.validated = false;
			frappe.msgprint(__('Please upload a CSV/Excel file.'));
			return;
		}
		
		// Basic file validation (extension check)
		if (frm.doc.csv_xl) {
			let file_url = frm.doc.csv_xl;
			let file_extension = file_url.split('.').pop().toLowerCase();
			
			if (!['csv', 'xlsx', 'xls'].includes(file_extension)) {
				frappe.validated = false;
				frappe.msgprint(__('Please upload a valid CSV or Excel file.'));
				return;
			}
		}
	}
});

// Auto-save functionality
let auto_save_timeout;
frappe.ui.form.on("Existing Vendor Import", {
	field_mapping(frm) {
		// Clear existing timeout
		if (auto_save_timeout) {
			clearTimeout(auto_save_timeout);
		}
		
		// Set new timeout for auto-save
		auto_save_timeout = setTimeout(() => {
			if (frm.doc.field_mapping && frm.doc.vendor_data) {
				frm.save();
			}
		}, 2000); // Auto-save after 2 seconds of inactivity
	}
});

// Keyboard shortcuts
$(document).on('keydown', function(e) {
	if (cur_frm && cur_frm.doctype === 'Existing Vendor Import') {
		// Ctrl+S for save
		if (e.ctrlKey && e.which === 83) {
			e.preventDefault();
			cur_frm.save();
		}
		
		// Ctrl+P for process
		if (e.ctrlKey && e.which === 80) {
			e.preventDefault();
			if (cur_frm.doc.field_mapping && !cur_frm.doc.existing_vendor_initialized) {
				process_vendors(cur_frm);
			}
		}
	}
});

// Form enhancement on load
frappe.ui.form.on("Existing Vendor Import", {
	onload(frm) {
		// Set initial state
		if (frm.is_new()) {
			frm.set_value('existing_vendor_initialized', 0);
		}
		
		// Add custom CSS
		style_form(frm);
		
		// Initialize tooltips
		setTimeout(() => {
			$('[data-toggle="tooltip"]').tooltip();
		}, 1000);
	}
});