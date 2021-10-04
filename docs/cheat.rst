Cheat sheet
===========

See `Tutorial <https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing>`_
for more details of commands.

Local install via pip3
**********************

* Create a Python virtual environment:

::

    $ python3 -m venv env

* Activate the virtual environment

::

    $ source env/bin/activate

* Install fedcloudclient via pip:

::

    $ pip3 install fedcloudclient

* Install IGTF certificates:

::

    $ wget https://raw.githubusercontent.com/tdviet/python-requests-bundle-certs/main/scripts/install_certs.sh
    $ bash install_certs.sh

Using Docker container
**********************

* Pull the latest version of fedcloudclient container

::

    $ sudo docker pull tdviet/fedcloudclient

* Start fedcloudclient container with oidc-agent account:

::

    $ sudo docker run -it -v ~/.config/oidc-agent/egi:/root/.config/oidc-agent/egi --name fedcloud tdviet/fedcloudclient bash

* Restart previously terminated container:

::

    $ sudo docker start -i fedcloud

Using oidc-agent
****************

* Create an oidc-agent account (if not done):

::

    $ oidc-gen --pub --issuer https://aai.egi.eu/oidc --scope "eduperson_entitlement email" egi

* Load oidc-agent account and set environment for fedcloudclient:

::

    $ eval `oidc-keychain --accounts egi` && export OIDC_AGENT_ACCOUNT=egi

Basic usages
************

* List your VO memberships according to the access token:

::

    $ fedcloud token list-vos

* List sites in EGI Federated Cloud:

::

    $ fedcloud site list

* Execute an OpenStack command:

::

    $ fedcloud openstack image list --site IISAS-FedCloud --vo eosc-synergy.eu

* Execute an OpenStack command on all sites:

::

    $ fedcloud openstack server list --site ALL_SITES --vo eosc-synergy.eu


* Print only selected values (for scripting):

::

    $ export OS_TOKEN=$(fedcloud openstack --site CESGA --vo vo.access.egi.eu token issue -c id -f value)

* All-sites commands with full JSON output:

::

    $ fedcloud openstack image list --site ALL_SITES --vo eosc-synergy.eu --json-output


Searching and selecting resources
*********************************

* Show all available projects:

::

    $ fedcloud endpoint projects --site ALL_SITES

* Show all Horizon dashboards:

::

    $ fedcloud endpoint list --service-type org.openstack.horizon --site ALL_SITES

* Search images with appliance title in AppDB:

::

    $ fedcloud openstack image list --property "dc:title"="Image for EGI Docker [Ubuntu/18.04/VirtualBox]" --site CESNET-MCC  --vo eosc-synergy.eu


* Select flavors with 2 CPUs and RAM >= 2048 on a site/VO:

::

    $ fedcloud select flavor --site IISAS-FedCloud --vo vo.access.egi.eu --vcpus 2 --flavor-specs "RAM>=2048" --output-format list


* Select EGI Ubuntu 20.04 images on a site/VO:

::

    # Simpler but longer way
    $ fedcloud select image --site IFCA-LCG2 --vo training.egi.eu --image-specs "Name =~ Ubuntu" --image-specs "Name =~ '20.04'" --image-specs "Name =~ EGI" --output-format list

::

    # Shorter but more complex regex
    $ fedcloud select image --site IFCA-LCG2 --vo training.egi.eu --image-specs "Name =~ 'EGI.*Ubuntu.*20.04'"  --output-format list


Mapping and filtering results from OpenStack commands
*****************************************************

* Select flavors with 2 CPUs:

::

    $ fedcloud openstack flavor list  --site IISAS-FedCloud --vo eosc-synergy.eu --json-output | \
      jq -r  '.[].Result[] | select(.VCPUs == 2) | .Name'

* Select GPU flavors and show their GPU properties on a site:

::

    $ fedcloud openstack flavor list --long --site IISAS-FedCloud --vo acc-comp.egi.eu --json-output | \
      jq -r '.[].Result | map(select(.Properties."Accelerator:Type" == "GPU")) | .'

* Select GPU flavors and show their GPU properties on all sites:

::

    $ fedcloud openstack flavor list --long --site ALL_SITES --vo vo.access.egi.eu --json-output | \
      jq -r 'map(select(."Error code" ==  0)) |
             map(.Result = (.Result| map(select(.Properties."Accelerator:Type" == "GPU")))) |
             map(select(.Result | length >  0))'


* Construct JSON objects just with site names and flavor names, remove all other properties:

::

    $ fedcloud openstack flavor list --long --site ALL_SITES --vo vo.access.egi.eu --json-output | \
      jq -r 'map(select(."Error code" ==  0)) |
             map({Site:.Site, Flavors:[.Result[].Name]})'


Useful commands
***************

* Check expiration time of access token (not work for oidc-agent-account):

::

    $ fedcloud token check


* Set OpenStack environment variables:

::

    $ eval $(fedcloud site env --site IISAS-FedCloud --vo vo.access.egi.eu)


* List all my own VMs:

::

    $  list-all-my-own-vms.sh --vo fedcloud.egi.eu


* Activate shell completion

::

    # Quick and dirty way (may be resulted in unresponsive shell)
    $ eval "$(_FEDCLOUD_COMPLETE=bash_source fedcloud)"

::

    # More systematic way
    $ wget https://raw.githubusercontent.com/tdviet/fedcloudclient/master/examples/fedcloud_bash_completion.sh
    $ source fedcloud_bash_completion.sh


More information
****************

* Get help:

::

    $ fedcloud --help
    $ fedcloud site --help

* Tutorial `Tutorial <https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing>`_
