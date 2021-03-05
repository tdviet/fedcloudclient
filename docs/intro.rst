Introduction
============

**fedcloudclient** is a command-line client and high-level Python package for interaction with EGI Federated Cloud.
This package is an extension of the `egicli <https://github.com/EGI-Foundation/egicli>`_ for Openstack commands.

The aim here was to create a simple client which would allow users to perform the various Openstack operations 
in EGI Federated Cloud. Performing any Openstack command on any site requires only three options: site, VO and
the command. For example:

* Listing images in fedcloud.egi.eu VO on CYFRONET-CLOUD site:

::

    $ fedcloud openstack image list --vo fedcloud.egi.eu --site CYFRONET-CLOUD

* Listing all VMs in eosc-synergy.eu VO on all sites in EGI Federated Cloud

::

    $ fedcloud openstack server list --vo eosc-synergy.eu --site ALL_SITES

Four modules are included: **fedcloudclient.checkin** for operation with EGI Check-in like
getting tokens, **fedcloudclient.endpoint** for searching endpoints via GOCDB, getting unscoped/scoped token from
Keystone, **fedcloudclient.sites** manages site configuration and finally **fedcloudclient.openstack** for
performing Openstack operations.


