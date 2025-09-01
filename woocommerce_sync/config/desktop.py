from frappe import _

def get_data():
	return [
		{
			"module_name": "Woocommerce Sync",
			"type": "module",
			"label": _( "Woocommerce Sync" )
		},
		{
			"module_name": "Woocommerce Sync",
			"type": "page",
			"name": "woocommerce-sync",
			"label": _( "WooCommerce Sync" ),
			"icon": "octicon octicon-sync",
			"link": "woocommerce-sync",
			"category": "Modules"
		}
	]
