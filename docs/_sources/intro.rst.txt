Introduction
============

.. image:: https://zenodo.org/badge/336671726.svg
   :target: https://zenodo.org/badge/latestdoi/336671726

The `FedCloud client <https://fedcloudclient.fedcloud.eu/>`_ is a high-level Python package for a command-line client
designed for interaction with the OpenStack services in the EGI infrastructure. The client can access various EGI
services and can perform many tasks for users including managing access tokens, listing services, and mainly execute
commands on OpenStack sites in EGI infrastructure.

The most notable features of FedCloud client are following:

* **Rich functionalities:** have wide ranges of useful commands, including checking access token, searching for
  services, listing sites and VOs, and interaction with OpenStack sites.

* **Simple usages:** can perform any OpenStack command on any sites with only three parameters: the site, the VO
  and the command. For example, to list virtual machines (VM) images available to members of ``vo.access.egi.eu`` VO
  on ``IISAS-FedCloud`` site, run the following command:

::

   $ fedcloud openstack image list --vo vo.access.egi.eu --site IISAS-FedCloud

* **Federation-wide:** Single client for all OpenStack sites and related services of EGI Cloud infrastructure.
  Single command may perform an action on all sites by specifying :code:`--site ALL_SITES`.

* **Programmable:** the client is designed for using in
  `scripts for automation <https://fedcloudclient.fedcloud.eu/scripts.html>`_
  or as a `Python library <https://fedcloudclient.fedcloud.eu/development.html>`_
  for programming FedCloud services.

The following modules are included:

* **fedcloudclient.conf** for handling fedcloudclient configuration,

* **fedcloudclient.checkin** for operation with EGI Check-in like getting tokens,

* **fedcloudclient.endpoint** for searching endpoints via GOCDB, getting unscoped/scoped token from
  OpenStack keystone,

* **fedcloudclient.sites** for managing site configurations,

* **fedcloudclient.openstack** for performing OpenStack operations on sites,

* **fedcloudclient.secret** for accessing secrets in
  `Secret management service <https://vault.docs.fedcloud.eu/index.html>`_,

* **fedcloudclient.ec3** for deploying elastic computing clusters in Cloud.

A short tutorial of the fedcloudclient is available in `this
presentation <https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing>`_.
The full documentation, including installation, usage and API description is available
at https://fedcloudclient.fedcloud.eu/.
