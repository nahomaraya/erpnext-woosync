"""
WooCommerce Configuration
This file contains the WooCommerce API configuration settings.
"""

# WooCommerce API Configuration
WOOCOMMERCE_CONFIG = {
    "url": "http://order.eco2.ca",  # Your WooCommerce store URL (e.g., "https://your-store.com")
    "consumer_key": "ck_20147c5f5be907ce1aaf5c5da7e3e3e455416687",  # Your WooCommerce consumer key
    "consumer_secret": "cs_6cadf54c66d8efba4731c4c750e68febbebad9a1",  # Your WooCommerce consumer secret
    "version": "wc/v3",  # WooCommerce API version
    "verify_ssl": True,  # SSL verification
    "timeout": 30,  # API request timeout in seconds
}

# Sync Configuration
SYNC_CONFIG = {
    "enable_sync": True,
    "sync_interval": "daily",  # Options: "daily", "weekly", "monthly"
    "sync_status": "",
    "last_sync": None
} 