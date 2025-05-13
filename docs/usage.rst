Usage
=====

**FedCloud client** has the following main groups of commands:

* **"fedcloud config"** for handling fedcloudclient configuration,

* **"fedcloud token"** for interactions with EGI Check-in and access tokens,

* **"fedcloud endpoint"** for interactions with GOCDB (and site endpoints according to GOCDB),

* **"fedcloud site"** for manipulations with site configurations,

* **"fedcloud openstack"** or **"fedcloud openstack-int"** for performing OpenStack commands on sites,

* **"fedcloud secret"** for accessing secrets in
  `Secret management service <https://vault.docs.fedcloud.eu/index.html>`_,

* **"fedcloud ec3"** as helper commands for deploying EC3.


Authentication
**************

Many **fedcloud** commands need access tokens for authentication. Users can choose whether to provide access tokens
directly (via option *"--oidc-access-token"*), via `oidc-agent <https://indigo-dc.gitbooks.io/oidc-agent/>`_
(via option *"--oidc-agent-account"*), or via `mytoken <https://mytoken.data.kit.edu/>`_ (via option *"--mytoken"*).

Users of EGI Check-in can get all information needed for obtaining access tokens from `EGI Check-in Token
Portal <https://aai.egi.eu/token>`_. For providing access token via *oidc-agent*, follow the instructions from
`oidc-agent <https://indigo-dc.gitbook.io/oidc-agent/user/oidc-gen/provider/egi/>`_ for registering a client, then
give the client name (account name in *oidc-agent*) to *FedCloud client* via option *"--oidc-agent-account"*.
On the other hand visit the `mytoken <https://mytoken.data.kit.edu/>`_ website to configure a *mytoken*,
remember to check *"Allows obtaining OpenID Connect Access Tokens"*, and use the option *"--mytoken"*
to pass it to *FedCloud client"*. Environment variables can be use instead of the command-line options,
as explained in the table below.

The default protocol is *"openid"*. Users can change default protocol via option *"--os-protocol"*. However,
sites may have protocol fixedly defined in site configuration, e.g. *"oidc"* for INFN-CLOUD-BARI.


Configuration
*************

Display the current configuration of *fedcloud* with:

::

    $ fedcloud config show

This will show a list of configuration parameters:

+----------------------------+------------------------------------------------------------------------------------+
|  Parameter                 |  Default value                                                                     |
+============================+====================================================================================+
|  site                      |  IISAS-FedCloud                                                                    |
+----------------------------+------------------------------------------------------------------------------------+
|  vo                        |  vo.access.egi.eu                                                                  |
+----------------------------+------------------------------------------------------------------------------------+
|  site_list_url             |  https://raw.githubusercontent.com/tdviet/fedcloudclient/master/config/sites.yaml  |
+----------------------------+------------------------------------------------------------------------------------+
|  site_dir                  |  ${HOME}/.config/fedcloud/site-config                                              |
+----------------------------+------------------------------------------------------------------------------------+
|  oidc_url                  |  https://aai.egi.eu/auth/realms/egi                                                |
+----------------------------+------------------------------------------------------------------------------------+
|  gocdb_public_url          |  https://goc.egi.eu/gocdbpi/public/                                                |
+----------------------------+------------------------------------------------------------------------------------+
|  gocdb_service_group       |  org.openstack.nova                                                                |
+----------------------------+------------------------------------------------------------------------------------+
|  vault_endpoint            |  https://vault.services.fedcloud.eu:8200                                           |
+----------------------------+------------------------------------------------------------------------------------+
|  vault_role                |                                                                                    |
+----------------------------+------------------------------------------------------------------------------------+
|  vault_mount_point         |  /secrets/                                                                         |
+----------------------------+------------------------------------------------------------------------------------+
|  vault_locker_mount_point  |  /v1/cubbyhole/                                                                    |
+----------------------------+------------------------------------------------------------------------------------+
|  vault_salt                |  fedcloud_salt                                                                     |
+----------------------------+------------------------------------------------------------------------------------+
|  log_file                  |  ${HOME}/.config/fedcloud/logs/fedcloud.log                                        |
+----------------------------+------------------------------------------------------------------------------------+
|  log_level                 |  DEBUG                                                                             |
+----------------------------+------------------------------------------------------------------------------------+
|  log_config_file           |  ${HOME}/.config/fedcloud/logging.conf                                             |
+----------------------------+------------------------------------------------------------------------------------+
|  requests_cert_file        |  ${HOME}/.config/fedcloud/cert/certs.pem                                           |
+----------------------------+------------------------------------------------------------------------------------+
|  oidc_agent_account        |  egi                                                                               |
+----------------------------+------------------------------------------------------------------------------------+
|  min_access_token_time     |  30                                                                                |
+----------------------------+------------------------------------------------------------------------------------+
|  mytoken_server            |  https://mytoken.data.kit.edu                                                      |
+----------------------------+------------------------------------------------------------------------------------+
|  os_protocol               |  openid                                                                            |
+----------------------------+------------------------------------------------------------------------------------+
|  os_auth_type              |  v3oidcaccesstoken                                                                 |
+----------------------------+------------------------------------------------------------------------------------+
|  os_identity_provider      |  egi.eu                                                                            |
+----------------------------+------------------------------------------------------------------------------------+

::

    $ fedcloud config show --source env_config
    parameter    value
    -----------  ----------------------------------
    tessss
    mytoken      eyJhbG

This will show configurations according to their source as: "DEFAULT_SETTINGS", "env_config", "saved_config"

The *fedcloud* configuration can be saved to a file with:

::

    $ fedcloud config create

By default the configuration file is saved to **${HOME}/.config/fedcloud/config.yaml**
but this can be changed:

::

    $ fedcloud config create --config-file /path/to/file.yaml

It is also possible to use the *FEDCLOUD_CONFIG_FILE* environment variable instead
of the *--config-file* option in the command line. This way users may save and load
multiple configuration files, one per project, with its own configuraion.

*fedcloud* parameters can be configured using:

#. comand-line options (highest priority); e.g.: *--site*

#. environment variables starting with the prefix *FEDCLOUD_*;
   e.g.: *FEDCLOUD_SITE*.

#. configuration file; e.g. *site* in *config.yaml*

#. default configuration (lowest priority), `harcoded <../fedcloudclient/conf.py#L16>`_.

The order is important: the default configuration is overwritten by the
configuration file, and this is overwritten by values stored in environment
variables, and this is overwritten by values in the command-line. For example,
the default configuration comes with *site = IISAS-FedCloud* and
*vo = vo.access.egi.eu*. This can be changed with:

::

    $ fedcloud openstack --vo training.egi.eu --site IFCA-LCG2 server list

or

::

    $ export FEDCLOUD_VO=training.egi.eu
    $ export FEDCLOUD_SITE=IFCA-LCG2
    $ fedcloud openstack server list

Note the nomenclature referring to the same parameter:

* *--oidc-agent-account* in the command-line

* *FEDCLOUD_OIDC_AGENT_ACCOUNT* as environment variable

* *oidc_agent_account* in the configuration file

They all refer to the same. All configuration parameters follow this
consistent approach.

Additional parameters can also be configured:

+------------------------------+-----------------------+
|  Environment variable        |  Command-line option  |
+==============================+=======================+
|  FEDCLOUD_OIDC_ACCESS_TOKEN  |  --oidc-access-token  |
+------------------------------+-----------------------+
|  FEDCLOUD_MYTOKEN            |  --mytoken            |
+------------------------------+-----------------------+
|  FEDCLOUD_LOCKER_TOKEN       |  --locker-token       |
+------------------------------+-----------------------+

For convenience, always set transient parameters like tokens via
environment variables, as it simplifies the call to *fedcloud*.


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
      config         Managing fedcloud configurations
      endpoint       Obtain endpoint details and scoped tokens
      openstack      Execute OpenStack commands on site and VO
      openstack-int  Interactive OpenStack client on site and VO
      secret         Commands for accessing secret objects
      select         Select resources according to specification
      site           Obtain site configurations
      token          Get details of access token


fedcloud token commands
***********************

* **"fedcloud token check"**: Check the expiration time of configured access token, so users can know whether
  they need to refresh it. As mentioned before, access token may be given via environment variable *FEDCLOUD_OIDC_ACCESS_TOKEN*,
  so the option *--oidc-access-token* is not shown in all examples bellows, even if the option is required.

::

    $ fedcloud token check
    Access token is valid to 2021-01-02 01:25:39 UTC
    Access token expires in 3571 seconds


* **"fedcloud token list-vos"** : Print the list of VO memberships according to EGI Check-in

::

    $ fedcloud token list-vos
    eosc-synergy.eu
    fedcloud.egi.eu
    training.egi.eu

* **"fedcloud token issue"** : Print the access_token

**Optional** possibilities are in access via:
* **OIDC agent:** --oidc-agent-account, for istance check token validity: **"fedcloud token check --oidc-agent-account <NAME_OF_USER_FOR_OIDC_AGENT>"**
* **access token:** --oidc-access-token: get "access token" from default access token stored as environment variable **FEDCLOUD_OIDC_ACCESS_TOKEN** or call with directly with access token **"fedcloud token check --oidc-access-token <ACCESS_TOKEN>"** or 
* **Mytoken:** --mytoken,  for istance check token validity: **"fedcloud token check --mytoken <TOKEN_FOR_MYTOKEN>"**, possible get from Mytoken: https://mytoken.data.kit.edu/
* **Mytoken server:** --mytoken-server

--oidc-access-token <ACCESS_TOKEN> 

::

    $ fedcloud token issue
    ABCD______

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
    export FEDCLOUD_OS_TOKEN="gAAAAA..."


* **"fedcloud endpoint env --site <SITE> --project-id <PROJECT> --oidc-access-token <ACCESS_TOKEN>"** : Print
  environment variables for working with the project ID on the site.

::

    $ fedcloud endpoint env --site IFCA-LCG2 --project-id 3b9754ad8c6046b4aec43ec21abe7d8c
    # environment for IFCA-LCG2
    export FEDCLOUD_OS_AUTH_URL="https://api.cloud.ifca.es:5000/v3/"
    export FEDCLOUD_OS_AUTH_TYPE="v3oidcaccesstoken"
    export FEDCLOUD_OS_IDENTITY_PROVIDER="egi.eu"
    export FEDCLOUD_OS_PROTOCOL="openid"
    export FEDCLOUD_OS_ACCESS_TOKEN="..."


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


* **"fedcloud site list --vo <VO-name>"** : List all sites supporting a Virtual Organization

::

    $ fedcloud site vo-list --vo vo.access.egi.eu
    BIFI
    CENI
    CESGA-CLOUD
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
    export FEDCLOUD_OS_AUTH_URL="https://cloud.ui.savba.sk:5000/v3/"
    export FEDCLOUD_OS_PROJECT_ID="51f736d36ce34b9ebdf196cfcabd24ee"


* **"fedcloud site env --site <SITE> --vo <VO>"**: set OpenStack environment variable for the VO on the site.

::

    $ fedcloud site env --site IISAS-FedCloud --vo eosc-synergy.eu
    export FEDCLOUD_OS_AUTH_URL="https://cloud.ui.savba.sk:5000/v3/"
    export FEDCLOUD_OS_AUTH_TYPE="v3oidcaccesstoken"
    export FEDCLOUD_OS_IDENTITY_PROVIDER="egi.eu"
    export FEDCLOUD_OS_PROTOCOL="openid"
    export FEDCLOUD_OS_PROJECT_ID="51f736d36ce34b9ebdf196cfcabd24ee"
    # Remember to set OS_ACCESS_TOKEN, e.g. :
    # export FEDCLOUD_OS_ACCESS_TOKEN=`oidc-token egi`


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


fedcloud config commands
***************************
* **"fedcloud config --config-file create"** : Create default configuration file in default location for configuration file



fedcloud secret commands
***************************

The **"fedcloud secret"** commands are described in details in the documentation of the
`Secret management service <https://vault.docs.fedcloud.eu/usage.html>`_.
