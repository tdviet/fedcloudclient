Installation
============

Installing fedcloudclient with pip
**********************************

Simply use the following **pip3** command (should be done without root privileges).

::

    $ pip3 install fedcloudclient

That will install latest version **fedcloudclient** package together with its required packages (like **openstackclient**).
It will also create executable files **"fedcloud"** and **"openstack"** and add them to corresponding directory
according to your Python execution environment (*$VIRTUAL_ENV/bin* for executing *pip3* in Python virtual environment,
*~/.local/bin* for executing *pip3* as user (with *--user* option), and */usr/local/bin* when executing *pip3* as root).
Make sure to add *~/.local/bin* to $PATH if installing as user.

Check if the installation is correct by executing the client

::

    $ fedcloud

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

Using fedcloudclient via Docker container
*****************************************

You can use Docker container for testing **fedcloudclient** without installation. EGI Core Trust Anchor certificates
and site configurations are preinstalled.

::

    $ sudo docker pull tdviet/fedcloudclient
    $ sudo docker run -it  tdviet/fedcloudclient bash



