FAQ and Troubleshooting
=======================

1. *fedcloudclient* gives error message *"SSL exception connecting to https:// ..."* when connecting to some sites

Some sites use certificates issued by national certificate authorities that are not included in the default
OS distribution. If you receive error message *"SSL exception connecting to https:// ..."*,
follow `instructions <https://github.com/tdviet/python-requests-bundle-certs/blob/main/docs/Install_certificates.md>`_
for installing EGI Core Trust Anchor certificates and add them to the certificate bundle of Python requests. For quick
test in virtual environment, just execute the following commands. See this
`README.md <https://github.com/tdviet/python-requests-bundle-certs#usage>`_ for more details.

::

    $ wget https://raw.githubusercontent.com/tdviet/python-requests-bundle-certs/main/scripts/install_certs.sh
    $ bash install_certs.sh


2. *fedcloudclient* frozen during initialization (mainly on virtual machines at some sites)

It is a known problem of *libsodium* which is used by *oidc-agent* Python library. The problem is described
`here <https://doc.libsodium.org/usage#sodium_init-stalling-on-linux>`_. Check the entropy on the VMs by executing command
*"cat /proc/sys/kernel/random/entropy_avail"*, and if the result is lower than 300, install *haveged* or *rng-tools*.
On VMs with Centos, you also have to start the daemon manually after installation (or reboot the VMs)





