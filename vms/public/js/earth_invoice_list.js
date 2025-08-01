

frappe.listview_settings['Earth Invoice'] = {
    onload: function(listview) {
       
        if (frappe.user_roles.includes('Earth')) {
           
            listview.page.add_menu_item(__('Import Excel Data'), function() {
                show_import_dialog();
            }, true);
            
            
            listview.page.add_inner_button(__('Import Excel'), function() {
                show_import_dialog();
            }, __('Actions'));
        }
    },
    
    
    get_indicator: function(doc) {
        const colors = {
            'Bus Booking': 'blue',
            'Domestic Air Booking': 'green', 
            'Hotel Booking': 'orange',
            'International Air Booking': 'red',
            'Railway Booking': 'purple'
        };
        
        if (doc.type) {
            return [doc.type, colors[doc.type] || 'gray', 'type,=,' + doc.type];
        }
    }
};

function show_import_dialog() {
    let dialog = new frappe.ui.Dialog({
        title: __('Import Earth Invoice Data'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'import_help',
                options: `
                    <div class="alert alert-info">
                        <h5><i class="fa fa-info-circle"></i> Import Instructions</h5>
                        <ul>
                            <li>Upload your Excel file with booking data sheets</li>
                            <li><strong>TYPE field is mandatory</strong> - must be one of: Bus Booking, Hotel Booking, Domestic Air Booking, International Air Booking, Railway Booking</li>
                            <li>System will validate all records before import</li>
                            <li>You'll see detailed error reports for failed records</li>
                        </ul>
                    </div>
                `
            },
            {
                fieldtype: 'Attach',
                fieldname: 'excel_file',
                label: __('Select Excel File'),
                reqd: 1
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldtype: 'HTML',
                fieldname: 'upload_status',
                options: '<div id="upload-status"></div>'
            }
        ],
        primary_action: function(values) {
            if (!values.excel_file) {
                frappe.msgprint(__('Please select an Excel file'));
                return;
            }
            
            start_import(values.excel_file);
            dialog.hide();
        },
        primary_action_label: __('Import Data'),
        secondary_action_label: __('Cancel')
    });
    
    // Add file change handler
    dialog.fields_dict.excel_file.$input.on('change', function() {
        let file = this.files[0];
        if (file) {
            $('#upload-status').html(`
                <div class="alert alert-success">
                    <strong>File Selected:</strong> ${file.name}<br>
                    <strong>Size:</strong> ${(file.size / 1024 / 1024).toFixed(2)} MB<br>
                    <strong>Type:</strong> ${file.type}
                </div>
            `);
        }
    });
    
    dialog.show();
}

function start_import(file_url) {
    // Show progress with more details
    frappe.show_progress(__('Importing Data'), 0, 100, __('Uploading and processing Excel file...'));
    
    // First test file access
    frappe.call({
        method: 'vms.APIs.import_api.import_api.test_file_access',
        args: {
            file_url: file_url
        },
        callback: function(test_result) {
            console.log('File access test:', test_result.message);
            
            if (test_result.message && test_result.message.file_exists) {
                // File exists, proceed with import
                proceed_with_import(file_url);
            } else {
                // File doesn't exist, wait a bit and try again
                frappe.show_progress(__('Importing Data'), 25, 100, __('Waiting for file upload to complete...'));
                
                setTimeout(function() {
                    proceed_with_import(file_url);
                }, 3000); // Wait 3 seconds
            }
        },
        error: function(r) {
            frappe.hide_progress();
            console.error('File access test failed:', r);
            // Still try to proceed with import
            proceed_with_import(file_url);
        }
    });
}

function proceed_with_import(file_url) {
    frappe.show_progress(__('Importing Data'), 50, 100, __('Processing Excel sheets and validating records...'));
    
    frappe.call({
        method: 'vms.APIs.import_api.import_api.import_earth_invoice_data',
        args: {
            file_url: file_url
        },
        timeout: 300, // 5 minutes timeout
        callback: function(r) {
            frappe.hide_progress();
            
            if (r.message) {
                show_enhanced_import_results(r.message);
                // Refresh the list view
                cur_list.refresh();
            } else {
                frappe.msgprint({
                    title: __('Import Status Unknown'),
                    message: __('Import completed but no response received. Please check the list for imported records.'),
                    indicator: 'orange'
                });
                cur_list.refresh();
            }
        },
        error: function(r) {
            frappe.hide_progress();
            
            let error_message = 'Unknown error occurred during import.';
            
            if (r.message) {
                error_message = r.message;
            } else if (r.exc) {
                // Try to extract meaningful error from exception
                let exc_lines = r.exc.split('\n');
                for (let line of exc_lines) {
                    if (line.includes('FileNotFoundError') || line.includes('No such file')) {
                        error_message = 'File not found. Please try uploading the file again.';
                        break;
                    } else if (line.includes('ValidationError:')) {
                        error_message = line.replace('ValidationError:', '').trim();
                        break;
                    }
                }
            }
            
            frappe.msgprint({
                title: __('Import Failed'),
                message: __('Error: {0}<br><br>Please try:<br>1. Re-uploading the file<br>2. Checking file format (.xlsx or .xls)<br>3. Ensuring TYPE field is present and valid', [error_message]),
                indicator: 'red'
            });
            
            console.error('Import error details:', r);
        }
    });
}

function show_enhanced_import_results(results) {
    let status = 'green';
    let title = 'Import Successful';
    
    if (results.failed_count > 0 && results.imported_count === 0) {
        status = 'red';
        title = 'Import Failed - All Records Rejected';
    } else if (results.failed_count > 0) {
        status = 'orange';
        title = 'Import Completed with Some Errors';
    }
    
    let results_dialog = new frappe.ui.Dialog({
        title: __(title),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'summary_stats',
                options: generate_summary_html(results)
            },
            {
                fieldtype: 'Section Break',
                label: __('Import Details by Sheet')
            },
            {
                fieldtype: 'HTML',
                fieldname: 'sheet_summary',
                options: generate_sheet_summary_html(results)
            }
        ],
        primary_action_label: __('Close')
    });
    
    if (results.failed_count > 0) {
        results_dialog.add_custom_action(__('View Failed Records'), function() {
            show_failed_records_detail(results.failed_records);
        });
        
        results_dialog.add_custom_action(__('Download Failed Records'), function() {
            download_failed_records(results.failed_records);
        });
    }
    
    results_dialog.show();
}

function generate_summary_html(results) {
    return `
        <div class="import-results">
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center" style="border: 1px solid #dee2e6; margin: 5px;">
                        <div class="card-body">
                            <h3 class="text-primary">${results.total_records}</h3>
                            <p><strong>Total Records</strong></p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center" style="border: 1px solid #dee2e6; margin: 5px;">
                        <div class="card-body">
                            <h3 class="text-success">${results.imported_count}</h3>
                            <p><strong>Successfully Imported</strong></p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center" style="border: 1px solid #dee2e6; margin: 5px;">
                        <div class="card-body">
                            <h3 class="text-danger">${results.failed_count}</h3>
                            <p><strong>Failed Records</strong></p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center" style="border: 1px solid #dee2e6; margin: 5px;">
                        <div class="card-body">
                            <h3 class="text-info">${((results.imported_count / results.total_records) * 100).toFixed(1)}%</h3>
                            <p><strong>Success Rate</strong></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generate_sheet_summary_html(results) {
    if (!results.import_summary || Object.keys(results.import_summary).length === 0) {
        return '<p>No sheet summary available.</p>';
    }
    
    let html = `
        <div class="sheet-summary">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Sheet Name</th>
                        <th>Total Records</th>
                        <th>Imported</th>
                        <th>Failed</th>
                        <th>Success Rate</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (let [sheet_name, sheet_data] of Object.entries(results.import_summary)) {
        let success_rate = sheet_data.total_records > 0 ? 
            ((sheet_data.imported_count / sheet_data.total_records) * 100).toFixed(1) : '0.0';
        
        html += `
            <tr>
                <td><strong>${sheet_name}</strong></td>
                <td>${sheet_data.total_records}</td>
                <td class="text-success">${sheet_data.imported_count}</td>
                <td class="text-danger">${sheet_data.failed_count}</td>
                <td>${success_rate}%</td>
            </tr>
        `;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

function show_failed_records_detail(failed_records) {
    if (!failed_records || failed_records.length === 0) {
        frappe.msgprint(__('No failed records to display.'));
        return;
    }
    
    let failed_dialog = new frappe.ui.Dialog({
        title: __('Failed Records Details ({0} records)', [failed_records.length]),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'failed_records_table',
                options: generate_failed_records_html(failed_records)
            }
        ],
        primary_action_label: __('Close')
    });
    
    failed_dialog.show();
}

function generate_failed_records_html(failed_records) {
    let html = `
        <div class="failed-records-container">
            <div class="alert alert-warning">
                <strong>Failed Records:</strong> These records could not be imported due to validation errors or data issues.
            </div>
    `;
    
    failed_records.forEach((record, index) => {
        html += `
            <div class="failed-record-card" style="border: 1px solid #dee2e6; margin: 10px 0; padding: 15px; border-radius: 5px;">
                <div class="row">
                    <div class="col-md-6">
                        <h5 class="text-danger">Record #${index + 1} - Sheet: ${record.sheet}, Row: ${record.row}</h5>
                        
                        <h6>Record Preview:</h6>
                        <table class="table table-sm table-bordered">
        `;
        
        // Show record preview
        if (record.record_preview && Object.keys(record.record_preview).length > 0) {
            for (let [key, value] of Object.entries(record.record_preview)) {
                html += `
                    <tr>
                        <td><strong>${key}:</strong></td>
                        <td>${value}</td>
                    </tr>
                `;
            }
        } else {
            html += `<tr><td colspan="2">No preview data available</td></tr>`;
        }
        
        html += `
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-danger">Validation Errors:</h6>
                        <ul class="list-unstyled">
        `;
        
        // Show errors
        record.errors.forEach(error => {
            html += `<li><i class="fa fa-times text-danger"></i> ${error}</li>`;
        });
        
        html += `
                        </ul>
                        
                        <button class="btn btn-sm btn-info" onclick="show_full_record_data(${index})">
                            <i class="fa fa-eye"></i> View All Data
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    
    // Store failed records globally for access in other functions
    window.current_failed_records = failed_records;
    
    return html;
}

function show_full_record_data(record_index) {
    let record = window.current_failed_records[record_index];
    
    if (!record) {
        frappe.msgprint(__('Record data not found.'));
        return;
    }
    
    let data_html = `
        <div class="full-record-data">
            <h5>Complete Record Data - Row ${record.row}</h5>
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (let [key, value] of Object.entries(record.all_data)) {
        let display_value = value || '<em>Empty</em>';
        data_html += `
            <tr>
                <td><strong>${key}</strong></td>
                <td>${display_value}</td>
            </tr>
        `;
    }
    
    data_html += `
                </tbody>
            </table>
        </div>
    `;
    
    let data_dialog = new frappe.ui.Dialog({
        title: __('Full Record Data - Sheet: {0}, Row: {1}', [record.sheet, record.row]),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'full_data',
                options: data_html
            }
        ],
        primary_action_label: __('Close')
    });
    
    data_dialog.show();
}

function download_failed_records(failed_records) {
    if (!failed_records || failed_records.length === 0) {
        frappe.msgprint(__('No failed records to download.'));
        return;
    }
    
    // Prepare CSV data
    let csv_data = [];
    let headers = ['Sheet', 'Row', 'Errors', 'TYPE', 'EMPLOYEE CODE', 'BILLING COMPANY', 'BOOKING DATE'];
    
    // Add more headers based on available data
    let all_fields = new Set();
    failed_records.forEach(record => {
        if (record.all_data) {
            Object.keys(record.all_data).forEach(key => all_fields.add(key));
        }
    });
    
    // Convert set to array and add to headers (excluding already included ones)
    let additional_headers = Array.from(all_fields).filter(field => !headers.includes(field));
    headers = headers.concat(additional_headers);
    
    csv_data.push(headers);
    
    // Add data rows
    failed_records.forEach(record => {
        let row = [];
        row.push(record.sheet || '');
        row.push(record.row || '');
        row.push(record.errors.join('; ') || '');
        
        // Add data for each header
        headers.slice(3).forEach(header => {
            row.push(record.all_data && record.all_data[header] ? record.all_data[header] : '');
        });
        
        csv_data.push(row);
    });
    
    // Convert to CSV and download
    let csv_content = csv_data.map(row => 
        row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
    ).join('\n');
    
    let blob = new Blob([csv_content], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `failed_records_${new Date().toISOString().slice(0,10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    frappe.show_alert({
        message: __('Failed records CSV downloaded successfully'),
        indicator: 'green'
    });
}