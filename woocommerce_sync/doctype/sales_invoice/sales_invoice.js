frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        // Add custom button to sync with WooCommerce
        frm.add_custom_button(__('Sync to WooCommerce'), function() {
            sync_to_woocommerce(frm);
        });
    }
});

function sync_to_woocommerce(frm) {
    // Check if invoice is submitted
    if (frm.doc.docstatus !== 1) {
        frappe.msgprint(__('Please submit the invoice first'));
        return;
    }

    // Show loading message
    frappe.show_progress('Syncing to WooCommerce', 0, 100, 'Please wait...');

    // Call the server-side method
    frappe.call({
        method: 'woocommerce_sync.sync_invoice.sync_invoice',
        args: {
            invoice_name: frm.doc.name
        },
        callback: function(r) {
            frappe.hide_progress();
            if (r.message && r.message.status === 'success') {
                frappe.msgprint({
                    title: __('Success'),
                    message: r.message.message,
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Failed'),
                    message: r.message.message || __('Failed to sync to WooCommerce'),
                    indicator: 'red'
                });
            }
        },
        error: function(r) {
            frappe.hide_progress();
            frappe.msgprint({
                title: __('Failed'),
                message: __('Failed to sync to WooCommerce'),
                indicator: 'red'
            });
        }
    });
} 