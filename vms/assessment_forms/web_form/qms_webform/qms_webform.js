
// frappe.ready(function() {
//     // Get the vendor_onboarding value from URL parameters or form field
//     const urlParams = new URLSearchParams(window.location.search);
//     const vendorOnboarding = urlParams.get('vendor_onboarding') || 
//                            $('[data-fieldname="vendor_onboarding"]').val();
    
//     // Check if vendor_onboarding is null or empty
//     if (!vendorOnboarding) {
//         showValidationMessage("This is not a valid form. Missing vendor onboarding information.");
//         return;
//     }
    
//     // Check if record already exists
//     frappe.call({
//         method: 'frappe.client.get_list',
//         args: {
//             doctype: 'Supplier QMS Assessment Form',
//             filters: {
//                 vendor_onboarding: vendorOnboarding
//             },
//             limit: 1
//         },
//         callback: function(r) {
//             if (r.message && r.message.length > 0) {
//                 showValidationMessage("You have already filled this form for this vendor onboarding.");
//             }
//         }
//     });
// });

// function showValidationMessage(message) {
//     // Hide the form
//     $('.web-form-wrapper').hide();
    
//     // Show validation message
//     $('.web-form-wrapper').before(`
//         <div class="alert alert-warning" style="margin: 20px;">
//             <h4>Form Access Restricted</h4>
//             <p>${message}</p>
//             <a href="/" class="btn btn-primary">Go Back to Home</a>
//         </div>
//     `);
// }

// Method 1: Client-side validation in webform
// Add this to your webform's custom script






// frappe.ready(function() {
//     // Get the vendor_onboarding value from URL parameters or form field
//     const urlParams = new URLSearchParams(window.location.search);
//     const vendorOnboarding = urlParams.get('vendor_onboarding') || 
//                            $('[data-fieldname="vendor_onboarding"]').val();
    
//     // Check if vendor_onboarding is null or empty
//     if (!vendorOnboarding) {
//         showValidationMessage("This is not a valid form. Missing vendor onboarding information.");
//         return;
//     }
    
//     // Check if record already exists
//     frappe.call({
//         method: 'frappe.client.get_list',
//         args: {
//             doctype: 'Supplier QMS Assessment Form',
//             filters: {
//                 vendor_onboarding: vendorOnboarding
//             },
//             limit: 1
//         },
//         callback: function(r) {
//             if (r.message && r.message.length > 0) {
//                 showValidationMessage("You have already filled this form for this vendor onboarding.");
//             }
//         }
//     });
// });

// function showValidationMessage(message) {
//     // Hide the entire form and all its controls
//     $('.web-form-wrapper').hide();
//     $('.form-footer').hide();
//     $('.web-form-actions').hide();
//     $('.btn-primary').hide();
//     $('.btn-secondary').hide();
//     $('.form-steps').hide();
//     $('.form-steps-indicator').hide();
//     $('.progress-indicator').hide();
    
//     // Hide pagination/navigation controls
//     $('.form-page .page-actions').hide();
//     $('.form-page .prev-btn').hide();
//     $('.form-page .next-btn').hide();
//     $('.form-page .submit-btn').hide();
    
//     // Hide any other form navigation elements
//     $('.form-tabs').hide();
//     $('.form-sidebar').hide();
    
//     // Show validation message
//     $('.web-form-wrapper').before(`
//         <div class="alert alert-warning" style="margin: 20px;">
//             <h4>Form Access Restricted</h4>
//             <p>${message}</p>
//         </div>
//     `);
// }









//  <div class="alert alert-warning" style="margin: 20px;">
//             <h4>Form Access Restricted</h4>
//             <p>${message}</p>
//             <a href="/" class="btn btn-primary">Go Back to Home</a>
//         </div>

// Method 2: Server-side validation using custom method
// Create this method in your custom app's hooks or in a custom Python file

// In your custom app, create a file: custom_app/custom_app/webform_validation.py



//------------------------------------------------------------FINNNAL test 1---------------------------------------------

// frappe.ready(function() {
//     // Hide header and footer first
//     hideHeaderFooter();
    
//     // Hide specific fields
//     hideSpecificFields();
    
//     // Get the vendor_onboarding value from URL parameters or form field
//     const urlParams = new URLSearchParams(window.location.search);
//     const vendorOnboarding = urlParams.get('vendor_onboarding') || 
//                            $('[data-fieldname="vendor_onboarding"]').val();
    
//     // Check if vendor_onboarding is null or empty
//     if (!vendorOnboarding) {
//         showValidationMessage("This is not a valid form. Missing vendor onboarding information.");
//         return;
//     }
    
//     // Auto-fill the hidden vendor_onboarding field
//     if (vendorOnboarding) {
//         $('[data-fieldname="vendor_onboarding"]').val(vendorOnboarding);
//     }
    
//     // Check if record already exists
//     frappe.call({
//         method: 'frappe.client.get_list',
//         args: {
//             doctype: 'Supplier QMS Assessment Form',
//             filters: {
//                 vendor_onboarding: vendorOnboarding
//             },
//             limit: 1
//         },
//         callback: function(r) {
//             if (r.message && r.message.length > 0) {
//                 showValidationMessage("You have already filled this form for this vendor onboarding.");
//             }
//         }
//     });
// });

// function hideHeaderFooter() {
//     // Hide website header
//     $('.navbar').hide();
//     $('.website-header').hide();
//     $('header').hide();
//     $('.header').hide();
    
//     // Hide website footer
//     $('.footer').hide();
//     $('.website-footer').hide();
//     $('footer').hide();
    
//     // Hide breadcrumbs
//     $('.breadcrumb').hide();
//     $('.breadcrumb-container').hide();
    
//     // Hide page title if needed
//     $('.page-title').hide();
    
//     // Optional: Add some top margin to compensate for hidden header
//     $('.main-section, .container').css('margin-top', '20px');
// }

// function hideSpecificFields() {
//     // Hide the specific fields
//     const fieldsToHide = [
//         'vendor_onboarding',
//         'ref_no', 
//         'vendor_name'
//     ];
    
//     fieldsToHide.forEach(function(fieldname) {
//         // Hide by data-fieldname attribute
//         $(`[data-fieldname="${fieldname}"]`).closest('.form-group').hide();
//         $(`[data-fieldname="${fieldname}"]`).closest('.control-input').hide();
//         $(`[data-fieldname="${fieldname}"]`).closest('.frappe-control').hide();
        
//         // Hide by name attribute
//         $(`input[name="${fieldname}"]`).closest('.form-group').hide();
//         $(`select[name="${fieldname}"]`).closest('.form-group').hide();
//         $(`textarea[name="${fieldname}"]`).closest('.form-group').hide();
        
//         // Hide labels
//         $(`label[for="${fieldname}"]`).hide();
//         $(`.control-label:contains("${fieldname.replace('_', ' ')}")`).closest('.form-group').hide();
//     });
    
//     // Alternative method using CSS
//     $('<style>')
//         .prop('type', 'text/css')
//         .html(`
//             [data-fieldname="vendor_onboarding"],
//             [data-fieldname="ref_no"],
//             [data-fieldname="vendor_name"] {
//                 display: none !important;
//             }
            
//             [data-fieldname="vendor_onboarding"] .form-group,
//             [data-fieldname="ref_no"] .form-group,
//             [data-fieldname="vendor_name"] .form-group,
//             .form-group:has([data-fieldname="vendor_onboarding"]),
//             .form-group:has([data-fieldname="ref_no"]),
//             .form-group:has([data-fieldname="vendor_name"]) {
//                 display: none !important;
//             }
//         `)
//         .appendTo('head');
// }

// function showValidationMessage(message) {
//     // Hide the entire form and all its controls
//     $('.web-form-wrapper').hide();
//     $('.form-footer').hide();
//     $('.web-form-actions').hide();
//     $('.btn-primary').hide();
//     $('.btn-secondary').hide();
//     $('.form-steps').hide();
//     $('.form-steps-indicator').hide();
//     $('.progress-indicator').hide();
    
//     // Hide pagination/navigation controls
//     $('.form-page .page-actions').hide();
//     $('.form-page .prev-btn').hide();
//     $('.form-page .next-btn').hide();
//     $('.form-page .submit-btn').hide();
    
//     // Hide any other form navigation elements
//     $('.form-tabs').hide();
//     $('.form-sidebar').hide();
    
//     // Show validation message
//     $('.web-form-wrapper').before(`
//         <div class="alert alert-warning" style="margin: 20px;">
//             <h4>Form Access Restricted</h4>
//             <p>${message}</p>
//         </div>
//     `);
// }

// // Additional function to auto-populate hidden fields if needed
// function autoPopulateHiddenFields() {
//     const urlParams = new URLSearchParams(window.location.search);
    
//     // Auto-populate vendor_onboarding
//     const vendorOnboarding = urlParams.get('vendor_onboarding');
//     if (vendorOnboarding) {
//         $('[data-fieldname="vendor_onboarding"]').val(vendorOnboarding);
//         $('input[name="vendor_onboarding"]').val(vendorOnboarding);
//     }
    
//     // Auto-populate ref_no if passed in URL
//     const refNo = urlParams.get('ref_no');
//     if (refNo) {
//         $('[data-fieldname="ref_no"]').val(refNo);
//         $('input[name="ref_no"]').val(refNo);
//     }
    
//     // Auto-populate vendor_name if passed in URL
//     const vendorName = urlParams.get('vendor_name');
//     if (vendorName) {
//         $('[data-fieldname="vendor_name"]').val(vendorName);
//         $('input[name="vendor_name"]').val(vendorName);
//     }
// }

// // Call auto-populate after fields are hidden
// setTimeout(autoPopulateHiddenFields, 500);


//$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$4



frappe.ready(function() {
    // Hide header and footer first
    hideHeaderFooter();
    
    // Hide specific fields
    hideSpecificFields();
    
    // Fix file upload permissions
    // fixFileUpload();
    
    // Get the vendor_onboarding value from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const vendorOnboarding = urlParams.get('vendor_onboarding');
    
    // Check if vendor_onboarding is null or empty
    if (!vendorOnboarding) {
        showValidationMessage("This is not a valid form. Missing vendor onboarding information.");
        return;
    }
    // if (!vendorOnboarding) {
    //     showValidationMessage("This is not a valid form. Missing vendor onboarding information.");
    //     return;
    // }
    
    // Auto-fill the hidden vendor_onboarding field
    if (vendorOnboarding) {
        $('[data-fieldname="vendor_onboarding"]').val(vendorOnboarding);
    }
    
    // Check if record already exists
    frappe.call({
    method: 'vms.assessment_forms.web_form.qms_webform.qms_webform.check_supplier_qms_filled',
    args: {
        vendor_onboarding: vendorOnboarding
    },
    callback: function(r) {
        if (r.message && r.message.exists) {
            showValidationMessage("You have already filled this form for this vendor onboarding.");
        }
        }
    });

    
    // Auto-fill the hidden vendor_onboarding field
    setTimeout(function() {
        autoPopulateHiddenFields();
    }, 500);
    
    // Override form submission to show custom thank you message
    overrideFormSubmission();
    
    // Skip the duplicate check for now since it requires whitelisted methods
    // You can add this later if needed
});

function hideHeaderFooter() {
    // Hide website header
    $('.navbar').hide();
    $('.website-header').hide();
    $('header').hide();
    $('.header').hide();
    
    // Hide website footer
    $('.footer').hide();
    $('.website-footer').hide();
    $('footer').hide();
    
    // Hide breadcrumbs
    $('.breadcrumb').hide();
    $('.breadcrumb-container').hide();
    
    // Hide page title if needed
    $('.page-title').hide();
    
    // Add some top margin to compensate for hidden header
    $('.main-section, .container').css('margin-top', '20px');
}

function hideSpecificFields() {
    // Hide the specific fields
    const fieldsToHide = [
        'vendor_onboarding',
        'ref_no', 
        'vendor_name1'
    ];
    
    fieldsToHide.forEach(function(fieldname) {
        // Hide by data-fieldname attribute
        $(`[data-fieldname="${fieldname}"]`).closest('.form-group').hide();
        $(`[data-fieldname="${fieldname}"]`).closest('.control-input').hide();
        $(`[data-fieldname="${fieldname}"]`).closest('.frappe-control').hide();
        
        // Hide by name attribute
        $(`input[name="${fieldname}"]`).closest('.form-group').hide();
        $(`select[name="${fieldname}"]`).closest('.form-group').hide();
        $(`textarea[name="${fieldname}"]`).closest('.form-group').hide();
        
        // Hide labels
        $(`label[for="${fieldname}"]`).hide();
    });
    
    // CSS method for bulletproof hiding
    $('<style>')
        .prop('type', 'text/css')
        .html(`
            [data-fieldname="vendor_onboarding"],
            [data-fieldname="ref_no"],
            [data-fieldname="vendor_name"] {
                display: none !important;
            }
            
            [data-fieldname="vendor_onboarding"] .form-group,
            [data-fieldname="ref_no"] .form-group,
            [data-fieldname="vendor_name"] .form-group {
                display: none !important;
            }
        `)
        .appendTo('head');
}

function overrideFormSubmission() {
    // Override form submission success callback
    $(document).on('web_form_doc_insert', function(e, data) {
        // Hide the default success message
        $('.alert-success').hide();
        $('.msgprint').hide();
        
        // Show custom thank you message
        setTimeout(function() {
            showThankYouMessage(data.name);
        }, 100);
    });
    
    // Alternative: Listen for form submission
    $(document).on('save', '.web-form form', function(e) {
        // Don't prevent default, let Frappe handle the submission
        // Just prepare to show thank you message after success
        
        // Store original success handler
        const originalSuccess = window.frappe && window.frappe.web_form && window.frappe.web_form.after_submit;
        
        // Override success handler
        if (window.frappe && window.frappe.web_form) {
            window.frappe.web_form.after_submit = function(data) {
                // Hide default success elements
                $('.alert-success').hide();
                $('.web-form-message').hide();
                $('.msgprint').hide();
                
                // Show custom thank you
                showThankYouMessage(data && data.name);
            };
        }
    });
}

function showThankYouMessage(docName = null) {
    // Replace entire page content with beautiful thank you message
    $('body').html(`
        <div class="thank-you-container" style="
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        ">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-8 col-lg-6">
                        <div class="card border-0 shadow-lg" style="border-radius: 20px; overflow: hidden;">
                            <div class="card-body text-center py-5 px-4">
                                <!-- Success Icon -->
                                <div class="success-icon mb-4">
                                    <div style="
                                        width: 80px;
                                        height: 80px;
                                        background: linear-gradient(135deg, #28a745, #20c997);
                                        border-radius: 50%;
                                        margin: 0 auto;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        animation: pulse 2s infinite;
                                    ">
                                        <svg width="40" height="40" fill="white" viewBox="0 0 16 16">
                                            <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
                                        </svg>
                                    </div>
                                </div>
                                
                                <!-- Thank You Message -->
                                <h1 class="display-4 text-success mb-3" style="font-weight: 600;">
                                    Thank You!
                                </h1>
                                
                                <h4 class="text-dark mb-4" style="font-weight: 400;">
                                    Your QMS Assessment Form has been submitted successfully
                                </h4>
                                
                                <p class="text-muted mb-4" style="font-size: 1.1rem; line-height: 1.6;">
                                    We have received your supplier quality management assessment. 
                                    Our team will review your submission and get back to you within 
                                    <strong>3-5 business days</strong>.
                                </p>
                                
                                <!-- Features -->
                                <div class="row text-start mb-4">
                                    <div class="col-md-6 mb-3">
                                        <div class="d-flex align-items-center">
                                            <div style="
                                                width: 40px;
                                                height: 40px;
                                                background: #e3f2fd;
                                                border-radius: 50%;
                                                display: flex;
                                                align-items: center;
                                                justify-content: center;
                                                margin-right: 15px;
                                            ">
                                                <svg width="20" height="20" fill="#1976d2" viewBox="0 0 16 16">
                                                    <path d="M8 1a2.5 2.5 0 0 1 2.5 2.5V4h-5v-.5A2.5 2.5 0 0 1 8 1zm3.5 3v-.5a3.5 3.5 0 1 0-7 0V4H1v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4h-3.5zM2 5h12v9a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5z"/>
                                                </svg>
                                            </div>
                                            <div>
                                                <h6 class="mb-1">Secure Submission</h6>
                                                <small class="text-muted">Your data is encrypted and secure</small>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="d-flex align-items-center">
                                            <div style="
                                                width: 40px;
                                                height: 40px;
                                                background: #f3e5f5;
                                                border-radius: 50%;
                                                display: flex;
                                                align-items: center;
                                                justify-content: center;
                                                margin-right: 15px;
                                            ">
                                                <svg width="20" height="20" fill="#7b1fa2" viewBox="0 0 16 16">
                                                    <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V4Zm2-1a1 1 0 0 0-1 1v.217l7 4.2 7-4.2V4a1 1 0 0 0-1-1H2Zm13 2.383-4.708 2.825L15 11.105V5.383Zm-.034 6.876-5.64-3.471L8 9.583l-1.326-.795-5.64 3.47A1 1 0 0 0 2 13h12a1 1 0 0 0 .966-.741ZM1 11.105l4.708-2.897L1 5.383v5.722Z"/>
                                                </svg>
                                            </div>
                                            <div>
                                                <h6 class="mb-1">Email Confirmation</h6>
                                                <small class="text-muted">Confirmation sent to your email</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Reference Number -->
                                <div class="alert alert-light border-0 mb-4" style="background: #f8f9fa;">
                                    <strong>Reference ID:</strong> ${docName || 'QMS-' + new Date().getFullYear() + '-' + Math.random().toString(36).substr(2, 9).toUpperCase()}
                                </div>
                                
                                <!-- Action Button -->
                                <div class="mt-4">
                                    <a href="/" class="btn btn-primary btn-lg px-4 py-2" style="
                                        background: linear-gradient(135deg, #667eea, #764ba2);
                                        border: none;
                                        border-radius: 50px;
                                        font-weight: 500;
                                        transition: transform 0.2s;
                                    " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                        <svg width="16" height="16" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                                            <path d="M8.354 1.146a.5.5 0 0 0-.708 0l-6 6A.5.5 0 0 0 1.5 7.5v7a.5.5 0 0 0 .5.5h4.5a.5.5 0 0 0 .5-.5v-4h2v4a.5.5 0 0 0 .5.5H14a.5.5 0 0 0 .5-.5v-7a.5.5 0 0 0-.146-.354L8.354 1.146zM2.5 14V7.707l5.5-5.5 5.5 5.5V14H10v-4a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5v4H2.5z"/>
                                        </svg>
                                        Back to Home
                                    </a>
                                </div>
                                
                                <!-- Footer -->
                                <p class="text-muted mt-4 mb-0" style="font-size: 0.9rem;">
                                    Need help? Contact our support team at 
                                    <a href="mailto:support@company.com" style="color: #667eea;">support@company.com</a>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
        </style>
    `);
}

function showValidationMessage(message) {
    // Hide the entire form and all its controls
    $('.web-form-wrapper').hide();
    $('.form-footer').hide();
    $('.web-form-actions').hide();
    $('.btn-primary').hide();
    $('.btn-secondary').hide();
    $('.form-steps').hide();
    $('.form-steps-indicator').hide();
    $('.progress-indicator').hide();
    
    // Hide pagination/navigation controls
    $('.form-page .page-actions').hide();
    $('.form-page .prev-btn').hide();
    $('.form-page .next-btn').hide();
    $('.form-page .submit-btn').hide();
    
    // Hide any other form navigation elements
    $('.form-tabs').hide();
    $('.form-sidebar').hide();
    
    // Show validation message
    $('.web-form-wrapper').before(`
        <div class="alert alert-warning" style="margin: 20px;">
            <h4>Form Access Restricted</h4>
            <p>${message}</p>
        </div>
    `);
}

function autoPopulateHiddenFields() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Auto-populate vendor_onboarding
    const vendorOnboarding = urlParams.get('vendor_onboarding');
    if (vendorOnboarding) {
        $('[data-fieldname="vendor_onboarding"]').val(vendorOnboarding);
        $('input[name="vendor_onboarding"]').val(vendorOnboarding);
    }
    
    // Auto-populate ref_no if passed in URL
    const refNo = urlParams.get('ref_no');
    if (refNo) {
        $('[data-fieldname="ref_no"]').val(refNo);
        $('input[name="ref_no"]').val(refNo);
    }
    
    // Auto-populate vendor_name if passed in URL
    const vendorName = urlParams.get('vendor_name');
    if (vendorName) {
        $('[data-fieldname="vendor_name"]').val(vendorName);
        $('input[name="vendor_name"]').val(vendorName);
    }
}

// function fixFileUpload() {
//     // Override the file upload functionality to use custom method
//     if (window.frappe) {
//         const originalCall = frappe.call;
//         frappe.call = function(options) {
//             if (options.method === 'upload_file' || options.method === 'frappe.handler.upload_file') {
//                 // Use our bypass method instead
//                 options.method = 'vms.assessment_forms.web_form.qms_webform.qms_webform.bypass_upload_file';
//             }
//             return originalCall.call(this, options);
//         };
//     }
    
//     // Alternative: Override jQuery file upload for webforms
//     $(document).on('change', 'input[type="file"]', function() {
//         const fileInput = this;
//         const file = fileInput.files[0];
        
//         if (file) {
//             // Create custom upload function for this file input
//             const formData = new FormData();
//             formData.append('file', file);
            
//             // Show upload progress
//             const $progress = $('<div class="progress mt-2"><div class="progress-bar" style="width: 0%"></div></div>');
//             $(fileInput).after($progress);
            
//             // Upload file using custom method
//             $.ajax({
//                 url: '/api/method/vms.assessment_forms.web_form.qms_webform.qms_webform.simple_file_upload',
//                 type: 'POST',
//                 data: formData,
//                 processData: false,
//                 contentType: false,
//                 xhr: function() {
//                     const xhr = new window.XMLHttpRequest();
//                     xhr.upload.addEventListener("progress", function(evt) {
//                         if (evt.lengthComputable) {
//                             const percentComplete = (evt.loaded / evt.total) * 100;
//                             $progress.find('.progress-bar').css('width', percentComplete + '%');
//                         }
//                     }, false);
//                     return xhr;
//                 },
//                 success: function(response) {
//                     $progress.remove();
//                     if (response.message && response.message.success) {
//                         // Store file URL in a hidden field or data attribute.....vms.assessment_forms.web_form.qms_webform.qms_webform
//                         $(fileInput).attr('data-file-url', response.message.file_url);
//                         $(fileInput).attr('data-file-name', response.message.file_name);
                        
//                         // Show success message
//                         $(fileInput).after('<small class="text-success">✓ File uploaded successfully</small>');
//                     } else {
//                         $(fileInput).after('<small class="text-danger">✗ Upload failed</small>');
//                     }
//                 },
//                 error: function() {
//                     $progress.remove();
//                     $(fileInput).after('<small class="text-danger">✗ Upload failed</small>');
//                 }
//             });
//         }
//     });
// }