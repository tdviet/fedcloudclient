"""
Implementation of "fedcloud openstack" or "fedcloud openstack-int" for performing
OpenStack commands on sites
"""

import concurrent.futures
import json
import os
import subprocess  # nosec Subprocess is required for invoking openstack client
from distutils.spawn import find_executable

import click
from fedcloudclient.checkin import get_access_token, oidc_params
from fedcloudclient.decorators import (
    DEFAULT_AUTH_TYPE,
    DEFAULT_IDENTITY_PROVIDER,
    DEFAULT_PROTOCOL,
    openstack_params,
)
from fedcloudclient.sites import (
    find_endpoint_and_project_id,
    list_sites,
    site_vo_params,
)

__OPENSTACK_CLIENT = "openstack"
__MAX_WORKER_THREAD = 30


def fedcloud_openstack_full(
    oidc_access_token,
    openstack_auth_protocol,
    openstack_auth_type,
    checkin_identity_provider,
    site,
    vo,
    openstack_command,
    json_output=True,
):
    """
    Calling openstack client with full options specified, including support
    for other identity providers and protocols

    :param oidc_access_token: Checkin access token. Passed to openstack client
           as --os-access-token
    :param openstack_auth_protocol: Checkin protocol (openid, oidc). Passed to
           openstack client as --os-protocol
    :param openstack_auth_type: Checkin authentication type (v3oidcaccesstoken).
           Passed to openstack client as --os-auth-type
    :param checkin_identity_provider: Checkin identity provider in mapping (egi.eu).
           Passed to openstack client as --os-identity-provider
    :param site: site ID in GOCDB
    :param vo: VO name
    :param openstack_command: OpenStack command in tuple,
           e.g. ("image", "list", "--long")
    :param json_output: if result is JSON object or string. Default:True

    :return: error code, result or error message
    """

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    if endpoint is None:
        return 11, ("VO %s not found on site %s\n" % (vo, site))

    if protocol is None:
        protocol = openstack_auth_protocol

    options = (
        "--os-auth-url",
        endpoint,
        "--os-auth-type",
        openstack_auth_type,
        "--os-protocol",
        protocol,
        "--os-identity-provider",
        checkin_identity_provider,
        "--os-access-token",
        oidc_access_token,
    )

    if vo:
        options = options + ("--os-project-id", project_id)

    # Output JSON format is useful for further machine processing
    if json_output:
        options = options + ("--format", "json")

    # Remove conflicting environment
    my_env = os.environ.copy()
    my_env.pop("OS_TOKEN", None)

    # Calling openstack client as subprocess, caching stdout/stderr
    # Ignore bandit warning
    completed = subprocess.run(
        (__OPENSTACK_CLIENT,) + openstack_command + options,  # nosec
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=my_env,
    )

    error_code = completed.returncode
    error_message = completed.stderr.decode("utf-8")
    result_str = completed.stdout.decode("utf-8")

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
        # But attach also result string, as applications may print
        # error messages to stdout instead stderr
        return error_code, error_message + result_str


def fedcloud_openstack(
    oidc_access_token, site, vo, openstack_command, json_output=True
):
    """
    Simplified version of fedcloud_openstack_full() function using
    default EGI setting for identity provider and protocols
    Call openstack client with default options for EGI Check-in

    :param oidc_access_token: Checkin access token.
           Passed to openstack client as --os-access-token
    :param site: site ID in GOCDB
    :param vo: VO name
    :param openstack_command: OpenStack command in tuple,
           e.g. ("image", "list", "--long")
    :param json_output: if result is JSON object or string. Default:True

    :return: error code, result or error message
    """

    return fedcloud_openstack_full(
        oidc_access_token,
        DEFAULT_PROTOCOL,
        DEFAULT_AUTH_TYPE,
        DEFAULT_IDENTITY_PROVIDER,
        site,
        vo,
        openstack_command,
        json_output,
    )


def check_openstack_client_installation():
    """
    Check if openstack command-line client is installed and available via $PATH

    :return: True if available
    """

    return find_executable(__OPENSTACK_CLIENT) is not None


def print_result(
    site,
    vo,
    command,
    exc_msg,
    error_code,
    result,
    json_output,
    ignore_missing_vo,
    first,
):
    """
    Print output from an OpenStack command

    :param site:
    :param vo:
    :param command:
    :param exc_msg:
    :param error_code:
    :param result:
    :param json_output:
    :param ignore_missing_vo:
    :param first:
    :return:
    """

    command = " ".join(command)
    if not json_output:
        if exc_msg:
            print("Site: %s, VO: %s, command: %s" % (site, vo, command))
            print("%s generated an exception: %s" % (site, exc_msg))
            print("Error message: %s" % result)

        elif error_code != 0:
            if not ignore_missing_vo or (error_code != 11):
                print("Site: %s, VO: %s, command: %s" % (site, vo, command))
                print("Error code: ", error_code)
                print("Error message: ", result)
        else:
            print("Site: %s, VO: %s, command: %s" % (site, vo, command))
            print(result)
    else:
        site_data = {
            "Site": site,
            "VO": vo,
            "command": command,
            "Exception": exc_msg,
            "Error code": error_code,
            "Result": result,
        }
        separator = "[" if first else ","
        print(separator)
        print(json.dumps(site_data, indent=2))


@click.command(context_settings={"ignore_unknown_options": True})
@oidc_params
@openstack_params
@site_vo_params
@click.option(
    "--ignore-missing-vo",
    "-i",
    help="Ignore sites that do not support the VO",
    is_flag=True,
)
@click.option(
    "--json-output",
    "-j",
    help="Print output as a big JSON object",
    is_flag=True,
)
@click.argument("openstack_command", required=True, nargs=-1)
def openstack(
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    openstack_auth_protocol,
    openstack_auth_type,
    openstack_auth_provider,
    site,
    vo,
    ignore_missing_vo,
    json_output,
    openstack_command,
):
    """
    Executing OpenStack commands on site and VO
    """

    if not check_openstack_client_installation():
        print('Error: OpenStack command-line client "openstack" not found')
        exit(1)

    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )

    if site == "ALL_SITES":
        sites = list_sites()
    else:
        sites = [site]

    # Multi-thread execution of OpenStack commands
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=__MAX_WORKER_THREAD
    ) as executor:
        # Start OpenStack operation with each site
        results = {
            executor.submit(
                fedcloud_openstack_full,
                access_token,
                openstack_auth_protocol,
                openstack_auth_type,
                openstack_auth_provider,
                site,
                vo,
                openstack_command,
                json_output,
            ): site
            for site in sites
        }

        # Get results and print them
        first = True

        # Get the result, first come first serve
        for future in concurrent.futures.as_completed(results):
            site = results[future]
            exc_msg = None
            try:
                error_code, result = future.result()
            except Exception as exc:
                exc_msg = exc

            # Print result
            print_result(
                site,
                vo,
                openstack_command,
                exc_msg,
                error_code,
                result,
                json_output,
                ignore_missing_vo,
                first,
            )
            first = False

        # Print list enclosing ']' for JSON
        if json_output:
            print("]")


@click.command()
@oidc_params
@openstack_params
@site_vo_params
def openstack_int(
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    openstack_auth_protocol,
    openstack_auth_type,
    openstack_auth_provider,
    site,
    vo,
):
    """
    Interactive OpenStack client on site and VO
    """

    if not check_openstack_client_installation():
        print('Error: OpenStack command-line client "openstack" not found')
        exit(1)

    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    if endpoint is None:
        raise SystemExit("Error: VO %s not found on site %s" % (vo, site))

    if protocol is None:
        protocol = openstack_auth_protocol
    my_env = os.environ.copy()
    my_env["OS_AUTH_URL"] = endpoint
    my_env["OS_AUTH_TYPE"] = openstack_auth_type
    my_env["OS_PROTOCOL"] = protocol
    my_env["OS_IDENTITY_PROVIDER"] = openstack_auth_provider
    my_env["OS_ACCESS_TOKEN"] = access_token
    my_env["OS_PROJECT_ID"] = project_id

    # Calling OpenStack client as subprocess
    # Ignore bandit warning
    subprocess.run(__OPENSTACK_CLIENT, env=my_env)  # nosec
