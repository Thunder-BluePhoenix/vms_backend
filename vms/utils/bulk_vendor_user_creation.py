import frappe
from frappe import _
import string
import random
from frappe.utils.background_jobs import enqueue


@frappe.whitelist()
def start_bulk_vendor_processing():
    """
    Start background processing of imported vendors
    Called by list view button - runs in background
    """
    try:
        # Count pending vendors
        pending_count = frappe.db.count('Vendor Master', {
            'via_data_import': 1,
            'user_create': 0,
            'is_blocked': 0,
            'office_email_primary': ['!=', ''],
            'office_email_primary': ['is', 'set']
        })
        
        if pending_count == 0:
            return {"status": "info", "message": "No pending vendors to process"}
        
        # Create log for tracking
        log_doc = frappe.get_doc({
            "doctype": "Vendor User Creation Log",
            "total_vendors": pending_count,
            "processed": 0,
            "failed": 0,
            "status": "Queued",
            "start_time": frappe.utils.now()
        })
        log_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Enqueue the background job
        enqueue(
            'vms.utils.bulk_vendor_user_creation.process_all_vendors',
            queue='long',
            timeout=3600,  # 1 hour timeout
            log_id=log_doc.name,
            is_async=True
        )
        
        return {
            "status": "success",
            "message": f"Processing started for {pending_count} vendors in background. Check log: {log_doc.name}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error starting bulk processing: {str(e)}")
        return {"status": "error", "message": str(e)}


# ============================================
# BACKGROUND WORKER FUNCTION
# ============================================

def process_all_vendors(log_id):
    """
    Process all pending vendors in background
    This function runs in background worker
    """
    try:
        # Update log status
        log_doc = frappe.get_doc("Vendor User Creation Log", log_id)
        log_doc.status = "Processing"
        log_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Get all pending vendors
        vendors = frappe.db.sql("""
            SELECT name, vendor_name, office_email_primary
            FROM `tabVendor Master`
            WHERE via_data_import = 1
            AND user_create = 0
            AND is_blocked = 0
            AND office_email_primary IS NOT NULL
            AND office_email_primary != ''
            ORDER BY name
        """, as_dict=True)
        
        processed = 0
        failed = 0
        skipped = 0  # Track skipped vendors with existing users
        
        for vendor in vendors:
            try:
                # Check if user exists
                if frappe.db.exists("User", vendor.office_email_primary):
                    # User exists - just mark as done, don't send email
                    vendor_doc = frappe.get_doc("Vendor Master", vendor.name)
                    
                    # Skip if blocked
                    if vendor_doc.is_blocked:
                        frappe.logger().info(f"Skipping blocked vendor: {vendor.name}")
                        skipped += 1
                        continue
                    
                    # Just mark user_create as 1, don't send email
                    vendor_doc.user_create = 1
                    vendor_doc.save(ignore_permissions=True)
                    skipped += 1
                    frappe.logger().info(f"Skipped vendor {vendor.name} - user already exists")
                else:
                    # Create user and send email
                    process_new_user_vendor(vendor.name)
                    processed += 1
                
                # Commit after every 10 vendors to avoid long transactions
                if (processed + skipped) % 10 == 0:
                    frappe.db.commit()
                    # Update log
                    log_doc.reload()
                    log_doc.processed = processed
                    log_doc.failed = failed
                    log_doc.skipped = skipped  # If you add this field to log
                    log_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                
            except Exception as e:
                failed += 1
                frappe.log_error(
                    f"Error processing vendor {vendor.name}: {str(e)}", 
                    "Vendor Processing Error"
                )
                frappe.db.rollback()
        
        # Final update
        log_doc.reload()
        log_doc.processed = processed
        log_doc.failed = failed
        log_doc.status = "Completed"
        log_doc.end_time = frappe.utils.now()
        log_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.logger().info(f"Completed processing: {processed} processed, {failed} failed, {skipped} skipped")
        
    except Exception as e:
        frappe.log_error(f"Error in process_all_vendors: {str(e)}")
        # Update log to failed
        try:
            log_doc = frappe.get_doc("Vendor User Creation Log", log_id)
            log_doc.status = "Failed"
            log_doc.save(ignore_permissions=True)
            frappe.db.commit()
        except:
            pass



# ============================================
# VENDOR PROCESSING FUNCTIONS
# ============================================

def process_new_user_vendor(vendor_name):
    """Create user and send email for vendor"""
    vendor_doc = frappe.get_doc("Vendor Master", vendor_name)
    
    # Skip blocked vendors
    if vendor_doc.is_blocked:
        frappe.logger().info(f"Skipping blocked vendor: {vendor_name}")
        return
    
    # Generate password
    password = generate_random_password()
    
    # Create user
    new_user = frappe.new_doc("User")
    new_user.email = vendor_doc.office_email_primary
    new_user.first_name = vendor_doc.vendor_name or "Vendor"
    new_user.send_welcome_email = 0
    new_user.module_profile = "Vendor"
    new_user.role_profile_name = "Vendor"
    new_user.new_password = password
    new_user.insert(ignore_permissions=True)
    
    # Collect vendor codes
    vendor_code_data = collect_all_vendor_codes(vendor_doc)
    
    # Get CC list
    cc = get_vendor_cc_list(vendor_doc)
    
    # Send email
    send_vendor_email_with_pdf_imported(
        email=vendor_doc.office_email_primary,
        username=vendor_doc.office_email_primary,
        password=password,
        vendor_name=vendor_doc.vendor_name or "Vendor",
        vendor_code_data=vendor_code_data,
        is_new_user=True,
        cc=cc
    )
    
    # Mark as done
    vendor_doc.user_create = 1
    vendor_doc.save(ignore_permissions=True)


def process_existing_user_vendor(vendor_name):
    """Send email for vendor with existing user"""
    vendor_doc = frappe.get_doc("Vendor Master", vendor_name)
    
    # Skip blocked vendors
    if vendor_doc.is_blocked:
        frappe.logger().info(f"Skipping blocked vendor: {vendor_name}")
        return
    
    # Collect vendor codes
    vendor_code_data = collect_all_vendor_codes(vendor_doc)
    
    # Get CC list
    cc = get_vendor_cc_list(vendor_doc)
    
    # Send email (no credentials)
    send_vendor_email_with_pdf_imported(
        email=vendor_doc.office_email_primary,
        username=vendor_doc.office_email_primary,
        password=None,
        vendor_name=vendor_doc.vendor_name or "Vendor",
        vendor_code_data=vendor_code_data,
        is_new_user=False,
        cc=cc
    )
    
    # Mark as done
    vendor_doc.user_create = 1
    vendor_doc.save(ignore_permissions=True)


# ============================================
# HELPER FUNCTIONS (Keep your existing ones)
# ============================================

def collect_all_vendor_codes(vendor_doc):
    """Collect all vendor codes"""
    all_vendor_data = []
    
    try:
        if not hasattr(vendor_doc, 'multiple_company_data') or not vendor_doc.multiple_company_data:
            return all_vendor_data
        
        for company_data_row in vendor_doc.multiple_company_data:
            if hasattr(company_data_row, 'company_vendor_code') and company_data_row.company_vendor_code:
                try:
                    company_vendor_code_doc = frappe.get_doc(
                        "Company Vendor Code", 
                        company_data_row.company_vendor_code
                    )
                    
                    if hasattr(company_vendor_code_doc, 'vendor_code') and company_vendor_code_doc.vendor_code:
                        for vendor_code_row in company_vendor_code_doc.vendor_code:
                            vendor_info = {
                                'company_name': getattr(company_vendor_code_doc, 'company_name', ''),
                                'state': getattr(vendor_code_row, 'state', ''),
                                'gst_no': getattr(vendor_code_row, 'gst_no', ''),
                                'vendor_code': getattr(vendor_code_row, 'vendor_code', '')
                            }
                            all_vendor_data.append(vendor_info)
                except:
                    continue
    except:
        pass
    
    return all_vendor_data


def get_vendor_cc_list(vendor_doc):
    """Get CC emails"""
    cc = []
    try:
        if vendor_doc.vendor_onb_records:
            ven_onb = frappe.get_doc(
                "Vendor Onboarding",
                safe_get(vendor_doc, "vendor_onb_records", -1, "vendor_onboarding_no")
            )
            
            approvers = [
                ven_onb.registered_by,
                ven_onb.purchase_t_approval,
                ven_onb.purchase_h_approval,
                ven_onb.accounts_t_approval,
                ven_onb.accounts_head_approval,
            ]
            
            seen = set()
            cc = [email for email in approvers if email and not (email in seen or seen.add(email))]
    except:
        pass
    
    return cc


def send_vendor_email_with_pdf_imported(email, username, password, vendor_name, 
                                       vendor_code_data, is_new_user=True, cc=None):
    """Send email with PDF"""
    from vms.utils.custom_send_mail import custom_sendmail
    from frappe.utils.pdf import get_pdf
    
    # Generate PDF
    pdf_content = create_vendor_data_pdf_imported(vendor_name, vendor_code_data)
    
    # Prepare email
    if is_new_user and password:
        subject = f"Welcome {vendor_name} - Vendor Portal Access & Vendor Codes"
        message = f"""
        <p>Dear {vendor_name},</p>
        <p>Welcome to our Vendor Portal! Your account has been created successfully.</p>
        <p><strong>Login Credentials:</strong></p>
        <ul>
            <li>Username: {username}</li>
            <li>Password: {password}</li>
        </ul>
        <p>Please find your vendor codes attached in the PDF.</p>
        <p>Thank you!</p>
        """
    else:
        subject = f"Vendor Codes Information - {vendor_name}"
        message = f"""
        <p>Dear {vendor_name},</p>
        <p>Please find your vendor codes in the attached PDF.</p>
        <p>Thank you!</p>
        """
    
    # Send email
    custom_sendmail(
        recipients=[email],
        cc=cc,
        subject=subject,
        message=message,
        attachments=[{
            'fname': f'Vendor_Codes_{vendor_name}.pdf',
            'fcontent': pdf_content
        }],
        now=True
    )


def create_vendor_data_pdf_imported(vendor_name, vendor_code_data):
    """Create PDF - Keep your existing function"""
    from frappe.utils.pdf import get_pdf
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f5f5f5; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Vendor Code Information</h1>
        <h2>Vendor: {vendor_name}</h2>
        <table>
            <thead>
                <tr>
                    <th>S.No.</th>
                    <th>Company Name</th>
                    <th>State</th>
                    <th>GST Number</th>
                    <th>Vendor Code</th>
                </tr>
            </thead>
            <tbody>
    """
    
    if vendor_code_data:
        for idx, data in enumerate(vendor_code_data, 1):
            if isinstance(data, dict):
                html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td>{data.get('company_name', '')}</td>
                        <td>{data.get('state', '')}</td>
                        <td>{data.get('gst_no', '')}</td>
                        <td>{data.get('vendor_code', '')}</td>
                    </tr>
                """
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    return get_pdf(html_content)


def generate_random_password():
    """Generate random password"""
    length = 12
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for i in range(length))


def safe_get(obj, attr, index=None, subattr=None):
    """Safely get attribute - Keep your existing function"""
    try:
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            if index is not None and isinstance(value, list):
                if len(value) > 0:
                    if (index < 0 and abs(index) <= len(value)) or (index >= 0 and index < len(value)):
                        value = value[index]
                        if subattr and hasattr(value, subattr):
                            return getattr(value, subattr)
                        return value
            elif index is None:
                return value
    except:
        pass
    return None
