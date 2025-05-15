#!/usr/bin/env bash

# This script will print a all VMs owned by the user in the given VO on all sites
# Required fedcloudclient and list-my-own-vms.sh script
# OIDC token for authentication should be set via environment variable
# either via OIDC_ACCESS_TOKEN or OIDC_AGENT_ACCOUNT
# See https://fedcloudclient.fedcloud.eu/quickstart.html for more information

# Usage: list-all-my-own-vms.sh --vo <VO>

# Usage info
show_help() {
cat << EOF
Usage: ${0##*/} [-h] --vo <VO>
List all VMs owned by the user in the given VO on all sites in EGI Cloud federation
Arguments:
    -h, --help, help  : Display this help message and exit
    --vo <VO>         : VO name
EOF
}

# Default values for SITE and VO
VO=UNKNOWN

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --vo)
    VO="$2"
    shift # past argument
    shift # past value
    ;;
    -h|--help|help)
    show_help
    exit 0
    ;;
    *)
    echo "Error: Invalid argument: $key"
    show_help
    exit 1
    ;;
esac
done

if [ -z "$OIDC_ACCESS_TOKEN" ] && [ -z "$OIDC_AGENT_ACCOUNT" ]; then
    echo "Access token via OIDC_ACCESS_TOKEN or OIDC_AGENT_ACCOUNT is required"
    exit 1
fi

if [[ $VO == "UNKNOWN" ]]; then
    echo "Error: VO name is required."
    show_help
    exit 1
fi

# Get list of all sites
SITES=$(fedcloud site list)

# and call list-my-own-vms.sh script for each site in parallel
for SITE in $SITES; do
    list-my-own-vms.sh --site "$SITE" --vo "$VO" &
done
wait
