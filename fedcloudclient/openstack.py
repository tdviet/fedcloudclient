import json
import os
from distutils.spawn import find_executable

import click

# Subprocess is required for invoking openstack client, so ignored bandit check
import subprocess       # nosec

from fedcloudclient.checkin import get_access_token, DEFAULT_CHECKIN_URL
from fedcloudclient.sites import find_endpoint_and_project_id, list_sites

DEFAULT_PROTOCOL = "openid"
DEFAULT_AUTH_TYPE = "v3oidcaccesstoken"
DEFAULT_IDENTITY_PROVIDER = "egi.eu"

OPENSTACK_CLIENT = "openstack"


def fedcloud_openstack_full(
        checkin_access_token,
        checkin_protocol,
        checkin_auth_type,
        checkin_identity_provider,
        site,
        vo,
        openstack_command,
        json_output=True
):
    """
    Calling openstack client with full options specified, including support
    for other identity providers and protocols

    :param checkin_access_token: Checkin access token. Passed to openstack client as --os-access-token
    :param checkin_protocol: Checkin protocol (openid, oidc). Passed to openstack client as --os-protocol
    :param checkin_auth_type: Checkin authentication type (v3oidcaccesstoken). Passed to openstack client as --os-auth-type
    :param checkin_identity_provider: Checkin identity provider in mapping (egi.eu). Passed to openstack client as --os-identity-provider
    :param site: site ID in GOCDB
    :param vo: VO name
    :param openstack_command: Openstack command in tuple, e.g. ("image", "list", "--long")
    :param json_output: if result is JSON object or string. Default:True

    :return: error code, result or error message
    """

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    if endpoint is None:
        return 1, ("VO %s not found on site %s" % (vo, site))

    if protocol is None:
        protocol = checkin_protocol

    options = ("--os-auth-url", endpoint,
               "--os-auth-type", checkin_auth_type,
               "--os-protocol", protocol,
               "--os-identity-provider", checkin_identity_provider,
               "--os-access-token", checkin_access_token
               )

    if vo:
        options = options + ("--os-project-id", project_id)

    # Output JSON format is useful for further machine processing
    if json_output:
        options = options + ("--format", "json")

    # Calling openstack client as subprocess, caching stdout/stderr
    # Ignore bandit warning
    completed = subprocess.run((OPENSTACK_CLIENT,) + openstack_command + options,   # nosec
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    error_code = completed.returncode
    error_message = completed.stderr.decode('utf-8')
    result_str = completed.stdout.decode('utf-8')

    if error_code == 0:
        if json_output:
            # Test if openstack command ignore JSON format option
            try:
                json_object = json.loads(result_str)
                return error_code, json_object
            except ValueError:
                return error_code, result_str
        else:
            return error_code, result_str
    else:
        # If error code != 0, return error message instead of result
        # But attach also result string, as applications may print error messages to stdout instead stderr
        return error_code, error_message + result_str


def fedcloud_openstack(
        checkin_access_token,
        site,
        vo,
        openstack_command,
        json_output=True
):
    """
    Simplified version of fedcloud_openstack_full() function using
    default EGI setting for identity provider and protocols
    Call openstack client with default options for EGI Check-in

    :param checkin_access_token: Checkin access token. Passed to openstack client as --os-access-token
    :param site: site ID in GOCDB
    :param vo: VO name
    :param openstack_command: Openstack command in tuple, e.g. ("image", "list", "--long")
    :param json_output: if result is JSON object or string. Default:True

    :return: error code, result or error message
    """

    return fedcloud_openstack_full(
        checkin_access_token,
        DEFAULT_PROTOCOL,
        DEFAULT_AUTH_TYPE,
        DEFAULT_IDENTITY_PROVIDER,
        site,
        vo,
        openstack_command,
        json_output
    )


def check_openstack_client_installation():
    """
    Check if openstack command-line client is installed and available via $PATH

    :return: True if available
    """

    return find_executable(OPENSTACK_CLIENT) is not None


@click.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "--checkin-client-id",
    help="Check-in client id",
    envvar="CHECKIN_CLIENT_ID",
)
@click.option(
    "--checkin-client-secret",
    help="Check-in client secret",
    envvar="CHECKIN_CLIENT_SECRET",
)
@click.option(
    "--checkin-refresh-token",
    help="Check-in refresh token",
    envvar="CHECKIN_REFRESH_TOKEN",
)
@click.option(
    "--checkin-access-token",
    help="Check-in access token",
    envvar="CHECKIN_ACCESS_TOKEN",
)
@click.option(
    "--checkin-url",
    help="Check-in OIDC URL",
    envvar="CHECKIN_OIDC_URL",
    default=DEFAULT_CHECKIN_URL,
    show_default=True,
)
@click.option(
    "--checkin-protocol",
    help="Check-in protocol",
    envvar="CHECKIN_PROTOCOL",
    default=DEFAULT_PROTOCOL,
    show_default=True,
)
@click.option(
    "--checkin-auth-type",
    help="Check-in authentication type",
    envvar="CHECKIN_AUTH_TYPE",
    default=DEFAULT_AUTH_TYPE,
    show_default=True,
)
@click.option(
    "--checkin-provider",
    help="Check-in identity provider",
    envvar="CHECKIN_PROVIDER",
    default=DEFAULT_IDENTITY_PROVIDER,
    show_default=True,
)
@click.option(
    "--site",
    help="Name of the site",
    required=True,
    envvar="EGI_SITE",
)
@click.option(
    "--vo",
    help="Name of the VO",
    envvar="EGI_VO",
)
@click.argument(
    "openstack_command",
    required=True,
    nargs=-1
)
def openstack(
        checkin_client_id,
        checkin_client_secret,
        checkin_refresh_token,
        checkin_access_token,
        checkin_url,
        checkin_protocol,
        checkin_auth_type,
        checkin_provider,
        site,
        vo,
        openstack_command
):
    """
    Executing Openstack commands on site and VO
    """

    if not check_openstack_client_installation():
        print("Error: Openstack command-line client \"openstack\" not found")
        exit(1)

    access_token = get_access_token(checkin_access_token,
                                    checkin_refresh_token,
                                    checkin_client_id,
                                    checkin_client_secret,
                                    checkin_url)

    if site == "ALL_SITES":
        sites = list_sites()
    else:
        sites = [site]
    for current_site in sites:
        print("Site: %s, VO: %s" % (current_site, vo))
        error_code, result = fedcloud_openstack_full(
            access_token,
            checkin_protocol,
            checkin_auth_type,
            checkin_provider,
            current_site,
            vo,
            openstack_command,
            False  # No JSON output in shell mode
        )
        if error_code != 0:
            print("Error code: ", error_code)
            print("Error message: ", result)
        else:
            print(result)


@click.command()
@click.option(
    "--checkin-client-id",
    help="Check-in client id",
    envvar="CHECKIN_CLIENT_ID",
)
@click.option(
    "--checkin-client-secret",
    help="Check-in client secret",
    envvar="CHECKIN_CLIENT_SECRET",
)
@click.option(
    "--checkin-refresh-token",
    help="Check-in refresh token",
    envvar="CHECKIN_REFRESH_TOKEN",
)
@click.option(
    "--checkin-access-token",
    help="Check-in access token",
    envvar="CHECKIN_ACCESS_TOKEN",
)
@click.option(
    "--checkin-url",
    help="Check-in OIDC URL",
    envvar="CHECKIN_OIDC_URL",
    default=DEFAULT_CHECKIN_URL,
    show_default=True,
)
@click.option(
    "--checkin-protocol",
    help="Check-in protocol",
    envvar="CHECKIN_PROTOCOL",
    default=DEFAULT_PROTOCOL,
    show_default=True,
)
@click.option(
    "--checkin-auth-type",
    help="Check-in authentication type",
    envvar="CHECKIN_AUTH_TYPE",
    default=DEFAULT_AUTH_TYPE,
    show_default=True,
)
@click.option(
    "--checkin-provider",
    help="Check-in identity provider",
    envvar="CHECKIN_PROVIDER",
    default=DEFAULT_IDENTITY_PROVIDER,
    show_default=True,
)
@click.option(
    "--site",
    help="Name of the site",
    required=True,
    envvar="EGI_SITE",
)
@click.option(
    "--vo",
    help="Name of the VO",
    required=True,
    envvar="EGI_VO",
)
def openstack_int(
        checkin_client_id,
        checkin_client_secret,
        checkin_refresh_token,
        checkin_access_token,
        checkin_url,
        checkin_protocol,
        checkin_auth_type,
        checkin_provider,
        site,
        vo
):
    """
    Interactive Openstack client on site and VO
    """

    if not check_openstack_client_installation():
        print("Error: Openstack command-line client \"openstack\" not found")
        exit(1)

    access_token = get_access_token(checkin_access_token,
                                    checkin_refresh_token,
                                    checkin_client_id,
                                    checkin_client_secret,
                                    checkin_url)

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    if endpoint is None:
        raise SystemExit("Error: VO %s not found on site %s" % (vo, site))

    if protocol is None:
        protocol = checkin_protocol
    my_env = os.environ.copy()
    my_env["OS_AUTH_URL"] = endpoint
    my_env["OS_AUTH_TYPE"] = checkin_auth_type
    my_env["OS_PROTOCOL"] = protocol
    my_env["OS_IDENTITY_PROVIDER"] = checkin_provider
    my_env["OS_ACCESS_TOKEN"] = access_token
    my_env["OS_PROJECT_ID"] = project_id

    # Calling Openstack client as subprocess
    # Ignore bandit warning
    subprocess.run(OPENSTACK_CLIENT, env=my_env)        # nosec
