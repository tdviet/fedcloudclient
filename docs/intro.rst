Introduction
============

**fedcloudclient** is a command-line client and high-level Python package for interaction with EGI Federated Cloud.
The aim here was to create a simple client which would allow users to perform the various OpenStack operations
in EGI Federated Cloud. Performing any OpenStack command on any site requires only three options: site, VO and
the command. For example:

* Listing images in fedcloud.egi.eu VO on CYFRONET-CLOUD site:

::

    $ fedcloud openstack image list --vo fedcloud.egi.eu --site CYFRONET-CLOUD

* Listing all VMs in eosc-synergy.eu VO on all sites in EGI Federated Cloud

::

    $ fedcloud openstack server list --vo eosc-synergy.eu --site ALL_SITES

Five modules are included: **fedcloudclient.checkin** for operation with EGI Check-in like
getting tokens, **fedcloudclient.endpoint** for searching endpoints via GOCDB, getting unscoped/scoped token from
OpenStack keystone, **fedcloudclient.sites** manages site configurations, **fedcloudclient.openstack** for
performing OpenStack operations, and finally **fedcloudclient.ec3** for deploying elastic computing clusters in Cloud.


