FedCloud client: Command-line client and library for EGI Federated Cloud
========================================================================

**fedcloudclient** is a command-line client and high-level Python package for interaction with EGI Federated Cloud.
This package is an extension of the [egicli](https://github.com/EGI-Foundation/egicli) for Openstack commands.

The aim here was to create a simple client which would allow users to perform the various Openstack operations 
in EGI Federated Cloud. Four modules are included: **fedcloudclient.checkin** for operation with EGI Check-in like
getting tokens, **fedcloudclient.endpoint** for searching endpoints via GOCDB, getting unscoped/scoped token from
Keystone, **fedcloudclient.sites** manages site configuration and finally **fedcloudclient.openstack** for
performing Openstack operations.

A short presentation of the fedcloudclient is available at 
[Quick start](https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing). 

The full documentation, including installation, usage and API description is available 
at [readthedocs.io](https://fedcloudclient.readthedocs.io/).

Quick start
-----------

-   Install FedCloud client via *pip*:

<!-- -->

    $ pip3 install fedcloudclient

or use Docker container:

<!-- -->

    $ docker run -it  tdviet/fedcloudclient bash

-   Get a new access token from EGI Check-in according to instructions from
    FedCloud [Check-in client](https://aai.egi.eu/fedcloud/) and set
    environment variable.

<!-- -->

    $ export CHECKIN_ACCESS_TOKEN=<ACCESS_TOKEN>

-   Check the expiration time of the access token using *fedcloud*
    command:

<!-- -->

    $ fedcloud token check

-   List the VO memberships of the access token:

<!-- -->

    $ fedcloud token list-vos

-   List the Openstack sites available in EGI Federated Cloud. That may
    take few seconds because all site configurations are retrieved from
    [GitHub repository](https://github.com/EGI-Foundation/fedcloud-catchall-operations/tree/master/sites)

<!-- -->

    $ fedcloud site list

-   Save the site configuration to local machine at
    *\~/.fedcloud-site-config/* to speed up the client's start in the
    next time:

<!-- -->

    $ fedcloud site save-config

-   Execute an Openstack command, e.g. list images in fedcloud.egi.eu VO on CYFRONET-CLOUD site (or other
    combination of site and VO you have access):

<!-- -->

    $ fedcloud openstack image list --site CYFRONET-CLOUD --vo fedcloud.egi.eu

-   Execute an Openstack command on all sites, e.g. list VMs in eosc-synergy.eu VO on all Openstack sites in
    EGI Federated Cloud

<!-- -->

    $ fedcloud openstack server list --site ALL_SITES --vo eosc-synergy.eu

-   Learn more commands of *fedcloud* client and experiment with them:

<!-- -->

    $ fedcloud --help

    $ fedcloud site --help

-   Read the [Quick start](https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing)
    for more information about customizations and advanced usages.

Using fedcloudclient as development library
-------------------------------------------

All functionalities offered by the *fedcloud* client can be used as a
library for development of other tools and services for EGI Federated
Cloud. For example, performing openstack command as a function in
Python:

<!-- -->

    from fedcloudclient.openstack import fedcloud_openstack
    ....
    error_code, result = fedcloud_openstack(checkin_access_token,
                                                 site,
                                                 vo,
                                                 openstack_command)

See a working example [*"demo.py"*](https://github.com/tdviet/fedcloudclient/blob/master/examples/demo.py). 
The documentation of fedcloudclient API is available at [readthedocs.io](https://fedcloudclient.readthedocs.io/).

FAQ
---

1.  The *fedcloud* client is slow.

> Execute command *"fedcloud site save-config"* to download site
> configurations from
> [GitHub repository](https://github.com/EGI-Foundation/fedcloud-catchall-operations/tree/master/sites)
> and save them on a local machine. That will significantly speedup site
> configurations loading.
> 
> Some sites in the repository may not respond, and client has to wait for long time before report 
> "Connection time out". You can remove the sites from your local repository to speed-up all-sites operations

2.  The *fedcloud* client fails with error message *"SSL exception
    connecting to <https://> ..."* when attempts to interact with some
    sites.

> Some sites use certificates issued by national grid CAs that are not
> included in default distribution, so *fedcloud* client cannot verify
> them. Follow this [instruction](https://github.com/tdviet/python-requests-bundle-certs/blob/main/docs/Install_certificates.md)
> to install [EGI Core Trust Anchor](http://repository.egi.eu/category/production/cas/) and add
> certificates to Python request certificate bundle.
> 
> In the case of using virtual environment for quick test, you can download 
> and import bundle certificates by using
> the script from [this repository](https://github.com/tdviet/python-requests-bundle-certs)

3.  The *fedcloud* client fails with error message *"VO XX not found on site YY"*, but they do exist.

> Site configurations at
> [GitHub repository](https://github.com/EGI-Foundation/fedcloud-catchall-operations/tree/master/sites)
> may be incomplete. Check the site configurations stored in
> *\~/.fedcloud-site-config/* if the VOs are included. If not, you can
> ask site admins to fix site configuration. You can also execute
> *"fedcloud endpoint projects --site SITE --checkin-access-token
> ACCESS\_TOKEN"* to find project IDs of the VOs on the site and add the VOs to
> local site configuration on your machine manually.

4.  I would like to add supports for additional sites/VOs/identity
    providers that are not parts of EGI Federated Cloud.

> Other identity providers may be specified via option *"--checkin-url"*
> or environment variable *"CHECKIN\_OIDC\_URL"*. Additional sites and
> VOs may be added to local site configuration files.

5.  Why there are options for both access token and refresh token? Which
    one should be used?

> Cloud operations need only access tokens, not refresh tokens. If a
> refresh token is given as parameter to *fedcloud* client (together
> with client ID and client secret), an access token will be generated
> on the fly from the refresh token and client ID/secret.
>
> Refresh tokens have long lifetime (one year in EGI Check-in), so they
> should be securely protected. In secured environment, e.g. private
> computers, refresh tokens may be conveniently specified via environment
> variables *CHECKIN\_REFRESH\_TOKEN*, *CHECKIN\_CLIENT\_ID*,
> *CHECKIN\_CLIENT\_SECRET*; so users don't have to set token for
> *fedcloud* client via command-line parameters.
>
> Access tokens have short lifetime (one hour in EGI Check-in), so they
> have lower security constraints. However, they have to be refreshed
> frequently, that may be inconvenient for some users. In shared
> environment, e.g. VMs in Cloud, access tokens should be used instead
> of refreshed tokens. If refresh token must be used, consider to use
> [oidc-agent](https://indigo-dc.gitbook.io/oidc-agent/) for storing the token. 
