# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from frappe.utils import now_datetime, add_to_date, get_datetime
import json

class OTPVerification(Document):
    def after_insert(self):
        # Set expiration timestamp for cron-based processing
        exp_doc = frappe.get_doc("OTP Settings") or None
        
        if exp_doc != None:
            exp_t_min = float(exp_doc.otp_expiration_time)
        else:
            exp_t_min = 5  # Default 5 minutes
        
        # Set expiration time
        self.db_set('expiration_time', add_to_date(now_datetime(), minutes=exp_t_min), update_modified=False)
        frappe.db.commit()
        
        # exp_t_sec = exp_t_min * 60
        
        # # Enqueue background jobs (existing approach)
        # exp_d_sec = exp_t_sec + 300
        # frappe.enqueue(
        #     method=self.handle_otp_expiration,
        #     queue='default',
        #     timeout=exp_d_sec,
        #     now=False,
        #     job_name=f'otp_expiration_{self.name}',
        # )

        # frappe.enqueue(
        #     method=self.delete_otp_doc,
        #     queue='default',
        #     timeout=exp_d_sec,
        #     now=False,
        #     job_name=f'otp_deletion_{self.name}',
        # )
        
    def handle_otp_expiration(self):
        """Background job to expire OTP"""
        exp_doc = frappe.get_doc("OTP Settings") or None
        
        if exp_doc != None:
            exp_t_min = float(exp_doc.otp_expiration_time)
            exp_t_sec = exp_t_min * 60
        else:
            exp_t_sec = 300
            
        time.sleep(exp_t_sec)
        
        self.db_set('expired', 1, update_modified=False)
        frappe.db.commit()

    def delete_otp_doc(self):
        """Background job to delete OTP"""
        exp_doc = frappe.get_doc("OTP Settings") or None
        if exp_doc != None:
            exp_t_min = float(exp_doc.otp_expiration_time)
            exp_t_sec = exp_t_min * 60
        else:
            exp_t_sec = 300
        
        exp_d_sec = exp_t_sec + 120
        time.sleep(exp_d_sec)
        
        frappe.delete_doc("OTP Verification", self.name, force=1)
        frappe.db.commit()
        



@frappe.whitelist(allow_guest = True)
def verify_otp_and_delete(data):
    input_otp= data.get("otp")
    user = data.get("user")
    doc = frappe.get_doc("OTP Verification", {"otp":input_otp}) or None

    if doc != None or doc.expired != 1 or doc.is_not_verified != 1:
        if doc.email == user :
            doc.is_verified = 1
            doc.save()
            frappe.delete_doc("OTP Verification", doc.name, force=1)
            frappe.db.commit()
            return {"status": "success", "message": "OTP verified"}

        else:
            doc.is_not_verified = 1
            doc.save()
            frappe.delete_doc("OTP Verification", doc.name, force=1)
            frappe.db.commit()
            return {"status": "Failed", "message": "Wrong OTP"}
        
    else:
        return {"status": "Failed", "message": "Invalid OTP"}




    # Mark as verified
    

   
    



def expire_otps():
    """
    Cron job to expire OTPs that have passed their expiration time
    Runs every 5 minutes
    """
    try:
        # Get all non-expired OTPs
        otps = frappe.get_all(
            "OTP Verification",
            filters={
                "expired": 0,
                "expiration_time": ["<=", now_datetime()]
            },
            pluck="name"
        )
        
        if otps:
            for otp_name in otps:
                frappe.db.set_value("OTP Verification", otp_name, "expired", 1, update_modified=False)
            
            frappe.db.commit()
            frappe.logger().info(f"Expired {len(otps)} OTP(s)")
            
    except Exception as e:
        frappe.log_error(f"Error in expire_otps: {str(e)}", "OTP Expiration Error")


def delete_expired_otps():
    """
    Cron job to delete expired OTPs after retention period
    Runs every 10 minutes
    """
    try:
        # Get OTP Settings for deletion time
        exp_doc = frappe.get_doc("OTP Settings") or None
        
        if exp_doc and hasattr(exp_doc, 'otp_deletion_time'):
            deletion_minutes = float(exp_doc.otp_deletion_time)
        else:
            deletion_minutes = 2  # Default 2 minutes after expiration
        
        # Calculate deletion threshold
        deletion_threshold = frappe.utils.add_to_date(now_datetime(), minutes=-deletion_minutes)
        
        # Get expired OTPs that are ready for deletion
        otps_to_delete = frappe.get_all(
            "OTP Verification",
            filters={
                "expired": 1,
                "expiration_time": ["<=", deletion_threshold]
            },
            pluck="name"
        )
        
        if otps_to_delete:
            for otp_name in otps_to_delete:
                frappe.delete_doc("OTP Verification", otp_name, force=1)
            
            frappe.db.commit()
            frappe.logger().info(f"Deleted {len(otps_to_delete)} expired OTP(s)")
            
    except Exception as e:
        frappe.log_error(f"Error in delete_expired_otps: {str(e)}", "OTP Deletion Error")


def cleanup_old_otps():
    """
    Daily cleanup job to remove very old OTP records
    Runs once daily
    """
    try:
        # Delete OTPs older than 24 hours
        old_threshold = frappe.utils.add_to_date(now_datetime(), days=-1)
        
        old_otps = frappe.get_all(
            "OTP Verification",
            filters={
                "creation": ["<=", old_threshold]
            },
            pluck="name"
        )
        
        if old_otps:
            for otp_name in old_otps:
                frappe.delete_doc("OTP Verification", otp_name, force=1)
            
            frappe.db.commit()
            frappe.logger().info(f"Cleaned up {len(old_otps)} old OTP(s)")
            
    except Exception as e:
        frappe.log_error(f"Error in cleanup_old_otps: {str(e)}", "OTP Cleanup Error")

    

