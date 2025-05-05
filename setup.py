from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in woocommerce_sync/__init__.py
from woocommerce_sync import __version__ as version

setup(
	name="woocommerce_sync",
	version=version,
	description="Custom woocommrece sync",
	author="Nahom",
	author_email="nahomaraya8@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
