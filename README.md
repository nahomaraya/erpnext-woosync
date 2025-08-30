# WooCommerce Sync App

The woocommerce_sync application is a custom Frappe app designed to synchronize data between a Frappe ERPNext instance and a WooCommerce store. This app streamlines business processes by ensuring that sales orders, invoices, and other critical data are consistent across both platforms.

## Features
- Sales Order Synchronization: Automatically syncs sales orders from WooCommerce to Frappe.

- Invoice Generation: Creates corresponding invoices in Frappe based on synchronized sales orders.

- Real-time Updates: Maintains data consistency through scheduled background jobs.

- User-friendly Interface: Provides a simple web interface to manage and debug synchronization processes.

How It Works
The app operates by listening for new sales orders in WooCommerce and then creating them as sales orders and invoices within your Frappe instance. This process is managed by a set of Python controllers and scheduled jobs.

Data Flow
graph TD
    A[WooCommerce] --> B{Sync Sales Orders};
    B --> C[Frappe ERPNext];
    C --> D[Create Sales Invoice];

Installation
Clone the App:
Clone the app into your Frappe bench's apps directory:

bench get-app [https://github.com/your-username/woocommerce_sync.git](https://github.com/your-username/woocommerce_sync.git)

Install on Your Site:
Install the app on your Frappe site:

bench --site your_site_name install-app woocommerce_sync

Setup and Configuration:

Navigate to the WooCommerce Settings DocType in your Frappe Desk.

Enter your WooCommerce API keys and store URL.

Configure the synchronization settings to meet your needs.

Technical Details
DocTypes:

WooCommerce Settings: To store API keys and configuration.

WooCommerce Sync Log: To log synchronization activities and errors.

Sales Invoice (custom fields): Custom fields may be added to this standard DocType to support synchronization.

Hooks: The hooks.py file is used to define background jobs and other events.

Controllers: The sync_sales_orders.py, sync_invoice.py, and sales_order_to_woocommerce.py files contain the core business logic.

Contributing
We welcome contributions! If you would like to contribute, please fork the repository and submit a pull request.

License
This project is licensed under the MIT License.
