Using fedcloud client for development
======================================

fedcloudclient can be used as a library for developing other services and tools for EGI Federated Cloud. Most of
functionalities of fedcloudclient can be called directly from other codes without side effects. An example of the code
using fedcloud client is available at `GitHub <https://github.com/tdviet/fedcloudclient/blob/master/examples/demo.py>`_.
Just copy/download the code, add your access token and execute *"python demo.py"* to see how it works.

::

    # Import fedcloudclient library
    from fedcloudclient.openstack import fedcloud_openstack
    import json

    # Setting values for input parameters: token, site, VO
    token = "YOUR_ACCESS_TOKEN"
    site = "CYFRONET-CLOUD"
    vo = "fedcloud.egi.eu"

    # Openstack command and options. Must be a tuple
    command = ("image", "list", "--long")

    # Execute the Openstack command on the site/VO with single line of code
    # If command finishes correctly, the error_code is 0 and the result is stored
    # in JSON object for easy processing

    error_code, result = fedcloud_openstack(token, site, vo, command)

    # Check error code and print the result if OK
    if error_code == 0:
        print(json.dumps(result, indent=4))
    else:
        # If error, result is string containing error message
        print("Error message is %s" % result)


Read the `fedcloudclient API references <https://fedcloudclient.readthedocs.io/en/master/fedcloudclient.html>`_
for more details about each function in fedcloudclient library. Check the output of the equivalent command of
fedcloudclient and its source code to see how the function is used.