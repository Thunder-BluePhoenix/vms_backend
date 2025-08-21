# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime
from frappe import _
import qrcode
import base64
import json
import io
from frappe.utils import now, get_site_path
from frappe.utils.file_manager import save_file
import os


class DispatchItem(Document):
	def before_save(self):
		if self.dispatch_form_submitted == 1 and self.qr_code_generated != 1:
			self.generate_qr_code()



	def on_update(self, method=None):
		calculate_pending_qty(self, method=None)
		try:
			for row in self.purchase_number:
				if not row.purchase_number:
					continue

				po = frappe.get_doc("Purchase Order", row.purchase_number)
				current_date = now_datetime()

				for item in po.po_items:
					# Skip if item already added
					if any(existing.row_id == item.name for existing in self.items):
						continue

					self.append("items", {
						"row_id": item.name,
						"po_number": po.name,
						"product_code": item.product_code,
						"product_name": item.product_name,
						"description": item.short_text,
						"quantity": item.quantity,
						"hsnsac": item.hsnsac,
						"uom": item.uom,
						"rate": item.rate,
						"amount": item.price,
						"pending_qty": item.pending_qty
					})

			# self.save(ignore_permissions=True)
				found = False
				for dis_id in po.dispatch_ids:
					if dis_id.dispatch_id == self.name:
						dis_id.dispatch_datetime = current_date
						found = True
						break
				if found == False:
					po.append("dispatch_ids", {
						"dispatch_id" : self.name,
						"dispatch_datetime": current_date
					})
				po.save()
				
			

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "DispatchItem after_insert Error")





	def generate_qr_code(self):
		"""Generate QR code with document data"""
		try:
			# Prepare data to embed in QR code
			qr_data = self.prepare_qr_data()
			
			# Generate QR code
			qr_code_image_url = self.create_qr_code_image(qr_data)
			
			if qr_code_image_url:
				# Update document fields
				self.qr_code_image = qr_code_image_url
				self.qr_code_data = json.dumps(qr_data, indent=2)
				self.qr_code_generated = 1
				self.qr_generation_date = now()
				
				frappe.msgprint(f"QR Code generated successfully for {self.name}")
			else:
				frappe.throw("Failed to generate QR code image")
				
		except Exception as e:
			frappe.log_error(f"QR Code generation error for {self.name}: {str(e)}")
			frappe.throw(f"Error generating QR code: {str(e)}")

	def prepare_qr_data(self):
		try:
			qr_data = {
				"doc_id": self.name,
				"doctype": "Dispatch Item", 
				"creation": str(self.creation) if self.creation else None,
				"modified": str(self.modified) if self.modified else None,
				"owner": self.owner,
				"vendor_code":self.vendor_code,
				"courier_number": self.courier_number,
				"docket_number": self.docket_number,
				"invoice_number": self.invoice_number,
				"dispatch_form_submitted": self.dispatch_form_submitted,
				"timestamp": now()
			}
			
			# Serialize purchase orders
			qr_data["purchase_orders"] = self.serialize_table_field('purchase_number')
			
			# Serialize items
			qr_data["details_of_orders"] = self.serialize_table_field('items')
			
			# Check QR data size (QR codes have limits)
			qr_json = json.dumps(qr_data)
			data_size = len(qr_json.encode('utf-8'))
			
			# If data is too large (>2KB), use simplified version
			if data_size > 2048:
				frappe.msgprint(f"QR data size ({data_size} bytes) is large. Consider using simplified version.", alert=True)
				
			return qr_data
			
		except Exception as e:
			frappe.log_error(f"Error preparing QR data: {str(e)}")
			# Fallback to simple version
			return {
				"doc_id": self.name,
				"doctype": "Dispatch Item",
				"timestamp": now(),
				"error": "Full data generation failed"
			}
	
	
	
	
	def serialize_table_field(self, table_field_name):
		"""Helper method to serialize table fields"""
		if not hasattr(self, table_field_name):
			return []

		table_data = getattr(self, table_field_name)
		if not table_data:
			return []

		serialized_rows = []
		for row in table_data:
			row_data = {}
			for field in row.meta.fields:
				if field.fieldtype not in ['Section Break', 'Column Break', 'HTML', 'Button']:
					value = getattr(row, field.fieldname, None)
					if value is not None:
						# Handle different data types
						if hasattr(value, 'strftime'):  # DateTime
							row_data[field.fieldname] = value.strftime('%Y-%m-%d %H:%M:%S')
						elif isinstance(value, (int, float, bool)):
							row_data[field.fieldname] = value
						elif isinstance(value, list):
							row_data[field.fieldname] = [str(item) for item in value]
						else:
							row_data[field.fieldname] = str(value)
			serialized_rows.append(row_data)

		return serialized_rows

	def create_qr_code_image(self, data):
		"""Create QR code image and save as file"""
		try:
			# Convert data to JSON string
			qr_content = json.dumps(data)
			
			# Create QR code instance
			qr = qrcode.QRCode(
				version=1,  # Controls the size (1 is smallest)
				error_correction=qrcode.constants.ERROR_CORRECT_L,  # Low error correction
				box_size=10,  # Size of each box in pixels
				border=4,  # Border size
			)
			
			# Add data to QR code
			qr.add_data(qr_content)
			qr.make(fit=True)
			
			# Create QR code image
			qr_image = qr.make_image(fill_color="black", back_color="white")
			
			# Convert image to bytes
			img_buffer = io.BytesIO()
			qr_image.save(img_buffer, format='PNG')
			img_buffer.seek(0)
			
			# Generate filename
			filename = f"qr_code_{self.name}_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}.png"
			
			# Save file using Frappe's file manager
			file_doc = save_file(
				filename,
				img_buffer.getvalue(),
				"Dispatch Item",
				self.name,
				decode=False,
				is_private=0
			)
			
			return file_doc.file_url
			
		except Exception as e:
			frappe.log_error(f"QR Code image creation error: {str(e)}")
			raise e

	@frappe.whitelist()
	def regenerate_qr_code(self):
		"""Method to manually regenerate QR code"""
		if self.dispatch_form_submitted != 1:
			frappe.throw("Cannot generate QR code. Dispatch form must be submitted first.")
		
		# Reset QR code fields
		self.qr_code_generated = 0
		self.qr_code_image = ""
		self.qr_code_data = ""
		self.qr_generation_date = ""
		
		# Generate new QR code
		self.generate_qr_code()
		self.save()
		
		return "QR Code regenerated successfully"

	@frappe.whitelist()
	def get_qr_data(self):
		"""Get QR code data for external use"""
		if self.qr_code_data:
			return json.loads(self.qr_code_data)
		return None



# calculating Pending Qty 
def calculate_pending_qty(doc, method=None):
	try:
		for row in doc.items:
			row.pending_qty = int(row.quantity) - int(row.dispatch_qty)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Pending Qty Calculation Error")








@frappe.whitelist()
def generate_qr_for_dispatch_item(doc_name):
    """API method to generate QR code for a specific dispatch item"""
    try:
        doc = frappe.get_doc("Dispatch Item", doc_name)
        
        if doc.dispatch_form_submitted != 1:
            return {
                "success": False,
                "message": "Dispatch form must be submitted before generating QR code"
            }
        
        if doc.qr_code_generated == 1:
            return {
                "success": False,
                "message": "QR code has already been generated for this dispatch item"
            }
        
        doc.generate_qr_code()
        doc.save()
        
        return {
            "success": True,
            "message": "QR code generated successfully",
            "qr_code_url": doc.qr_code_image
        }
        
    except Exception as e:
        frappe.log_error(f"API QR generation error: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@frappe.whitelist()
def bulk_generate_qr_codes(filters=None):
    """Bulk generate QR codes for multiple dispatch items"""
    try:
        # Default filters
        if not filters:
            filters = {
                "dispatch_form_submitted": 1,
                "qr_code_generated": 0
            }
        
        dispatch_items = frappe.get_all("Dispatch Item", filters=filters, fields=["name"])
        
        success_count = 0
        error_count = 0
        errors = []
        
        for item in dispatch_items:
            try:
                doc = frappe.get_doc("Dispatch Item", item.name)
                doc.generate_qr_code()
                doc.save()
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"{item.name}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Processed {len(dispatch_items)} items. Success: {success_count}, Errors: {error_count}",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10]  # Return first 10 errors
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Bulk generation error: {str(e)}"
        }

@frappe.whitelist()
def decode_qr_data(qr_content):
    """Decode QR code content and return document information"""
    try:
        # Parse QR content as JSON
        qr_data = json.loads(qr_content)
        
        # Validate required fields
        if "doc_id" not in qr_data or "doctype" not in qr_data:
            return {
                "success": False,
                "message": "Invalid QR code format"
            }
        
        # Get document if it exists
        if frappe.db.exists(qr_data["doctype"], qr_data["doc_id"]):
            doc = frappe.get_doc(qr_data["doctype"], qr_data["doc_id"])
            
            return {
                "success": True,
                "message": "QR code decoded successfully",
                "document": {
                    "name": doc.name,
                    "doctype": doc.doctype,
                    "creation": doc.creation,
                    "dispatch_form_submitted": doc.dispatch_form_submitted,
                    "qr_code_generated": doc.qr_code_generated
                },
                "qr_data": qr_data
            }
        else:
            return {
                "success": False,
                "message": "Document referenced in QR code not found"
            }
            
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "Invalid QR code content - not valid JSON"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error decoding QR code: {str(e)}"
        }