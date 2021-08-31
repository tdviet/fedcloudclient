Using fedcloudclient in scripts
===============================

fedcloudclient can be used in scripts for simple automation, either for setting environment variables for other tools
or processing outputs from OpenStack commands.

Setting environment variables for external tools
************************************************

Outputs from fedcloud commands for setting environment variables are already in the forms *"export VAR=VALUE"*. Simple
*eval* command in scripts can be used for setting environment variables for external tools:

::

    $ fedcloud site show-project-id --site IISAS-FedCloud --vo eosc-synergy.eu
    export OS_AUTH_URL="https://cloud.ui.savba.sk:5000/v3/"
    export OS_PROJECT_ID="51f736d36ce34b9ebdf196cfcabd24ee"

    # This command will set environment variables
    $ eval $(fedcloud site show-project-id --site IISAS-FedCloud --vo eosc-synergy.eu)

    # Check the value of the variable
    $ echo $OS_AUTH_URL
    https://cloud.ui.savba.sk:5000/v3/


Processing JSON outputs from OpenStack commands via jq
******************************************************

The outputs from Openstack command can be printed in JSON formats with *--json-output* parameter for further machine
processing. The JSON outputs can be processed in scripts by `jq <https://stedolan.github.io/jq/>`_ command.
For examples, if users want to select flavors with 2 CPUs:

::

    $ fedcloud openstack flavor list  --site IISAS-FedCloud --vo eosc-synergy.eu --json-output
    [
    {
      "Site": "IISAS-FedCloud",
      "VO": "eosc-synergy.eu",
      "command": "flavor list",
      "Exception": null,
      "Error code": 0,
      "Result": [
        {
          "ID": "0",
          "Name": "m1.nano",
          "RAM": 64,
          "Disk": 1,
          "Ephemeral": 0,
          "VCPUs": 1,
          "Is Public": true
        },
        {
          "ID": "2e562a51-8861-40d5-8fc9-2638bab4662c",
          "Name": "m1.xlarge",
          "RAM": 16384,
          "Disk": 40,
          "Ephemeral": 0,
          "VCPUs": 8,
          "Is Public": true
        },
        ...
      ]
    }
    ]

    # The following jq command selects flavors with VCPUs=2 and print their names
    $ fedcloud openstack flavor list  --site IISAS-FedCloud --vo eosc-synergy.eu --json-output | \
        jq -r  '.[].Result[] | select(.VCPUs == 2) | .Name'
    m1.medium

The following example is more complex:

* List all flavors in the VO vo.access.egi.eu on all sites and print them in JSON format

* Filter out sites with error code > 0

* Select only GPU flavors

* Filter out sites with empty list of GPU flavors

* Print the result (list of all GPU flavors on all sites) in JSON format

::

    $ fedcloud openstack flavor list --long --site ALL_SITES --vo vo.access.egi.eu --json-output | \
        jq -r 'map(select(."Error code" ==  0)) |
               map(.Result = (.Result| map(select(.Properties."Accelerator:Type" == "GPU")))) |
               map(select(.Result | length >  0))'

Note that only OpenStack commands that have outputs can be used with *--json-output*. Using the parameter with
commands without outputs (e.g. setting properties) will generate errors of unsupported parameters.


