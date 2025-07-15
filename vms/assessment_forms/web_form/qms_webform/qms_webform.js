
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








//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// frappe.ready(function() {
//     // Hide header and footer first
//     hideHeaderFooter();
    
//     // Hide specific fields
//     hideSpecificFields();
    
//     // Fix file upload permissions
//     // fixFileUpload();
    
//     // Get the vendor_onboarding value from URL parameters
//     const urlParams = new URLSearchParams(window.location.search);
//     const vendorOnboarding = urlParams.get('vendor_onboarding');
    
//     // Check if vendor_onboarding is null or empty
//     if (!vendorOnboarding) {
//         showValidationMessage("This is not a valid form. Missing vendor onboarding information.");
//         return;
//     }
//     // if (!vendorOnboarding) {
//     //     showValidationMessage("This is not a valid form. Missing vendor onboarding information.");
//     //     return;
//     // }
    
//     // Auto-fill the hidden vendor_onboarding field
//     if (vendorOnboarding) {
//         $('[data-fieldname="vendor_onboarding"]').val(vendorOnboarding);
//     }
    
//     // Check if record already exists
//     frappe.call({
//     method: 'vms.assessment_forms.web_form.qms_webform.qms_webform.check_supplier_qms_filled',
//     args: {
//         vendor_onboarding: vendorOnboarding
//     },
//     callback: function(r) {
//         if (r.message && r.message.exists) {
//             showValidationMessage("You have already filled this form for this vendor onboarding.");
//         }
//         }
//     });

    
//     // Auto-fill the hidden vendor_onboarding field
//     setTimeout(function() {
//         autoPopulateHiddenFields();
//     }, 500);
    
//     // Override form submission to show custom thank you message
//     overrideFormSubmission();
    
//     // Skip the duplicate check for now since it requires whitelisted methods
//     // You can add this later if needed
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
    
//     // Add some top margin to compensate for hidden header
//     $('.main-section, .container').css('margin-top', '20px');
// }

// function hideSpecificFields() {
//     // Hide the specific fields
//     const fieldsToHide = [
//         'vendor_onboarding',
//         'ref_no', 
//         'vendor_name1'
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
//     });
    
//     // CSS method for bulletproof hiding
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
//             [data-fieldname="vendor_name"] .form-group {
//                 display: none !important;
//             }
//         `)
//         .appendTo('head');
// }

// function overrideFormSubmission() {
//     // Override form submission success callback
//     $(document).on('web_form_doc_insert', function(e, data) {
//         // Hide the default success message
//         $('.alert-success').hide();
//         $('.msgprint').hide();
        
//         // Show custom thank you message
//         setTimeout(function() {
//             showThankYouMessage(data.name);
//         }, 100);
//     });
    
//     // Alternative: Listen for form submission
//     $(document).on('save', '.web-form form', function(e) {
//         // Don't prevent default, let Frappe handle the submission
//         // Just prepare to show thank you message after success
        
//         // Store original success handler
//         const originalSuccess = window.frappe && window.frappe.web_form && window.frappe.web_form.after_submit;
        
//         // Override success handler
//         if (window.frappe && window.frappe.web_form) {
//             window.frappe.web_form.after_submit = function(data) {
//                 // Hide default success elements
//                 $('.alert-success').hide();
//                 $('.web-form-message').hide();
//                 $('.msgprint').hide();
                
//                 // Show custom thank you
//                 showThankYouMessage(data && data.name);
//             };
//         }
//     });
// }

// function showThankYouMessage(docName = null) {
//     // Replace entire page content with beautiful thank you message
//     $('body').html(`
//         <div class="thank-you-container" style="
//             min-height: 100vh;
//             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
//             display: flex;
//             align-items: center;
//             justify-content: center;
//             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
//         ">
//             <div class="container">
//                 <div class="row justify-content-center">
//                     <div class="col-md-8 col-lg-6">
//                         <div class="card border-0 shadow-lg" style="border-radius: 20px; overflow: hidden;">
//                             <div class="card-body text-center py-5 px-4">
//                                 <!-- Success Icon -->
//                                 <div class="success-icon mb-4">
//                                     <div style="
//                                         width: 80px;
//                                         height: 80px;
//                                         background: linear-gradient(135deg, #28a745, #20c997);
//                                         border-radius: 50%;
//                                         margin: 0 auto;
//                                         display: flex;
//                                         align-items: center;
//                                         justify-content: center;
//                                         animation: pulse 2s infinite;
//                                     ">
//                                         <svg width="40" height="40" fill="white" viewBox="0 0 16 16">
//                                             <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
//                                         </svg>
//                                     </div>
//                                 </div>
                                
//                                 <!-- Thank You Message -->
//                                 <h1 class="display-4 text-success mb-3" style="font-weight: 600;">
//                                     Thank You!
//                                 </h1>
                                
//                                 <h4 class="text-dark mb-4" style="font-weight: 400;">
//                                     Your QMS Assessment Form has been submitted successfully
//                                 </h4>
                                
//                                 <p class="text-muted mb-4" style="font-size: 1.1rem; line-height: 1.6;">
//                                     We have received your supplier quality management assessment. 
//                                     Our team will review your submission and get back to you within 
//                                     <strong>3-5 business days</strong>.
//                                 </p>
                                
//                                 <!-- Features -->
//                                 <div class="row text-start mb-4">
//                                     <div class="col-md-6 mb-3">
//                                         <div class="d-flex align-items-center">
//                                             <div style="
//                                                 width: 40px;
//                                                 height: 40px;
//                                                 background: #e3f2fd;
//                                                 border-radius: 50%;
//                                                 display: flex;
//                                                 align-items: center;
//                                                 justify-content: center;
//                                                 margin-right: 15px;
//                                             ">
//                                                 <svg width="20" height="20" fill="#1976d2" viewBox="0 0 16 16">
//                                                     <path d="M8 1a2.5 2.5 0 0 1 2.5 2.5V4h-5v-.5A2.5 2.5 0 0 1 8 1zm3.5 3v-.5a3.5 3.5 0 1 0-7 0V4H1v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4h-3.5zM2 5h12v9a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5z"/>
//                                                 </svg>
//                                             </div>
//                                             <div>
//                                                 <h6 class="mb-1">Secure Submission</h6>
//                                                 <small class="text-muted">Your data is encrypted and secure</small>
//                                             </div>
//                                         </div>
//                                     </div>
//                                     <div class="col-md-6 mb-3">
//                                         <div class="d-flex align-items-center">
//                                             <div style="
//                                                 width: 40px;
//                                                 height: 40px;
//                                                 background: #f3e5f5;
//                                                 border-radius: 50%;
//                                                 display: flex;
//                                                 align-items: center;
//                                                 justify-content: center;
//                                                 margin-right: 15px;
//                                             ">
//                                                 <svg width="20" height="20" fill="#7b1fa2" viewBox="0 0 16 16">
//                                                     <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V4Zm2-1a1 1 0 0 0-1 1v.217l7 4.2 7-4.2V4a1 1 0 0 0-1-1H2Zm13 2.383-4.708 2.825L15 11.105V5.383Zm-.034 6.876-5.64-3.471L8 9.583l-1.326-.795-5.64 3.47A1 1 0 0 0 2 13h12a1 1 0 0 0 .966-.741ZM1 11.105l4.708-2.897L1 5.383v5.722Z"/>
//                                                 </svg>
//                                             </div>
//                                             <div>
//                                                 <h6 class="mb-1">Email Confirmation</h6>
//                                                 <small class="text-muted">Confirmation sent to your email</small>
//                                             </div>
//                                         </div>
//                                     </div>
//                                 </div>
                                
//                                 <!-- Reference Number -->
//                                 <div class="alert alert-light border-0 mb-4" style="background: #f8f9fa;">
//                                     <strong>Reference ID:</strong> ${docName || 'QMS-' + new Date().getFullYear() + '-' + Math.random().toString(36).substr(2, 9).toUpperCase()}
//                                 </div>
                                
//                                 <!-- Action Button -->
//                                 <div class="mt-4">
//                                     <a href="/" class="btn btn-primary btn-lg px-4 py-2" style="
//                                         background: linear-gradient(135deg, #667eea, #764ba2);
//                                         border: none;
//                                         border-radius: 50px;
//                                         font-weight: 500;
//                                         transition: transform 0.2s;
//                                     " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
//                                         <svg width="16" height="16" fill="currentColor" class="me-2" viewBox="0 0 16 16">
//                                             <path d="M8.354 1.146a.5.5 0 0 0-.708 0l-6 6A.5.5 0 0 0 1.5 7.5v7a.5.5 0 0 0 .5.5h4.5a.5.5 0 0 0 .5-.5v-4h2v4a.5.5 0 0 0 .5.5H14a.5.5 0 0 0 .5-.5v-7a.5.5 0 0 0-.146-.354L8.354 1.146zM2.5 14V7.707l5.5-5.5 5.5 5.5V14H10v-4a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5v4H2.5z"/>
//                                         </svg>
//                                         Back to Home
//                                     </a>
//                                 </div>
                                
//                                 <!-- Footer -->
//                                 <p class="text-muted mt-4 mb-0" style="font-size: 0.9rem;">
//                                     Need help? Contact our support team at 
//                                     <a href="mailto:support@company.com" style="color: #667eea;">support@company.com</a>
//                                 </p>
//                             </div>
//                         </div>
//                     </div>
//                 </div>
//             </div>
//         </div>
        
//         <style>
//             @keyframes pulse {
//                 0% { transform: scale(1); }
//                 50% { transform: scale(1.05); }
//                 100% { transform: scale(1); }
//             }
//         </style>
//     `);
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



//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@













frappe.ready(function() {
    // Hide header and footer first
    hideHeaderFooter();
    
    // Hide specific fields
    hideSpecificFields();
    
    // Hide modal dialogs and popups
    hideModalDialogs();


    initializeMultiselectCheckboxes();
    //  initializeMultiselectCheckboxes();


    // setTimeout(function() {
    //     addCompanyFieldCSS();
    //     safeExecuteCompanyLogic();
        
    //     // Debug fields after a delay
    //     setTimeout(debugFormFields, 5000);
    // }, 3000);
    setTimeout(function() {
        autoCheckCompanyFields();
    }, 1000);
    // Add this line
    setTimeout(function() {
        setupMultiselectDataCapture();
    }, 2000);
    
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
    // overrideFormSubmission();
    overrideFormSubmissionWithMultiselect();
});

// ADD THIS COMPLETE FUNCTION TO YOUR EXISTING CODE

// ADD THIS COMPLETE FUNCTION TO YOUR EXISTING CODE

function setupConditionalFieldVisibility() {
    console.log('Setting up conditional field visibility...');
    
    // Configuration for conditional fields
    const conditionalFields = {
        // 2a. Inspected By Others (small text field) - shows when "Others" is selected in sites_inspected_by (select field)
        'inspected_by_others': {
            triggerType: 'select',
            triggerField: 'sites_inspected_by',
            triggerValue: 'Others',
            description: '2a. Inspected By Others (small text field)'
        },
        
        // 6a. Review frequency (small text field) - shows when "Yes" is selected in regular_review_quality_system (select field)
        'if_yes_provide_the_review_frequency': {
            triggerType: 'select',
            triggerField: 'regular_review_quality_system',
            triggerValue: 'Yes',
            description: '6a. If yes provide the review frequency (small text field)'
        }
    };
    
    // Configuration for conditional CHECKBOX GROUPS (custom HTML checkboxes)
    const conditionalCheckboxGroups = {
        // 4a. If yes for prior notification checkboxes - shows when "Yes" is selected in prior_notification
        'if_yes_for_prior_notification': {
            triggerType: 'dropdown',
            triggerField: 'prior_notification',
            triggerValue: 'Yes',
            description: '4a. If yes for prior notification (checkboxes)'
        },
        
        // 9a. Details of batch records checkboxes - shows when "Yes" is selected in batch_record
        'details_of_batch_records': {
            triggerType: 'dropdown',
            triggerField: 'batch_record',
            triggerValue: 'Yes',
            description: '9a. Details of batch records (checkboxes)'
        }
    };
    
    // Function to show/hide conditional regular fields
    function toggleConditionalField(fieldName, show) {
        const selectors = [
            `[data-fieldname="${fieldName}"]`,
            `[name="${fieldName}"]`
        ];
        
        selectors.forEach(function(selector) {
            const field = $(selector);
            const container = field.closest('.form-group, .frappe-control, .web-form-field');
            
            if (show) {
                container.show();
                field.show();
                console.log(`✅ Showing field: ${fieldName}`);
            } else {
                container.hide();
                field.hide();
                console.log(`❌ Hiding field: ${fieldName}`);
            }
        });
    }
    
    // Function to show/hide conditional checkbox groups
    function toggleConditionalCheckboxGroup(fieldName, show) {
        const checkboxGroup = $(`.custom-checkbox-group[data-field="${fieldName}"]`);
        
        if (show) {
            checkboxGroup.show();
            console.log(`✅ Showing checkbox group: ${fieldName}`);
        } else {
            checkboxGroup.hide();
            console.log(`❌ Hiding checkbox group: ${fieldName}`);
        }
    }
    
    // Function to check if "Others" checkbox is selected in quality_control_system
    function checkOthersCheckbox() {
        const checkboxGroup = $(`.custom-checkbox-group[data-field="quality_control_system"]`);
        if (checkboxGroup.length > 0) {
            const isChecked = checkboxGroup.find(`input[type="checkbox"][value="Others"]:checked`).length > 0;
            return isChecked;
        }
        return false;
    }
    
    // Function to check checkbox conditions
    function checkCheckboxCondition(triggerField, triggerValue) {
        const checkboxGroup = $(`.custom-checkbox-group[data-field="${triggerField}"]`);
        if (checkboxGroup.length > 0) {
            const isChecked = checkboxGroup.find(`input[type="checkbox"][value="${triggerValue}"]:checked`).length > 0;
            return isChecked;
        }
        return false;
    }
    
    // Function to check dropdown/select conditions
    function checkSelectCondition(triggerField, triggerValue) {
        const selectSelectors = [
            `[data-fieldname="${triggerField}"] select`,
            `[data-fieldname="${triggerField}"] input`,
            `select[name="${triggerField}"]`,
            `input[name="${triggerField}"]`
        ];
        
        for (let selector of selectSelectors) {
            const field = $(selector);
            if (field.length > 0) {
                const selectedValue = field.val();
                console.log(`Checking ${triggerField}: current value = "${selectedValue}", looking for = "${triggerValue}"`);
                return selectedValue === triggerValue;
            }
        }
        return false;
    }
    
    // Function to update all conditional fields
    function updateConditionalFields() {
        // Handle regular conditional fields
        Object.keys(conditionalFields).forEach(function(fieldName) {
            const config = conditionalFields[fieldName];
            let shouldShow = false;
            
            if (config.triggerType === 'select') {
                shouldShow = checkSelectCondition(config.triggerField, config.triggerValue);
            }
            
            toggleConditionalField(fieldName, shouldShow);
        });
        
        // Handle conditional checkbox groups
        Object.keys(conditionalCheckboxGroups).forEach(function(fieldName) {
            const config = conditionalCheckboxGroups[fieldName];
            let shouldShow = false;
            
            if (config.triggerType === 'dropdown') {
                shouldShow = checkSelectCondition(config.triggerField, config.triggerValue);
            }
            
            toggleConditionalCheckboxGroup(fieldName, shouldShow);
        });
        
        // Special case: Show "others_certificates" when "Others" is checked in quality_control_system
        const showOthersCerts = checkOthersCheckbox();
        toggleConditionalField('others_certificates', showOthersCerts);
    }
    
    // Initially hide all conditional fields and checkbox groups
    setTimeout(function() {
        // Hide regular conditional fields
        Object.keys(conditionalFields).forEach(function(fieldName) {
            toggleConditionalField(fieldName, false);
        });
        
        // Hide conditional checkbox groups
        Object.keys(conditionalCheckboxGroups).forEach(function(fieldName) {
            toggleConditionalCheckboxGroup(fieldName, false);
        });
        
        // Then check and show/hide based on current values
        updateConditionalFields();
    }, 500);
    
    // Listen for checkbox changes
    $(document).on('change', '.custom-checkbox-group input[type="checkbox"]', function() {
        console.log('Checkbox changed:', $(this).val(), 'checked:', $(this).is(':checked'));
        setTimeout(updateConditionalFields, 100);
    });
    
    // Listen for dropdown/select changes
    $(document).on('change', 'select, input[type="radio"]', function() {
        const fieldName = $(this).attr('name') || $(this).closest('[data-fieldname]').attr('data-fieldname');
        const value = $(this).val();
        console.log('Dropdown/Radio changed:', fieldName, 'value:', value);
        setTimeout(updateConditionalFields, 100);
    });
    
    // Listen for any input changes (covers text inputs, selects, etc.)
    $(document).on('input change', '.web-form input, .web-form select', function() {
        setTimeout(updateConditionalFields, 100);
    });
    
    // Periodic check to ensure fields are properly shown/hidden
    setInterval(updateConditionalFields, 2000);
    
    console.log('✅ Conditional field visibility setup complete');
    
    // Debug function to check current states
    window.debugConditionalFields = function() {
        console.log('=== CONDITIONAL FIELDS DEBUG ===');
        
        // Debug regular fields
        Object.keys(conditionalFields).forEach(function(fieldName) {
            const config = conditionalFields[fieldName];
            let shouldShow = false;
            
            if (config.triggerType === 'select') {
                shouldShow = checkSelectCondition(config.triggerField, config.triggerValue);
                console.log(`${fieldName}: Select ${config.triggerField}="${config.triggerValue}" = ${shouldShow}`);
            }
        });
        
        // Debug checkbox groups
        Object.keys(conditionalCheckboxGroups).forEach(function(fieldName) {
            const config = conditionalCheckboxGroups[fieldName];
            let shouldShow = false;
            
            if (config.triggerType === 'dropdown') {
                shouldShow = checkSelectCondition(config.triggerField, config.triggerValue);
                console.log(`${fieldName} (checkbox group): Select ${config.triggerField}="${config.triggerValue}" = ${shouldShow}`);
            }
        });
        
        // Debug Others checkbox
        const showOthersCerts = checkOthersCheckbox();
        console.log(`others_certificates: Others checkbox in quality_control_system = ${showOthersCerts}`);
    };
}




// UPDATE YOUR EXISTING initializeMultiselectCheckboxes() FUNCTION
// Add this line at the end of your initializeMultiselectCheckboxes() function:

/*
function initializeMultiselectCheckboxes() {
    // ... your existing multiselect code ...
    
    // ADD THIS LINE AT THE END:
    setTimeout(function() {
        setupConditionalFieldVisibility();
    }, 2000);
    
    console.log('✅ Multiselect checkboxes initialized successfully');
}
*/

// OR ADD THIS TO YOUR MAIN frappe.ready() FUNCTION:

/*
frappe.ready(function() {
    // ... your existing code ...
    
    initializeMultiselectCheckboxes();
    
    // ADD THIS LINE:
    setTimeout(function() {
        setupConditionalFieldVisibility();
    }, 3000);
    
    // ... rest of your code ...
});
*/

// UPDATE YOUR EXISTING initializeMultiselectCheckboxes() FUNCTION
// Add this line at the end of your initializeMultiselectCheckboxes() function:

/*
function initializeMultiselectCheckboxes() {
    // ... your existing multiselect code ...
    
    // ADD THIS LINE AT THE END:
    setTimeout(function() {
        setupConditionalFieldVisibility();
    }, 2000);
    
    console.log('✅ Multiselect checkboxes initialized successfully');
}
*/

// OR ADD THIS TO YOUR MAIN frappe.ready() FUNCTION:

/*
frappe.ready(function() {
    // ... your existing code ...
    
    initializeMultiselectCheckboxes();
    
    // ADD THIS LINE:
    setTimeout(function() {
        setupConditionalFieldVisibility();
    }, 3000);
    
    // ... rest of your code ...
});
*/

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
        'vendor_name1',
        // 'for_company_7000',
        // 'for_company_2000'
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
            [data-fieldname="vendor_name"],
            [data-fieldname="for_company_7000"],
            [data-fieldname="for_company_2000"] {
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

function hideModalDialogs() {
    // Function to check if success page is visible
    function isSuccessPageVisible() {
        return $('.success-page').length > 0 && $('.success-page').is(':visible');
    }
    
    // Function to hide modal dialogs only on success page
    function hideModalsOnSuccessPage() {
        if (isSuccessPageVisible()) {
            // Hide the specific modal content structure you mentioned
            $('.modal-content').each(function() {
                const $modalContent = $(this);
                const $modalBody = $modalContent.find('.modal-body');
                const $msgprint = $modalBody.find('.msgprint');
                
                // Check if this modal contains any error message
                if ($msgprint.length > 0 && $msgprint.text().trim() !== '') {
                    // Hide the entire modal
                    $modalContent.closest('.modal').hide();
                    $modalContent.hide();
                }
            });
            
            // Also hide modal backdrop
            $('.modal-backdrop').hide();
            
            // Remove modal-open class from body
            $('body').removeClass('modal-open');
        }
    }
    
    // Monitor for success page appearance and hide modals accordingly
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Check if success page appeared
                if (isSuccessPageVisible()) {
                    hideModalsOnSuccessPage();
                }
            }
        });
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Also check periodically for success page
    setInterval(function() {
        hideModalsOnSuccessPage();
    }, 100);
    
    // Listen for modal show events and prevent them only on success page
    $(document).on('show.bs.modal', '.modal', function(e) {
        if (isSuccessPageVisible()) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    });
    
    // Override frappe.msgprint function only on success page
    const originalMsgprint = window.frappe && window.frappe.msgprint;
    if (window.frappe && window.frappe.msgprint) {
        window.frappe.msgprint = function() {
            if (isSuccessPageVisible()) {
                // Do nothing - suppress message prints on success page
                return;
            } else {
                // Call original function on other pages
                return originalMsgprint.apply(this, arguments);
            }
        };
    }
    
    // Add CSS to hide modals only when success page is visible
    $('<style>')
        .prop('type', 'text/css')
        .html(`
            /* Hide modal dialogs only when success page is visible */
            .success-page ~ .modal,
            body:has(.success-page) .modal {
                display: none !important;
            }
            
            .success-page ~ .modal-backdrop,
            body:has(.success-page) .modal-backdrop {
                display: none !important;
            }
            
            /* Alternative CSS for older browsers */
            .modal {
                display: none !important;
            }
            
            .modal-backdrop {
                display: none !important;
            }
            
            /* Show modals again when success page is not present */
            body:not(:has(.success-page)) .modal:not(.hidden-modal) {
                display: block !important;
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
function initializeMultiselectCheckboxes() {
    // Prevent multiple initialization
    if (window._multiselect_initialized) {
        console.log('Multiselect checkboxes already initialized, skipping...');
        return;
    }
    
    // Define your multiselect fields and their options
    const multiselectFields = {
        'quality_control_system': {
            label: '1. Quality Control System is derived to comply',
            options: [
                'ISO 9001',
                'ISO 13485',
                'GMP',
                'ISO/IEC 17025:2005',
                'ISO 14001',
                'ISO 45001',
                'Others'
            ]
        },
        'have_documentsprocedure': {
            label: '3. Have Documents/procedure',
            options: [
                'Quality Management Manual',
                'Internal Quality Audit',
                'Change Control',
                'Corrective and Preventive Action',
                'Environmental Monitoring',
                'Risk Management',
                'Calibration',
                'Emergency Mitigation plan'
            ]
        },
        'if_yes_for_prior_notification': {
            label: '4a. If yes for prior notification',
            options: [
                'Change in the method of manufacturing',
                'Change in the manufacturing site',
                'Change in the registration / licensing status of the site',
                'Change in the Raw Material specification'
            ]
        },
        'details_of_batch_records': {
            label: '9a. Details of batch records',
            options: [
                'Description, Lot Number & Quantities of Material used',
                'Processing Conditions - Temperature, Time, etc',
                'The identification of the personnel who performed the particular step',
                'Results of any In-process tests',
                'Details of deviations from standard conditions'
            ]
        }
    };
    
    // Create checkboxes for each field (only once)
    setTimeout(function() {
        Object.keys(multiselectFields).forEach(function(fieldName) {
            createSimpleCheckboxes(fieldName, multiselectFields[fieldName]);
        });
    }, 1000);
    
    // Hide original multiselect fields (only once)
    setTimeout(function() {
        hideOriginalMultiselectFields(Object.keys(multiselectFields));
    }, 1500);
    

    setTimeout(function() {
        setupConditionalFieldVisibility();
    }, 2000);
    // Override form submission (only once)
    // overrideFormSubmissionForMultiselect(multiselectFields);
    
    // Mark as initialized
    window._multiselect_initialized = true;
    console.log('✅ Multiselect checkboxes initialized successfully');
}

function createSimpleCheckboxes(fieldName, fieldConfig) {
    const options = fieldConfig.options;
    const fieldLabel = fieldConfig.label;
    
    // Check if checkboxes already exist for this field
    if ($(`.custom-checkbox-group[data-field="${fieldName}"]`).length > 0) {
        console.log(`Checkboxes for ${fieldName} already exist, skipping creation`);
        return;
    }
    
    // Simple, clean checkbox HTML
    const checkboxHTML = `
        <div class="custom-checkbox-group" data-field="${fieldName}">
            <h6 class="checkbox-label">${fieldLabel}</h6>
            <div class="checkbox-container">
                ${options.map((option, index) => `
                    <div class="checkbox-item">
                        <input type="checkbox" 
                               id="${fieldName}_${index}" 
                               value="${option}"
                               data-field="${fieldName}">
                        <label for="${fieldName}_${index}">${option}</label>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    // Add simple CSS only once
    if (!$('#custom-checkbox-styles').length) {
        $('head').append(`
            <style id="custom-checkbox-styles">
                .custom-checkbox-group {
                    margin: 20px 0;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background: #f9f9f9;
                }
                
                .checkbox-label {
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #333;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 5px;
                }
                
                .checkbox-container {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 10px;
                }
                
                .checkbox-item {
                    display: flex;
                    align-items: center;
                    padding: 5px;
                }
                
                .checkbox-item input[type="checkbox"] {
                    margin-right: 8px;
                    transform: scale(1.2);
                }
                
                .checkbox-item label {
                    cursor: pointer;
                    font-size: 14px;
                    line-height: 1.3;
                }
                
                .checkbox-item:hover {
                    background: #e9e9e9;
                    border-radius: 3px;
                }
            </style>
        `);
    }
    
    // Single placement strategy - find the field and place after it
    let placed = false;
    
    // Strategy 1: Look for the actual multiselect field
    setTimeout(function() {
        if (!placed) {
            const multiselectField = $(`[data-fieldname="${fieldName}"]`);
            if (multiselectField.length > 0) {
                const container = multiselectField.closest('.form-group, .frappe-control, .web-form-field');
                if (container.length > 0) {
                    container.after(checkboxHTML);
                    placed = true;
                    console.log(`✅ Placed checkboxes for ${fieldName} using field detection`);
                }
            }
        }
        
        // // Strategy 2: Fallback - append to form
        // if (!placed) {
        //     $('.web-form form, .form-container, .container').first().append(checkboxHTML);
        //     console.log(`✅ Placed checkboxes for ${fieldName} using fallback method`);
        // }
    }, 1000);
}

function getSearchTexts(fieldName) {
    const searchMap = {
        'quality_control_system': ['quality control', 'iso 9001', 'comply'],
        'have_documentsprocedure': ['documents', 'procedure', 'quality management'],
        'if_yes_for_prior_notification': ['prior notification', 'manufacturing'],
        'details_of_batch_records': ['batch records', 'lot number', 'processing conditions']
    };
    return searchMap[fieldName] || [fieldName.replace(/_/g, ' ')];
}

function hideOriginalMultiselectFields(fieldNames) {
    fieldNames.forEach(function(fieldName) {
        // Hide by data-fieldname
        $(`[data-fieldname="${fieldName}"]`).closest('.form-group, .frappe-control, .web-form-field').hide();
        
        // Hide by name attribute
        $(`[name="${fieldName}"]`).closest('.form-group, .frappe-control, .web-form-field').hide();
        
        console.log(`Hidden original field: ${fieldName}`);
    });
}


// Debug function to check what fields exist
function debugFields() {
    console.log('=== FIELD DEBUG INFO ===');
    
    console.log('Fields with data-fieldname:');
    $('[data-fieldname]').each(function() {
        console.log('- ' + $(this).attr('data-fieldname'), $(this)[0]);
    });
    
    console.log('Fields with name attribute:');
    $('[name]').each(function() {
        console.log('- ' + $(this).attr('name'), $(this)[0]);
    });
    
    console.log('All form inputs:');
    $('input, select, textarea').each(function() {
        console.log('- ' + this.tagName + ': ' + ($(this).attr('name') || $(this).attr('data-fieldname') || 'no-name'), $(this)[0]);
    });
}





function setupMultiselectDataCapture() {
    // Hide the multiselect JSON field first
    hideMultiselectJsonField();
    
    // Find the JSON storage field (assuming it has data-fieldname="multiselect_data_json" or similar)
    // Adjust the field name according to your actual field name
    const jsonFieldSelectors = [
        '[data-fieldname="multiselect_data_json"]',
        '[data-fieldname="multiselect_json"]',
        '[name="multiselect_data_json"]',
        '[name="multiselect_json"]',
        // Add more potential field names as needed
        'input[type="text"]:contains("Multiselect data json")',
        'textarea:contains("Multiselect data json")'
    ];
    
    let jsonField = null;
    for (let selector of jsonFieldSelectors) {
        jsonField = $(selector);
        if (jsonField.length > 0) break;
    }
    
    // If not found by field name, try to find by label
    if (!jsonField || jsonField.length === 0) {
        $('label').each(function() {
            if ($(this).text().trim().toLowerCase().includes('multiselect data json')) {
                const fieldId = $(this).attr('for');
                if (fieldId) {
                    jsonField = $(`#${fieldId}`);
                    return false; // break loop
                }
                // Also try to find nearby input
                jsonField = $(this).siblings('input, textarea').first();
                if (jsonField.length > 0) return false;
                jsonField = $(this).closest('.form-group, .frappe-control').find('input, textarea').first();
                if (jsonField.length > 0) return false;
            }
        });
    }
    
    if (!jsonField || jsonField.length === 0) {
        console.warn('Multiselect data json field not found');
        return;
    }
    
    console.log('Found JSON storage field:', jsonField[0]);
    
    // Function to collect checkbox data and update JSON field
    function updateMultiselectJson() {
        const data = {};
        
        // Iterate through each multiselect field group
        $('.custom-checkbox-group').each(function() {
            const fieldName = $(this).attr('data-field');
            const selectedValues = [];
            
            // Get all checked checkboxes for this field
            $(this).find('input[type="checkbox"]:checked').each(function() {
                selectedValues.push({
                    "name": $(this).val(),
                    "value": $(this).val()
                });
            });
            
            // Only add to data if there are selected values
            if (selectedValues.length > 0) {
                data[fieldName] = selectedValues;
            }
        });
        
        // Create the final JSON structure
        const jsonData = {
            "data": data
        };
        
        // Update the JSON field
        const jsonString = JSON.stringify(jsonData);
        jsonField.val(jsonString);
        
        console.log('Updated multiselect JSON:', jsonString);
        
        return jsonData;
    }
    
    // Listen for checkbox changes and update JSON immediately
    $(document).on('change', '.custom-checkbox-group input[type="checkbox"]', function() {
        updateMultiselectJson();
    });
    
    // Also update before form submission
    $(document).on('submit', '.web-form form', function(e) {
        updateMultiselectJson();
        console.log('Form submitted with multiselect data');
    });
    
    // Update JSON when form is about to be saved (Frappe specific)
    if (window.frappe && window.frappe.web_form) {
        const originalValidate = window.frappe.web_form.validate;
        window.frappe.web_form.validate = function() {
            updateMultiselectJson();
            if (originalValidate) {
                return originalValidate.apply(this, arguments);
            }
            return true;
        };
    }
    
    // Alternative: Listen for any form field changes to update JSON
    $(document).on('change input', '.web-form input, .web-form select, .web-form textarea', function() {
        // Small delay to ensure all changes are captured
        setTimeout(updateMultiselectJson, 100);
    });
    
    console.log('✅ Multiselect JSON data capture setup complete');
}

// Update your overrideFormSubmission function to include JSON update
function overrideFormSubmissionWithMultiselect() {
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
    
    // Listen for form submission and update multiselect data
    $(document).on('submit', '.web-form form', function(e) {
        // Update multiselect JSON before submission
        updateMultiselectJsonBeforeSubmit();
        
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


// Standalone function to update JSON before form submission
function updateMultiselectJsonBeforeSubmit() {
    const data = {};
    
    // Collect data from all multiselect checkbox groups
    $('.custom-checkbox-group').each(function() {
        const fieldName = $(this).attr('data-field');
        const selectedValues = [];
        
        $(this).find('input[type="checkbox"]:checked').each(function() {
            selectedValues.push($(this).val());
        });
        
        if (selectedValues.length > 0) {
            data[fieldName] = selectedValues.join(',');
        }
    });
    
    const jsonData = { "data": data };
    const jsonString = JSON.stringify(jsonData);
    
    // Try multiple ways to find and update the JSON field
    const possibleSelectors = [
        '[data-fieldname="multiselect_data_json"]',
        '[data-fieldname="multiselect_json"]',
        '[name="multiselect_data_json"]',
        '[name="multiselect_json"]'
    ];
    
    let fieldUpdated = false;
    for (let selector of possibleSelectors) {
        const field = $(selector);
        if (field.length > 0) {
            field.val(jsonString);
            fieldUpdated = true;
            console.log(`Updated ${selector} with:`, jsonString);
            break;
        }
    }
    
    if (!fieldUpdated) {
        console.warn('Could not find multiselect JSON field to update');
    }
    
    return jsonData;
}
function hideMultiselectJsonField() {
    const jsonFieldSelectors = [
        '[data-fieldname="multiselect_data_json"]',
        '[data-fieldname="multiselect_json"]',
        '[name="multiselect_data_json"]',
        '[name="multiselect_json"]'
    ];
    
    // Hide by direct selectors
    jsonFieldSelectors.forEach(function(selector) {
        $(selector).closest('.form-group, .frappe-control, .web-form-field').hide();
        $(selector).hide();
    });
    
    // Hide by label text search
    $('label').each(function() {
        if ($(this).text().toLowerCase().includes('multiselect data json') || 
            $(this).text().toLowerCase().includes('multiselect json')) {
            $(this).closest('.form-group, .frappe-control, .web-form-field').hide();
            $(this).hide();
            
            // Also hide associated input/textarea
            const fieldId = $(this).attr('for');
            if (fieldId) {
                $(`#${fieldId}`).closest('.form-group, .frappe-control, .web-form-field').hide();
            }
            
            $(this).siblings('input, textarea').closest('.form-group, .frappe-control, .web-form-field').hide();
        }
    });
    
    // Add CSS to ensure complete hiding
    if (!$('#hide-multiselect-json-css').length) {
        $('head').append(`
            <style id="hide-multiselect-json-css">
                /* Hide multiselect JSON field completely */
                [data-fieldname*="multiselect_data_json"],
                [data-fieldname*="multiselect_json"],
                [name*="multiselect_data_json"],
                [name*="multiselect_json"] {
                    display: none !important;
                    visibility: hidden !important;
                }
                
                [data-fieldname*="multiselect_data_json"] .form-group,
                [data-fieldname*="multiselect_json"] .form-group,
                [name*="multiselect_data_json"] .form-group,
                [name*="multiselect_json"] .form-group {
                    display: none !important;
                    visibility: hidden !important;
                }
                
                /* Hide by label content */
                label:contains("Multiselect data json"),
                label:contains("multiselect data json"),
                label:contains("Multiselect JSON"),
                label:contains("multiselect json") {
                    display: none !important;
                }
            </style>
        `);
    }
    
    console.log('✅ Multiselect JSON field hidden');
}



// Add this function to your existing frappe.ready() block
function setupCompanyBasedFieldVisibility() {
    const urlParams = new URLSearchParams(window.location.search);
    const vendorOnboarding = urlParams.get('vendor_onboarding');
    
    if (!vendorOnboarding) {
        console.warn('No vendor onboarding ID found in URL');
        return;
    }
    
    // Use custom API to get vendor onboarding and company data
    frappe.call({
        method: 'vms.assessment_forms.web_form.qms_webform.qms_webform.get_vendor_company_data',
        args: {
            vendor_onboarding: vendorOnboarding
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                const data = r.message.data;
                console.log('Vendor Company Data:', data);
                
                // Get company codes from the response
                const companyCodes = data.company_codes || [];
                console.log('Company Codes:', companyCodes);
                
                // Show/hide fields based on company codes
                toggleFieldsByCompanyCode(companyCodes);
            } else {
                console.error('Could not fetch vendor company data:', r.message ? r.message.message : 'Unknown error');
                hideAllCompanyFields();
            }
        },
        error: function(err) {
            console.error('API Error:', err);
            hideAllCompanyFields();
        }
    });
}


function toggleFieldsByCompanyCode(companyCodes) {
    console.log('Processing company codes:', companyCodes);
    
    // Define field groups
    const mdplFields = [
        'mdpl_quality_agreement',
        'mdpl_qa_date',
        'supplier_company_name',
        'name_of_person',
        'signed_date',
        'mdpl_quality_agreement_duplicate', // Assuming this is a different field name for the duplicate
        'designation_of_person',
        'person_signature',
        'list_of_products_in_qa',
        'products_in_qa'
    ];
    
    const mlsplFields = [
        'mlspl_qa',
        'tissue_supplier',
        'new_supplier',
        'technical_agreement_labs',
        'amendent_existing_supplier', // Fixed typo from "amendent"
        'mlspl_qa_list'
    ];
    
    // Check which company codes are present
    const hasMDPL = companyCodes.includes('7000');
    const hasMLSPL = companyCodes.includes('2000');
    
    console.log('Company Code Analysis:', {
        companyCodes,
        hasMDPL,
        hasMLSPL
    });
    
    // Show/hide MDPL fields
    if (hasMDPL) {
        showFields(mdplFields, 'MDPL');
    } else {
        hideFields(mdplFields, 'MDPL');
    }
    
    // Show/hide MLSPL fields
    if (hasMLSPL) {
        showFields(mlsplFields, 'MLSPL');
    } else {
        hideFields(mlsplFields, 'MLSPL');
    }
    
    // Log final visibility state
    console.log('Field Visibility Summary:', {
        MDPL_visible: hasMDPL,
        MLSPL_visible: hasMLSPL,
        total_codes: companyCodes.length
    });
}

function showFields(fieldNames, groupName) {
    console.log(`Showing ${groupName} fields:`, fieldNames);
    
    fieldNames.forEach(fieldName => {
        // Show by data-fieldname attribute
        const fieldElement = $(`[data-fieldname="${fieldName}"]`);
        if (fieldElement.length) {
            fieldElement.closest('.form-group, .frappe-control, .web-form-field').show();
            fieldElement.show();
        }
        
        // Show by name attribute
        const nameElement = $(`[name="${fieldName}"]`);
        if (nameElement.length) {
            nameElement.closest('.form-group, .frappe-control, .web-form-field').show();
            nameElement.show();
        }
        
        // Show labels
        $(`label[for="${fieldName}"]`).show();
        
        // Remove any hiding CSS classes
        $(`[data-fieldname="${fieldName}"], [name="${fieldName}"]`)
            .removeClass('hidden-field')
            .css('display', '');
    });
}

function hideFields(fieldNames, groupName) {
    console.log(`Hiding ${groupName} fields:`, fieldNames);
    
    fieldNames.forEach(fieldName => {
        // Hide by data-fieldname attribute
        const fieldElement = $(`[data-fieldname="${fieldName}"]`);
        if (fieldElement.length) {
            fieldElement.closest('.form-group, .frappe-control, .web-form-field').hide();
            fieldElement.hide();
        }
        
        // Hide by name attribute
        const nameElement = $(`[name="${fieldName}"]`);
        if (nameElement.length) {
            nameElement.closest('.form-group, .frappe-control, .web-form-field').hide();
            nameElement.hide();
        }
        
        // Hide labels
        $(`label[for="${fieldName}"]`).hide();
        
        // Add CSS class for hiding
        $(`[data-fieldname="${fieldName}"], [name="${fieldName}"]`)
            .addClass('hidden-field');
    });
}

function hideAllCompanyFields() {
    console.log('Hiding all company-specific fields due to error or no valid companies');
    
    const allCompanyFields = [
        // MDPL fields
        'mdpl_quality_agreement',
        'mdpl_qa_date',
        'supplier_company_name',
        'name_of_person',
        'signed_date',
        'mdpl_quality_agreement_duplicate',
        'designation_of_person',
        'person_signature',
        'list_of_products_in_qa',
        'products_in_qa',
        // MLSPL fields
        'mlspl_qa',
        'tissue_supplier',
        'new_supplier',
        'technical_agreement_labs',
        'amendment_existing_supplier',
        'mlspl_qa_list'
    ];
    
    hideFields(allCompanyFields, 'ALL');
}

// Add CSS for hidden fields
function addCompanyFieldCSS() {
    if (!$('#company-field-css').length) {
        $('head').append(`
            <style id="company-field-css">
                .hidden-field {
                    display: none !important;
                    visibility: hidden !important;
                }
                
                .hidden-field .form-group,
                .hidden-field .frappe-control,
                .hidden-field .web-form-field {
                    display: none !important;
                    visibility: hidden !important;
                }
                
                /* Smooth transitions for field visibility */
                .form-group, .frappe-control, .web-form-field {
                    transition: opacity 0.3s ease-in-out;
                }
                
                /* Debug styling for company fields */
                .company-field-debug {
                    border: 2px solid #007bff;
                    background-color: rgba(0, 123, 255, 0.1);
                }
            </style>
        `);
    }
}

// Debug function to list all form fields
function debugFormFields() {
    console.log('=== ALL FORM FIELDS DEBUG ===');
    
    $('[data-fieldname], [name]').each(function() {
        const fieldname = $(this).attr('data-fieldname') || $(this).attr('name');
        const fieldType = this.tagName.toLowerCase();
        const isVisible = $(this).is(':visible');
        
        console.log(`Field: ${fieldname} | Type: ${fieldType} | Visible: ${isVisible}`);
    });
}

// Enhanced error handling wrapper
function safeExecuteCompanyLogic() {
    try {
        setupCompanyBasedFieldVisibility();
    } catch (error) {
        console.error('Error in company-based field visibility logic:', error);
        // Fallback: hide all company fields on error
        hideAllCompanyFields();
    }
}



// Add this function to your existing JavaScript code
function autoCheckCompanyFields() {
    console.log('Setting up auto-check for company fields...');
    
    const urlParams = new URLSearchParams(window.location.search);
    const companyCode = urlParams.get('company_code');
    
    if (!companyCode) {
        console.log('No company_code parameter found in URL');
        return;
    }
    
    console.log('Raw company_code from URL:', companyCode);
    
    // Decode the URL-encoded string (%2C becomes comma)
    const decodedCompanyCode = decodeURIComponent(companyCode);
    console.log('Decoded company_code:', decodedCompanyCode);
    
    // Split by comma to get individual company codes
    const companyCodes = decodedCompanyCode.split(',').map(code => code.trim());
    console.log('Individual company codes:', companyCodes);
    
    // Check company 7000 field
    if (companyCodes.includes('7000')) {
        checkCompanyField('for_company_7000', true);
        console.log('✅ Checked for_company_7000');
    } else {
        checkCompanyField('for_company_7000', false);
        console.log('❌ Unchecked for_company_7000');
    }
    
    // Check company 2000 field
    if (companyCodes.includes('2000')) {
        checkCompanyField('for_company_2000', true);
        console.log('✅ Checked for_company_2000');
    } else {
        checkCompanyField('for_company_2000', false);
        console.log('❌ Unchecked for_company_2000');
    }
    
    // You can add more company codes here as needed
    // Example for 4785:
    if (companyCodes.includes('4785')) {
        // If you have a field for company 4785, uncomment and modify:
        // checkCompanyField('for_company_4785', true);
        console.log('📝 Company 4785 detected (no corresponding field found)');
    }
}

function checkCompanyField(fieldName, shouldCheck) {
    // Multiple strategies to find and check the field
    const selectors = [
        `[data-fieldname="${fieldName}"]`,
        `[name="${fieldName}"]`,
        `input[data-fieldname="${fieldName}"]`,
        `input[name="${fieldName}"]`,
        `#${fieldName}`
    ];
    
    let fieldFound = false;
    
    for (let selector of selectors) {
        const field = $(selector);
        if (field.length > 0) {
            // Check if it's a checkbox
            if (field.is('input[type="checkbox"]') || field.attr('type') === 'checkbox') {
                field.prop('checked', shouldCheck);
                field.attr('checked', shouldCheck);
                
                // Trigger change event to ensure Frappe handles it properly
                field.trigger('change');
                
                fieldFound = true;
                console.log(`Set ${fieldName} checkbox to ${shouldCheck} using selector: ${selector}`);
                break;
            }
            // Handle Frappe's custom checkbox implementation
            else if (field.hasClass('checkbox') || field.closest('.checkbox').length > 0) {
                if (shouldCheck) {
                    field.addClass('checked');
                    field.closest('.checkbox').addClass('checked');
                } else {
                    field.removeClass('checked');
                    field.closest('.checkbox').removeClass('checked');
                }
                
                field.trigger('change');
                fieldFound = true;
                console.log(`Set ${fieldName} Frappe checkbox to ${shouldCheck} using selector: ${selector}`);
                break;
            }
        }
    }
    
    // If field not found by selectors, try finding by label
    if (!fieldFound) {
        $('label').each(function() {
            const labelText = $(this).text().trim();
            if (labelText.includes(fieldName) || 
                (fieldName === 'for_company_7000' && labelText.includes('For Company 7000')) ||
                (fieldName === 'for_company_2000' && labelText.includes('For Company 2000'))) {
                
                const labelFor = $(this).attr('for');
                if (labelFor) {
                    const associatedField = $(`#${labelFor}`);
                    if (associatedField.length > 0) {
                        associatedField.prop('checked', shouldCheck);
                        associatedField.trigger('change');
                        fieldFound = true;
                        console.log(`Set ${fieldName} to ${shouldCheck} via label association`);
                        return false; // break loop
                    }
                }
                
                // Look for nearby input fields
                const nearbyInput = $(this).siblings('input[type="checkbox"]').first();
                if (nearbyInput.length > 0) {
                    nearbyInput.prop('checked', shouldCheck);
                    nearbyInput.trigger('change');
                    fieldFound = true;
                    console.log(`Set ${fieldName} to ${shouldCheck} via nearby input`);
                    return false; // break loop
                }
            }
        });
    }
    
    if (!fieldFound) {
        console.warn(`Could not find field: ${fieldName}`);
    }
    
    return fieldFound;
}


// Add this to your existing frappe.ready() function
// Call this after other initialization is complete



// Run debug after page loads
setTimeout(debugFields, 3000);

// Call pre-populate function after checkboxes are created
// Call pre-populate function after checkboxes are created
// setTimeout(function() {
//     const multiselectFields = {
//         'quality_control_system': {
//             htmlField: 'quality_control_system_html',
//             label: '1. Quality Control System is derived to comply',
//             options: [
//                 'ISO 9001',
//                 'ISO 13485',
//                 'GMP',
//                 'ISO/IEC 17025:2005',
//                 'ISO 14001',
//                 'ISO 45001',
//                 'Others'
//             ]
//         },
//         'have_documentsprocedure': {
//             htmlField: 'have_documentsprocedure_html',
//             label: '3. Have Documents/procedure',
//             options: [
//                 'Quality Management Manual',
//                 'Internal Quality Audit',
//                 'Change Control',
//                 'Corrective and Preventive Action',
//                 'Environmental Monitoring',
//                 'Risk Management',
//                 'Calibration',
//                 'Emergency Mitigation plan'
//             ]
//         },
//         'if_yes_for_prior_notification': {
//             htmlField: 'if_yes_for_prior_notification_html',
//             label: '4a. If yes for prior notification',
//             options: [
//                 'Change in the method of manufacturing',
//                 'Change in the manufacturing site',
//                 'Change in the registration / licensing status of the site',
//                 'Change in the Raw Material specification'
//             ]
//         },
//         'details_of_batch_records': {
//             htmlField: 'details_of_batch_records_html',
//             label: '9a. Details of batch records',
//             options: [
//                 'Description, Lot Number & Quantities of Material used',
//                 'Processing Conditions - Temperature, Time, etc',
//                 'The identification of the personnel who performed the particular step',
//                 'Results of any In-process tests',
//                 'Details of deviations from standard conditions'
//             ]
//         }
//     };
    
//     if (typeof prePopulateCheckboxes === 'function') {
//         prePopulateCheckboxes(multiselectFields);
//     }
// }, 3000);// Add 

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