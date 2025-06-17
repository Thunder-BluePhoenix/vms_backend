// // Simple Web Form Client Script - Replace entire content

// $(document).ready(function() {
//     console.log("Setting up product filter for web form...");
    
//     setTimeout(function() {
//         // Set up filtering for all category dropdowns
//         $(document).on('change', '[data-fieldname="category_type"]', function() {
//             var categoryValue = $(this).val();
//             var $row = $(this).closest('tr');
//             var $productField = $row.find('[data-fieldname="product_name"]');
            
//             console.log("Category changed to:", categoryValue);
            
//             if ($productField.length) {
//                 // Clear current selection
//                 $productField.val('').trigger('change');
                
//                 if (categoryValue) {
//                     console.log("Loading products for category:", categoryValue);
                    
//                     // Load filtered products
//                     $.get('/api/method/frappe.client.get_list', {
//                         doctype: 'VMS Product Master',
//                         filters: JSON.stringify({category_type: categoryValue}),
//                         fields: JSON.stringify(['name', 'product_name']),
//                         order_by: 'product_name'
//                     })
//                     .done(function(response) {
//                         console.log("Products loaded:", response.message);
                        
//                         // Clear and populate dropdown
//                         $productField.empty();
//                         $productField.append('<option value="">Select Product</option>');
                        
//                         if (response.message && response.message.length > 0) {
//                             response.message.forEach(function(product) {
//                                 $productField.append(
//                                     '<option value="' + product.name + '">' + 
//                                     (product.product_name || product.name) + 
//                                     '</option>'
//                                 );
//                             });
//                         } else {
//                             $productField.append('<option value="">No products found</option>');
//                         }
//                     })
//                     .fail(function(error) {
//                         console.error("Error loading products:", error);
//                         $productField.empty();
//                         $productField.append('<option value="">Error loading products</option>');
//                     });
//                 } else {
//                     // No category selected
//                     $productField.empty();
//                     $productField.append('<option value="">Select category first</option>');
//                 }
//             }
//         });
        
//         console.log("Product filter setup complete");
//     }, 1000);
// });