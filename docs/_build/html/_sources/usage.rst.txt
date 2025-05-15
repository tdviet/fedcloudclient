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



Authentication Options
======================

**FedCloud** commands require access tokens for authentication. Users have multiple options for providing these tokens:

- **Direct access token**: Use the ``--oidc-access-token`` option to provide an access token directly. You can retrieve this token from the environment variable ``FEDCLOUD_OIDC_ACCESS_TOKEN``, or pass it explicitly, e.g.:

  ``fedcloud token check --oidc-access-token <ACCESS_TOKEN>``

- **OIDC agent**: Use the ``--oidc-agent-account`` option to integrate with `oidc-agent <https://indigo-dc.gitbooks.io/oidc-agent/>`_. For example, check token validity with:

  ``fedcloud token check --oidc-agent-account <NAME_OF_USER_FOR_OIDC_AGENT>``

  To use this method, follow the instructions at `oidc-agent for EGI <https://indigo-dc.gitbook.io/oidc-agent/user/oidc-gen/provider/egi/>`_ to register a client, then pass the client (account) name to the FedCloud client.

- **Mytoken**: Use the ``--mytoken`` option to authenticate with a token from the `Mytoken service <https://mytoken.data.kit.edu/>`_. To check token validity:

  ``fedcloud token check --mytoken <TOKEN_FOR_MYTOKEN>``

  When creating a Mytoken, ensure you select **"Allows obtaining OpenID Connect Access Tokens"**. You may also use the ``--mytoken-server`` option to authenticate with a specific Mytoken server.

Alternatively, you can obtain tokens using the `EGI Check-in Token Portal <https://aai.egi.eu/token>`_, which provides all necessary information for EGI Check-in users.

In addition to command-line options, environment variables can be used for passing tokens, as summarized in the table below (not shown here).

By default, the protocol used is ``openid``. This can be changed using the ``--os-protocol`` option. Note that some sites may have a fixed protocol defined in their site configuration (e.g., ``oidc`` for INFN-CLOUD-BARI).


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


The **FedCloud client** supports multiple types of configuration:

- **Default settings** – accessible using **``DEFAULT_SETTINGS``**, these are the built-in default values.
- **Local environment settings** – custom configuration values defined in the environment and loaded via **``env_config``**.
- **Saved configuration settings** – user-defined settings stored in a JSON file, accessible via **``saved_config``**.

For example, to print the environment configuration, use the following command::

    $ fedcloud config show --source env_config
  

**Testing new version.....**
This command shows, for instance, the following output:

+----------------------------+-------------------------------------------------------------------+
|  Parameter                  |  Default value                                                   |
+============================+===================================================================+
|  oidc_agent_account         |  <NAME_OF_USER>                                                  |
+-----------------------------+------------------------------------------------------------------+
|  ...                        |  ...                                                             |
+-----------------------------+------------------------------------------------------------------+
      


The *fedcloud* configuration can be saved to a file using the following command

::
    $ fedcloud config create

By default, the configuration file is saved to **${HOME}/.config/fedcloud/config.yaml**,  
but this location can be changed using the ``--config`` option. For example:

::

    $ fedcloud config create --config-file /path/to/file.yaml


Using Environment Variables and Configuration Priorities
--------------------------------------------------------

It is also possible to use the *FEDCLOUD_CONFIG_FILE* environment variable instead of the ``--config`` option in the command line.  
This allows users to manage and switch between multiple configuration files—one per project—each with its own settings.

The *fedcloud* client supports configuration from multiple sources, in the following order of priority (highest to lowest):

#. **Command-line options** – override all other settings.  
   Example: ``--site IISAS-FedCloud``

#. **Environment variables** – must begin with the prefix ``FEDCLOUD_``.  
   Example: ``FEDCLOUD_SITE=IISAS-FedCloud``

#. **Configuration file** – typically stored as ``config.yaml``.  
   Example: the ``site`` setting in ``config.yaml``

#. **Default configuration** – hardcoded defaults (lowest priority).  
   See the `source code <https://github.com/jaro221/fedcloudclient>`_ for details.

The priority order is important:  
default values are overridden by the configuration file,  
which is overridden by environment variables,  
which are in turn overridden by command-line options.

For example, the default configuration includes:

- ``site = IISAS-FedCloud``
- ``vo = vo.access.egi.eu``

These values can be changed using any of the higher-priority methods. For example:

::

    $ fedcloud openstack --vo training.egi.eu --site IFCA-LCG2 server list

or

::

    $ export FEDCLOUD_VO=training.egi.eu
    $ export FEDCLOUD_SITE=IFCA-LCG2
    $ fedcloud openstack server list


Consistent Parameter Naming
---------------------------

Note the consistent naming convention for configuration parameters across different sources. For example, the same parameter is represented as:

* ``--oidc-agent-account`` in the **command-line**
* ``FEDCLOUD_OIDC_AGENT_ACCOUNT`` as an **environment variable**
* ``oidc_agent_account`` in the **configuration file**

All configuration parameters follow this consistent mapping across command-line options, environment variables, and configuration files.

Additional Configurable Parameters
----------------------------------

In addition to ``oidc_agent_account``, the following parameters can also be configured in the same way:

* ``site`` – the OpenStack site to target
* ``vo`` – the Virtual Organisation (VO)
* ``check_in_url`` – the EGI Check-in OIDC endpoint
* ``client_id`` – the OIDC client ID
* ``scopes`` – requested OIDC scopes
* ``access_token`` – manually provided access token
* ``output_format`` – format of output, e.g., ``table``, ``json``, or ``yaml``

These parameters can be specified via:

- command-line options (e.g., ``--site``, ``--vo``),
- environment variables (e.g., ``FEDCLOUD_SITE``, ``FEDCLOUD_VO``), or
- configuration files (e.g., ``site: IISAS-FedCloud`` in ``config.yaml``).

This design allows flexible and convenient configuration for various usage scenarios.

+------------------------------+-------------------------+
|  Environment variable        |  Command-line option    |
+==============================+=========================+
|  FEDCLOUD_OIDC_ACCESS_TOKEN  |  --oidc-access-token    |
+------------------------------+-------------------------+
|  FEDCLOUD_MYTOKEN            |  --mytoken              |
+------------------------------+-------------------------+
|  FEDCLOUD_OIDC_AGENT_ACCOUNT |  --oidc-agent-account   |
+------------------------------+-------------------------+

For convenience, it is recommended to set transient parameters—such as access tokens—via **environment variables**.  
This simplifies the usage of *fedcloud* commands by avoiding the need to specify these parameters on the command line each time.


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

* **``fedcloud token check``** – Checks the expiration time of the configured access token,  
  allowing users to determine whether it needs to be refreshed.

As mentioned earlier, the access token can be provided via the environment variable ``FEDCLOUD_OIDC_ACCESS_TOKEN``.  
For this reason, the ``--oidc-access-token`` option is not shown in all examples below, even though it may be required if the token is not set via environment variables.


::

    $ fedcloud token check

Output is shown as:
::
    Access token is valid to 2021-01-02 01:25:39 UTC
    Access token expires in 3571 seconds


* **"fedcloud token list-vos"** : Print the list of VO memberships according to EGI Check-in

::

    $ fedcloud token list-vos

Sample output:
::
    eosc-synergy.eu
    fedcloud.egi.eu
    training.egi.eu

* **"fedcloud token issue"** : Print the access_token

::

    $ fedcloud token issue
    
Sample output:
::
  egwergwregrwegreg...

fedcloud endpoint commands
**************************

**"fedcloud endpoint"** commands are complementary part of the **"fedcloud site"** commands. Instead of using site
configurations defined in files saved in GitHub repository or local disk, the commands try to get site information
directly from GOCDB (Grid Operations Configuration Management Database) https://goc.egi.eu/ or make probe test on sites

* **"fedcloud endpoint list"** : List of endpoints of sites defined in GOCDB.

::

    $ fedcloud endpoint list

Sample output:

::
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
    export FEDCLOUD_OS_TOKEN="eayeghjtjtj..."


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
