Usage
=====

**fedcloudclient** has four groups of commands: **"fedcloud token"** for interactions with EGI Check-in and access tokens,
**"fedcloud endpoint"** for interactions with GOCDB (and site endpoints according to GOCDB), **"fedcloud site"** for
manipulations with site configurations, and **"fedcloud openstack"** or **"fedcloud openstack-int"** for performing
OpenStack commands on sites.

Authentication
**************

Many **fedcloud** commands need access tokens for authentication. Users can choose whether to provide access tokens
directly (via option *"--oidc-access-token"*), or via oidc-agent (via option *"--oidc-agent-account"*), use refresh
tokens (must be provided together with Check-in client ID and secret) to generate access tokens on the fly. Therefore,
in most cases, the option *"--oidc-access-token"* can be replaced by the option *"--oidc-agent-account"*, or the
combination of *"--oidc-refresh-token"*, *"--oidc-client-id"* and *"--oidc-client-secret"*.

Users of EGI Check-in can get all information needed for obtaining refresh and access tokens from `EGI Check-in Token
Portal <https://aai.egi.eu/token>`_. For providing access token via *oidc-agent*, follow the instructions from
`oidc-agent <https://indigo-dc.gitbook.io/oidc-agent/user/oidc-gen/provider/egi/>`_ for registering a client, then
give the client name (account name in *oidc-agent*) to *fedcloudclient* via option *"--oidc-agent-account"*.

Refresh tokens have long lifetime (one year in EGI Check-in), so they must be properly protected. Exposing refresh
tokens via environment variables or command-line options is considered as insecure and will be disable in near
future in favor of using *oidc-agent*. If multiple methods of getting access tokens are given at the same time,
the client will try to get the tokens from the oidc-agent first, then from refresh tokens.

The default OIDC identity provider is EGI Check-in (https://aai.egi.eu/oidc). Users can set other OIDC identity
provider via option *"--oidc-url"*. Remember to set identity provider's name *"--openstack-auth-provider"* accordingly
for OpenStack commands.

The default protocol is *"openid"*. Users can change default protocol via option *"--openstack-auth-protocol"*. However,
sites may have protocol fixedly defined in site configuration, e.g. *"oidc"* for INFN-CLOUD-BARI.

Environment variables
*********************

Most of fedcloud options, including options for tokens can be set via environment variables:

+-----------------------------+---------------------------------+----------------------------------+
|     Environment variables   |   Command-line options          |          Default value           |
+=============================+=================================+==================================+
|    OIDC_AGENT_ACCOUNT       |   --oidc-agent-account          |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    OIDC_ACCESS_TOKEN        |   --oidc-access-token           |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    OIDC_REFRESH_TOKEN       |   --oidc-refresh-token          |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    OIDC_CLIENT_ID           |   --oidc-client-id              |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    OIDC_CLIENT_SECRET       |   --oidc-client-secret          |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    OIDC_URL                 |   --oidc-url                    |    https://aai.egi.eu/oidc       |
+-----------------------------+---------------------------------+----------------------------------+
|    OPENSTACK_AUTH_PROTOCOL  |   --openstack-auth-protocol     |             openid               |
+-----------------------------+---------------------------------+----------------------------------+
|    OPENSTACK_AUTH_PROVIDER  |   --openstack-auth-provider     |             egi.eu               |
+-----------------------------+---------------------------------+----------------------------------+
|    OPENSTACK_AUTH_TYPE      |   --openstack-auth-type         |         v3oidcaccesstoken        |
+-----------------------------+---------------------------------+----------------------------------+
|    EGI_SITE                 |   --site                        |                                  |
+-----------------------------+---------------------------------+----------------------------------+
|    EGI_VO                   |   --vo                          |                                  |
+-----------------------------+---------------------------------+----------------------------------+

For convenience, always set the frequently used options like tokens via environment variables, that can save a lot of
time.

Shell completion
****************

Shell completion for *fedcloud* command in *bash* can be activated by executing the following command:

::

    $ eval "$(_FEDCLOUD_COMPLETE=bash_source fedcloud)"

The command above may affect responsiveness of the shell. For long work, it is recommended to copy the
`fedcloud_bash_completion.sh script
<https://github.com/tdviet/fedcloudclient/blob/master/examples/fedcloud_bash_completion.sh>`_ to a local file, and
source it from ~/.bashrc. Refer `Click documentation
<https://click.palletsprojects.com/en/8.0.x/shell-completion/#enabling-completion>`_ for a long explanation.

After enabling shell completion, press <TAB> twice for shell completion:

::

    $ fedcloud site <TAB><TAB>
    env              list             save-config      show             show-project-id


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
      openstack      Executing OpenStack commands on site and VO
      openstack-int  Interactive OpenStack client on site and VO
      site           Site command group for manipulation with site configurations
      token          Token command group for manipulation with tokens


fedcloud token commands
***********************

* **"fedcloud token check --oidc-access-token <ACCESS_TOKEN>"**: Check the expiration time of access token, so users can know whether
  they need to refresh it. As mentioned before, access token may be given via environment variable *OIDC_ACCESS_TOKEN*,
  so the option *--oidc-access-token* is not shown in all examples bellows, even if the option is required.

::

    $ fedcloud token check
    Access token is valid to 2021-01-02 01:25:39 UTC
    Access token expires in 3571 seconds


* **"fedcloud token list-vos --oidc-access-token <ACCESS_TOKEN>"** : Print the list of VO memberships according to EGI Check-in

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


* **"fedcloud endpoint projects --site <SITE> --oidc-access-token <ACCESS_TOKEN>"** : List of projects to which the owner
  of the access token has access at the given site

::

    $ fedcloud endpoint projects --site IFCA-LCG2
    id                                Name                        enabled    site
    --------------------------------  --------------------------  ---------  ---------
    2a7e2cd4b6dc4e609dd934964c1715c6  VO:demo.fedcloud.egi.eu     True       IFCA-LCG2
    3b9754ad8c6046b4aec43ec21abe7d8c  VO:eosc-synergy.eu          True       IFCA-LCG2
    ...

If the site is set to *ALL_SITES*, or the argument *-a* is used, the command will show accessible projects from all sites of the EGI Federated Cloud.


* **"fedcloud endpoint vos --site <SITE> --oidc-access-token <ACCESS_TOKEN>"** : List of Virtual Organisations (VOs)
   to which the owner of the access token has access at the given site

::

    $ fedcloud endpoint vos --site IFCA-LCG2
    VO                id                                Project name         enabled    site
    ----------------  --------------------------------  -------------------  ---------  ---------
    vo.access.egi.eu  233f045cb1ff46842a15ebb33af69460  VO:vo.access.egi.eu  True       IFCA-LCG2
    training.egi.eu   d340308880134d04294097524eace710  VO:training.egi.eu   True       IFCA-LCG2
    ...

If the site is set to *ALL_SITES*, or the argument *-a* is used, the command will show accessible VOs from all sites of the EGI Federated Cloud.

::

    $ fedcloud endpoint vos -a
    VO                   id                                Project name         enabled    site
    -------------------  --------------------------------  -------------------  ---------  -----------------
    vo.access.egi.eu     233f045cb1ff46842a15ebb33af69460  VO:vo.access.egi.eu  True       IFCA-LCG2
    training.egi.eu      d340308880134d04294097524eace710  VO:training.egi.eu   True       IFCA-LCG2
    vo.access.egi.eu     7101022b9ae74ed9ac1a574497279499  EGI_access           True       IN2P3-IRES
    vo.access.egi.eu     5bbdb5c1e0b2bcbac29904f4ac22dcaa  vo_access_egi_eu     True       UNIV-LILLE
    vo.access.egi.eu     4cab325ca8c2495bf2d4e8f230bcd51a  VO:vo.access.egi.eu  True       INFN-PADOVA-STACK
    ...


* **"fedcloud endpoint token --site <SITE> --project-id <PROJECT> --oidc-access-token <ACCESS_TOKEN>"** : Get
  OpenStack keystone scoped token on the site for the project ID.

::

    $ fedcloud endpoint token --site IFCA-LCG2 --project-id 3b9754ad8c6046b4aec43ec21abe7d8c
    export OS_TOKEN="gAAAAA..."


* **"fedcloud endpoint env --site <SITE> --project-id <PROJECT> --oidc-access-token <ACCESS_TOKEN>"** : Print
  environment variables for working with the project ID on the site.

::

    $ fedcloud endpoint env --site IFCA-LCG2 --project-id 3b9754ad8c6046b4aec43ec21abe7d8c
    # environment for IFCA-LCG2
    export OS_AUTH_URL="https://api.cloud.ifca.es:5000/v3/"
    export OS_AUTH_TYPE="v3oidcaccesstoken"
    export OS_IDENTITY_PROVIDER="egi.eu"
    export OS_PROTOCOL="openid"
    export OS_ACCESS_TOKEN="..."


fedcloud ec3 commands
**************************

**"fedcloud ec3"** commands are helper commands for deploying EC3 (Elastic Cloud Compute Cluster) in Cloud
via Infrastructure Manager. The commands will create necessary template and authorization files for EC3 client.

* **"fedcloud ec3 init --site <SITE> --vo <VO> --oidc-access-token <ACCESS_TOKEN> --auth-file auth.dat --template-dir
  ./templates"** : Generate authorization file (by default *auth.dat*) and template file (by default
  *./templates/refresh.radl*) for EC3 client.

::

    $ fedcloud ec3 init --site CESGA --vo vo.access.egi.eu


* **"fedcloud ec3 refresh --site <SITE> --vo <VO> --oidc-access-token <ACCESS_TOKEN> --auth-file auth.dat"** :
  Refresh the access token stored in authorization file (by default *auth.dat*).

::

    $ fedcloud ec3 init --site CESGA --vo vo.access.egi.eu



fedcloud site commands
**********************

**"fedcloud site"** commands will read site configurations and manipulate with them. If the local site configurations
exist at *~/.config/fedcloud/site-config/*, **fedcloud** will read them from there, otherwise the commands will read
from `GitHub repository <https://github.com/EGI-Foundation/fedcloud-catchall-operations/tree/master/sites>`_.

By default, **fedcloud** does not save anything on local disk, users have to save the site configuration to local disk
explicitly via **"fedcloud site save-config"** command. The advantage of having local
site configurations, beside faster loading, is to give users ability to make customizations, e.g. add additional VOs,
remove sites they do not have access, and so on.

* **"fedcloud site save-config"** : Read the default site configurations from GitHub
  and save them to *~/.config/fedcloud/site-config/* local directory. The command will overwrite existing site configurations
  in the local directory.

::

    $ fedcloud site save-config
    Saving site configs to directory /home/viet/.config/fedcloud/site-config/


After saving site configurations, users can edit and customize them, e.g. remove inaccessible sites, add new
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


* **"fedcloud site show-project-id --site <SITE> --vo <VO>"**: show the project ID of the VO on the site.

::

    $ fedcloud site show-project-id --site IISAS-FedCloud --vo eosc-synergy.eu
    export OS_AUTH_URL="https://cloud.ui.savba.sk:5000/v3/"
    export OS_PROJECT_ID="51f736d36ce34b9ebdf196cfcabd24ee"


* **"fedcloud site env --site <SITE> --vo <VO>"**: set OpenStack environment variable for the VO on the site.

::

    $ fedcloud site env --site IISAS-FedCloud --vo eosc-synergy.eu
    export OS_AUTH_URL="https://cloud.ui.savba.sk:5000/v3/"
    export OS_AUTH_TYPE="v3oidcaccesstoken"
    export OS_IDENTITY_PROVIDER="egi.eu"
    export OS_PROTOCOL="openid"
    export OS_PROJECT_ID="51f736d36ce34b9ebdf196cfcabd24ee"
    # Remember to set OS_ACCESS_TOKEN, e.g. :
    # export OS_ACCESS_TOKEN=`oidc-token egi`


The main differences between *"fedcloud endpoint env"* and *"fedcloud site env"* commands are that the second command
needs VO name as input parameter instead of project ID. The command may set also environment variable OS_ACCESS_TOKEN,
if access token is provided, otherwise it will print notification.


fedcloud select commands
***************************

* **"fedcloud select flavor --site <SITE> --vo <VO> --oidc-access-token <ACCESS_TOKEN> --flavor-specs <flavor-specs>"** :
  Select flavor according to the specification in *flavor-specs*. The specifications may be repeated,
  e.g. *--flavor-specs "VCPUs==2" --flavor-specs "RAM>=2048"*, or may be joined, e.g.
  *--flavor-specs "VCPUs==2 & Disk>10"*. For frequently used specs, short-option alternatives are available, e.g.
  *--vcpus 2* is equivalent to *--flavor-specs "VCPUs==2"*. The output is sorted, flavors using less resources
  (in the order: GPUs, CPUs, RAM, Disk) are placed on the first places. Users can choose to print only the best-matched
  flavor with *--output-format first* (suitable for scripting) or the full list of all matched flavors in list/YAML/JSON
  format.

::

    $ fedcloud select flavor --site IISAS-FedCloud --vo vo.access.egi.eu --flavor-specs "RAM>=2096" --flavor-specs "Disk > 10" --output-format list
    m1.medium
    m1.large
    m1.xlarge
    m1.huge
    g1.c08r30-K20m
    g1.c16r60-2xK20m


* **"fedcloud select image --site <SITE> --vo <VO> --oidc-access-token <ACCESS_TOKEN> --image-specs <image-specs>"** :
  Select image according to the specification in *image-specs*. The specifications may be repeated,
  e.g. *--image-specs "Name=~Ubuntu" --image-specs "Name=~'20.04'"*. The output is sorted, newest images
  are placed on the first places. Users can choose to print only the best-matched
  image with *--output-format first* (suitable for scripting) or the full list of all matched images in list/YAML/JSON
  format.

::

    $ fedcloud select image --site INFN-CATANIA-STACK --vo training.egi.eu --image-specs "Name =~ Ubuntu" --output-format list
    TRAINING.EGI.EU Image for EGI Docker [Ubuntu/18.04/VirtualBox]
    TRAINING.EGI.EU Image for EGI Ubuntu 20.04 [Ubuntu/20.04/VirtualBox]


* **"fedcloud select network --site <SITE> --vo <VO> --oidc-access-token <ACCESS_TOKEN> --network-specs <flavor-specs>"** :
  Select network according to the specification in *network-specs*. User can choose to select only public or private
  network, or both (default). The output is sorted in the order: public, shared,
  private. Users can choose to print only the best-matched network with *--output-format first*
  (suitable for scripting) or the full list of all matched networks in list/YAML/JSON format.

::

    $ fedcloud select network --site IISAS-FedCloud --vo training.egi.eu --network-specs default --output-format list
    public-network
    private-network


fedcloud openstack commands
***************************

* **"fedcloud openstack --site <SITE> --vo <VO> --oidc-access-token <ACCESS_TOKEN> <OPENSTACK_COMMAND>"** : Execute an
  OpenStack command on the site and VO. Examples of OpenStack commands are *"image list"*, *"server list"* and can be used
  with additional options for the commands, e.g. *"image list --long"*, *"server list --format json"*. The list of all
  OpenStack commands, and their parameters/usages are available
  `here <https://docs.openstack.org/python-openstackclient/latest/cli/command-list.html>`_.

::

    $ fedcloud openstack image list --site IISAS-FedCloud --vo eosc-synergy.eu
    Site: IISAS-FedCloud, VO: eosc-synergy.eu
    +--------------------------------------+-------------------------------------------------+--------+
    | ID                                   | Name                                            | Status |
    +--------------------------------------+-------------------------------------------------+--------+
    | 862d4ede-6a11-4227-8388-c94141a5dace | Image for EGI CentOS 7 [CentOS/7/VirtualBox]    | active |
    ...


If the site is *ALL_SITES*, the OpenStack command will be executed on all sites in EGI Federated Cloud.

* **"fedcloud openstack-int --site <SITE> --vo <VO> --oidc-access-token <ACCESS_TOKEN>"** : Call OpenStack client without
  command, so users can work with OpenStack site in interactive mode. This is useful when users need to perform multiple
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


