frappe.pages['woocommerce-sync-dashboard'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'WooCommerce Sync',
        single_column: true
    });

    // Load the HTML template into the page body
    $(frappe.render_template("woocommerce_sync_dashboard")).appendTo(page.body);

    // Initial sync status
    updateSyncStatus();

    // Event listeners
    $(page.body).on('click', '#sync-button', function() {
        syncOrders();
    });
};

function updateSyncStatus() {
    frappe.call({
        method: 'woocommerce_sync.sync_sales_orders.get_sync_status',
        callback: function(response) {
            if (response.message) {
                $('#last-sync').text(response.message.last_sync || '-');
                $('#status').text(response.message.sync_status || '-');
            }
        }
    });
}

function syncOrders() {
    $('#sync-button').prop('disabled', true);
    $('#sync-message').html('<div class="alert alert-info">Syncing orders from WooCommerce...</div>');

    frappe.call({
        method: 'woocommerce_sync.sync_sales_orders.sync_orders',
        callback: function(response) {
            if (response.message.status === 'success') {
                $('#sync-message').html('<div class="alert alert-success">' + response.message.message + '</div>');
            } else {
                $('#sync-message').html('<div class="alert alert-danger">' + response.message.message + '</div>');
            }
            $('#sync-button').prop('disabled', false);
            updateSyncStatus();
        }
    });
}
