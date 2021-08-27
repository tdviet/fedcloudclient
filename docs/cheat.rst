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

* Pull latest version of fedcloudclient container

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

    $ oidc-gen --pub --issuer https://aai.egi.eu/oidc --scope eduperson_entitlement egi

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

Useful commands
***************

* Select flavors with 2 CPUs:

::

    $ fedcloud openstack flavor list  --site IISAS-FedCloud --vo eosc-synergy.eu --json-output | \
    jq -r  '.[].Result[] | select(.VCPUs == 2) | .Name'

* Select GPU flavors and show their GPU properties:

::

    $ fedcloud openstack flavor list --long --site IISAS-FedCloud --vo acc-comp.egi.eu --json-output | \
    jq -r '.[].Result | map(select(.Properties."Accelerator:Type" == "GPU")) | .'

* Search images with appliance title in AppDB:

::

    $ fedcloud openstack image list --property "dc:title"="Image for EGI Docker [Ubuntu/18.04/VirtualBox]" --site CESNET-MCC  --vo eosc-synergy.eu

* List all my own VMs:

::

    $  list-all-my-own-vms.sh --vo fedcloud.egi.eu

More information
****************

* Get help:

::

    $ fedcloud --help
    $ fedcloud site --help

* Tutorial `Tutorial <https://docs.google.com/presentation/d/1aOdcceztXe8kZaIeVnioF9B0vIHLzJeklSNOdVCL3Rw/edit?usp=sharing>`_
