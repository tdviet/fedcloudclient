Introduction
============

**fedcloudclient** is a command-line client and high-level Python package for interaction with EGI Federated Cloud.
This package is an extension of the `egicli <https://github.com/EGI-Foundation/egicli>`_ for Openstack commands.

The aim here was to create a simple client which would allow users to perform the various Openstack operations 
in EGI Federated Cloud. Four modules are included: **fedcloudclient.checkin** for operation with EGI Check-in like
getting tokens, **fedcloudclient.endpoint** for searching endpoints via GOCDB, getting unscoped/scoped token from
Keystone, **fedcloudclient.sites** manages site configuration and finally **fedcloudclient.openstack** for
performing Openstack operations.

See `Quick start <https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing>`_
for instruction how to install and use **fedcloud** command-line client and **fedcloudclient** package.

