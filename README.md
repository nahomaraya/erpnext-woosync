# WooCommerce Sync - ERPNext Integration

A comprehensive Frappe/ERPNext application that synchronizes orders, customers, and products between WooCommerce and ERPNext, enabling seamless e-commerce and ERP integration.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Application Logic](#application-logic)
- [Status Mapping](#status-mapping)
- [Logging and Monitoring](#logging-and-monitoring)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

The WooCommerce Sync app bridges the gap between your WooCommerce online store and ERPNext ERP system. It automatically:

- **Syncs orders** from WooCommerce to ERPNext as Sales Orders
- **Creates customers** in ERPNext from WooCommerce customer data
- **Creates items** in ERPNext from WooCommerce products
- **Updates order statuses** when orders change in WooCommerce
- **Syncs invoices** back to WooCommerce when created in ERPNext
- **Maintains data integrity** by preventing duplicate orders

Access the webpage at http://localhost/sync_sales_orders

## Features

### Core Functionality

- ✅ **Bidirectional Sync**: Orders from WooCommerce → ERPNext, Invoices from ERPNext → WooCommerce
- ✅ **Automatic Customer Creation**: Creates ERPNext customers from WooCommerce billing data
- ✅ **Automatic Item Creation**: Creates ERPNext items from WooCommerce products (using SKU)
- ✅ **Status Synchronization**: Maps and updates order statuses between both systems
- ✅ **Duplicate Prevention**: Uses `woocommerce_order_id` to prevent duplicate order creation
- ✅ **Comprehensive Logging**: All operations are logged for audit trail and debugging
- ✅ **Error Handling**: Graceful error handling with detailed error messages
- ✅ **Manual & Scheduled Sync**: Supports both manual triggers and scheduled synchronization

### Supported Order Statuses

The app syncs orders with the following WooCommerce statuses:
- `pending`
- `processing`
- `on-hold`
- `completed`
- `cancelled`
- `refunded`
- `failed`

## Architecture

### Module Structure

```
woocommerce_sync/
├── sales_order_to_woocommerce.py  # Core sync logic (WooCommerceSync class)
├── sync_sales_orders.py            # API endpoints for order sync
├── sync_invoice.py                 # API endpoints for invoice sync
├── woocommerce_config.py           # Configuration management
├── logger.py                       # Centralized logging
├── after_install.py                # Post-installation setup
├── public/
│   └── woocommerce_sync.js         # Frontend JavaScript
└── www/
    └── sync_sales_orders.html      # Web interface
```

### Key Components

1. **WooCommerceSync Class** (`sales_order_to_woocommerce.py`)
   - Main synchronization engine
   - Handles all WooCommerce API interactions
   - Manages order, customer, and item creation/updates

2. **Configuration Module** (`woocommerce_config.py`)
   - Manages WooCommerce API credentials
   - Stores sync settings (enable/disable, interval)
   - Tracks sync status and timestamps

3. **Logging System** (`logger.py`)
   - Centralized logging to WooCommerce Sync Log doctype
   - Tracks all operations with timestamps and details
   - Provides error tracebacks for debugging

4. **API Endpoints** (`sync_sales_orders.py`, `sync_invoice.py`)
   - Whitelisted methods callable from frontend
   - Handle manual sync triggers
   - Manage configuration updates

## How It Works

### Order Synchronization Flow

<img width="564" height="621" alt="Untitled Diagram-Page-1 drawio" src="https://github.com/user-attachments/assets/5023dc8f-0681-463f-adc8-637d5ede4c5a" />


### Detailed Process

1. **Initialization**
   - Loads WooCommerce API configuration (URL, keys)
   - Validates configuration completeness
   - Initializes WooCommerce API client

2. **Order Fetching**
   - Connects to WooCommerce REST API (wc/v3)
   - Fetches all orders with supported statuses
   - Validates API response

3. **Order Processing** (for each order)
   - **Validation**: Checks required fields (ID, billing, line items, prices)
   - **Duplicate Check**: Searches for existing Sales Order by `woocommerce_order_id`
   - **Status Update** (if exists): Updates order status if changed in WooCommerce
   - **Order Creation** (if new):
     - Creates/gets customer from billing information
     - Creates/gets items from line items (using SKU)
     - Creates Sales Order with items, taxes, and status
     - Submits order if not in Draft/Cancelled status

4. **Customer Creation Logic**
   - First checks by `woocommerce_customer_id` (if available)
   - If not found, creates new customer from billing data
   - Ensures required Customer Group and Territory exist
   - Links customer to WooCommerce via `woocommerce_customer_id` field

5. **Item Creation Logic**
   - Extracts SKU from multiple possible locations:
     - Main `sku` field
     - `meta_data` array
     - `_ywapo_meta_data` (for YITH WooCommerce Add-ons)
   - If no SKU, generates fallback code from item name
   - Creates item with default settings (stock item, sales item, purchase item)

6. **Status Mapping**
   - Maps WooCommerce statuses to ERPNext statuses
   - Handles status transitions based on business rules
   - Prevents invalid status updates

7. **Logging & Status Update**
   - Logs all operations to WooCommerce Sync Log
   - Updates sync status (Success/Failed/Partial Success)
   - Records last sync timestamp

## Installation

### Prerequisites

- Frappe/ERPNext version 14 or 15
- WooCommerce store with REST API enabled
- WooCommerce REST API credentials (Consumer Key & Secret)

### Installation Steps

1. **Clone the app** into your Frappe bench's apps directory:
   ```bash
   cd /path/to/your/bench/apps
   git clone <repository-url> woocommerce_sync
   ```

2. **Install the app** on your Frappe site:
   ```bash
   bench --site your_site_name install-app woocommerce_sync
   ```

3. **Migrate the site** (if needed):
   ```bash
   bench --site your_site_name migrate
   ```

4. **Restart bench**:
   ```bash
   bench restart
   ```

## Configuration

### WooCommerce Settings

1. Navigate to **WooCommerce Settings** doctype in ERPNext
2. Enter your WooCommerce store configuration:
   - **WooCommerce URL**: Your store URL (e.g., `https://yourstore.com`)
   - **Consumer Key**: WooCommerce REST API consumer key
   - **Consumer Secret**: WooCommerce REST API consumer secret
   - **Enable Sync**: Toggle to enable/disable synchronization
   - **Sync Interval**: Choose Daily, Weekly, or Monthly (for scheduled syncs)

### Getting WooCommerce API Credentials

1. Log in to your WooCommerce admin panel
2. Go to **WooCommerce → Settings → Advanced → REST API**
3. Click **Add Key**
4. Set permissions to **Read/Write**
5. Copy the **Consumer Key** and **Consumer Secret**

## Usage

### Manual Synchronization

1. Navigate to **Woocommerce Sync Data** from the ERPNext desk
2. Click **Sync from WooCommerce** button
3. Monitor the sync status and messages
4. View detailed logs in **WooCommerce Sync Log**

### Scheduled Synchronization

Configure scheduled tasks in Frappe to run `woocommerce_sync.sync_sales_orders.sync_orders` at your desired interval.

### Viewing Sync Logs

1. Navigate to **WooCommerce Sync Log** list view
2. Filter by:
   - Log Type (Sync, Order, Customer, Item)
   - Status (Success, Failed, Info)
   - Date range
3. Click on any log entry to view details

## Application Logic

### Order Status Mapping

| WooCommerce Status | ERPNext Status | Notes |
|-------------------|----------------|-------|
| `pending` | `Draft` | Order is created but not submitted |
| `processing` | `To Deliver and Bill` | Order is being processed |
| `on-hold` | `On Hold` | Order is temporarily on hold |
| `completed` | `Completed` | Order is fully completed |
| `cancelled` | `Cancelled` | Order has been cancelled |
| `refunded` | `Closed` | Order has been refunded |
| `failed` | `Cancelled` | Payment failed |

### Status Update Rules

- **Draft Orders**: Can be updated to any status
- **Submitted Orders**: Only allow specific transitions:
  - `To Deliver and Bill` → `Completed` or `Cancelled`
  - `Completed` → `Cancelled` only
  - `Cancelled` → No further updates allowed
- **Existing Status**: If order is already in target status, no update is performed

### Duplicate Prevention

The app uses the `woocommerce_order_id` custom field on Sales Orders to:
- Identify existing orders during sync
- Prevent duplicate order creation
- Enable status updates for existing orders

### Error Handling

- **Individual Order Errors**: If one order fails, the sync continues with other orders
- **API Errors**: Validates API responses and provides detailed error messages
- **Data Validation**: Validates order data before processing to catch issues early
- **Database Conflicts**: Retry logic handles concurrent updates

### Tax Handling

- Extracts tax information from WooCommerce `tax_lines`
- Maps to ERPNext tax entries with:
  - Charge Type: "On Net Total"
  - Account Head: Default tax account
  - Rate: From WooCommerce tax rate
  - Description: From WooCommerce tax label

### Invoice Sync (ERPNext → WooCommerce)

When a Sales Invoice is created in ERPNext:
1. System checks if it's linked to a Sales Order
2. Retrieves the `woocommerce_order_id` from the Sales Order
3. Updates the WooCommerce order:
   - Sets status to `completed`
   - Adds metadata linking the ERPNext invoice

## Status Mapping

### WooCommerce → ERPNext

The app automatically maps WooCommerce order statuses to appropriate ERPNext Sales Order statuses, ensuring workflow compatibility.

### Business Rules

- Orders in `Draft` status are not automatically submitted
- Orders in `processing` or `completed` status are submitted in ERPNext
- Status updates respect ERPNext's business rules for status transitions

## Logging and Monitoring

### Log Types

- **Sync**: Overall sync process start/end
- **Order**: Individual order creation/update operations
- **Customer**: Customer creation operations
- **Item**: Item creation operations

### Log Statuses

- **Success**: Operation completed successfully
- **Failed**: Operation failed with error
- **Info**: Informational messages

### Log Details

Each log entry includes:
- Timestamp
- Log type and status
- Message
- Additional details (JSON format)
- Reference to related documents (if applicable)
- Error traceback (for failures)
- WooCommerce order ID (for order logs)

## Troubleshooting

### Common Issues

1. **"WooCommerce configuration is incomplete"**
   - **Solution**: Check WooCommerce Settings doctype and ensure all fields are filled

2. **"Failed to sync order"**
   - **Check**: WooCommerce Sync Log for detailed error messages
   - **Common causes**: Missing customer email, invalid item data, API connection issues

3. **"Order already exists" but status not updating**
   - **Check**: Order's current status and docstatus in ERPNext
   - **Note**: Some status transitions are restricted by business rules

4. **Items not being created**
   - **Check**: SKU extraction logic - verify SKU exists in WooCommerce product
   - **Note**: If no SKU, system generates a fallback code

5. **API Connection Errors**
   - **Verify**: WooCommerce URL, Consumer Key, and Consumer Secret
   - **Check**: WooCommerce REST API is enabled
   - **Test**: Use WooCommerce API test tools to verify credentials

### Debugging Tips

1. **Check Sync Logs**: Always start by reviewing WooCommerce Sync Log
2. **Verify API Access**: Test WooCommerce API credentials independently
3. **Check Order Data**: Review raw WooCommerce order data in logs
4. **Validate Configuration**: Ensure all required settings are configured
5. **Review Error Messages**: Error messages include specific details about failures

## Technical Details

### API Version

- WooCommerce REST API: `wc/v3`
- ERPNext: Version 14/15 compatible

### Dependencies

- `woocommerce` Python library for API communication
- Frappe framework for ERPNext integration

### Custom Fields

The app automatically adds a custom field to Sales Order doctype:
- **Field Name**: `woocommerce_order_id`
- **Type**: Data
- **Purpose**: Links ERPNext Sales Orders to WooCommerce orders

### Database Tables

- **WooCommerce Settings**: Stores configuration (Single doctype)
- **WooCommerce Sync Log**: Stores all sync operation logs
- **Sales Order**: Extended with `woocommerce_order_id` field

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or contributions, please refer to the project repository.

---

**Tested on**: ERPNext 14/15 and WooCommerce wc/v3
