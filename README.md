# ERPNEXT WooCommerce Sync App(erpnext-woosync)

The application is a custom Frappe app designed to synchronize data between a Frappe ERPNext instance and a WooCommerce store. This app streamlines business processes by ensuring that sales orders, invoices, and other critical data are consistent across both platforms.

## Current Features
- Syncs sales orders, customers, and products from WooCommerce to ERPNEXT.

- Manual or scheduled synchronization


## How It Works

The app operates by listening for new sales orders in WooCommerce and then creating them as sales orders and invoices within your Frappe instance. This process is managed by a set of Python controllers and scheduled jobs.

Tested on ERPNEXT 14/15 and Woocommerce wc/v3

## Installation

Clone the app into your Frappe bench's apps directory:
```
bench get-app https://github.com/nahomaraya/woocommerce-sync.git
```
Install the app on your Frappe site:
```
bench --site your_site_name install-app woocommerce_sync
```

## Setup and Configuration:

Navigate to the WooCommerce Settings DocType in your Frappe Desk.

Enter your WooCommerce API keys and store URL.

Configure the synchronization settings to meet your needs.

WooCommerce Settings: To store API keys and configuration.

WooCommerce Sync Log: To log synchronization activities and errors.

## License
This project is licensed under the MIT License.
