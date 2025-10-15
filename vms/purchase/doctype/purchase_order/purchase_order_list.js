frappe.listview_settings['Purchase Order'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__('Bulk Validate Vendor Codes'), function() {
            frappe.confirm(
                'This will validate vendor codes for all Purchase Orders in the background. Continue?',
                function() {
                    frappe.call({
                        method: "vms.purchase.doctype.purchase_order.po_vm_validation_corn.enqueue_bulk_validate_vendor_codes",
                        args: {
                            batch_size: 5000
                        },
                        callback: function(r) {
                            if (r.message.status === "success") {
                                frappe.show_alert({
                                    message: r.message.message,
                                    indicator: 'green'
                                }, 5);
                            } else {
                                frappe.msgprint({
                                    title: 'Error',
                                    indicator: 'red',
                                    message: r.message.message
                                });
                            }
                        }
                    });
                }
            );
        });
    }
};