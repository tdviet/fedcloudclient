Using FedCloud client in Python
===============================

FedCloud client can be used as a library for developing other services and tools for EGI Federated Cloud. Most of
functionalities of FedCloud client can be called directly from other codes without side effects. An example of the code
using FedCloud client is available at `GitHub <https://github.com/tdviet/fedcloudclient/blob/master/examples/demo.py>`_.
Just copy/download the code, add your access token and execute *"python demo.py"* to see how it works.

::

    # Import FedCloud client library
    from fedcloudclient.openstack import fedcloud_openstack
    import json

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


Read the `FedCloud client API references <https://fedcloudclient.fedcloud.eu/fedcloudclient.html>`_
for more details about each function in FedCloud client library. Check the output of the equivalent command of
FedCloud client and its source code to see how the function is used.