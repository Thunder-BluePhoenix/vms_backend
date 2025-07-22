// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Request For Quotation", {
// 	refresh(frm) {

// 	},
// });

// frappe.ui.form.on('Request For Quotation', {
// 	after_save: function (frm) {
//         console.log("runinininini")
// 		// Delay of 1.5 seconds before calling method
// 		setTimeout(() => {
// 			frappe.call({
// 				method: "vms.purchase.doctype.request_for_quotation.request_for_quotation.get_version_data",
// 				args: {
// 					docname: frm.doc.name
// 				},
// 				callback: function (r) {
// 					if (!r.exc) {
// 						console.log("Version data processed");
// 					}
// 				}
// 			});
// 		}, 1500);
// 	}
// });
