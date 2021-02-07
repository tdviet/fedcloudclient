"""
This is a simple demo code how to use fedcloudclient code as a library
for development of tools and services for EGI Federated Cloud

Only single call is needed for any Openstack command at any site/VO
"""

from fedcloudclient.openstack import fedcloud_openstack
import json

# Add your token there
token = "YOUR_ACCESS_TOKEN"

# Change site/VO if needed according to your VO membership
site = "CYFRONET-CLOUD"
vo = "fedcloud.egi.eu"

# Openstack command and options. Must be a tuple
command = ("image", "list", "--long")

# Except for setting input, that is the only line of code needed
# The result is stored in a JSON object for further processing
# ===============================================================

error_code, result = fedcloud_openstack(token, site, vo, command)

# ==============================================================

# Check error code
if error_code == 0:
    print(json.dumps(result, indent=4))
else:
    # If error, result is string containing error message
    print("Error message is %s" % result)
