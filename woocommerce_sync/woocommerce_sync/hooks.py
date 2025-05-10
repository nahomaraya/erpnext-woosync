from __future__ import unicode_literals

# App configuration
app_name = "woocommerce_sync"
app_title = "WooCommerce Sync"
app_publisher = "Your Company"
app_description = "Sync Sales Orders from WooCommerce to ERPNext"
app_email = "your@email.com"
app_license = "MIT"

# Scheduled Tasks
scheduler_events = {
    "daily": [
        "woocommerce_sync.sales_order_to_woocommerce.WooCommerceSync.sync_from_woocommerce"
    ],
    "weekly": [
        "woocommerce_sync.sales_order_to_woocommerce.WooCommerceSync.sync_from_woocommerce"
    ],
    "monthly": [
        "woocommerce_sync.sales_order_to_woocommerce.WooCommerceSync.sync_from_woocommerce"
    ]
}

# Website Context
website_context = {
    "favicon": "/assets/woocommerce_sync/images/favicon.png",
    "splash_image": "/assets/woocommerce_sync/images/splash.png"
} 