Using fedcloudclient as command-line client
===========================================

**fedcloudclient** has four groups of commands: **"fedcloud token"** for interactions with EGI Check-in and access tokens,
**"fedcloud endpoint"** for interactions with GOCDB (and site endpoints according to GOCDB), **"fedcloud site"** for
manipulations with site configurations, and **"fedcloud openstack"** or **"fedcloud openstack-int"** for performing
Openstack commands on sites.

Authentication
**************

Many **fedcloud** commands need access tokens for authentication. Users can choose whether to provide access tokens
directly (via option *"--checkin-access-token"*), or via oidc-agent (via option *"--oidc-agent-account"*), use refresh
tokens (must be provided together with Check-in client ID and secret) to generate access tokens on the fly. Therefore,
in most cases, the option *"--checkin-access-token"* can be replaced by the option *"--oidc-agent-account"*, or the
combination of *"--checkin-refresh-token"*, *"--checkin-client-id"* and *"--checkin-client-secret"*.

Users of EGI Check-in can get all information needed for obtaining refresh and access tokens from `CheckIn FedCloud
client <https://aai.egi.eu/fedcloud/>`_. For providing access token via *oidc-agent*, follow the instructions from
`oidc-agent <https://indigo-dc.gitbook.io/oidc-agent/user/oidc-gen/provider/egi/>`_ for registering a client, then
give the client name (account name in *oidc-agent*) to *fedcloudclient* via option *"--oidc-agent-account"*.

Refresh tokens have long lifetime (one year in EGI Check-in), so they must be properly protected. Exposing refresh
tokens via environment variables or command-line options is considered as insecure and will be disable in near
future in favor of using *oidc-agent*. If multiple methods of getting access tokens are given at the same time,
the client will try to get the tokens from the oidc-agent first, then from refresh tokens.

The default OIDC identity provider is EGI Check-in (https://aai.egi.eu/oidc). Users can set other OIDC identity
provider via option *"--checkin-url"*. Remember to set identity provider's name *"--checkin-provider"* accordingly
for Openstack commands.

The default protocol is *"openid"*. Users can change default protocol via option *"--checkin-protocol"*. However,
sites may have protocol fixedly defined in site configuration, e.g. *"oidc"* for INFN-CLOUD-BARI.

Environment variables
*********************

Most of fedcloud options, including options for tokens can be set via environment variables:

+-----------------------------+---------------------------------+----------------------------------+
|     Environment variables   |   Command-line options          |          Default value           |
+=============================+=================================+==================================+
|    CHECKIN_ACCESS_TOKEN     |   --checkin-access-token        |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    CHECKIN_REFRESH_TOKEN    |   --checkin-refresh-token       |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    CHECKIN_CLIENT_ID        |   --checkin-client-id           |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    CHECKIN_CLIENT_SECRET    |   --checkin-client-secret       |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    CHECKIN_URL              |   --checkin-url                 |    https://aai.egi.eu/oidc       |
+-----------------------------+---------------------------------+----------------------------------+
|    CHECKIN_PROTOCOL         |   --checkin-protocol            |             openid               |
+-----------------------------+---------------------------------+----------------------------------+
|    CHECKIN_PROVIDER         |   --checkin-provider            |             egi.eu               |
+-----------------------------+---------------------------------+----------------------------------+
|    CHECKIN_AUTH_TYPE        |   --checkin-auth-type           |         v3oidcaccesstoken        |
+-----------------------------+---------------------------------+----------------------------------+
|    EGI_SITE                 |   --site                        |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    EGI_VO                   |   --vo                          |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    OIDC_AGENT_ACCOUNT       |   --oidc-agent-account          |                                  |
+-----------------------------+---------------------------------+----------------------------------+

For convenience, always set the frequently used options like tokens via environment variables, that can save a lot of time.

fedcloud --help command
***********************

* **"fedcloud --help"** command will print help message. When using it in combination with other
  commands, e.g. **"fedcloud token --help"**, **"fedcloud token check --hep"**, it will print list of options for the
  corresponding commands

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


fedcloud token commands
***********************

* **"fedcloud token check --checkin-access-token <ACCESS_TOKEN>"**: Check the expiration time of access token, so users can know whether
  they need to refresh it. As mentioned before, access token may be given via environment variable *CHECKIN_ACCESS_TOKEN*,
  so the option *--checkin-access-token* is not shown in all examples bellows, even if the option is required.

::

    $ fedcloud token check
    Access token is valid to 2021-01-02 01:25:39 UTC
    Access token expires in 3571 seconds


* **"fedcloud token list-vos --checkin-access-token <ACCESS_TOKEN>"** : Print the list of VO memberships according to the EGI Check-in

::

    $ fedcloud token list-vos
    eosc-synergy.eu
    fedcloud.egi.eu
    training.egi.eu



fedcloud endpoint commands
**************************

**"fedcloud endpoint"** commands are complementary part of the **"fedcloud site"** commands. Instead of using site
configurations defined in files saved in GitHub repository or local disk, the commands try to get site information
directly from GOCDB (Grid Operations Configuration Management Database) https://goc.egi.eu/ or make probe test on sites

* **"fedcloud endpoint list"** : List of endpoints of sites defined in GOCDB.

::

    $ fedcloud endpoint list
    Site                type                URL
    ------------------  ------------------  ------------------------------------------------
    IFCA-LCG2           org.openstack.nova  https://api.cloud.ifca.es:5000/v3/
    IN2P3-IRES          org.openstack.nova  https://sbgcloud.in2p3.fr:5000/v3
    ...

* **"fedcloud endpoint projects --site <SITE> --checkin-access-token <ACCESS_TOKEN>"** : List of projects that the owner
  of the access token can have access on the given site

::

    $ fedcloud endpoint projects --site IFCA-LCG2
    id                                Name                        enabled    site
    --------------------------------  --------------------------  ---------  ---------
    2a7e2cd4b6dc4e609dd934964c1715c6  VO:demo.fedcloud.egi.eu     True       IFCA-LCG2
    3b9754ad8c6046b4aec43ec21abe7d8c  VO:eosc-synergy.eu          True       IFCA-LCG2
    ...

* **"fedcloud endpoint token --site <SITE> --project-id <PROJECT> --checkin-access-token <ACCESS_TOKEN>"** : Get
  Openstack keystone scoped token on the site for the project ID.

::

    $ fedcloud endpoint token --site IFCA-LCG2 --project-id 3b9754ad8c6046b4aec43ec21abe7d8c
    export OS_TOKEN="gAAAAA..."

* **"fedcloud endpoint env --site <SITE> --project-id <PROJECT> --checkin-access-token <ACCESS_TOKEN>"** : Print
  environment variables for working with the project ID on the site.

::

    $ fedcloud endpoint env --site IFCA-LCG2 --project-id 3b9754ad8c6046b4aec43ec21abe7d8c
    # environment for IFCA-LCG2
    export OS_AUTH_URL="https://api.cloud.ifca.es:5000/v3/"
    export OS_AUTH_TYPE="v3oidcaccesstoken"
    export OS_IDENTITY_PROVIDER="egi.eu"
    export OS_PROTOCOL="openid"
    export OS_ACCESS_TOKEN="..."


fedcloud site commands
**********************

**"fedcloud site"** commands will read site configurations and manipulate with them. If the local site configurations exist
at *~/.fedcloud-site-config/*, **fedcloud** will read them from there, otherwise the commands will read from `GitHub repository
<https://github.com/EGI-Foundation/fedcloud-catchall-operations/tree/master/sites>`_.

By default, **fedcloud** does not save anything on local disk, users have to save the site configuration to local disk
explicitly via **"fedcloud site save-config"** command. The advantage of having local
site configurations, beside faster loading, is to give users ability to make customizations, e.g. add additional VOs,
remove sites they do not have access, and so on.

* **"fedcloud site save-config"** : Read the default site configurations from GitHub
  and save them to *~/.fedcloud-site-config/* local directory. The command will overwrite existing site configurations
  in the local directory.

::

    $ fedcloud site save-config
    Saving site configs to directory /home/viet/.fedcloud-site-config

After saving site configurations, users can edit and customize them, e.g. remove unaccessible sites, add new
VOs and so on.

* **"fedcloud site list"** : List of existing sites in the site configurations

::

    $ fedcloud site list
    100IT
    BIFI
    CESGA
    ...

* **"fedcloud site show --site <SITE>"** : Show configuration of the corresponding site.

::

    $ fedcloud site show --site IISAS-FedCloud
    endpoint: https://cloud.ui.savba.sk:5000/v3/
    gocdb: IISAS-FedCloud
    vos:
    - auth:
        project_id: a22bbffb007745b2934bf308b0a4d186
      name: covid19.eosc-synergy.eu
    - auth:
        project_id: 51f736d36ce34b9ebdf196cfcabd24ee
      name: eosc-synergy.eu


* **"fedcloud site show-all"** : Show configurations of all sites.

|

* **"fedcloud site show-project-id --site <SITE> --vo <VO>"**: show the project ID of the VO on the site.

::

    $ fedcloud site show-project-id --site IISAS-FedCloud --vo eosc-synergy.eu
     Endpoint : https://cloud.ui.savba.sk:5000/v3/
     Project ID : 51f736d36ce34b9ebdf196cfcabd24ee


fedcloud openstack commands
***************************

* **"fedcloud openstack --site <SITE> --vo <VO> --checkin-access-token <ACCESS_TOKEN> <OPENSTACK_COMMAND>"** : Execute an
  Openstack command on the site and VO. Examples of Openstack commands are *"image list"*, *"server list"* and can be used
  with additional options for the commands, e.g. *"image list --long"*, *"server list --format json"*. The list of all
  Openstack commands, and their parameters/usages are available
  `here <https://docs.openstack.org/python-openstackclient/latest/cli/command-list.html>`_.

::

    $ fedcloud openstack image list --site IISAS-FedCloud --vo eosc-synergy.eu
    Site: IISAS-FedCloud, VO: eosc-synergy.eu
    +--------------------------------------+-------------------------------------------------+--------+
    | ID                                   | Name                                            | Status |
    +--------------------------------------+-------------------------------------------------+--------+
    | 862d4ede-6a11-4227-8388-c94141a5dace | Image for EGI CentOS 7 [CentOS/7/VirtualBox]    | active |
    ...

If the site is *ALL_SITES*, the Openstack command will be executed on all sites in EGI Federated Cloud.

* **"fedcloud openstack-int --site <SITE> --vo <VO> --checkin-access-token <ACCESS_TOKEN>"** : Call Openstack client without
  command, so users can work with Openstack site in interactive mode. This is useful when users need to perform multiple
  commands successively. For example, users may need get list of images, list of flavors, list of networks before
  creating a VM. OIDC authentication is done only once at the beginning, then the keystone token is cached and will
  be used for successive commands without authentication via CheckIn again.

::

    $ fedcloud openstack-int --site IISAS-FedCloud --vo eosc-synergy.eu
    (openstack) image list
    +--------------------------------------+-------------------------------------------------+--------+
    | ID                                   | Name                                            | Status |
    +--------------------------------------+-------------------------------------------------+--------+
    | 862d4ede-6a11-4227-8388-c94141a5dace | Image for EGI CentOS 7 [CentOS/7/VirtualBox]    | active |
    ...
    (openstack) flavor list
    +--------------------------------------+-----------+-------+------+-----------+-------+-----------+
    | ID                                   | Name      |   RAM | Disk | Ephemeral | VCPUs | Is Public |
    +--------------------------------------+-----------+-------+------+-----------+-------+-----------+
    | 5bd8397c-b97f-462d-9d2b-5b533844996c | m1.small  |  2048 |   10 |         0 |     1 | True      |
    | df25f80f-ed19-4e0b-805e-d34620ba0334 | m1.medium |  4096 |   40 |         0 |     2 | True      |
    ...
    (openstack)





