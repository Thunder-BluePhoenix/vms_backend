frappe.listview_settings['Vendor Master'] = {
    onload(listview) {
        listview.page.add_menu_item(__('Danger'), function() {
            let selected = listview.get_checked_items();

            if (!selected.length) {
                frappe.msgprint(__('Please select at least one Vendor Master.'));
                return;
            }

            // Build a list of vendors
            let vendor_names = selected.map(row => row.name).join(", ");

            // Friendly dialog box
            frappe.prompt(
                [
                    {
                        fieldname: 'confirm_text',
                        label: 'Type DELETE to confirm',
                        fieldtype: 'Data',
                        reqd: 1
                    }
                ],
                (values) => {
                    if (values.confirm_text !== "DELETE") {
                        frappe.msgprint(__('Action cancelled. You must type DELETE to confirm.'));
                        return;
                    }

                    // Call Danger API for each vendor
                    frappe.call({
                        method: "vms.vms_masters.doctype.vendor_master.vendor_master.danger_action_bulk", // update path
                        args: { vendor_name: vendor_names },
                        freeze: true,
                        freeze_message: __('Deleting selected vendors...'),
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.show_alert({
                                    message: __('Vendors deleted successfully'),
                                    indicator: 'red'
                                });
                                listview.refresh();
                            }
                        }
                    });
                },
                __('⚠️ Confirm Danger Delete'),
                __('Delete')
            );
        });
    }
};
