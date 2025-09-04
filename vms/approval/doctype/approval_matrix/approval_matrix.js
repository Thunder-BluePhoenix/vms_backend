// Copyright (c) 2024, Meril and contributors
// For license information, please see license.txt

/**
 * Fetch and populate the Conditional Field dropdown for the selected DocType.
 */
function get_dynamic_select_options(frm) {
  if (!frm.doc.for_doc_type) return;

  frappe.call({
    method: "vms.utils.get_doc_fields_list.get_doc_fields_list",
    args: {
      doctype: frm.doc.for_doc_type,
    },
    callback: function (response) {
      const options = response?.message || [];

      // Update the parent field (if you need it)
      frm.set_df_property("conditional_field", "options", options);

      // Update the child-table field
      frm.get_field('conditions')
        .grid
        .update_docfield_property(
          'conditional_field',
          'options',
          options
        );
    },
  });
}

// === Parent Doctype Hooks ===
frappe.ui.form.on("Approval Matrix", {
  refresh: function (frm) {
    // Populate Conditional Field options & initialize Value fields
    get_dynamic_select_options(frm);
  },
  for_doc_type: get_dynamic_select_options,
});
