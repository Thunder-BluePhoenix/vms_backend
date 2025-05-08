# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document

class OTPVerification(Document):
    pass


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

