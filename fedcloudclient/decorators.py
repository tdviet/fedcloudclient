"""
Decorators for command-line parameters
"""

import functools

import click
from click_option_group import (
    RequiredAnyOptionGroup,
    RequiredMutuallyExclusiveOptionGroup,
    optgroup,
)

DEFAULT_OIDC_URL = "https://aai.egi.eu/oidc"
DEFAULT_PROTOCOL = "openid"
DEFAULT_AUTH_TYPE = "v3oidcaccesstoken"
DEFAULT_IDENTITY_PROVIDER = "egi.eu"

ALL_SITES_KEYWORDS = {"ALL_SITES", "ALL-SITES"}


def oidc_access_token_params(func):
    @click.option(
        "--oidc-access-token",
        help="OIDC access token",
        envvar="OIDC_ACCESS_TOKEN",
        metavar="token",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def oidc_refresh_token_params(func):
    @click.option(
        "--oidc-refresh-token",
        help="OIDC refresh token",
        envvar="OIDC_REFRESH_TOKEN",
        metavar="token",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def site_params(func):
    @click.option(
        "--site",
        help="Name of the site",
        required=True,
        envvar="EGI_SITE",
        metavar="site-name",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def all_site_params(func):
    @optgroup.group(
        "Site",
        cls=RequiredMutuallyExclusiveOptionGroup,
        help="Single Openstack site or all sites",
    )
    @optgroup.option(
        "--site",
        help="Name of the site or ALL_SITES",
        envvar="EGI_SITE",
        metavar="site-name",
    )
    @optgroup.option(
        "--all-sites",
        "-a",
        help="Short option for all sites (equivalent --site ALL_SITES)",
        is_flag=True,
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def project_id_params(func):
    @click.option(
        "--project-id",
        help="Project ID",
        required=True,
        envvar="OS_PROJECT_ID",
        metavar="project-id",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def auth_file_params(func):
    @click.option(
        "--auth-file",
        help="Authorization file",
        default="auth.dat",
        show_default=True,
        metavar="auth-file",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def vo_params(func):
    @click.option(
        "--vo",
        help="Name of the VO",
        required=True,
        envvar="EGI_VO",
        metavar="vo-name",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def site_vo_params(func):
    """
    Decorator for site and VO parameters

    :param func:
    :return:
    """

    @site_params
    @vo_params
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def oidc_params(func):
    """
    Decorator for OIDC parameters

    :param func:
    :return:
    """

    @optgroup.group("OIDC token", help="oidc-gent account or tokens for authentication")
    @optgroup.option(
        "--oidc-agent-account",
        help="Account name in oidc-agent",
        envvar="OIDC_AGENT_ACCOUNT",
        metavar="account",
    )
    @optgroup.option(
        "--oidc-access-token",
        help="OIDC access token",
        envvar="OIDC_ACCESS_TOKEN",
        metavar="token",
    )
    @optgroup.option(
        "--oidc-refresh-token",
        help="OIDC refresh token",
        envvar="OIDC_REFRESH_TOKEN",
        metavar="token",
    )
    @optgroup.option(
        "--oidc-client-id",
        help="OIDC client id",
        envvar="OIDC_CLIENT_ID",
        metavar="id",
    )
    @optgroup.option(
        "--oidc-client-secret",
        help="OIDC client secret",
        envvar="OIDC_CLIENT_SECRET",
        metavar="secret",
    )
    @optgroup.option(
        "--oidc-url",
        help="OIDC identity provider URL",
        envvar="OIDC_URL",
        default=DEFAULT_OIDC_URL,
        show_default=True,
        metavar="provider-url",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def openstack_params(func):
    """
    Decorator for OpenStack authentication parameters

    :param func:
    :return:
    """

    @optgroup.group(
        "OpenStack authentication",
        help="Only change default values if necessary",
    )
    @optgroup.option(
        "--openstack-auth-protocol",
        help="Authentication protocol",
        envvar="OPENSTACK_AUTH_PROTOCOL",
        default=DEFAULT_PROTOCOL,
        show_default=True,
        metavar="",
    )
    @optgroup.option(
        "--openstack-auth-provider",
        help="Identity provider",
        envvar="OPENSTACK_AUTH_PROVIDER",
        default=DEFAULT_IDENTITY_PROVIDER,
        show_default=True,
        metavar="",
    )
    @optgroup.option(
        "--openstack-auth-type",
        help="Authentication type",
        envvar="OPENSTACK_AUTH_TYPE",
        default=DEFAULT_AUTH_TYPE,
        show_default=True,
        metavar="",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def output_format_params(func):
    @optgroup.group(
        "Output format",
        help="Parameters for formatting outputs",
    )
    @optgroup.option(
        "--ignore-missing-vo",
        "-i",
        help="Ignore sites that do not support the VO",
        is_flag=True,
    )
    @optgroup.option(
        "--json-output",
        "-j",
        help="Print output as JSON object",
        is_flag=True,
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def flavor_specs_params(func):
    @optgroup.group(
        "Flavor specs options",
        cls=RequiredAnyOptionGroup,
        help="Parameters for flavor specification",
    )
    @optgroup.option(
        "--flavor-specs",
        help="Flavor specifications, e.g. 'VCPUs==2' or 'Disk>100'."
        " May be specified more times, or joined, e.g. 'VCPUs==2 & RAM>2048'",
        multiple=True,
        metavar="flavor-specs",
    )
    @optgroup.option(
        "--vcpus",
        help="Number of VCPUs (equivalent --flavor-specs VCPUs==vcpus)",
        metavar="vcpus",
    )
    @optgroup.option(
        "--RAM",
        help="Amount of RAM in MB (equivalent --flavor-specs RAM==memory)",
        metavar="memory",
    )
    @optgroup.option(
        "--gpus",
        help="Number of GPUs (equivalent --flavor-specs Properties.Accelerator:Number==gpus)",
        metavar="gpus",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def flavor_output_params(func):
    @optgroup.group(
        "Flavor output options",
        help="Parameters for printing flavor",
    )
    @optgroup.option(
        "--flavor-output",
        help="Flavor output option, 'first' for printing only best matched flavor,"
        " 'list' for printing all matched flavor names, and 'YAML' or 'JSON' for full output",
        type=click.Choice(["first", "list", "YAML", "JSON"], case_sensitive=False),
        default="JSON",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def image_specs_params(func):
    @optgroup.group(
        "Image specs options",
        help="Parameters for image specification",
    )
    @optgroup.option(
        "--image-specs",
        required=True,
        help="Image specifications, e.g. 'Name=~\"20.04\"' or 'Name=~\"CentOS 8\"'",
        multiple=True,
        metavar="image-specs",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def image_output_params(func):
    @optgroup.group(
        "Image output options",
        help="Parameters for printing image",
    )
    @optgroup.option(
        "--image-output",
        help="Image output option, 'first' for printing only best matched image,"
        " 'list' for printing all matched image names, and 'YAML' or 'JSON' for full output",
        type=click.Choice(["first", "list", "YAML", "JSON"], case_sensitive=False),
        default="JSON",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def network_specs_params(func):
    @optgroup.group(
        "Network specs options",
        help="Parameters for network specification",
    )
    @optgroup.option(
        "--network-specs",
        required=True,
        help="Network specifications: 'default', 'public', 'private'",
        type=click.Choice(["default", "public", "private"], case_sensitive=False),
        default="default",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def network_output_params(func):
    @optgroup.group(
        "Network output options",
        help="Parameters for printing network",
    )
    @optgroup.option(
        "--network-output",
        help="Network output option, 'first' for printing only best matched network,"
        " 'list' for printing all accessible network names, and 'YAML' or 'JSON' for full output",
        type=click.Choice(["first", "list", "YAML", "JSON"], case_sensitive=False),
        default="JSON",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
