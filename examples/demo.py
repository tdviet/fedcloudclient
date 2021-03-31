"""
This is a simple demo code how to use fedcloudclient code as a library
for development of tools and services for EGI Federated Cloud
Only single call is needed for any OpenStack command at any site/VO

Usage: add your access token to line 14, and execute "python demo.py"
"""

import json

# Import fedcloudclient library
from fedcloudclient.openstack import fedcloud_openstack

# Setting values for input parameters: token, site, VO
token = "YOUR_ACCESS_TOKEN"
site = "CYFRONET-CLOUD"
vo = "fedcloud.egi.eu"

# OpenStack command and options. Must be a tuple
command = ("image", "list", "--long")

# Execute the OpenStack command on the site/VO with single line of code
# If command finishes correctly, the error_code is 0 and the result is stored
# in JSON object for easy processing

error_code, result = fedcloud_openstack(token, site, vo, command)

# Check error code and print the result if OK
if error_code == 0:
    print(json.dumps(result, indent=4))
else:
    # If error, result is string containing error message
    print("Error message is %s" % result)
