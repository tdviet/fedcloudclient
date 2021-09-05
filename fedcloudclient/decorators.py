"""
Decorators for command-line parameters
"""

import functools

import click
from click_option_group import RequiredMutuallyExclusiveOptionGroup, optgroup

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
