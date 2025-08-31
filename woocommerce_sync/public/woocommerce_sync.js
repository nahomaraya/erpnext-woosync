frappe.ready(function() {
    // Load initial sync status
    updateSyncStatus();

    // Add click handler for sync button
    $('#sync-button').click(function() {
        syncOrders();
    });

    // Handle configuration form submission
    $('#config-form').submit(function(e) {
        e.preventDefault();
        saveConfiguration();
    });
});

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

function saveConfiguration() {
    const configData = {
        woocommerce: {
            url: $('#woocommerce_url').val(),
            consumer_key: $('#consumer_key').val(),
            consumer_secret: $('#consumer_secret').val()
        },
        sync: {
            enable_sync: $('#enable_sync').is(':checked'),
            sync_interval: $('#sync_interval').val()
        }
    };

    frappe.call({
        method: 'woocommerce_sync.sync_sales_orders.update_config',
        args: {
            config_data: configData
        },
        callback: function(response) {
            if (response.message.status === 'success') {
                frappe.show_alert({
                    message: 'Configuration saved successfully',
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: 'Error saving configuration: ' + response.message.message,
                    indicator: 'red'
                });
            }
        }
    });
}

function testConnection() {
    $('#test-connection-button').prop('disabled', true);
    $('#connection-test-result').html('<div class="alert alert-info">Testing WooCommerce connection...</div>');

    frappe.call({
        method: 'woocommerce_sync.sync_sales_orders.test_connection',
        callback: function(response) {
            if (response.message.status === 'success') {
                $('#connection-test-result').html('<div class="alert alert-success">' + response.message.message + '</div>');
            } else {
                $('#connection-test-result').html('<div class="alert alert-danger">' + response.message.message + '</div>');
                if (response.message.details) {
                    $('#connection-test-result').append('<div class="mt-2"><small><strong>Details:</strong><br>' + JSON.stringify(response.message.details, null, 2) + '</small></div>');
                }
            }
            $('#test-connection-button').prop('disabled', false);
        }
    });
}
