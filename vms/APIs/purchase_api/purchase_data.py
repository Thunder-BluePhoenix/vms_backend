import frappe
from frappe import _
from frappe.utils.pdf import get_pdf

@frappe.whitelist(allow_guest=True)
def get_purchase_order_data(po_id):

    try:
        if not po_id:
            return {
                "status": "error",
                "message": "Missing required field: 'po_id'."
            }

       
        if not frappe.db.exists("Purchase Order", po_id):
            return {
                "status": "error",
                "message": f"Purchase Order '{po_id}' not found."
            }

        
        po_doc = frappe.get_doc("Purchase Order", po_id)
        
        
        po_data = po_doc.as_dict()
        
       
        if po_doc.get('dispatched'):
            
            return {
                "status": "success",
                "message": "Purchase Order data retrieved successfully.",
                "data": po_data
            }
        else:
          
            fields_to_exclude = ['user_confirmation', 'payment_release']  
            
            for field in fields_to_exclude:
                po_data.pop(field, None)
            
            #  Remove sensitive fields if needed
            # sensitive_fields = ['owner', 'modified_by', 'creation', 'modified']
            # for field in sensitive_fields:
            #     po_data.pop(field, None)
            
            return {
                "status": "success",
                "message": "Purchase Order data retrieved successfully.",
                "data": po_data
            }

    except frappe.PermissionError:
        return {
            "status": "error",
            "message": "Permission denied. You don't have access to this Purchase Order."
        }
    
    except frappe.DoesNotExistError:
        return {
            "status": "error",
            "message": f"Purchase Order '{po_id}' does not exist."
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_purchase_order_data: {str(e)}")
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }



# ✅ SOLUTION 1: Frappe Backend API to handle image conversion
# File: your_app/api/image_utils.py

import frappe
import base64
import requests
from frappe.utils import get_url
import mimetypes

@frappe.whitelist(allow_guest=True)
def get_image_base64():
    """Convert image URL to base64 to avoid CORS issues"""
    try:
        image_url = frappe.form_dict.get('image_url')
        
        if not image_url:
            return {
                "status": "error",
                "message": "Image URL is required"
            }
        
        # Handle relative URLs
        if image_url.startswith('/'):
            image_url = get_url() + image_url
        
        # Fetch image from URL
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Get content type
        content_type = response.headers.get('content-type', 'image/png')
        
        # Convert to base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        data_url = f"data:{content_type};base64,{image_base64}"
        
        return {
            "status": "success",
            "base64_image": data_url,
            "content_type": content_type
        }
        
    except Exception as e:
        frappe.log_error(str(e), "Image Base64 Conversion Error")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True) 
def proxy_image():
    """Proxy image requests to avoid CORS"""
    try:
        image_url = frappe.form_dict.get('url')
        
        if not image_url:
            frappe.throw("Image URL is required")
        
        # Handle relative URLs
        if image_url.startswith('/'):
            image_url = get_url() + image_url
        
        # Fetch image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Set appropriate headers
        content_type = response.headers.get('content-type', 'image/png')
        
        frappe.local.response.headers = {
            'Content-Type': content_type,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Cache-Control': 'public, max-age=3600'  # Cache for 1 hour
        }
        
        frappe.local.response.type = "binary"
        frappe.local.response.data = response.content
        
    except Exception as e:
        frappe.log_error(str(e), "Image Proxy Error")
        frappe.throw(str(e))

# ✅ SOLUTION 2: Enhanced file download with CORS headers
@frappe.whitelist(allow_guest=True)
def download_file_with_cors():
    """Download file with proper CORS headers"""
    try:
        file_url = frappe.form_dict.get('file_url')
        
        if not file_url:
            frappe.throw("File URL is required")
        
        # Handle relative URLs
        if file_url.startswith('/'):
            file_url = get_url() + file_url
        
        # If it's a local file, read it directly
        if file_url.startswith(get_url()):
            # Extract file path
            file_path = file_url.replace(get_url(), '')
            
            # Use Frappe's file manager
            from frappe.utils.file_manager import get_file_content_and_type
            content, content_type = get_file_content_and_type(file_path)
            
            frappe.local.response.headers = {
                'Content-Type': content_type,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            }
            
            frappe.local.response.type = "binary"
            frappe.local.response.data = content
        else:
            # External URL - proxy it
            response = requests.get(file_url, timeout=10)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', 'application/octet-stream')
            
            frappe.local.response.headers = {
                'Content-Type': content_type,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            }
            
            frappe.local.response.type = "binary"
            frappe.local.response.data = response.content
            
    except Exception as e:
        frappe.log_error(str(e), "File Download with CORS Error")
        frappe.throw(str(e))

# ✅ SOLUTION 3: Bulk image conversion for PDF generation
@frappe.whitelist(allow_guest=True)
def convert_po_images_to_base64():
    """Convert all images in PO to base64 for PDF generation"""
    try:
        po_name = frappe.form_dict.get('po_name')
        
        if not po_name:
            return {"status": "error", "message": "PO name is required"}
        
        # Get PO document
        po_doc = frappe.get_doc("Purchase Order", po_name)
        
        # Common image fields that might need conversion
        image_fields = []
        
        # Add company logo
        if hasattr(po_doc, 'company'):
            company_doc = frappe.get_doc("Company", po_doc.company)
            if hasattr(company_doc, 'company_logo'):
                image_fields.append({
                    'field': 'company_logo',
                    'url': company_doc.company_logo
                })
        
        # Add signature images (if any)
        signature_fields = ['sign_url1', 'sign_url2', 'sign_url3']
        for field in signature_fields:
            if hasattr(po_doc, field) and getattr(po_doc, field):
                image_fields.append({
                    'field': field,
                    'url': getattr(po_doc, field)
                })
        
        # Convert all images to base64
        converted_images = {}
        
        for img_field in image_fields:
            try:
                image_url = img_field['url']
                
                # Handle relative URLs
                if image_url.startswith('/'):
                    image_url = get_url() + image_url
                
                # Fetch and convert image
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', 'image/png')
                    image_base64 = base64.b64encode(response.content).decode('utf-8')
                    data_url = f"data:{content_type};base64,{image_base64}"
                    
                    converted_images[img_field['field']] = {
                        'original_url': img_field['url'],
                        'base64_url': data_url,
                        'content_type': content_type
                    }
                    
            except Exception as img_error:
                frappe.log_error(str(img_error), f"Image Conversion Error: {img_field['field']}")
                # Continue with other images even if one fails
                continue
        
        return {
            "status": "success",
            "converted_images": converted_images,
            "total_converted": len(converted_images)
        }
        
    except Exception as e:
        frappe.log_error(str(e), "Bulk Image Conversion Error")
        return {
            "status": "error",
            "message": str(e)
        }



# # In your custom app's api.py file

# @frappe.whitelist()
# def generate_po_pdf(po_name, po_format_name, html_content=None):
#     """Generate PDF for PO using Frappe's built-in PDF generator"""
#     try:
#         if html_content:
#             # Method 1: Generate PDF from custom HTML
#             pdf_content = get_pdf(html_content, {
#                 "page-size": "A4",
#                 "margin-top": "10mm",
#                 "margin-bottom": "10mm", 
#                 "margin-left": "10mm",
#                 "margin-right": "10mm",
#                 "encoding": "UTF-8",
#                 "no-outline": None
#             })
#         else:
#             # Method 2: Use Frappe's print format system
#             pdf_content = frappe.get_print(
#                 doctype="Purchase Order",  # Your doctype
#                 name=po_name,
#                 print_format=po_format_name,
#                 as_pdf=True,
#                 letterhead=1
#             )
        
#         # Set response headers for PDF download
#         frappe.local.response.filename = f"PO_{po_name}.pdf"
#         frappe.local.response.filecontent = pdf_content
#         frappe.local.response.type = "download"
#         frappe.local.response["Content-Type"] = "application/pdf"
        
#         return {
#             "success": True,
#             "message": "PDF generated successfully"
#         }
        
#     except Exception as e:
#         frappe.log_error(f"PDF Generation Error: {str(e)}")
#         frappe.throw(f"Failed to generate PDF: {str(e)}")

# @frappe.whitelist()
# def get_po_print_data(po_name, po_format_name):
#     """Get PO data formatted for PDF generation"""
#     try:
#         # Get your PO document
#         po_doc = frappe.get_doc("Purchase Order", po_name)  # Adjust doctype as needed
        
#         # Get print format
#         print_format = frappe.get_doc("Print Format", po_format_name)
        
#         # Generate HTML using Frappe's print system
#         html = frappe.get_print(
#             doctype="Purchase Order",
#             name=po_name, 
#             print_format=po_format_name,
#             letterhead=1
#         )
        
#         return {
#             "html": html,
#             "data": po_doc.as_dict()
#         }
        
#     except Exception as e:
#         frappe.log_error(f"Print Data Error: {str(e)}")
#         frappe.throw(f"Failed to get print data: {str(e)}")





# # In your custom app's api.py file
# import frappe
# from frappe.utils.pdf import get_pdf
# import base64

# @frappe.whitelist()
# def generate_po_pddf(po_name, po_format_name):
#     """Generate PDF for PO using Frappe's built-in PDF generator"""
#     try:
#         # Use Frappe's print format system
#         pdf_content = frappe.get_print(
#             doctype="Purchase Order",  # Change to your actual doctype
#             name=po_name,
#             print_format=po_format_name,
#             as_pdf=True,
#             letterhead=1
#         )
        
#         # Method 1: Return as base64 for frontend handling
#         pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
#         return {
#             "status": "success",
#             "message": {
#                 "pdf_base64": pdf_base64,
#                 "filename": f"PO_{po_name}.pdf"
#             }
#         }
        
#         # Method 2: Alternative - Direct download (uncomment if preferred)
#         # frappe.local.response.filename = f"PO_{po_name}.pdf"
#         # frappe.local.response.filecontent = pdf_content
#         # frappe.local.response.type = "download"
#         # frappe.local.response["Content-Type"] = "application/pdf"
        
#     except Exception as e:
#         frappe.log_error(f"PDF Generation Error: {str(e)}")
#         return {
#             "status": "error", 
#             "message": f"Failed to generate PDF: {str(e)}"
#         }
# # In your custom app's api.py file
# import frappe
# from frappe.utils.pdf import get_pdf
# import base64
# import json

# @frappe.whitelist()
# def generate_p0o_pdf(po_name, po_format_name, html_content, styles):
#     """Generate PDF from custom HTML content (not using print format)"""
#     try:
#         # Log the request for debugging
#         frappe.logger().info(f"Generating PDF for PO: {po_name}, Format: {po_format_name}")
        
#         # Create complete HTML document with embedded styles
#         complete_html = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="utf-8">
#             <title>PO_{po_name}</title>
#             <style>
#                 /* Reset and base styles */
#                 * {{ margin: 0; padding: 0; box-sizing: border-box; }}
#                 body {{ 
#                     font-family: Arial, Helvetica, sans-serif; 
#                     line-height: 1.4;
#                     color: #333;
#                     background: white;
#                     margin: 0;
#                     padding: 20px;
#                 }}
                
#                 /* Table styles */
#                 table {{ 
#                     width: 100%; 
#                     border-collapse: collapse; 
#                     margin: 10px 0; 
#                 }}
#                 th, td {{ 
#                     border: 1px solid #ddd; 
#                     padding: 8px; 
#                     text-align: left; 
#                     font-size: 12px; 
#                 }}
#                 th {{ 
#                     background-color: #f5f5f5; 
#                     font-weight: bold; 
#                 }}
                
#                 /* Image styles */
#                 img {{ 
#                     max-width: 100%; 
#                     height: auto; 
#                 }}
                
#                 /* Print styles */
#                 @media print {{
#                     body {{ margin: 0; padding: 15px; }}
#                     table {{ page-break-inside: avoid; }}
#                 }}
                
#                 /* Custom styles from frontend */
#                 {styles}
#             </style>
#         </head>
#         <body>
#             <div class="pdf-content">
#                 {html_content}
#             </div>
#         </body>
#         </html>
#         """
        
#         # Generate PDF using Frappe's wkhtmltopdf
#         pdf_options = {
#             "page-size": "A4",
#             "page-height": "297mm",
#             "page-width": "210mm", 
#             "margin-top": "10mm",
#             "margin-bottom": "10mm", 
#             "margin-left": "10mm",
#             "margin-right": "10mm",
#             "encoding": "UTF-8",
#             "no-outline": None,
#             "disable-smart-shrinking": None,
#             "print-media-type": None,
#             "enable-local-file-access": None
#         }
        
#         pdf_content = get_pdf(complete_html, pdf_options)
        
#         # Return as base64 for frontend download
#         pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
#         return {
#             "status": "success",
#             "message": {
#                 "pdf_base64": pdf_base64,
#                 "filename": f"PO_{po_name}_{po_format_name}.pdf"
#             }
#         }
        
#     except Exception as e:
#         # Log the full error
#         frappe.log_error(f"PDF Generation Error for PO {po_name}: {str(e)}", "PDF Generation")
        
#         return {
#             "status": "error",
#             "message": f"Failed to generate PDF: {str(e)}"
#         }

# # Alternative method for direct download (if you prefer)

# # In your file: vms/APIs/purchase_api/purchase_data.py
# import frappe
# from frappe.utils.pdf import get_pdf
# import base64
# import json

# @frappe.whitelist()
# def generate_pooo_pdf():
#     """Generate PDF from custom HTML content"""
#     try:
#         # Get data from Frappe request
#         if frappe.request.method == "POST":
#             request_data = json.loads(frappe.request.data)
#             data = request_data.get('data', {})
#         else:
#             data = frappe.form_dict
        
#         po_name = data.get('po_name')
#         po_format_name = data.get('po_format_name', '')
#         html_content = data.get('html_content', '')
#         styles = data.get('styles', '')
        
#         # Log for debugging
#         frappe.logger().info(f"PDF Request - PO: {po_name}, Format: {po_format_name}")
        
#         if not po_name:
#             frappe.throw("PO Name is required")
        
#         if not html_content:
#             frappe.throw("HTML content is required")
        
#         # Create complete HTML document
#         complete_html = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="utf-8">
#             <title>PO_{po_name}</title>
#             <style>
#                 * {{ margin: 0; padding: 0; box-sizing: border-box; }}
#                 body {{ 
#                     font-family: Arial, Helvetica, sans-serif; 
#                     line-height: 1.4;
#                     color: #333;
#                     background: white;
#                     margin: 0;
#                     padding: 20px;
#                 }}
#                 table {{ 
#                     width: 100%; 
#                     border-collapse: collapse; 
#                     margin: 10px 0; 
#                 }}
#                 th, td {{ 
#                     border: 1px solid #ddd; 
#                     padding: 8px; 
#                     text-align: left; 
#                     font-size: 12px; 
#                 }}
#                 th {{ 
#                     background-color: #f5f5f5; 
#                     font-weight: bold; 
#                 }}
#                 img {{ 
#                     max-width: 100%; 
#                     height: auto; 
#                 }}
#                 @media print {{
#                     body {{ margin: 0; padding: 15px; }}
#                 }}
#                 {styles}
#             </style>
#         </head>
#         <body>
#             {html_content}
#         </body>
#         </html>
#         """
        
#         # PDF generation options
#         pdf_options = {
#             "page-size": "A4",
#             "margin-top": "10mm",
#             "margin-bottom": "10mm", 
#             "margin-left": "10mm",
#             "margin-right": "10mm",
#             "encoding": "UTF-8",
#             "no-outline": None,
#         }
        
#         # Generate PDF
#         pdf_content = get_pdf(complete_html, pdf_options)
        
#         # Return as base64
#         pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
#         return {
#             "status": "success",
#             "message": {
#                 "pdf_base64": pdf_base64,
#                 "filename": f"PO_{po_name}.pdf"
#             }
#         }
        
#     except Exception as e:
#         # Log the full error for debugging
#         import traceback
#         error_msg = traceback.format_exc()
#         frappe.log_error(f"PDF Generation Error: {error_msg}", "PDF Generation")
        
#         return {
#             "status": "error",
#             "message": f"Failed to generate PDF: {str(e)}"
#         }

# # Simpler test method
# @frappe.whitelist()
# def test_pdf():
#     """Simple test method to debug"""
#     try:
#         return {
#             "status": "success", 
#             "message": "PDF method is accessible"
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }
    



# # # In your file: vms/APIs/purchase_api/purchase_data.py
# # import frappe
# # from frappe.utils.pdf import get_pdf
# # import base64
# # import json

# # @frappe.whitelist(allow_guest=True)
# # def download_po_pdf():
# #     """Generate PDF from exact HTML content - no modifications"""
# #     try:
# #         frappe.logger().info("PDF API called successfully")
        
# #         # Get data from request
# #         if frappe.request.method == "POST":
# #             request_data = json.loads(frappe.request.data)
# #             data = request_data.get('data', {})
# #         else:
# #             data = frappe.form_dict
        
# #         po_name = data.get('po_name')
# #         po_format_name = data.get('po_format_name', '')
# #         html_content = data.get('html_content', '')
# #         styles = data.get('styles', '')
        
# #         frappe.logger().info(f"Received PO name: {po_name}")
        
# #         # Validation
# #         if not po_name:
# #             return {
# #                 "status": "error",
# #                 "message": "PO name is required"
# #             }
        
# #         if not html_content:
# #             return {
# #                 "status": "error", 
# #                 "message": "HTML content is required"
# #             }
        
# #         # Use the exact HTML content from frontend - NO MODIFICATIONS
# #         complete_html = html_content
        
# #         frappe.logger().info("Using exact HTML content, generating PDF...")
        
# #         # Generate PDF directly from the provided HTML
# #         pdf_content = get_pdf(complete_html, {
# #             "page-size": "A4",
# #             "margin-top": "10mm",
# #             "margin-bottom": "10mm",
# #             "margin-left": "10mm", 
# #             "margin-right": "10mm",
# #             "encoding": "UTF-8",
# #             "enable-local-file-access": None
# #         })
        
# #         # Convert to base64
# #         pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
# #         frappe.logger().info("PDF generated successfully")
        
# #         return {
# #             "status": "success",
# #             "pdf_base64": pdf_base64,
# #             "filename": f"PO_{po_name}.pdf"
# #         }
        
# #     except Exception as e:
# #         # Log the full error
# #         import traceback
# #         error_msg = traceback.format_exc()
# #         frappe.log_error(error_msg, "PDF Generation Error")
        
# #         return {
# #             "status": "error",
# #             "message": str(e)
# #         }




# import frappe
# from frappe.utils.pdf import get_pdf
# import base64
# import json
# import re
# from datetime import datetime

# @frappe.whitelist(allow_guest=True)
# def download_po_pdf():
#     """Simple PDF generation for Tailwind-converted HTML with inline styles"""
#     try:
#         frappe.logger().info("Tailwind PDF API called successfully")
        
#         # Get data from request
#         if frappe.request.method == "POST":
#             request_data = json.loads(frappe.request.data)
#             data = request_data.get('data', {})
#         else:
#             data = frappe.form_dict
        
#         po_name = data.get('po_name')
#         po_format_name = data.get('po_format_name', '')
#         html_content = data.get('html_content', '')
#         pdf_options = data.get('pdf_options', {})
        
#         frappe.logger().info(f"Received PO name: {po_name}")
        
#         # Validation
#         if not po_name:
#             return {
#                 "status": "error",
#                 "message": "PO name is required"
#             }
        
#         if not html_content:
#             return {
#                 "status": "error", 
#                 "message": "HTML content is required"
#             }
        
#         # ✅ Process HTML (minimal processing since frontend did the heavy lifting)
#         processed_html = process_tailwind_html_for_pdf(html_content)
        
#         # ✅ PDF options optimized for inline-styled HTML
#         pdf_options_final = {
#             "page-size": pdf_options.get("format", "A4"),
#             "margin-top": pdf_options.get("margin", "20mm"),
#             "margin-bottom": pdf_options.get("margin", "20mm"),
#             "margin-left": pdf_options.get("margin", "20mm"), 
#             "margin-right": pdf_options.get("margin", "20mm"),
#             "encoding": "UTF-8",
#             "enable-local-file-access": None,
#             "print-media-type": None,
#             "no-outline": None,
#             # ✅ Options for inline-styled content
#             "disable-smart-shrinking": None,
#             "viewport-size": "1280x1024",
#             "dpi": pdf_options.get("dpi", 96),
#             "image-quality": 100,
#             "javascript-delay": 500,  # Reduced since no dynamic CSS loading needed
#         }
        
#         # Add orientation if specified
#         if pdf_options.get("landscape"):
#             pdf_options_final["orientation"] = "Landscape"
        
#         # Add print background option
#         if pdf_options.get("printBackground", True):
#             pdf_options_final["print-media-type"] = None
        
#         frappe.logger().info("Generating PDF from Tailwind-converted HTML...")
        
#         try:
#             # Generate PDF - should work well since we have inline styles
#             pdf_content = get_pdf(processed_html, pdf_options_final)
#         except Exception as pdf_error:
#             frappe.logger().error(f"PDF generation failed: {str(pdf_error)}")
#             # Try with minimal fallback options
#             fallback_options = {
#                 "page-size": "A4",
#                 "margin-top": "20mm",
#                 "margin-bottom": "20mm", 
#                 "margin-left": "20mm",
#                 "margin-right": "20mm",
#                 "encoding": "UTF-8",
#                 "disable-smart-shrinking": None
#             }
#             pdf_content = get_pdf(processed_html, fallback_options)
        
#         # Validate PDF content
#         if not pdf_content or len(pdf_content) < 100:
#             raise Exception("Generated PDF is empty or corrupted")
        
#         # Convert to base64
#         pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
#         # Generate filename
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"PO_{po_name}_{timestamp}.pdf"
        
#         # Log success
#         file_size_kb = len(pdf_content) / 1024
#         frappe.logger().info(f"Tailwind PDF generated successfully - Size: {file_size_kb:.1f}KB")
        
#         return {
#             "status": "success",
#             "pdf_base64": pdf_base64,
#             "filename": filename,
#             "file_size_kb": round(file_size_kb, 1),
#             "generated_at": datetime.now().isoformat()
#         }
        
#     except Exception as e:
#         # Enhanced error logging
#         import traceback
#         error_msg = traceback.format_exc()
#         frappe.log_error(error_msg, "Tailwind PDF Generation Error")
        
#         # Return user-friendly error message
#         user_message = "PDF generation failed due to technical issues"
#         if "timeout" in str(e).lower():
#             user_message = "PDF generation timed out - please try again"
#         elif "memory" in str(e).lower():
#             user_message = "PDF generation failed due to large content size"
#         elif "wkhtmltopdf" in str(e).lower():
#             user_message = "PDF rendering engine error - please try again"
        
#         return {
#             "status": "error",
#             "message": user_message,
#             "technical_error": str(e) if frappe.conf.get("developer_mode") else None
#         }

# def process_tailwind_html_for_pdf(html_content):
#     """Minimal processing for HTML that already has inline styles from Tailwind conversion"""
    
#     # ✅ Fix relative image URLs to absolute URLs
#     try:
#         base_url = frappe.utils.get_url()
#         html_content = re.sub(r'src="(/[^"]*)"', f'src="{base_url}\\1"', html_content)
#         # Also fix any background-image URLs in inline styles
#         html_content = re.sub(r'background-image:\s*url\((["\']?)(/[^)]*)\1\)', f'background-image: url({base_url}\\2)', html_content)
#     except Exception as e:
#         frappe.logger().warning(f"Could not fix image URLs: {str(e)}")
    
#     # ✅ Remove any remaining script tags
#     html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    
#     # ✅ Clean up HTML entities
#     html_content = html_content.replace('&nbsp;', ' ')
    
#     # ✅ Add minimal PDF-specific CSS (since most styling is already inline)
#     additional_css = """
#     <style>
#     /* Minimal PDF enhancements */
#     @page {
#         margin: 20mm;
#         size: A4;
#     }
    
#     * {
#         -webkit-print-color-adjust: exact !important;
#         color-adjust: exact !important;
#         print-color-adjust: exact !important;
#     }
    
#     body {
#         font-family: Arial, sans-serif !important;
#     }
    
#     /* Ensure images don't overflow */
#     img {
#         max-width: 100% !important;
#         height: auto !important;
#     }
    
#     /* Table rendering improvements */
#     table {
#         border-collapse: collapse !important;
#     }
    
#     /* Page break handling */
#     .break-inside-avoid {
#         break-inside: avoid !important;
#     }
#     </style>
#     """
    
#     # Insert CSS before closing head tag or at the beginning
#     if '</head>' in html_content:
#         html_content = html_content.replace('</head>', additional_css + '</head>')
#     elif '<body>' in html_content:
#         html_content = html_content.replace('<body>', additional_css + '<body>')
#     else:
#         html_content = additional_css + html_content
    
#     return html_content