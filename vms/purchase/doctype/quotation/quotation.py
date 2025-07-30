import frappe
import json
from frappe.model.document import Document

class Quotation(Document):
    
    def on_update(self):
        if not self.flags.get('skip_ranking_update'):
            frappe.enqueue(
                'vms.purchase.doctype.quotation.quotation.background_update_rankings',
                quotation_name=self.name,
                rfq_number=self.rfq_number,
                queue='short',
                timeout=300
            )
        
        if not self.flags.get('skip_rfq_update'):
            set_quotation_id_in_rfq(self)
    
    def update_quotation_rankings(self):
        try:
            quotations = frappe.get_all(
                "Quotation",
                filters={
                    "rfq_number": self.rfq_number,
                },
                fields=["name", "quote_amount"]
            )
            
            if not quotations:
                return
            
            valid_quotations = []
            invalid_quotations = []
            
            for q in quotations:
                try:
                    if q.quote_amount and str(q.quote_amount).strip():
                        quote_amount_float = float(str(q.quote_amount).replace(',', ''))
                        if quote_amount_float > 0:
                            q.quote_amount_float = quote_amount_float
                            valid_quotations.append(q)
                        else:
                            invalid_quotations.append(q)
                    else:
                        invalid_quotations.append(q)
                except (ValueError, TypeError):
                    invalid_quotations.append(q)
            
            if not valid_quotations:
                return
            
            valid_quotations.sort(key=lambda x: x.quote_amount_float)
		    
            
        
            for index, quotation in enumerate(valid_quotations):
                rank = index + 1
                try:
                    frappe.db.sql("""
                        UPDATE `tabQuotation` 
                        SET rank = %s, modified = NOW() 
                        WHERE name = %s
                    """, (str(rank), quotation.name))
                    
                    frappe.logger().info(f"Updated Quotation {quotation.name} rank to {rank} for RFQ {self.rfq_number}")
                except Exception as e:
                    frappe.log_error(f"Failed to update rank for {quotation.name}: {str(e)}", "Ranking Update Error")
            
           
            for quotation in invalid_quotations:
                try:
                    frappe.db.sql("""
                        UPDATE `tabQuotation` 
                        SET rank = '', modified = NOW() 
                        WHERE name = %s
                    """, (quotation.name,))
                except Exception as e:
                    frappe.log_error(f"Failed to clear rank for {quotation.name}: {str(e)}", "Ranking Clear Error")
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error updating quotation rankings for RFQ {self.rfq_number}: {str(e)}", "Quotation Ranking Error")
            
            frappe.logger().error(f"Failed to update quotation rankings: {str(e)}")



def background_update_rankings(quotation_name, rfq_number):
    try:
        quotation = frappe.get_doc("Quotation", quotation_name)
        quotation.flags.skip_ranking_update = True 
        quotation.update_quotation_rankings()
    except Exception as e:
        frappe.log_error(f"Background ranking update failed for {quotation_name}: {str(e)}", "Background Ranking Error")



# def set_quotation_id_in_rfq(doc):
#     if not doc.rfq_number:
#         return

#     try:
   
#         if doc.ref_no or doc.office_email_primary:
#             frappe.db.sql("""
#                 UPDATE `tabVendor Details` 
#                 SET quotation = %s 
#                 WHERE parent = %s AND ref_no = %s AND (quotation IS NULL OR quotation = '')
#             """, (doc.name, doc.rfq_number, doc.ref_no))

#         if doc.office_email_primary:
#             frappe.db.sql("""
#                 UPDATE `tabNon Onboarded Vendor Details` 
#                 SET quotation = %s 
#                 WHERE parent = %s AND office_email_primary = %s AND (quotation IS NULL OR quotation = '')
#             """, (doc.name, doc.rfq_number, doc.office_email_primary))
            
#         frappe.db.commit()
        
#     except Exception as e:
#         frappe.log_error(f"Error setting quotation ID in RFQ {doc.rfq_number}: {str(e)}", "RFQ Update Error")

def set_quotation_id_in_rfq(doc):
    if not doc.rfq_number:
        return

    try:
        conditions = []
        values = []

        # Build dynamic condition for Vendor Details
        if doc.ref_no:
            conditions.append("(ref_no = %s)")
            values.append(doc.ref_no)
        if doc.office_email_primary:
            conditions.append("(office_email_primary = %s)")
            values.append(doc.office_email_primary)

        if conditions:
            condition_clause = " OR ".join(conditions)
            frappe.db.sql(f"""
                UPDATE `tabVendor Details` 
                SET quotation = %s 
                WHERE parent = %s AND ({condition_clause}) AND (quotation IS NULL OR quotation = '')
            """, tuple([doc.name, doc.rfq_number] + values))

        # Non-Onboarded Vendor: Only use office_email_primary
        if doc.office_email_primary:
            frappe.db.sql("""
                UPDATE `tabNon Onboarded Vendor Details` 
                SET quotation = %s 
                WHERE parent = %s AND office_email_primary = %s AND (quotation IS NULL OR quotation = '')
            """, (doc.name, doc.rfq_number, doc.office_email_primary))

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error setting quotation ID in RFQ {doc.rfq_number}: {str(e)}", "RFQ Update Error")