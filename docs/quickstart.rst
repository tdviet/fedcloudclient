Quick start
===========

The `Quick start <https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing>`_
presentation is designed for new users of **fedcloudclient**. It starts with the quick setup and basic usages,
then step by step to more advanced scenarios.

Setup
*****

* Install fedcloudclient via pip:

::

    $ pip3 install fedcloudclient

or use Docker container:

::

    $ docker run -it  tdviet/fedcloudclient bash


* Get a new access token from EGI Check-in according to instructions from `FedCloud Check-in
  client <https://aai.egi.eu/fedcloud/>`_ and set environment variable.

::

    $ export CHECKIN_ACCESS_TOKEN=<ACCESS_TOKEN>

Basic usages
************

* List your VO memberships according to the access token:

::

    $ fedcloud token list-vos
    eosc-synergy.eu
    fedcloud.egi.eu
    training.egi.eu
    ...

* List sites in EGI Federated Cloud

::

    $ fedcloud site list
    100IT
    BIFI
    CESGA
    ...

* Execute an Openstack command, e.g. list images in eosc-synergy.eu VO on IISAS-FedCloud site
  (or other combination of site and VO you have access):

::

    $ fedcloud openstack image list --site IISAS-FedCloud --vo eosc-synergy.eu
    Site: IISAS-FedCloud, VO: eosc-synergy.eu
    +--------------------------------------+-------------------------------------------------+--------+
    | ID                                   | Name                                            | Status |
    +--------------------------------------+-------------------------------------------------+--------+
    | 862d4ede-6a11-4227-8388-c94141a5dace | Image for EGI CentOS 7 [CentOS/7/VirtualBox]    | active |
    ...

* Get helps from the client

::

    $ fedcloud --help
    Usage: fedcloud [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      endpoint       Endpoint command group for interaction with GOCDB and endpoints
      openstack      Executing Openstack commands on site and VO
      openstack-int  Interactive Openstack client on site and VO
      site           Site command group for manipulation with site configurations
      token          Token command group for manipulation with tokens

* Read the `Quick start <https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing>`_
  presentation or next sections for more information.