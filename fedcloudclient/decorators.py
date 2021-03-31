"""
Decorators for command-line parameters
"""

import functools

import click

DEFAULT_OIDC_URL = "https://aai.egi.eu/oidc"
DEFAULT_PROTOCOL = "openid"
DEFAULT_AUTH_TYPE = "v3oidcaccesstoken"
DEFAULT_IDENTITY_PROVIDER = "egi.eu"


def oidc_access_token_params(func):
    @click.option(
        "--oidc-access-token",
        help="OIDC access token",
        envvar="OIDC_ACCESS_TOKEN",
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
    @click.option(
        "--vo",
        help="Name of the VO",
        required=True,
        envvar="EGI_VO",
    )
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

    @click.option(
        "--oidc-client-id",
        help="OIDC client id",
        envvar="OIDC_CLIENT_ID",
    )
    @click.option(
        "--oidc-client-secret",
        help="OIDC client secret",
        envvar="OIDC_CLIENT_SECRET",
    )
    @oidc_refresh_token_params
    @oidc_access_token_params
    @click.option(
        "--oidc-url",
        help="OIDC URL",
        envvar="OIDC_URL",
        default=DEFAULT_OIDC_URL,
        show_default=True,
    )
    @click.option(
        "--oidc-agent-account",
        help="short account name in oidc-agent",
        envvar="OIDC_AGENT_ACCOUNT",
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

    @click.option(
        "--openstack-auth-protocol",
        help="Check-in protocol",
        envvar="OPENSTACK_AUTH_PROTOCOL",
        default=DEFAULT_PROTOCOL,
        show_default=True,
    )
    @click.option(
        "--openstack-auth-type",
        help="Check-in authentication type",
        envvar="OPENSTACK_AUTH_TYPE",
        default=DEFAULT_AUTH_TYPE,
        show_default=True,
    )
    @click.option(
        "--openstack-auth-provider",
        help="Check-in identity provider",
        envvar="OPENSTACK_AUTH_PROVIDER",
        default=DEFAULT_IDENTITY_PROVIDER,
        show_default=True,
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
