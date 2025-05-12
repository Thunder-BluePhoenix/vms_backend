# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue

class OTPVerification(Document):
    def after_insert(self):
        exp_doc = frappe.get_doc("OTP Settings") or None
        print("@@@@@@@@@@@@@@@@@", exp_doc)
        
        if exp_doc != None:
            exp_t_min = float(exp_doc.otp_expiration_time)
            print("@@@@@@@@@@@@@@@@@", exp_t_min)
            exp_t_sec = exp_t_min * 60
            print("@@@@@@@@@@@@@@@@@", exp_t_sec)
        else:
            exp_t_sec = 300
            
        # Enqueue a background job to handle OTP expiration
        exp_d_sec = exp_t_sec + 300
        frappe.enqueue(
            method=self.handle_otp_expiration,
            queue='default',
            timeout=exp_d_sec,
            now=False,
            job_name=f'otp_expiration_{self.name}',
            # enqueue_after_commit = False
        )

        frappe.enqueue(
            method=self.delete_otp_doc,
            queue='default',
            timeout=exp_d_sec,
            now=False,
            job_name=f'otp_deletion_{self.name}',
            # enqueue_after_commit = False
        )
        
    def handle_otp_expiration(self):
        # This will run in the background after the specified time
        # Put your OTP expiration logic here
        # frappe.delete_doc("OTP Verification", self.name, force = 1)
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ OTP expiration job executed")
        # frappe.db.commit()
        
        # For example, you might want to update the status of the OTP verification
        exp_doc = frappe.get_doc("OTP Settings") or None
        
        if exp_doc != None:
            exp_t_min = float(exp_doc.otp_expiration_time)
            exp_t_sec = exp_t_min * 60
           
        else:
            exp_t_sec = 300
        time.sleep(exp_t_sec)
        
        self.db_set('expired', 1, update_modified=False)

        # exp_d_sec = exp_t_sec + 300
        frappe.db.commit()

        

    def delete_otp_doc(self):
        exp_doc = frappe.get_doc("OTP Settings") or None
        if exp_doc != None:
            exp_t_min = float(exp_doc.otp_expiration_time)
            exp_t_sec = exp_t_min * 60
           
        else:
            exp_t_sec = 300
        

        exp_d_sec = exp_t_sec + 120
        time.sleep(exp_d_sec)
        
        frappe.delete_doc("OTP Verification", self.name, force = 1)
        frappe.db.commit()



        



@frappe.whitelist(allow_guest = True)
def verify_otp_and_delete(docname, input_otp):
    """Verify OTP, wait 30 sec, delete if verified, and return success message."""
    doc = frappe.get_doc("OTP Verification", docname)

    if doc.otp != input_otp:
        frappe.throw("Invalid OTP")

    # Mark as verified
    doc.is_verified = 1
    doc.save()

    # Wait for 30 seconds
    # time.sleep(3)

    # Delete the document (move to Trash)
    frappe.delete_doc("OTP Verification", docname, force=1)
    frappe.db.commit()

    return {"status": "success", "message": "OTP verified and record deleted"}

