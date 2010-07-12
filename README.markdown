## cisco_ssapi
A Python API to Cisco's EOX (Smart Support Web Services API)

Cisco provides a SOAP API to EOX data through their Smart Support Web Services
API. This cisco_ssapi module provides a Python wrapper around that interface to
make it easy to retrieve EOX data from Cisco from Python.

### Requirements
As of v0.7 this module requires the suds module.

### Installation
Install like any other Python module: `sudo python setup.py install`

### Usage
In addition to being a Python API to access EOX data, the cisco_ssapi module
also provides some example scripts for access this information from the
command line.

Example script usage:

* `get_eox -u USERNAME -p PASSWORD`
* `get_eox_products -u USERNAME -p PASSWORD`
* `get_eox_by_dates -u USERNAME -p PASSWORD -s 2010-05-21 -e 2010-05-28`
* `get_eox_by_oid -u USERNAME -p PASSWORD -h hardwareType OID1 OID2 ...`
* `get_eox_by_product -u USERNAME -p PASSWORD prodID1 prodID2 ...`
* `get_eox_by_sw -u USERNAME -p PASSWORD -o osType sw1 sw2 ...`
* `get_eox_by_serial -u USERNAME -p PASSWORD serial1 serial2 ...`

Look into the cisco_ssapi/scripts.py for the source to these scripts and as
examples on using the API directly.
