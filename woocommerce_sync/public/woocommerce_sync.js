/**
 * WooCommerce Sync - Frontend JavaScript
 * 
 * This file handles the client-side interactions for the WooCommerce Sync application.
 * It provides UI controls for manual synchronization, status updates, and configuration management.
 */

/**
 * Initialize the page when Frappe framework is ready
 * Sets up event handlers and loads initial sync status
 */
frappe.ready(function() {
    // Load initial sync status from the server
    updateSyncStatus();

    // Add click handler for manual sync button
    $('#sync-button').click(function() {
        syncOrders();
    });

    // Handle configuration form submission
    $('#config-form').submit(function(e) {
        e.preventDefault();
        saveConfiguration();
    });
});

/**
 * Update the sync status display on the page
 * Fetches the latest sync status from the server and updates the UI
 */
function updateSyncStatus() {
    frappe.call({
        method: 'woocommerce_sync.sync_sales_orders.get_sync_status',
        callback: function(response) {
            if (response.message) {
                // Update last sync timestamp
                $('#last-sync').text(response.message.last_sync || '-');
                // Update current sync status
                $('#status').text(response.message.sync_status || '-');
            }
        }
    });
}

/**
 * Trigger manual synchronization of orders from WooCommerce to ERPNext
 * Disables the sync button during operation and shows progress/result messages
 */
function syncOrders() {
    // Disable button to prevent multiple simultaneous syncs
    $('#sync-button').prop('disabled', true);
    // Show progress message
    $('#sync-message').html('<div class="alert alert-info">Syncing orders from WooCommerce...</div>');

    // Call the server-side sync method
    frappe.call({
        method: 'woocommerce_sync.sync_sales_orders.sync_orders',
        callback: function(response) {
            // Display success or error message based on response
            if (response.message.status === 'success') {
                $('#sync-message').html('<div class="alert alert-success">' + response.message.message + '</div>');
            } else {
                $('#sync-message').html('<div class="alert alert-danger">' + response.message.message + '</div>');
            }
            // Re-enable the sync button
            $('#sync-button').prop('disabled', false);
            // Refresh the sync status display
            updateSyncStatus();
        }
    });
}

/**
 * Save WooCommerce configuration settings
 * Collects form data and sends it to the server to update configuration
 */
function saveConfiguration() {
    // Build configuration object from form inputs
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

    // Send configuration to server
    frappe.call({
        method: 'woocommerce_sync.sync_sales_orders.update_config',
        args: {
            config_data: configData
        },
        callback: function(response) {
            // Show success or error notification
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

/**
 * Test the connection to WooCommerce API
 * Validates that the configured credentials can successfully connect to WooCommerce
 */
function testConnection() {
    // Disable button during test
    $('#test-connection-button').prop('disabled', true);
    // Show testing message
    $('#connection-test-result').html('<div class="alert alert-info">Testing WooCommerce connection...</div>');

    // Call server-side connection test method
    frappe.call({
        method: 'woocommerce_sync.sync_sales_orders.test_connection',
        callback: function(response) {
            // Display test results
            if (response.message.status === 'success') {
                $('#connection-test-result').html('<div class="alert alert-success">' + response.message.message + '</div>');
            } else {
                $('#connection-test-result').html('<div class="alert alert-danger">' + response.message.message + '</div>');
                // If error details are provided, display them
                if (response.message.details) {
                    $('#connection-test-result').append('<div class="mt-2"><small><strong>Details:</strong><br>' + JSON.stringify(response.message.details, null, 2) + '</small></div>');
                }
            }
            // Re-enable the test button
            $('#test-connection-button').prop('disabled', false);
        }
    });
}
