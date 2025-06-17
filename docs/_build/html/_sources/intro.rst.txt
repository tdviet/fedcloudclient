Introduction
============

.. image:: https://zenodo.org/badge/336671726.svg
   :target: https://zenodo.org/badge/latestdoi/336671726

FedCloud Client
===============

The **FedCloud Client** (`https://fedcloudclient.fedcloud.eu/`) is a high-level Python package providing a unified command-line interface to the EGI Federated Cloud’s OpenStack services. It streamlines tasks such as managing access tokens, discovering services, and executing OpenStack commands across multiple sites.

Key Features
------------

- **Comprehensive Command Set**  
  Access a broad range of operations, including:
  
  - Token management (retrieve, inspect, renew)  
  - Service discovery and endpoint lookup  
  - Listing and filtering sites, virtual organizations (VOs), and resources  
  - Direct interaction with OpenStack services (compute, image, network, etc.)

- **Minimal Syntax, Maximum Power**  
  Execute any OpenStack action on any site with just three parameters:
  
  .. code-block:: console

     $ fedcloud openstack <command> --vo <VO_NAME> --site <SITE_NAME>

  For example, to list all available VM images for the VO ``vo.access.egi.eu`` on the ``IISAS-FedCloud`` site:

  .. code-block:: console

     $ fedcloud openstack image list \
         --vo vo.access.egi.eu \
         --site IISAS-FedCloud

- **Federation-Wide Scope**  
  One client, all sites. Use the special ``ALL_SITES`` identifier to run a command across every configured site in the federation:

  .. code-block:: console

     $ fedcloud openstack server list --vo vo.access.egi.eu --site ALL_SITES

- **Scriptable & Extensible**  
  Designed for automation and integration:
  
  - **Shell scripting**: embed ``fedcloud`` calls in CI/CD pipelines or custom scripts. See :doc:`scripts </scripts.html>`.  
  - **Python library**: import and invoke client functionality programmatically. See :doc:`developer guide </development.html>`.

Core Modules
------------

.. list-table::
   :header-rows: 1

   * - Module
     - Purpose
   * - ``fedcloudclient.conf``
     - Manage and validate client configuration (profiles, defaults).
   * - ``fedcloudclient.checkin``
     - Interact with EGI Check-in: fetch and renew OpenID Connect tokens.
   * - ``fedcloudclient.endpoint``
     - Discover service endpoints via GOCDB; obtain unscoped and scoped tokens from Keystone.
   * - ``fedcloudclient.sites``
     - Configure and query site metadata (regions, URLs, capabilities).
   * - ``fedcloudclient.openstack``
     - Execute OpenStack CLI commands (``nova``, ``glance``, ``neutron``) against specified sites.
   * - ``fedcloudclient.secret``
     - Retrieve and manage secrets from the EGI Vault service.
   * - ``fedcloudclient.auth``
     - Validate access tokens and credentials; utilities for checking token expiration and scopes.

Getting Started
---------------

A concise introductory walkthrough is available in this `presentation <https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing>`_.  

For detailed installation instructions, full usage examples, and API references, see the official documentation:

`https://fedcloudclient.fedcloud.eu/ <https://fedcloudclient.fedcloud.eu/>`_
