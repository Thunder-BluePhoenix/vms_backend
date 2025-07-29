# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd
import json
import os
from frappe.utils import cstr, flt, cint, today, now, get_site_path, validate_email_address
from frappe.utils.file_manager import get_file
import zipfile
from io import BytesIO
import re


class ExistingVendorImport(Document):
	def validate(self):
		if self.csv_xl and not self.existing_vendor_initialized:
			self.parse_and_validate_data()

	def parse_and_validate_data(self):
		"""Parse CSV/Excel file and validate data - UPDATED"""
		try:
			# Get file content
			file_doc = frappe.get_doc("File", {"file_url": self.csv_xl})
			file_path = file_doc.get_full_path()
			
			# Read file based on extension
			if file_path.endswith('.csv'):
				df = pd.read_csv(file_path)
			else:
				df = pd.read_excel(file_path)
			
			# Clean column names
			df.columns = df.columns.str.strip()
			
			# Store original headers for mapping
			self.original_headers = json.dumps(list(df.columns))
			
			# Convert DataFrame to list of dictionaries
			vendor_data = df.to_dict('records')
			
			# Store parsed data
			self.vendor_data = json.dumps(vendor_data, indent=2, default=str)
			
			# Generate field mapping interface
			self.generate_field_mapping_html(df.columns)
			
			# Auto-apply mapping if not manually set
			if not self.field_mapping:
				auto_mapping = self.generate_auto_mapping(df.columns)
				self.field_mapping = json.dumps(auto_mapping, indent=2)
			
			# ADD THIS LINE: Generate mapping statistics
			self.mapping_statistics = self.generate_mapping_statistics_html()
			
			# Validate and process data
			validation_results = self.validate_vendor_data(vendor_data)
			self.success_fail_rate = json.dumps(validation_results, indent=2)
			
			# Generate HTML for display
			self.generate_display_html(vendor_data, validation_results)
			
		except Exception as e:
			frappe.throw(f"Error parsing file: {str(e)}")




	def generate_auto_mapping(self, csv_headers):
		"""Generate automatic field mapping based on header similarity"""
		
		# Define mapping patterns including Multiple Company Data fields
		mapping_patterns = {
			# Vendor Master fields
			'vendor_name': ['vendor name', 'company name', 'supplier name', 'name'],
			'office_email_primary': ['primary email', 'email-id', 'email', 'contact email', 'office email'],
			'office_email_secondary': ['secondary email', 'alternate email', 'backup email'],
			'mobile_number': ['contact no', 'phone', 'mobile', 'telephone', 'contact number'],
			'country': ['country'],
			
			# Company Vendor Code fields
			'company_code': ['c.code', 'company code', 'comp code'],
			'vendor_code': ['vendor code', 'supplier code', 'sap code'],
			'gst_no': ['gstn no', 'gst no', 'gst number', 'gstin'],
			'state': ['state'],
			
			# Company Details fields
			'company_pan_number': ['pan no', 'pan number', 'pan'],
			'address_line_1': ['address01', 'address 1', 'address line 1', 'street 1'],
			'address_line_2': ['address02', 'address 2', 'address line 2', 'street 2'],
			'city': ['city'],
			'pincode': ['pincode', 'pin code', 'postal code', 'zip'],
			'telephone_number': ['telephone number', 'landline', 'office phone'],
			
			# Multiple Company Data fields
			'purchase_organization': ['purchase organization', 'purchase org', 'po', 'porg'],
			'account_group': ['account group', 'acc group', 'account grp'],
			'terms_of_payment': ['terms of payment', 'payment terms', 'payment condition'],
			'purchase_group': ['purchase group', 'purchasing group', 'purch group'],
			'order_currency': ['order currency', 'currency', 'curr'],
			'incoterms': ['incoterm', 'incoterms', 'delivery terms'],
			'reconciliation_account': ['reconciliation account', 'recon account', 'gl account'],
			
			# Payment Details fields
			'bank_name': ['bank name'],
			'ifsc_code': ['ifsc code', 'ifsc'],
			'account_number': ['account number', 'bank account'],
			'name_of_account_holder': ['name of account holder', 'account holder name'],
			'type_of_account': ['type of account', 'account type'],
			
			# Additional fields
			'vendor_gst_classification': ['vendor gst classification', 'gst classification'],
			'nature_of_services': ['nature of services', 'service type'],
			'vendor_type': ['vendor type', 'supplier type'],
			'remarks': ['remarks', 'comments', 'notes']
		}
		
		auto_mapping = {}
		
		for csv_header in csv_headers:
			csv_header_lower = csv_header.lower().strip()
			mapped = False
			
			# Try to find exact or partial matches
			for field_name, patterns in mapping_patterns.items():
				for pattern in patterns:
					if pattern in csv_header_lower or csv_header_lower in pattern:
						auto_mapping[csv_header] = field_name
						mapped = True
						break
				if mapped:
					break
			
			# If no mapping found, set to None
			if not mapped:
				auto_mapping[csv_header] = None
		
		return auto_mapping

	def generate_field_mapping_html(self, csv_headers):
		"""Generate HTML interface for field mapping with statistics"""
	
		# Get all available target fields
		target_fields = self.get_all_target_fields()
		
		# Generate auto mapping
		auto_mapping = self.generate_auto_mapping(csv_headers)
		
		# Calculate mapping statistics
		mapped_count = sum(1 for v in auto_mapping.values() if v)
		unmapped_count = len(auto_mapping) - mapped_count
		mapping_percentage = (mapped_count / len(auto_mapping) * 100) if auto_mapping else 0
		
		html = f"""
		<div class="field-mapping-container">
			<div class="card">
				<div class="card-header bg-primary text-white">
					<h5 class="mb-0"><i class="fa fa-exchange-alt"></i> Field Mapping Configuration</h5>
					<small>Map your CSV columns to system fields. Auto-mapping has been applied based on header similarity.</small>
				</div>
				<div class="card-body">
					<!-- Mapping Statistics -->
					<div class="mapping-stats-section mb-4">
						<div class="row">
							<div class="col-md-8">
								<h6>Mapping Statistics</h6>
								<div class="progress mb-2" style="height: 25px;">
									<div class="progress-bar bg-success" role="progressbar" 
										style="width: {mapping_percentage}%" 
										aria-valuenow="{mapping_percentage}" 
										aria-valuemin="0" 
										aria-valuemax="100">
										{mapping_percentage:.1f}% Mapped
									</div>
								</div>
								<div class="mapping-summary">
									<span class="badge bg-success mapped-count">{mapped_count}</span> Mapped &nbsp;
									<span class="badge bg-warning unmapped-count">{unmapped_count}</span> Unmapped &nbsp;
									<span class="badge bg-info total-count">{len(auto_mapping)}</span> Total
								</div>
							</div>
							<div class="col-md-4">
								<div class="mapping-actions">
									<button type="button" class="btn btn-info btn-sm mb-1" onclick="apply_auto_mapping()">
										<i class="fa fa-magic"></i> Re-apply Auto Mapping
									</button><br>
									<button type="button" class="btn btn-warning btn-sm" onclick="clear_all_mapping()">
										<i class="fa fa-eraser"></i> Clear All Mapping
									</button>
								</div>
							</div>
						</div>
					</div>
					
					<div class="table-responsive">
						<table class="table table-bordered table-hover mapping-table">
							<thead class="table-dark">
								<tr>
									<th width="5%">#</th>
									<th width="35%">CSV Column Header</th>
									<th width="35%">Map to System Field</th>
									<th width="15%">Status</th>
									<th width="10%">Sample Data</th>
								</tr>
							</thead>
							<tbody>
		"""
		
		# Get sample data for preview
		sample_data = {}
		if self.vendor_data:
			vendor_data = json.loads(self.vendor_data)
			if vendor_data:
				sample_data = vendor_data[0]  # First row as sample
		
		for idx, header in enumerate(csv_headers):
			auto_mapped_field = auto_mapping.get(header, '')
			status_class = 'success' if auto_mapped_field else 'warning'
			status_text = 'Mapped' if auto_mapped_field else 'Unmapped'
			
			# Get sample data for this column
			sample_value = sample_data.get(header, 'N/A')
			if pd.isna(sample_value):
				sample_value = 'N/A'
			else:
				sample_value = str(sample_value)[:20] + '...' if len(str(sample_value)) > 20 else str(sample_value)
			
			options_html = '<option value="">-- Select Field --</option>'
			for field_group, fields in target_fields.items():
				options_html += f'<optgroup label="{field_group}">'
				for field_key, field_label in fields.items():
					selected = 'selected' if field_key == auto_mapped_field else ''
					options_html += f'<option value="{field_key}" {selected}>{field_label}</option>'
				options_html += '</optgroup>'
			
			html += f"""
				<tr data-header="{header}">
					<td>{idx + 1}</td>
					<td>
						<strong>{header}</strong>
					</td>
					<td>
						<select class="form-control field-mapping-select" 
								data-header="{header}" 
								onchange="update_mapping_status(this)">
							{options_html}
						</select>
					</td>
					<td>
						<span class="badge bg-{status_class} mapping-status">{status_text}</span>
					</td>
					<td>
						<small class="text-muted">{sample_value}</small>
					</td>
				</tr>
			"""
		
		html += """
						</tbody>
					</table>
				</div>
				
				<div class="card-footer">
					<div class="row">
						<div class="col-md-8">
							<div class="required-fields-info">
								<small><strong>Required Fields:</strong> Vendor Name, Vendor Code, Company Code, State</small>
							</div>
						</div>
						<div class="col-md-4 text-right">
							<button type="button" class="btn btn-primary" onclick="save_field_mapping()">
								<i class="fa fa-save"></i> Save Mapping
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
		
		<style>
			.mapping-stats-section {
				background: #f8f9fa;
				padding: 15px;
				border-radius: 8px;
				border: 1px solid #dee2e6;
			}
			
			.mapping-actions .btn {
				width: 100%;
			}
			
			.mapping-table th {
				background-color: #343a40 !important;
				color: white;
			}
			
			.mapping-table tr:hover {
				background-color: #f8f9fa;
			}
			
			.progress {
				border-radius: 10px;
			}
			
			.mapping-summary .badge {
				margin-right: 8px;
				padding: 6px 10px;
				font-size: 0.85rem;
			}
		</style>
		"""
		
		self.field_mapping_html = html









	


	def generate_mapping_statistics_html(self):
		"""Generate mapping statistics HTML"""
		if not self.field_mapping:
			return "<div class='alert alert-info'>Upload a file to see mapping statistics</div>"
		
		try:
			field_mapping = json.loads(self.field_mapping)
			
			# Calculate statistics
			total_fields = len(field_mapping)
			mapped_fields = sum(1 for v in field_mapping.values() if v)
			unmapped_fields = total_fields - mapped_fields
			mapping_percentage = (mapped_fields / total_fields * 100) if total_fields > 0 else 0
			
			# Required fields check
			required_fields = ['vendor_name', 'vendor_code', 'company_code', 'state']
			mapped_required = sum(1 for v in field_mapping.values() if v in required_fields)
			
			# Field category breakdown
			target_fields = self.get_all_target_fields()
			category_stats = {}
			for category in target_fields.keys():
				category_stats[category] = 0
			
			for system_field in field_mapping.values():
				if system_field:
					for category, fields in target_fields.items():
						if system_field in fields:
							category_stats[category] += 1
							break
			
			html = f"""
			<div class="mapping-statistics-container">
				<div class="card">
					<div class="card-header bg-info text-white">
						<h6 class="mb-0"><i class="fa fa-chart-pie"></i> Mapping Statistics</h6>
					</div>
					<div class="card-body">
						<!-- Overall Progress -->
						<div class="mb-3">
							<div class="d-flex justify-content-between mb-1">
								<span>Overall Mapping Progress</span>
								<span>{mapping_percentage:.1f}%</span>
							</div>
							<div class="progress" style="height: 20px;">
								<div class="progress-bar bg-success" role="progressbar" 
									style="width: {mapping_percentage}%" 
									aria-valuenow="{mapping_percentage}" 
									aria-valuemin="0" 
									aria-valuemax="100">
									{mapped_fields}/{total_fields}
								</div>
							</div>
						</div>
						
						<!-- Summary Cards -->
						<div class="row mb-3">
							<div class="col-md-3">
								<div class="stat-card bg-primary text-white">
									<div class="stat-number">{total_fields}</div>
									<div class="stat-label">Total Fields</div>
								</div>
							</div>
							<div class="col-md-3">
								<div class="stat-card bg-success text-white">
									<div class="stat-number">{mapped_fields}</div>
									<div class="stat-label">Mapped</div>
								</div>
							</div>
							<div class="col-md-3">
								<div class="stat-card bg-warning text-white">
									<div class="stat-number">{unmapped_fields}</div>
									<div class="stat-label">Unmapped</div>
								</div>
							</div>
							<div class="col-md-3">
								<div class="stat-card bg-info text-white">
									<div class="stat-number">{mapped_required}/4</div>
									<div class="stat-label">Required</div>
								</div>
							</div>
						</div>
						
						<!-- Category Breakdown -->
						<div class="category-breakdown">
							<h6>Field Categories</h6>
							<div class="row">
			"""
			
			for category, count in category_stats.items():
				percentage = (count / mapped_fields * 100) if mapped_fields > 0 else 0
				html += f"""
					<div class="col-md-6 mb-2">
						<div class="category-item">
							<div class="d-flex justify-content-between">
								<span class="category-name">{category}</span>
								<span class="category-count">{count}</span>
							</div>
							<div class="progress" style="height: 8px;">
								<div class="progress-bar bg-info" style="width: {percentage}%"></div>
							</div>
						</div>
					</div>
				"""
			
			html += """
						</div>
					</div>
				</div>
			</div>
			</div>
			
			<style>
				.stat-card {
					padding: 15px;
					border-radius: 8px;
					text-align: center;
					margin-bottom: 10px;
				}
				
				.stat-number {
					font-size: 1.8rem;
					font-weight: bold;
				}
				
				.stat-label {
					font-size: 0.9rem;
					opacity: 0.9;
				}
				
				.category-item {
					padding: 8px 12px;
					background: #f8f9fa;
					border-radius: 6px;
					border: 1px solid #dee2e6;
				}
				
				.category-name {
					font-size: 0.85rem;
					font-weight: 500;
				}
				
				.category-count {
					font-size: 0.85rem;
					font-weight: bold;
					color: #495057;
				}
			</style>
			"""
			
			return html
			
		except Exception as e:
			return f"<div class='alert alert-danger'>Error generating statistics: {str(e)}</div>"

	def generate_vendor_data_schema_html(self, vendor_data, validation_results):
		"""Generate enhanced vendor data HTML with schema and graph format - FIXED SYNTAX"""
		
		if not vendor_data:
			return "<div class='alert alert-info'>No vendor data available</div>"
		
		field_mapping = json.loads(self.field_mapping) if self.field_mapping else {}
		
		total_records = len(vendor_data)
		valid_records = validation_results.get('valid_records', 0)
		invalid_records = validation_results.get('invalid_records', 0)
		total_columns = len(field_mapping)
		
		html = """
		<div class="vendor-data-container">
			<!-- Data Overview -->
			<div class="card mb-3">
				<div class="card-header bg-primary text-white">
					<h5 class="mb-0"><i class="fa fa-database"></i> Vendor Data Schema & Preview</h5>
				</div>
				<div class="card-body">
					<div class="row">
						<div class="col-md-8">
							<div class="data-stats">
								<div class="row">
									<div class="col-md-3">
										<div class="stat-box bg-primary">
											<div class="stat-number">{}</div>
											<div class="stat-label">Total Records</div>
										</div>
									</div>
									<div class="col-md-3">
										<div class="stat-box bg-success">
											<div class="stat-number">{}</div>
											<div class="stat-label">Valid Records</div>
										</div>
									</div>
									<div class="col-md-3">
										<div class="stat-box bg-danger">
											<div class="stat-number">{}</div>
											<div class="stat-label">Invalid Records</div>
										</div>
									</div>
									<div class="col-md-3">
										<div class="stat-box bg-info">
											<div class="stat-number">{}</div>
											<div class="stat-label">CSV Columns</div>
										</div>
									</div>
								</div>
							</div>
						</div>
						<div class="col-md-4">
							<div class="validation-chart">
								<canvas id="validationChart" width="200" height="200"></canvas>
							</div>
						</div>
					</div>
				</div>
			</div>
			
			<!-- Data Schema Visualization -->
			<div class="card mb-3">
				<div class="card-header bg-info text-white">
					<h6 class="mb-0"><i class="fa fa-sitemap"></i> Data Flow Schema</h6>
				</div>
				<div class="card-body">
					<div class="schema-diagram">
						{}
					</div>
				</div>
			</div>
			
			<!-- Detailed Data Table -->
			<div class="card">
				<div class="card-header bg-dark text-white">
					<h6 class="mb-0"><i class="fa fa-table"></i> Vendor Records Preview</h6>
				</div>
				<div class="card-body">
					<div class="table-responsive">
						<table class="table table-striped table-bordered vendor-data-table">
							<thead class="table-dark">
								<tr>
									<th width="5%">ID</th>
									<th width="15%">Vendor Name</th>
									<th width="10%">Code</th>
									<th width="10%">Company</th>
									<th width="10%">State</th>
									<th width="15%">GST</th>
									<th width="15%">Email</th>
									<th width="10%">Phone</th>
									<th width="10%">Status</th>
								</tr>
							</thead>
							<tbody>
		""".format(total_records, valid_records, invalid_records, total_columns, self.generate_schema_diagram())
		
		# Display actual vendor data
		for idx, row in enumerate(vendor_data[:10], 1):  # Show first 10 records
			mapped_row = self.apply_field_mapping(row, field_mapping)
			
			# Determine status
			is_valid = idx <= valid_records
			status_class = "success" if is_valid else "danger"
			status_text = "Valid" if is_valid else "Invalid"
			
			# Get values with fallbacks
			vendor_name = mapped_row.get('vendor_name', 'N/A')
			vendor_code = mapped_row.get('vendor_code', 'N/A')
			company_code = mapped_row.get('company_code', 'N/A')
			state = mapped_row.get('state', 'N/A')
			gst = mapped_row.get('gst') or mapped_row.get('gst_no', 'N/A')
			email = mapped_row.get('office_email_primary', 'N/A')
			phone = mapped_row.get('mobile_number', 'N/A')
			
			# Truncate long values
			vendor_name = (vendor_name[:20] + '...') if len(str(vendor_name)) > 20 else vendor_name
			email = (email[:20] + '...') if len(str(email)) > 20 else email
			
			html += """
				<tr class="vendor-row" data-row="{}">
					<td>
						<span class="badge bg-secondary">{}</span>
					</td>
					<td>
						<strong>{}</strong>
					</td>
					<td>
						<code>{}</code>
					</td>
					<td>
						<span class="company-code">{}</span>
					</td>
					<td>
						<span class="state-name">{}</span>
					</td>
					<td>
						<small class="gst-number">{}</small>
					</td>
					<td>
						<small class="email-address">{}</small>
					</td>
					<td>
						<small class="phone-number">{}</small>
					</td>
					<td>
						<span class="badge bg-{}">{}</span>
					</td>
				</tr>
			""".format(idx, idx, vendor_name, vendor_code, company_code, state, gst, email, phone, status_class, status_text)
		
		if len(vendor_data) > 10:
			html += """
				<tr>
					<td colspan="9" class="text-center text-muted">
						<i class="fa fa-ellipsis-h"></i> ... and {} more records
					</td>
				</tr>
			""".format(len(vendor_data) - 10)
		
		# Add Chart.js script and CSS
		html += """
							</tbody>
						</table>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Chart.js for Validation Chart -->
		<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
		<script>
			document.addEventListener('DOMContentLoaded', function() {
				// Create validation pie chart
				const ctx = document.getElementById('validationChart');
				if (ctx) {
					const context = ctx.getContext('2d');
					new Chart(context, {
						type: 'pie',
						data: {
							labels: ['Valid Records', 'Invalid Records'],
							datasets: [{
								data: [""" + str(valid_records) + """, """ + str(invalid_records) + """],
								backgroundColor: ['#28a745', '#dc3545'],
								borderWidth: 2,
								borderColor: '#fff'
							}]
						},
						options: {
							responsive: true,
							maintainAspectRatio: false,
							plugins: {
								legend: {
									position: 'bottom',
									labels: {
										fontSize: 12,
										padding: 10
									}
								}
							}
						}
					});
				}
			});
		</script>
		
		<style>
			.vendor-data-container .card {
				box-shadow: 0 2px 4px rgba(0,0,0,0.1);
				border-radius: 8px;
			}
			
			.stat-box {
				padding: 15px;
				border-radius: 8px;
				text-align: center;
				color: white;
				margin-bottom: 10px;
			}
			
			.stat-number {
				font-size: 1.5rem;
				font-weight: bold;
			}
			
			.stat-label {
				font-size: 0.85rem;
				opacity: 0.9;
			}
			
			.validation-chart {
				height: 200px;
				position: relative;
			}
			
			.vendor-data-table {
				font-size: 0.9rem;
			}
			
			.vendor-row:hover {
				background-color: #f8f9fa !important;
			}
			
			.company-code, .state-name {
				background: #e3f2fd;
				padding: 2px 6px;
				border-radius: 3px;
				font-size: 0.8rem;
			}
			
			.gst-number, .email-address, .phone-number {
				font-family: monospace;
			}
			
			.schema-diagram {
				text-align: center;
				padding: 20px;
			}
		</style>
		"""
		
		return html

	def generate_schema_diagram(self):
		"""Generate a visual schema diagram"""
		return """
		<div class="schema-flow">
			<div class="schema-step">
				<div class="step-box csv-box">
					<i class="fa fa-file-csv fa-2x"></i>
					<div class="step-title">CSV Data</div>
					<div class="step-desc">Raw vendor data</div>
				</div>
			</div>
			<div class="schema-arrow">→</div>
			<div class="schema-step">
				<div class="step-box mapping-box">
					<i class="fa fa-exchange-alt fa-2x"></i>
					<div class="step-title">Field Mapping</div>
					<div class="step-desc">CSV to System fields</div>
				</div>
			</div>
			<div class="schema-arrow">→</div>
			<div class="schema-step">
				<div class="step-box validation-box">
					<i class="fa fa-check-circle fa-2x"></i>
					<div class="step-title">Validation</div>
					<div class="step-desc">Data quality checks</div>
				</div>
			</div>
			<div class="schema-arrow">→</div>
			<div class="schema-step">
				<div class="step-box processing-box">
					<i class="fa fa-cogs fa-2x"></i>
					<div class="step-title">Processing</div>
					<div class="step-desc">Create vendor records</div>
				</div>
			</div>
		</div>
		
		<div class="data-flow-details mt-3">
			<div class="row">
				<div class="col-md-3">
					<div class="flow-detail">
						<h6>Vendor Master</h6>
						<small>Basic vendor info</small>
					</div>
				</div>
				<div class="col-md-3">
					<div class="flow-detail">
						<h6>Company Data</h6>
						<small>Multi-company relationships</small>
					</div>
				</div>
				<div class="col-md-3">
					<div class="flow-detail">
						<h6>Vendor Codes</h6>
						<small>SAP codes by state</small>
					</div>
				</div>
				<div class="col-md-3">
					<div class="flow-detail">
						<h6>Company Details</h6>
						<small>Address & business info</small>
					</div>
				</div>
			</div>
		</div>
		
		<style>
			.schema-flow {
				display: flex;
				align-items: center;
				justify-content: center;
				flex-wrap: wrap;
				gap: 20px;
			}
			
			.step-box {
				padding: 20px;
				border-radius: 10px;
				text-align: center;
				color: white;
				min-width: 120px;
			}
			
			.csv-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
			.mapping-box { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
			.validation-box { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
			.processing-box { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
			
			.step-title {
				font-weight: bold;
				margin: 10px 0 5px 0;
			}
			
			.step-desc {
				font-size: 0.8rem;
				opacity: 0.9;
			}
			
			.schema-arrow {
				font-size: 1.5rem;
				color: #6c757d;
				font-weight: bold;
			}
			
			.flow-detail {
				background: #f8f9fa;
				padding: 10px;
				border-radius: 6px;
				border: 1px solid #dee2e6;
				text-align: center;
			}
			
			.flow-detail h6 {
				color: #495057;
				margin-bottom: 5px;
			}
			
			@media (max-width: 768px) {
				.schema-flow {
					flex-direction: column;
				}
				.schema-arrow {
					transform: rotate(90deg);
				}
			}
		</style>
		"""



	def generate_mapping_statistics_html(self):
		"""Generate mapping statistics HTML"""
		if not self.field_mapping:
			return "<div class='alert alert-info'>Upload a file to see mapping statistics</div>"
		
		try:
			field_mapping = json.loads(self.field_mapping)
			
			# Calculate statistics
			total_fields = len(field_mapping)
			mapped_fields = sum(1 for v in field_mapping.values() if v)
			unmapped_fields = total_fields - mapped_fields
			mapping_percentage = (mapped_fields / total_fields * 100) if total_fields > 0 else 0
			
			html = f"""
			<div class="card">
				<div class="card-header bg-info text-white">
					<h6><i class="fa fa-chart-pie"></i> Mapping Statistics</h6>
				</div>
				<div class="card-body">
					<div class="progress mb-3" style="height: 25px;">
						<div class="progress-bar bg-success" style="width: {mapping_percentage}%">
							{mapping_percentage:.1f}% Mapped
						</div>
					</div>
					<div class="row text-center">
						<div class="col-md-4">
							<h4 class="text-primary">{total_fields}</h4>
							<small>Total Fields</small>
						</div>
						<div class="col-md-4">
							<h4 class="text-success">{mapped_fields}</h4>
							<small>Mapped</small>
						</div>
						<div class="col-md-4">
							<h4 class="text-warning">{unmapped_fields}</h4>
							<small>Unmapped</small>
						</div>
					</div>
				</div>
			</div>
			"""
			return html
			
		except Exception as e:
			return f"<div class='alert alert-danger'>Error: {str(e)}</div>"



	def get_all_target_fields(self):
		"""Get all available target fields organized by DocType"""
		
		return {
			"Vendor Master": {
				"vendor_name": "Vendor Name",
				"office_email_primary": "Primary Email",
				"office_email_secondary": "Secondary Email", 
				"mobile_number": "Mobile Number",
				"country": "Country",
				"payee_in_document": "Payee in Document",
				"gr_based_inv_ver": "GR Based Invoice Verification",
				"service_based_inv_ver": "Service Based Invoice Verification",
				"check_double_invoice": "Check Double Invoice"
			},
			
			"Company Details": {
				"company_name": "Company Name",
				"gst": "GST Number",
				"company_pan_number": "PAN Number",
				"address_line_1": "Address Line 1",
				"address_line_2": "Address Line 2",
				"city": "City",
				"state": "State",
				"country": "Country",
				"pincode": "Pincode",
				"telephone_number": "Telephone Number",
				"nature_of_business": "Nature of Business",
				"type_of_business": "Type of Business",
				"corporate_identification_number": "CIN Number",
				"established_year": "Established Year"
			},
			
			"Company Vendor Code": {
				"company_code": "Company Code",
				"vendor_code": "Vendor Code", 
				"gst_no": "GST Number",
				"state": "State"
			},
			
			"Multiple Company Data": {
				"purchase_organization": "Purchase Organization",
				"account_group": "Account Group",
				"terms_of_payment": "Terms of Payment",
				"purchase_group": "Purchase Group",
				"order_currency": "Order Currency",
				"incoterms": "Incoterms",
				"reconciliation_account": "Reconciliation Account"
			},
			
			"Payment Details": {
				"bank_name": "Bank Name",
				"ifsc_code": "IFSC Code",
				"account_number": "Account Number",
				"name_of_account_holder": "Account Holder Name",
				"type_of_account": "Account Type"
			},
			
			"International Banking": {
				"beneficiary_name": "Beneficiary Name",
				"beneficiary_swift_code": "Beneficiary Swift Code",
				"beneficiary_iban_no": "Beneficiary IBAN",
				"beneficiary_aba_no": "Beneficiary ABA Number",
				"beneficiary_bank_address": "Beneficiary Bank Address",
				"beneficiary_bank_name": "Beneficiary Bank Name",
				"beneficiary_account_no": "Beneficiary Account Number",
				"beneficiary_currency": "Beneficiary Currency"
			},
			
			"Additional Fields": {
				"vendor_gst_classification": "GST Classification",
				"nature_of_services": "Nature of Services",
				"vendor_type": "Vendor Type",
				"remarks": "Remarks",
				"contact_person": "Contact Person",
				"hod": "HOD",
				"enterprise_registration_no": "Enterprise Registration Number"
			}
		}

	def validate_vendor_data(self, vendor_data):
		"""Validate each vendor record using current field mapping"""
		results = {
			"total_records": len(vendor_data),
			"valid_records": 0,
			"invalid_records": 0,
			"errors": [],
			"warnings": []
		}
		
		# Get current field mapping
		field_mapping = json.loads(self.field_mapping) if self.field_mapping else {}
		
		for idx, row in enumerate(vendor_data, 1):
			try:
				errors = []
				warnings = []
				
				# Apply field mapping to get system field values
				mapped_row = self.apply_field_mapping(row, field_mapping)
				
				# Mandatory field validation using mapped fields
				if not mapped_row.get('vendor_name'):
					errors.append(f"Row {idx}: Vendor Name is mandatory")
				
				if not mapped_row.get('vendor_code'):
					errors.append(f"Row {idx}: Vendor Code is mandatory")
				
				if not mapped_row.get('company_code'):
					errors.append(f"Row {idx}: Company Code is mandatory")
				
				if not mapped_row.get('state'):
					errors.append(f"Row {idx}: State is mandatory")
				
				# Email validation - check both primary and secondary
				email_primary = mapped_row.get('office_email_primary')
				if email_primary and not self.validate_email_format(email_primary):
					warnings.append(f"Row {idx}: Invalid primary email format: {email_primary}")
				
				email_secondary = mapped_row.get('office_email_secondary')
				if email_secondary and not self.validate_email_format(email_secondary):
					warnings.append(f"Row {idx}: Invalid secondary email format: {email_secondary}")
				
				# GST validation
				gst = mapped_row.get('gst') or mapped_row.get('gst_no')
				if gst and not self.validate_gst_format(gst):
					warnings.append(f"Row {idx}: Invalid GST format: {gst}")
				
				# PAN validation
				pan = mapped_row.get('company_pan_number')
				if pan and not self.validate_pan_format(pan):
					warnings.append(f"Row {idx}: Invalid PAN format: {pan}")
				
				# Phone validation
				phone = mapped_row.get('mobile_number')
				if phone and not self.validate_phone_format(phone):
					warnings.append(f"Row {idx}: Invalid phone format: {phone}")
				
				# Check if vendor already exists
				existing_vendor = frappe.db.exists("Vendor Master", {"vendor_name": mapped_row.get('vendor_name')})
				if existing_vendor:
					warnings.append(f"Row {idx}: Vendor '{mapped_row.get('vendor_name')}' already exists - will update")
				
				if errors:
					results["invalid_records"] += 1
					results["errors"].extend(errors)
				else:
					results["valid_records"] += 1
				
				if warnings:
					results["warnings"].extend(warnings)
					
			except Exception as e:
				results["invalid_records"] += 1
				results["errors"].append(f"Row {idx}: Validation error - {str(e)}")
		
		return results

	def validate_email_format(self, email):
		"""Validate email format"""
		if not email or pd.isna(email):
			return True
		
		email_str = str(email).strip()
		if not email_str:
			return True
			
		# Basic email validation
		email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
		return bool(re.match(email_pattern, email_str))

	def validate_gst_format(self, gst):
		"""Validate GST format"""
		if not gst or pd.isna(gst):
			return True
		
		gst_str = str(gst).strip()
		if not gst_str:
			return True
			
		# GST should be 15 characters alphanumeric
		return len(gst_str) == 15 and gst_str.isalnum()

	def validate_pan_format(self, pan):
		"""Validate PAN format"""
		if not pan or pd.isna(pan):
			return True
		
		pan_str = str(pan).strip()
		if not pan_str:
			return True
			
		# PAN should be 10 characters alphanumeric
		return len(pan_str) == 10 and pan_str.isalnum()

	def validate_phone_format(self, phone):
		"""Validate phone format"""
		if not phone or pd.isna(phone):
			return True
		
		phone_str = str(phone).strip()
		if not phone_str:
			return True
		
		# Remove non-digit characters and check length
		digits_only = re.sub(r'\D', '', phone_str)
		return 10 <= len(digits_only) <= 15

	def apply_field_mapping(self, row, field_mapping):
		"""Apply field mapping to convert CSV row to system fields"""
		mapped_row = {}
		
		for csv_header, system_field in field_mapping.items():
			if system_field and csv_header in row:
				value = row[csv_header]
				# Handle NaN values
				if pd.isna(value):
					mapped_row[system_field] = None
				else:
					mapped_row[system_field] = str(value).strip() if value else None
		
		return mapped_row

	def generate_display_html(self, vendor_data, validation_results):
		"""Generate HTML for displaying vendor data and validation results - FIXED SYNTAX"""
		
		total_records = validation_results.get('total_records', 0)
		valid_records = validation_results.get('valid_records', 0)
		invalid_records = validation_results.get('invalid_records', 0)
		warnings_count = len(validation_results.get('warnings', []))
		
		success_rate = (valid_records / total_records * 100) if total_records > 0 else 0
		
		# Use .format() instead of f-strings to avoid JavaScript conflicts
		success_html = """
		<div class="import-summary-container">
			<div class="card">
				<div class="card-header bg-primary text-white">
					<h5 class="mb-0"><i class="fa fa-chart-bar"></i> Import Summary & Statistics</h5>
				</div>
				<div class="card-body">
					<div class="row">
						<div class="col-md-4">
							<div class="text-center summary-stat">
								<div class="stat-circle bg-primary">
									<span class="stat-number">{}</span>
								</div>
								<p class="stat-label">Total Records</p>
							</div>
						</div>
						<div class="col-md-4">
							<div class="text-center summary-stat">
								<div class="stat-circle bg-success">
									<span class="stat-number">{}</span>
								</div>
								<p class="stat-label">Valid Records</p>
							</div>
						</div>
						<div class="col-md-4">
							<div class="text-center summary-stat">
								<div class="stat-circle bg-danger">
									<span class="stat-number">{}</span>
								</div>
								<p class="stat-label">Invalid Records</p>
							</div>
						</div>
					</div>
					
					<div class="mt-4">
						<div class="row">
							<div class="col-md-8">
								<div class="progress-section">
									<div class="d-flex justify-content-between mb-2">
										<span>Success Rate</span>
										<span>{:.1f}%</span>
									</div>
									<div class="progress" style="height: 25px;">
										<div class="progress-bar bg-success" role="progressbar" 
											style="width: {:.1f}%" 
											aria-valuenow="{}" 
											aria-valuemin="0" 
											aria-valuemax="{}">
											{}/{}
										</div>
									</div>
								</div>
							</div>
							<div class="col-md-4">
								<div class="download-actions">
									<button type="button" class="btn btn-success btn-sm mb-1" onclick="download_processed_data('valid')">
										<i class="fa fa-download"></i> Valid Records
									</button><br>
									<button type="button" class="btn btn-danger btn-sm mb-1" onclick="download_processed_data('invalid')">
										<i class="fa fa-download"></i> Invalid Records  
									</button><br>
									<button type="button" class="btn btn-info btn-sm" onclick="download_processed_data('all')">
										<i class="fa fa-download"></i> All Data
									</button>
								</div>
							</div>
						</div>
					</div>
					
					{}
				</div>
			</div>
		</div>
		
		{}
		""".format(
			total_records, valid_records, invalid_records,
			success_rate, success_rate, valid_records, total_records, valid_records, total_records,
			self.generate_validation_charts(validation_results),
			self.generate_errors_html(validation_results)
		)
		
		# Enhanced Vendor Data HTML with schema
		vendor_html = self.generate_vendor_data_schema_html(vendor_data, validation_results)
		
		# Add CSS
		css = """
		<style>
			.summary-stat {
				margin-bottom: 20px;
			}
			
			.stat-circle {
				width: 80px;
				height: 80px;
				border-radius: 50%;
				display: flex;
				align-items: center;
				justify-content: center;
				margin: 0 auto 10px auto;
				color: white;
			}
			
			.stat-number {
				font-size: 1.5rem;
				font-weight: bold;
			}
			
			.stat-label {
				font-weight: 500;
				color: #495057;
			}
			
			.progress-section {
				background: #f8f9fa;
				padding: 15px;
				border-radius: 8px;
				border: 1px solid #dee2e6;
			}
			
			.download-actions .btn {
				width: 100%;
			}
			
			.validation-charts {
				background: #fff;
				padding: 20px;
				border-radius: 8px;
				border: 1px solid #dee2e6;
				margin-top: 20px;
			}
		</style>
		"""
		
		self.success_fail_rate_html = success_html + css
		self.vendor_html = vendor_html
		
		# Also generate mapping statistics
		self.mapping_statistics = self.generate_mapping_statistics_html()



	def generate_validation_charts(self, validation_results):
		"""Generate validation charts section - FIXED SYNTAX"""
		if not validation_results:
			return ""
		
		errors_count = len(validation_results.get('errors', []))
		warnings_count = len(validation_results.get('warnings', []))
		valid_records = validation_results.get('valid_records', 0)
		invalid_records = validation_results.get('invalid_records', 0)
		
		# Use regular string formatting to avoid f-string conflicts with JavaScript
		html = """
		<div class="validation-charts">
			<div class="row">
				<div class="col-md-6">
					<h6>Validation Results</h6>
					<canvas id="validationResultsChart" width="300" height="200"></canvas>
				</div>
				<div class="col-md-6">
					<h6>Issue Breakdown</h6>
					<div class="issue-stats">
						<div class="issue-item">
							<div class="issue-icon bg-danger">
								<i class="fa fa-times"></i>
							</div>
							<div class="issue-details">
								<div class="issue-count">{}</div>
								<div class="issue-label">Errors</div>
							</div>
						</div>
						<div class="issue-item">
							<div class="issue-icon bg-warning">
								<i class="fa fa-exclamation-triangle"></i>
							</div>
							<div class="issue-details">
								<div class="issue-count">{}</div>
								<div class="issue-label">Warnings</div>
							</div>
						</div>
						<div class="issue-item">
							<div class="issue-icon bg-success">
								<i class="fa fa-check"></i>
							</div>
							<div class="issue-details">
								<div class="issue-count">{}</div>
								<div class="issue-label">Clean Records</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
		""".format(errors_count, warnings_count, valid_records)
		
		# Add JavaScript separately to avoid f-string conflicts
		javascript = """
		<script>
			document.addEventListener('DOMContentLoaded', function() {
				// Validation Results Chart
				const ctx2 = document.getElementById('validationResultsChart');
				if (ctx2) {
					const context = ctx2.getContext('2d');
					new Chart(context, {
						type: 'doughnut',
						data: {
							labels: ['Valid', 'Invalid', 'Errors', 'Warnings'],
							datasets: [{
								data: [""" + str(valid_records) + """, """ + str(invalid_records) + """, """ + str(errors_count) + """, """ + str(warnings_count) + """],
								backgroundColor: ['#28a745', '#dc3545', '#fd7e14', '#ffc107'],
								borderWidth: 2,
								borderColor: '#fff'
							}]
						},
						options: {
							responsive: true,
							maintainAspectRatio: false,
							plugins: {
								legend: {
									position: 'bottom',
									labels: {
										fontSize: 10,
										padding: 8
									}
								}
							}
						}
					});
				}
			});
		</script>
		"""
		
		css = """
		<style>
			.issue-stats {
				display: flex;
				flex-direction: column;
				gap: 15px;
			}
			
			.issue-item {
				display: flex;
				align-items: center;
				padding: 10px;
				background: #f8f9fa;
				border-radius: 8px;
				border: 1px solid #dee2e6;
			}
			
			.issue-icon {
				width: 40px;
				height: 40px;
				border-radius: 50%;
				display: flex;
				align-items: center;
				justify-content: center;
				color: white;
				margin-right: 15px;
			}
			
			.issue-details {
				flex: 1;
			}
			
			.issue-count {
				font-size: 1.2rem;
				font-weight: bold;
				color: #495057;
			}
			
			.issue-label {
				font-size: 0.9rem;
				color: #6c757d;
			}
		</style>
		"""
		
		return html + javascript + css


	def generate_errors_html(self, validation_results):
		"""Generate HTML for displaying errors and warnings"""
		if not validation_results.get('errors') and not validation_results.get('warnings'):
			return '<div class="alert alert-success">No validation errors found!</div>'
		
		html = ""
		
		if validation_results.get('errors'):
			html += """
			<div class="card mt-3">
				<div class="card-header bg-danger text-white">
					<h6>Validation Errors</h6>
				</div>
				<div class="card-body">
					<ul class="list-unstyled">
			"""
			for error in validation_results['errors'][:20]:  # Limit to 20 errors
				html += f'<li class="text-danger">• {error}</li>'
			
			if len(validation_results['errors']) > 20:
				html += f'<li class="text-muted">... and {len(validation_results["errors"]) - 20} more errors</li>'
			
			html += """
					</ul>
				</div>
			</div>
			"""
		
		if validation_results.get('warnings'):
			html += """
			<div class="card mt-3">
				<div class="card-header bg-warning">
					<h6>Validation Warnings</h6>
				</div>
				<div class="card-body">
					<ul class="list-unstyled">
			"""
			for warning in validation_results['warnings'][:20]:  # Limit to 20 warnings
				html += f'<li class="text-warning">• {warning}</li>'
			
			if len(validation_results['warnings']) > 20:
				html += f'<li class="text-muted">... and {len(validation_results["warnings"]) - 20} more warnings</li>'
			
			html += """
					</ul>
				</div>
			</div>
			"""
		
		return html
	def update_mapping_statistics_field(self):
		"""Update the mapping_statistics field in the document"""
		self.mapping_statistics = self.generate_mapping_statistics_html()

	@frappe.whitelist()
	def process_vendors(self):
		"""Process and create vendor records"""
		if not self.vendor_data:
			frappe.throw("No vendor data found. Please upload and validate the file first.")
		
		if not self.field_mapping:
			frappe.throw("Field mapping not configured. Please set up field mapping first.")
		
		vendor_data = json.loads(self.vendor_data)
		field_mapping = json.loads(self.field_mapping)
		
		results = {
			"total_processed": 0,
			"successful": 0,
			"failed": 0,
			"errors": []
		}
		
		for idx, row in enumerate(vendor_data, 1):
			try:
				mapped_row = self.apply_field_mapping(row, field_mapping)
				
				if self.is_valid_vendor_row(mapped_row):
					self.create_vendor_from_row(mapped_row, idx)
					results["successful"] += 1
				else:
					results["failed"] += 1
					results["errors"].append(f"Row {idx}: Validation failed - missing required fields")
				
				results["total_processed"] += 1
				
			except Exception as e:
				results["failed"] += 1
				results["errors"].append(f"Row {idx}: {str(e)}")
				frappe.log_error(frappe.get_traceback(), f"Vendor Import Error - Row {idx}")
		
		# Update status
		self.existing_vendor_initialized = 1
		self.save(ignore_permissions=True)
		
		# Return results
		frappe.msgprint(f"Import completed: {results['successful']} successful, {results['failed']} failed")
		return results

	def is_valid_vendor_row(self, mapped_row):
		"""Check if vendor row has all mandatory fields"""
		mandatory_fields = ['vendor_name', 'vendor_code', 'company_code', 'state']
		return all(mapped_row.get(field) for field in mandatory_fields)

	def create_vendor_from_row(self, mapped_row, row_idx):
		"""Create vendor master and related records from mapped row data"""
		
		# Check if vendor already exists
		existing_vendor = frappe.db.exists("Vendor Master", {"vendor_name": mapped_row.get('vendor_name')})
		if existing_vendor:
			vendor_name = existing_vendor
			self.update_existing_vendor(vendor_name, mapped_row)
		else:
			# Create new Vendor Master
			vendor = frappe.new_doc("Vendor Master")
			
			# Basic vendor details using mapped fields
			vendor.vendor_name = mapped_row.get('vendor_name')
			vendor.office_email_primary = mapped_row.get('office_email_primary')
			vendor.office_email_secondary = mapped_row.get('office_email_secondary')
			vendor.mobile_number = mapped_row.get('mobile_number')
			vendor.country = self.get_or_create_country(mapped_row.get('country', 'India'))
			vendor.status = "Active"
			vendor.created_from_registration = 0  # Existing vendor
			vendor.registered_date = now()
			
			# Set purchasing data
			vendor.payee_in_document = 1 if mapped_row.get('payee_in_document') else 0
			vendor.gr_based_inv_ver = 1
			vendor.service_based_inv_ver = 1
			vendor.check_double_invoice = 1
			
			# Save vendor master first
			vendor.insert(ignore_permissions=True)
			vendor_name = vendor.name
		
		# Create Company Vendor Code record
		company_vendor_code_name = self.create_company_vendor_code(vendor_name, mapped_row)
		
		# Create or update Multiple Company Data entry in Vendor Master
		self.create_multiple_company_data_entry(vendor_name, mapped_row, company_vendor_code_name)
		
		# Create vendor onboarding company details if needed
		self.create_vendor_company_details(vendor_name, mapped_row)
		
		return vendor_name

	def create_multiple_company_data_entry(self, vendor_ref_no, mapped_row, company_vendor_code_name):
		"""Create or update Multiple Company Data entry in Vendor Master"""
		
		vendor_doc = frappe.get_doc("Vendor Master", vendor_ref_no)
		company_code = str(mapped_row.get('company_code'))
		
		# Get company name from company code
		company_name = self.get_company_by_code(company_code)
		
		# Check if Multiple Company Data entry already exists for this company
		existing_entry = None
		if hasattr(vendor_doc, 'multiple_company_data') and vendor_doc.multiple_company_data:
			for entry in vendor_doc.multiple_company_data:
				if getattr(entry, 'company_name', '') == company_name:
					existing_entry = entry
					break
		
		if existing_entry:
			# Update existing entry
			existing_entry.company_vendor_code = company_vendor_code_name
			# Update other fields from mapped_row
			self.update_multiple_company_entry(existing_entry, mapped_row)
		else:
			# Create new Multiple Company Data entry
			new_entry = {
				"company_name": company_name,
				"company_vendor_code": company_vendor_code_name,
				"sap_client_code": company_code
			}
			
			# Add additional fields from mapped data
			self.populate_multiple_company_fields(new_entry, mapped_row)
			
			vendor_doc.append("multiple_company_data", new_entry)
		
		vendor_doc.save(ignore_permissions=True)
		return vendor_doc.name

	def populate_multiple_company_fields(self, entry, mapped_row):
		"""Populate Multiple Company Data fields from mapped CSV data"""
		
		# Map fields from CSV to Multiple Company Data fields
		field_mapping = {
			"purchase_organization": "purchase_organization",
			"account_group": "account_group", 
			"terms_of_payment": "terms_of_payment",
			"purchase_group": "purchase_group",
			"order_currency": "order_currency",
			"incoterms": "incoterm",
			"reconciliation_account": "reconciliation_account"
		}
		
		for csv_field, table_field in field_mapping.items():
			if csv_field in mapped_row and mapped_row[csv_field]:
				# Get master data reference
				master_value = self.get_master_data_reference(csv_field, mapped_row[csv_field])
				if master_value:
					entry[table_field] = master_value

	def update_multiple_company_entry(self, entry, mapped_row):
		"""Update existing Multiple Company Data entry"""
		self.populate_multiple_company_fields(entry, mapped_row)

	def get_master_data_reference(self, field_type, value):
		"""Get master data reference for Multiple Company Data fields"""
		
		master_mappings = {
			"purchase_organization": ("Purchase Organization Master", "purchase_organization_code"),
			"account_group": ("Account Group Master", "account_group_code"),
			"terms_of_payment": ("Terms of Payment Master", "payment_terms_code"),
			"purchase_group": ("Purchase Group Master", "purchase_group_code"),
			"order_currency": ("Currency Master", "currency_code"),
			"incoterms": ("Incoterm Master", "incoterm_code"),
			"reconciliation_account": ("Reconciliation Account", "account_code")
		}
		
		if field_type in master_mappings:
			doctype, field_name = master_mappings[field_type]
			
			# Try to find existing master record
			existing = frappe.db.exists(doctype, {field_name: value})
			if existing:
				return existing
			
			# If not found, try by name
			existing_by_name = frappe.db.exists(doctype, value)
			if existing_by_name:
				return existing_by_name
			
			# Log missing master data but don't fail
			frappe.log_error(f"Master data not found: {doctype} with {field_name} = {value}", "Vendor Import")
		
		return None

	def update_existing_vendor(self, vendor_name, mapped_row):
		"""Update existing vendor with new company/code data"""
		vendor = frappe.get_doc("Vendor Master", vendor_name)
		
		# Update basic info if not present
		if not vendor.office_email_primary and mapped_row.get('office_email_primary'):
			vendor.office_email_primary = mapped_row.get('office_email_primary')
		
		if not vendor.mobile_number and mapped_row.get('mobile_number'):
			vendor.mobile_number = mapped_row.get('mobile_number')
		
		vendor.save(ignore_permissions=True)

	def create_company_vendor_code(self, vendor_ref_no, mapped_row):
		"""Create or update Company Vendor Code record using mapped fields"""
		
		company_code = str(mapped_row.get('company_code'))
		vendor_code = str(mapped_row.get('vendor_code'))
		gst_no = mapped_row.get('gst_no') or mapped_row.get('gst', '')
		state = mapped_row.get('state', '')
		
		# Get company name from company code
		company_name = self.get_company_by_code(company_code)
		
		# Check if Company Vendor Code already exists
		existing_cvc = frappe.db.exists("Company Vendor Code", {
			"vendor_ref_no": vendor_ref_no,
			"company_code": company_code
		})
		
		if existing_cvc:
			# Update existing record
			cvc = frappe.get_doc("Company Vendor Code", existing_cvc)
		else:
			# Create new record
			cvc = frappe.new_doc("Company Vendor Code")
			cvc.vendor_ref_no = vendor_ref_no
			cvc.company_name = company_name
			cvc.company_code = company_code
			cvc.sap_client_code = company_code  # Assuming SAP client code is same as company code
		
		# Check if this exact vendor code already exists
		found_existing = False
		if hasattr(cvc, 'vendor_code') and cvc.vendor_code:
			for vc in cvc.vendor_code:
				if (getattr(vc, 'vendor_code', '') == vendor_code and 
					getattr(vc, 'gst_no', '') == gst_no and 
					getattr(vc, 'state', '') == state):
					found_existing = True
					break
		
		# Add new vendor code if not found
		if not found_existing:
			cvc.append("vendor_code", {
				"vendor_code": vendor_code,
				"gst_no": gst_no,
				"state": state
			})
		
		cvc.save(ignore_permissions=True)
		return cvc.name

	def create_vendor_company_details(self, vendor_ref_no, mapped_row):
		"""Create vendor onboarding company details record using mapped fields"""
		
		# Create company details record
		company_details = frappe.new_doc("Vendor Onboarding Company Details")
		
		# Basic company information using mapped fields
		company_details.vendor_name = mapped_row.get('vendor_name')
		company_details.company_name = mapped_row.get('company_name') or mapped_row.get('vendor_name')
		company_details.gst = mapped_row.get('gst') or mapped_row.get('gst_no')
		company_details.company_pan_number = mapped_row.get('company_pan_number')
		company_details.office_email_primary = mapped_row.get('office_email_primary')
		company_details.office_email_secondary = mapped_row.get('office_email_secondary')
		company_details.telephone_number = mapped_row.get('telephone_number') or mapped_row.get('mobile_number')
		
		# Address details
		company_details.address_line_1 = mapped_row.get('address_line_1')
		company_details.address_line_2 = mapped_row.get('address_line_2')
		company_details.city = self.get_or_create_city(mapped_row.get('city'))
		company_details.state = self.get_or_create_state(mapped_row.get('state'))
		company_details.country = self.get_or_create_country(mapped_row.get('country', 'India'))
		company_details.pincode = self.get_or_create_pincode(mapped_row.get('pincode'))
		
		# Business details
		company_details.nature_of_business = self.get_or_create_business_nature(
			mapped_row.get('nature_of_business', 'General Business')
		)
		company_details.type_of_business = mapped_row.get('type_of_business', 'Private Limited')
		company_details.corporate_identification_number = mapped_row.get('corporate_identification_number')
		company_details.established_year = mapped_row.get('established_year')
		
		company_details.insert(ignore_permissions=True)
		return company_details.name

	def get_company_by_code(self, company_code):
		"""Get company name by company code"""
		company = frappe.db.get_value("Company Master", {"company_code": company_code}, "name")
		if not company:
			# Create a default company if not found
			try:
				company_doc = frappe.new_doc("Company Master")
				company_doc.company_name = f"Company {company_code}"
				company_doc.company_code = company_code
				company_doc.sap_client_code = company_code
				company_doc.insert(ignore_permissions=True)
				frappe.log_error(f"Auto-created company with code {company_code}", "Vendor Import")
				return company_doc.name
			except:
				frappe.log_error(f"Company with code {company_code} not found and could not be created", "Vendor Import")
				return "Default Company"
		return company

	def get_or_create_country(self, country_name):
		"""Get or create country master"""
		if not country_name or country_name == "IN":
			country_name = "India"
		
		# Handle numeric country codes
		if str(country_name).isdigit():
			country_name = "India"
		
		country = frappe.db.exists("Country Master", {"country_name": country_name})
		if not country:
			try:
				country_doc = frappe.new_doc("Country Master")
				country_doc.country_name = country_name
				country_doc.country_code = country_name[:2].upper()
				country_doc.insert(ignore_permissions=True)
				return country_doc.name
			except:
				return None
		return country

	def get_or_create_state(self, state_name):
		"""Get or create state master"""
		if not state_name:
			return None
		
		state = frappe.db.exists("State Master", {"state_name": state_name})
		if not state:
			try:
				state_doc = frappe.new_doc("State Master")
				state_doc.state_name = state_name
				state_doc.state_code = state_name[:2].upper()
				state_doc.insert(ignore_permissions=True)
				return state_doc.name
			except:
				return None
		return state

	def get_or_create_city(self, city_name):
		"""Get or create city master"""
		if not city_name or pd.isna(city_name):
			return None
		
		city_str = str(city_name).strip()
		if not city_str:
			return None
		
		city = frappe.db.exists("City Master", {"city_name": city_str})
		if not city:
			try:
				city_doc = frappe.new_doc("City Master")
				city_doc.city_name = city_str
				city_doc.insert(ignore_permissions=True)
				return city_doc.name
			except:
				return None
		return city

	def get_or_create_pincode(self, pincode):
		"""Get or create pincode master"""
		if not pincode or pd.isna(pincode):
			return None
		
		pincode_str = str(pincode).strip()
		if not pincode_str:
			return None
		
		pincode_master = frappe.db.exists("Pincode Master", {"pincode": pincode_str})
		if not pincode_master:
			try:
				pincode_doc = frappe.new_doc("Pincode Master")
				pincode_doc.pincode = pincode_str
				pincode_doc.insert(ignore_permissions=True)
				return pincode_doc.name
			except:
				return None
		return pincode_master

	def get_or_create_business_nature(self, business_nature):
		"""Get or create business nature master"""
		if not business_nature:
			business_nature = "General Business"
		
		nature = frappe.db.exists("Business Nature Master", {"business_nature": business_nature})
		if not nature:
			try:
				nature_doc = frappe.new_doc("Business Nature Master")
				nature_doc.business_nature = business_nature
				nature_doc.insert(ignore_permissions=True)
				return nature_doc.name
			except:
				return None
		return nature


# API Methods
@frappe.whitelist()
def process_existing_vendors(docname):
	"""API method to process vendor import"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	return doc.process_vendors()


@frappe.whitelist()
def get_auto_mapping(docname):
	"""Get automatic field mapping for CSV headers"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.original_headers:
		return {}
	
	headers = json.loads(doc.original_headers)
	return doc.generate_auto_mapping(headers)


@frappe.whitelist()
def download_processed_data(docname, data_type="all"):
	"""Download processed data in various formats"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.vendor_data:
		frappe.throw("No vendor data found")
	
	vendor_data = json.loads(doc.vendor_data)
	field_mapping = json.loads(doc.field_mapping) if doc.field_mapping else {}
	validation_results = json.loads(doc.success_fail_rate) if doc.success_fail_rate else {}
	
	# Filter data based on type
	if data_type == "valid":
		# Get only valid records
		filtered_data = vendor_data[:validation_results.get('valid_records', 0)]
	elif data_type == "invalid":
		# Get only invalid records
		valid_count = validation_results.get('valid_records', 0)
		filtered_data = vendor_data[valid_count:]
	else:
		# Get all data
		filtered_data = vendor_data
	
	# Apply field mapping
	mapped_data = []
	for row in filtered_data:
		mapped_row = doc.apply_field_mapping(row, field_mapping)
		# Combine original and mapped data
		combined_row = {**row, **{f"mapped_{k}": v for k, v in mapped_row.items()}}
		mapped_data.append(combined_row)
	
	# Create DataFrame
	df = pd.DataFrame(mapped_data)
	
	# Generate filename
	timestamp = frappe.utils.now().replace(" ", "_").replace(":", "-")
	filename = f"vendor_import_{data_type}_{timestamp}.xlsx"
	
	# Create Excel file with multiple sheets
	output = BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		# Main data sheet
		df.to_excel(writer, sheet_name='Vendor Data', index=False)
		
		# Field mapping sheet
		mapping_df = pd.DataFrame([
			{"CSV Header": k, "System Field": v, "Mapped": "Yes" if v else "No"}
			for k, v in field_mapping.items()
		])
		mapping_df.to_excel(writer, sheet_name='Field Mapping', index=False)
		
		# Validation results sheet
		if validation_results:
			validation_df = pd.DataFrame([
				{"Metric": "Total Records", "Count": validation_results.get('total_records', 0)},
				{"Metric": "Valid Records", "Count": validation_results.get('valid_records', 0)},
				{"Metric": "Invalid Records", "Count": validation_results.get('invalid_records', 0)},
				{"Metric": "Errors", "Count": len(validation_results.get('errors', []))},
				{"Metric": "Warnings", "Count": len(validation_results.get('warnings', []))}
			])
			validation_df.to_excel(writer, sheet_name='Validation Summary', index=False)
			
			# Errors sheet
			if validation_results.get('errors'):
				errors_df = pd.DataFrame([{"Error": error} for error in validation_results['errors']])
				errors_df.to_excel(writer, sheet_name='Errors', index=False)
			
			# Warnings sheet
			if validation_results.get('warnings'):
				warnings_df = pd.DataFrame([{"Warning": warning} for warning in validation_results['warnings']])
				warnings_df.to_excel(writer, sheet_name='Warnings', index=False)
	
	output.seek(0)
	
	# Save file
	from frappe.utils.file_manager import save_file
	file_doc = save_file(filename, output.read(), doc.doctype, doc.name, is_private=0)
	
	return {
		"file_url": file_doc.file_url,
		"file_name": filename
	}


@frappe.whitelist()
def download_field_mapping_template():
	"""Download a template showing all available field mappings"""
	
	# Get an instance to access target fields
	temp_doc = frappe.new_doc("Existing Vendor Import")
	target_fields = temp_doc.get_all_target_fields()
	
	# Create template data
	template_data = []
	
	for category, fields in target_fields.items():
		for field_key, field_label in fields.items():
			template_data.append({
				"Category": category,
				"System Field Key": field_key,
				"System Field Label": field_label,
				"Description": f"Maps to {category} - {field_label}",
				"Sample CSV Header": field_label.replace(" ", "_").upper(),
				"Data Type": "Text",
				"Required": "Yes" if field_key in ['vendor_name', 'vendor_code', 'company_code', 'state'] else "No"
			})
	
	# Create DataFrame
	df = pd.DataFrame(template_data)
	
	# Generate filename
	filename = "field_mapping_template.xlsx"
	
	# Create Excel file
	output = BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, sheet_name='Field Mapping Guide', index=False)
		
		# Add sample CSV template
		sample_data = [{
			"VENDOR_NAME": "Sample Vendor Pvt Ltd",
			"VENDOR_CODE": "10001", 
			"COMPANY_CODE": "2000",
			"STATE": "Gujarat",
			"GST_NUMBER": "24AACCD0267F1Z4",
			"PAN_NUMBER": "AACCD0267F",
			"PRIMARY_EMAIL": "vendor@sample.com",
			"MOBILE_NUMBER": "9876543210",
			"ADDRESS_LINE_1": "Sample Address",
			"CITY": "Ahmedabad",
			"PINCODE": "380001"
		}]
		
		sample_df = pd.DataFrame(sample_data)
		sample_df.to_excel(writer, sheet_name='Sample CSV Format', index=False)
		
		# Add instructions
		instructions = [
			{"Step": 1, "Instruction": "Use the 'Field Mapping Guide' sheet to understand available system fields"},
			{"Step": 2, "Instruction": "Create your CSV with appropriate headers (can be any name)"},
			{"Step": 3, "Instruction": "Upload CSV to Existing Vendor Import"},
			{"Step": 4, "Instruction": "Use the field mapping interface to map CSV columns to system fields"},
			{"Step": 5, "Instruction": "Validate and process the import"},
			{"Step": 6, "Instruction": "Download processed data if needed"}
		]
		
		instructions_df = pd.DataFrame(instructions)
		instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
	
	output.seek(0)
	
	# Save file
	from frappe.utils.file_manager import save_file
	file_doc = save_file(filename, output.read(), "Existing Vendor Import", "Template", is_private=0)
	
	return {
		"file_url": file_doc.file_url,
		"file_name": filename
	}


@frappe.whitelist()
def fix_field_mapping(docname):
	"""Fix field mapping issues in existing import"""
	doc = frappe.get_doc("Existing Vendor Import", docname)
	
	if not doc.field_mapping:
		return {"error": "No field mapping found"}
	
	try:
		# Get current mapping
		current_mapping = json.loads(doc.field_mapping)
		
		# Fix common mapping issues from your data
		fixes_applied = []
		
		# Fix email fields that got mapped to wrong fields
		for csv_header, system_field in current_mapping.items():
			if "email" in csv_header.lower():
				if csv_header == "Secondary Email" and system_field == "office_email_primary":
					current_mapping[csv_header] = "office_email_secondary"
					fixes_applied.append(f"Fixed {csv_header} mapping to office_email_secondary")
				elif csv_header == "Email-Id" and not system_field:
					current_mapping[csv_header] = "office_email_primary"
					fixes_applied.append(f"Fixed {csv_header} mapping to office_email_primary")
			
			# Fix bank name mapping
			elif csv_header == "Bank Name" and system_field == "vendor_name":
				current_mapping[csv_header] = "bank_name"
				fixes_applied.append(f"Fixed {csv_header} mapping to bank_name")
			
			# Fix other misaligned fields
			elif csv_header == "Count" and system_field == "country":
				current_mapping[csv_header] = None
				fixes_applied.append(f"Cleared incorrect {csv_header} mapping")
		
		# Update the mapping
		doc.field_mapping = json.dumps(current_mapping, indent=2)
		doc.save(ignore_permissions=True)
		
		return {
			"success": True,
			"fixes_applied": fixes_applied,
			"message": f"Applied {len(fixes_applied)} fixes to field mapping"
		}
		
	except Exception as e:
		return {"error": f"Failed to fix mapping: {str(e)}"}