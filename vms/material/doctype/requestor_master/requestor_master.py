# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import string
from frappe.model.document import Document

BASE62 = string.digits + string.ascii_uppercase + string.ascii_lowercase

def base62_encode(num, length):
    arr = []
    base = len(BASE62)
    while num > 0:
        num, rem = divmod(num, base)
        arr.append(BASE62[rem])
    while len(arr) < length:
        arr.append('0')
    return ''.join(reversed(arr))

def get_next_request_id_reverse(length=7):
    max_counter = len(BASE62) ** length - 1
    counter_v = frappe.db.get_single_value("Material Onboarding Settings", "last_request_id_counter")
    counter = max_counter if counter_v is None else int(counter_v)

    while counter >= 0:
        request_id = base62_encode(counter, length)
        counter -= 1
        if not frappe.db.exists("Requestor Master", {"request_id": request_id}):
            frappe.db.set_value("Material Onboarding Settings", None, "last_request_id_counter", counter)
            return request_id

    frappe.throw("All Request IDs exhausted")

class RequestorMaster(Document):
    def validate(self):
        try:
            char_length = frappe.db.get_single_value("Material Onboarding Settings", "requestor_id_char_number") or 7
            try:
                char_length = int(char_length)
            except ValueError:
                char_length = 7

            if not self.request_id or self.is_duplicate_request_id(self.request_id):
                self.request_id = get_next_request_id_reverse(char_length)

            return {"status": "success", "message": "Request ID validated"}

        except Exception as e:
            frappe.log_error(f"Request ID validation error for {self.name}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def is_duplicate_request_id(self, request_id):
        exists = frappe.db.exists("Requestor Master", {"request_id": request_id, "name": ["!=", self.name]})
        return True if exists else False

    def after_save(self):
        try:
            from vms.material.doctype.material_aging_track.material_aging_track import create_or_update_aging_tracker_from_requestor
            create_or_update_aging_tracker_from_requestor(self.name)
            return {"status": "success", "message": "Aging tracker update completed"}
        except Exception as e:
            frappe.log_error(f"Aging tracker update error for {self.name}: {str(e)}")
            return {"status": "error", "message": str(e)}
