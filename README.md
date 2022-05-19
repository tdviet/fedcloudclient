# FedCloud client: Command-line client and library for EGI Federated Cloud

[![DOI](https://zenodo.org/badge/336671726.svg)](https://zenodo.org/badge/latestdoi/336671726)

TL;DR: Visit the [cheat sheet](https://fedcloudclient.fedcloud.eu/cheat.html#basic-usages) for real examples of
fedcloud commands.

The [FedCloud client](https://fedcloudclient.fedcloud.eu/) is a high-level Python package for a command-line client
designed for interaction with the OpenStack services in the EGI infrastructure. The client can access various EGI
services and can perform many tasks for users including managing access tokens, listing services, and mainly execute
commands on OpenStack sites in EGI infrastructure.

The most notable features of FedCloud client are following:

- have wide ranges of useful commands, including checking access token, searching for services, listing sites and VOs,
  and interaction with OpenStack sites.
- can perform any OpenStack command on any sites with only three parameters: the site, the VO and the command. For
  example, to list virtual machines (VM) images available to members of VO fedcloud.egi.eu on the site CYFRONET-CLOUD,
  run the following command:

  ```shell
  fedcloud openstack image list --vo fedcloud.egi.eu --site CYFRONET-CLOUD
  ```

- can perform an action/command on all OpenStack sites in EGI infrastructure by specifying `--site ALL_SITES`.
- can be used in [scripts for automation](https://fedcloudclient.fedcloud.eu/scripts.html) or called directly
  from [Python codes](https://fedcloudclient.fedcloud.eu/development.html).

Five modules are included: **fedcloudclient.checkin** for operation with EGI Check-in like getting tokens,
**fedcloudclient.endpoint** for searching endpoints via GOCDB, getting unscoped/scoped token from OpenStack keystone,
**fedcloudclient.sites** for managing site configurations, **fedcloudclient.openstack** for performing OpenStack
operations on sites, and finally **fedcloudclient.ec3** for deploying elastic computing clusters in Cloud.

A short tutorial of the fedcloudclient is available in this
[presentation](https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing).
The full documentation, including installation, usage and API description is available
at [https://fedcloudclient.fedcloud.eu/](https://fedcloudclient.fedcloud.eu/).

## Quick start

- Install FedCloud client via `pip`:

  ```shell
  pip3 install fedcloudclient
  ```

  or use Docker container:

  ```shell
  docker run -it  tdviet/fedcloudclient bash
  ```

- Get a new access token from EGI Check-in according to instructions from
   [EGI Check-in Token Portal](https://aai.egi.eu/token), or from
  [oidc-agent](https://indigo-dc.gitbook.io/oidc-agent/user/oidc-gen/provider/egi)
  and set environment variable.

  ```shell
  export OIDC_ACCESS_TOKEN=<ACCESS_TOKEN>
  ```

- Check the expiration time of the access token using `fedcloud` command:

  ```shell
  fedcloud token check
  ```

- List the VO memberships of the access token:

  ```shell
  fedcloud token list-vos
  ```

- List the OpenStack sites available in EGI Federated Cloud. That may take few seconds because all site configurations
  are retrieved from
  [GitHub repository](https://github.com/EGI-Foundation/fedcloud-catchall-operations/tree/master/sites)

  ```shell
  fedcloud site list
  ```

- Save the site configuration to local machine at
  `~/.config/fedcloud/site-config/` to speed up the client's start in the next time:

  ```shell
  fedcloud site save-config
  ```

- Execute an OpenStack command, e.g. list images in fedcloud.egi.eu VO on CYFRONET-CLOUD site (or other combination of
  site and VO you have access):

  ```shell
  fedcloud openstack image list --site CYFRONET-CLOUD --vo fedcloud.egi.eu
  ```

- Execute an OpenStack command on all sites, e.g. list VMs in eosc-synergy.eu VO on all OpenStack sites in EGI Federated
  Cloud

  ```shell
  fedcloud openstack server list --site ALL_SITES --vo eosc-synergy.eu
  ```

- Learn more commands of `fedcloud` client and experiment with them:

  ```shell
  fedcloud --help
  fedcloud site --help
  ```

- Read the
  [Quick start](https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing)
  for more information about customizations and advanced usages.

## Using fedcloudclient as development library

All functionalities offered by the _fedcloud_ client can be used as a library for development of other tools and
services for EGI Federated Cloud. For example, performing openstack command as a function in Python:

```python

from fedcloudclient.openstack import fedcloud_openstack

....
error_code, result = fedcloud_openstack(oidc_access_token,
                                        site,
                                        vo,
                                        openstack_command)
```

See a working example
[_"demo.py"_](https://github.com/tdviet/fedcloudclient/blob/master/examples/demo.py). The documentation of
fedcloudclient API is available at
[https://fedcloudclient.fedcloud.eu/](https://fedcloudclient.fedcloud.eu/).

## FAQ

1. The `fedcloud` client is slow.

   Execute command `fedcloud site save-config` to download site configurations from
   [GitHub repository](https://github.com/EGI-Foundation/fedcloud-catchall-operations/tree/master/sites)
   and save them on a local machine. That will significantly speed up site configurations loading.

   Some sites in the repository may not respond, and client has to wait for long time before report "Connection time
   out". You can remove the sites from your local repository to speed-up all-sites operations

   `libsodium` which is used by `oidc-agent` Python library may be frozen at initialization on VMs with low entropy. The
   problem is described
   [here](https://doc.libsodium.org/usage#sodium_init-stalling-on-linux). Check the entropy on the VMs by executing
   command
   `cat /proc/sys/kernel/random/entropy_avail`, and if the result is lower than 300, consider installing `haveged`
   or `rng-tools` to increase entropy. On VMs with CentOS, you also have to start the daemon manually after installation
   (or reboot the VMs)

1. The `fedcloud` client fails with error message
   `SSL exception connecting to <https://> ...` when attempts to interact with some sites.

   Some sites use certificates issued by national grid CAs that are not included in default distribution, so `fedcloud`
   client cannot verify them. Follow this
   [instruction](https://github.com/tdviet/python-requests-bundle-certs/blob/main/docs/Install_certificates.md)
   to install
   [EGI Core Trust Anchor](https://repository.egi.eu/sw/production/cas/)
   and add certificates to Python request certificate bundle.

   In the case of using virtual environment for quick test, you can download and import bundle certificates by using the
   script from
   [this repository](https://github.com/tdviet/python-requests-bundle-certs)

1. The `fedcloud` client fails with error message
   `"VO XX not found on site YY"`, but they do exist.

   Site configurations at
   [GitHub repository](https://github.com/EGI-Foundation/fedcloud-catchall-operations/tree/master/sites)
   may be incomplete. Check the site configurations stored in
   `~/.config/fedcloud/site-config/` if the VOs are included. If not, you can ask site admins to fix site configuration.
   You can also execute
   `fedcloud endpoint projects --site SITE --oidc-access-token ACCESS_TOKEN` to find project IDs of the VOs on the site
   and add the VOs to local site configuration on your machine manually.

1. I would like to add supports for additional sites/VOs/identity providers that are not parts of EGI Federated Cloud.

   Other identity providers may be specified via option `--oidc-url` or environment variable `CHECKIN_OIDC_URL`.
   Additional sites and VOs may be added to local site configuration files.

1. Why there are so many options for authentication: access token, refresh token, and oidc-agent? Which one should be
   used?

   Cloud operations need only access tokens, not refresh tokens. Access tokens have short lifetime (one hour in EGI
   Check-in), so they have lower security constraints. However, they have to be refreshed frequently, that may be
   inconvenient for some users.

   If a refresh token is given as parameter to `fedcloud` client (together with client ID and client secret), an access
   token will be generated on the fly from the refresh token and client ID/secret. However, using unencrypted refresh
   tokens is considered as insecure and will be removed in future versions in favor of oidc-agent.

   [oidc-agent](https://indigo-dc.gitbook.io/oidc-agent/) stores the refresh token securely and will automatically
   generate a new access token when the current one expires, so that is the recommended way to provide access token to
   fedcloudclient
