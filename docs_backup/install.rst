Installation
============

Installing FedCloud client with pip
***********************************

Simply use the following **pip3** command (should be done without root privileges).

::

    $ pip3 install -U fedcloudclient

Installation Notes
------------------

Installing the latest version of the **FedCloud client** package using ``pip3`` will also install all required dependencies (such as **openstackclient**). It will create the executable files **``fedcloud``** and **``openstack``**, placing them in the appropriate directory based on your Python environment:

* ``$VIRTUAL_ENV/bin`` – when using ``pip3`` inside a Python virtual environment,
* ``~/.local/bin`` – when installing with ``pip3 --user``,
* ``/usr/local/bin`` – when installing system-wide with ``pip3`` as root.

.. note::

   If you install the package with the ``--user`` option, make sure that ``~/.local/bin`` is included in your ``$PATH``.

Verifying the Installation
--------------------------

To check if the installation was successful, run the following command::

::

    $ fedcloud --help


This will show output::

::
    Usage: fedcloud [OPTIONS] COMMAND [ARGS]...

    CLI main function. Intentionally empty

    Options:
    --version  Show the version and exit.
    --help     Show this message and exit.

    Commands:
    ec3            EC3 cluster provisioning
    endpoint       Obtain endpoint details and scoped tokens
    openstack      Execute OpenStack commands on site and VO
    openstack-int  Interactive OpenStack client on site and VO
    secret         Commands for accessing secret objects
    select         Select resources according to specification
    site           Obtain site configurations
    token          Get details of access token    



Installing EGI Core Trust Anchor certificates
*********************************************

Some sites use certificates issued by national certificate authorities that are not included in the default
OS distribution. If you receive error message *"SSL exception connecting to https:// ..."*,
follow `instructions <https://github.com/tdviet/python-requests-bundle-certs/blob/main/docs/Install_certificates.md>`_
for installing EGI Core Trust Anchor certificates and add them to the certificate bundle of Python requests. For quick
test in virtual environment, just execute the following commands. See this
`README.md <https://github.com/tdviet/python-requests-bundle-certs#usage>`_ for more details.

::

    $ wget https://raw.githubusercontent.com/tdviet/python-requests-bundle-certs/main/scripts/install_certs.sh
    $ bash install_certs.sh

Using FedCloud client via Docker container
******************************************

You can use Docker container for testing **FedCloud client** without installation. EGI Core Trust Anchor certificates
and site configurations are preinstalled.

::

    $ sudo docker pull tdviet/fedcloudclient
    $ sudo docker run -it  tdviet/fedcloudclient bash



