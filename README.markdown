## cisco_ssapi
A Python API to Cisco's SSAPI (Smart Support Web Services API)

Cisco provides a SOAP API to EOX data through their Smart Support Web Services
API. This cisco_ssapi module provides a Python wrapper around that interface to
make it easy to retrieve EOX data from Cisco from Python.

### Installation
Install like any other Python module: `sudo python setup.py install`

### Usage
In addition to being a Python API to access EOX data, the cisco_ssapi module
also provides some example scripts for access this information from the
command line.

Example script usage:

* `get_eox_by_dates -u USERNAME -p PASSWORD -s 05/21/2010 -e 05/28/2010`
* `get_eox_by_serial -u USERNAME -p PASSWORD CAM09112822`

Look into the cisco_ssapi/scripts.py for the source to these scripts and as
examples on using the API directly.
