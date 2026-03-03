frappe.pages['woocommerce-config'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'WooCommerce Configuration',
        single_column: true
    });

    $(frappe.render_template("woocommerce_config", {})).appendTo(page.body);

    // Load existing config
    frappe.call({
        method: "woocommerce_sync.woocommerce_sync.page.woocommerce_config.woocommerce_config.get_config",
        callback: function(r) {
            if (r.message) {
                let cfg = r.message;
                $("#woocommerce_url").val(cfg.woocommerce_url || "");
                $("#consumer_key").val(cfg.consumer_key || "");
                $("#consumer_secret").val(cfg.consumer_secret || "");
                $("#enable_sync").prop("checked", cfg.enable_sync ? 1 : 0);
                $("#sync_interval").val(cfg.sync_interval || "Daily");
                $("#last_sync").text(cfg.last_sync || "-");
                $("#sync_status").text(cfg.sync_status || "-");
            }
        }
    });

    // Save config
    $("#save-config").on("click", function() {
        let config = {
            woocommerce_url: $("#woocommerce_url").val(),
            consumer_key: $("#consumer_key").val(),
            consumer_secret: $("#consumer_secret").val(),
            enable_sync: $("#enable_sync").is(":checked") ? 1 : 0,
            sync_interval: $("#sync_interval").val()
        };

        frappe.call({
            method: "woocommerce_sync.woocommerce_sync.page.woocommerce_config.woocommerce_config.save_config",
            args: { config },
            callback: function(r) {
                frappe.show_alert({ message: r.message, indicator: "green" });
            }
        });
    });

    // Test connection
    // $("#test-connection").on("click", function() {
    //     frappe.call({
    //         method: "woocommerce_sync.woocommerce_sync.page.woocommerce_config.woocommerce_config.test_connection",
    //         callback: function(r) {
    //             frappe.msgprint(r.message);
    //         }
    //     });
    // });

    // // Sync now
    // $("#sync-now").on("click", function() {
    //     frappe.call({
    //         method: "woocommerce_sync.woocommerce_sync.page.woocommerce_config.woocommerce_config.sync_now",
    //         callback: function(r) {
    //             frappe.msgprint(r.message);
    //         }
    //     });
    // });
};
