"""
Implementation of "fedcloud openstack" or "fedcloud openstack-int" for performing
OpenStack commands on sites
"""

import concurrent.futures
import json
import os
import subprocess  # nosec Subprocess is required for invoking openstack client
import sys
from distutils.spawn import find_executable

import click

from fedcloudclient.decorators import (
    ALL_SITES_KEYWORDS,
    DEFAULT_AUTH_TYPE,
    DEFAULT_IDENTITY_PROVIDER,
    DEFAULT_PROTOCOL,
    all_site_params,
    oidc_params,
    openstack_output_format_params,
    openstack_params,
    site_params,
    vo_params,
)
from fedcloudclient.sites import (
    find_endpoint_and_project_id,
    list_sites,
)

__OPENSTACK_CLIENT = "openstack"
__MAX_WORKER_THREAD = 30
__MISSING_VO_ERROR_CODE = 11

CONFLICTING_ENVS = ["OS_TOKEN", "OS_USER_DOMAIN_NAME"]


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
        return __MISSING_VO_ERROR_CODE, f"VO {vo} not found on site {site}\n"

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
    for env in CONFLICTING_ENVS:
        my_env.pop(env, None)

    # Calling openstack client as subprocess, caching stdout/stderr
    # Ignore bandit warning
    completed = subprocess.run(  # nosec
        (__OPENSTACK_CLIENT,) + openstack_command + options,
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
    Simplified version of fedcloud_openstack_full() using
    default EGI setting for identity provider and protocols
    Calls OpenStack CLI with default options for EGI Check-in

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
        if not ignore_missing_vo or (error_code != __MISSING_VO_ERROR_CODE):
            print(f"Site: {site}, VO: {vo}, command: {command}", file=sys.stderr)

        if exc_msg:
            print(f"{site} generated an exception: {exc_msg}")
            print(f"Error message: {result}")

        elif error_code != 0:
            if not ignore_missing_vo or (error_code != __MISSING_VO_ERROR_CODE):
                print("Error code: ", error_code)
                print("Error message: ", result)
        else:
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
@all_site_params
@vo_params
@oidc_params
@openstack_output_format_params
@openstack_params
@click.argument("openstack_command", required=True, nargs=-1)
def openstack(
    access_token,
    site,
    all_sites,
    vo,
    openstack_command,
    openstack_auth_protocol,
    openstack_auth_type,
    openstack_auth_provider,
    ignore_missing_vo,
    json_output,
):
    """
    Execute OpenStack commands on site and VO
    """

    if not check_openstack_client_installation():
        raise SystemExit('Error: OpenStack command-line client "openstack" not found')

    if site in ALL_SITES_KEYWORDS or all_sites:
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
@site_params
@vo_params
@oidc_params
@openstack_params
def openstack_int(
    access_token,
    site,
    vo,
    openstack_auth_protocol,
    openstack_auth_type,
    openstack_auth_provider,
):
    """
    Interactive OpenStack client on site and VO
    """

    if not check_openstack_client_installation():
        raise SystemExit('Error: OpenStack command-line client "openstack" not found')

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    if endpoint is None:
        raise SystemExit(f"Error: VO {vo} not found on site {site}")

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
