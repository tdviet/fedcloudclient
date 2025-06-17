"""
Decorators for command-line parameters
"""
import os
from functools import wraps

import click
from click_option_group import (
    RequiredAnyOptionGroup,
    optgroup, MutuallyExclusiveOptionGroup,
)

from fedcloudclient.conf import CONF
from fedcloudclient.exception import TokenError
from fedcloudclient.locker_auth import LockerToken
from fedcloudclient.vault_auth import VaultToken
from fedcloudclient.auth import OIDCToken
from fedcloudclient.logger import log_and_raise

ALL_SITES_KEYWORDS = {"ALL_SITES", "ALL-SITES"}

# Decorator for --oidc-access-token
oidc_access_token_params = click.option(
    "--oidc-access-token",
    help="OIDC access token",
    default=CONF.get("oidc_access_token"),
    metavar="token",
)

# Decorator for --site
site_params = click.option(
    "--site",
    help="Name of the site",
    default=CONF.get("site"),
    metavar="site-name",
)

# Output format for secret module
secret_output_params = click.option(
    "--output-format",
    "-f",
    required=False,
    help="Output format",
    type=click.Choice(["text", "YAML", "JSON"], case_sensitive=False),
)


def all_site_params(func):
    """
    Decorator for all-sites options
    """

    @optgroup.group(
        "Site",
        cls=MutuallyExclusiveOptionGroup,
        help="Single Openstack site or all sites",
    )
    @optgroup.option(
        "--site",
        help="Name of the site or ALL_SITES",
        default=CONF.get("site"),
        metavar="site-name",
    )
    @optgroup.option(
        "--all-sites",
        "-a",
        help="Short option for all sites (equivalent --site ALL_SITES)",
        is_flag=True,
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


# Decorator for --project-id
project_id_params = click.option(
    "--project-id",
    help="Project ID",
    default=CONF.get("project_id"),
    metavar="project-id",
)

# Decorator for --auth-file (used in ec3 module)
auth_file_params = click.option(
    "--auth-file",
    help="Authorization file",
    default="auth.dat",
    show_default=True,
    metavar="auth-file",
)

# Decorator for --vo
vo_params = click.option(
    "--vo",
    help="Name of the VO",
    default=CONF.get("vo"),
    metavar="vo-name",
)

# Optional decorator for --vo
vo_params_optional = click.option(
    "--vo",
    help="Name of the VO",
    required=False,
    envvar="EGI_VO",
    metavar="vo-name",
)


def site_vo_params(func):
    """
    Decorator for site and VO parameters
    """

    @site_params
    @vo_params
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def oidc_params(func):
    """
    Decorator for OIDC parameters.
    Get access token from oidc-* parameters and replace them in the wrapper function
    """

    @optgroup.group("OIDC token", help="Choose one of options for providing token")
    @optgroup.option(
        "--oidc-agent-account",
        help="Account name in oidc-agent",
        default=CONF.get("oidc_agent_account"),
        metavar="account",
    )
    @optgroup.option(
        "--oidc-access-token",
        help="OIDC access token",
        default=os.getenv("FEDCLOUD_OIDC_ACCESS_TOKEN"),
        metavar="token",
    )
    @optgroup.option(
        "--mytoken",
        help="Mytoken string",
        default=CONF.get("mytoken"),
        metavar="mytoken",
    )
    @optgroup.option(
        "--mytoken-server",
        help="Mytoken sever",
        default=CONF.get("mytoken_server"),
        metavar="url",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):

        token=OIDCToken()
        access_token = token.multiple_token(
            kwargs.pop("oidc_access_token"),
            kwargs.pop("oidc_agent_account"),
            kwargs.pop("mytoken"),
            kwargs.pop("mytoken_server"),
        ) # pylint: disable=assignment-from-none
        kwargs["access_token"] = access_token

        return func(*args, **kwargs)

    return wrapper


def openstack_params(func):
    """
    Decorator for OpenStack authentication parameters
    """

    @optgroup.group(
        "OpenStack authentication",
        help="Only change default values if necessary",
    )
    @optgroup.option(
        "--os-protocol",
        help="Authentication protocol",
        default=CONF.get("os_protocol"),
        show_default=True,
        metavar="",
    )
    @optgroup.option(
        "--os-identity-provider",
        help="Identity provider",
        default=CONF.get("os_identity_provider"),
        show_default=True,
        metavar="",
    )
    @optgroup.option(
        "--os-auth-type",
        help="Authentication type",
        default=CONF.get("os_auth_type"),
        show_default=True,
        metavar="",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def openstack_output_format_params(func):
    """
    Decorator for output format options for OpenStack
    """

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
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def flavor_specs_params(func):
    """
    Decorator for flavor specs
    """

    @optgroup.group(
        "Flavor specs options",
        cls=RequiredAnyOptionGroup,
        help="Parameters for flavor specification",
    )
    @optgroup.option(
        "--flavor-specs",
        help=(
            "Flavor specifications, e.g. 'VCPUs==2' or 'Disk>100'."
            " May be specified more times, or joined, e.g. 'VCPUs==2 & RAM>2048'"
        ),
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
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def image_specs_params(func):
    """
    Decorator for flavor specs
    """

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
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def network_specs_params(func):
    """
    Decorator for network specs
    """

    @optgroup.group(
        "Network specs options",
        help="Parameters for network specification",
    )
    @optgroup.option(
        "--network-specs",
        help="Network specifications: 'default', 'public', 'private'",
        type=click.Choice(["default", "public", "private"], case_sensitive=False),
        default="default",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def select_output_format_params(func):
    """
    Decorator for option for printing outputs from searching
    """

    @optgroup.group(
        "Output format",
        help="Parameters for formatting outputs",
    )
    @optgroup.option(
        "--output-format",
        help=(
            "Option for printing matched results, 'first' for printing only best matched item,"
            " 'list' for printing all matched resources, and 'YAML' or 'JSON' for full output"
        ),
        type=click.Choice(["first", "list", "YAML", "JSON"], case_sensitive=False),
        default="JSON",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def secret_token_params(func):
    """
    Decorator for secret token.
    If locker token is not defined, get access token from oidc-* parameters
    and replace them in the wrapper function
    """

    @optgroup.group("Token options", help="Choose one of options for providing token")
    @optgroup.option(
        "--locker-token",
        help="Locker token",
        default=CONF.get("locker_token"),
        metavar="locker_token",
    )
    @optgroup.option(
        "--vault-token",
        help="Vault token",
        default=CONF.get("vault_token"),
        metavar="vault_token",
    )
    @optgroup.option(
        "--oidc-agent-account",
        help="Account name in oidc-agent",
        default=CONF.get("oidc_agent_account"),
        metavar="account",
    )
    @optgroup.option(
        "--oidc-access-token",
        help="OIDC access token",
        default=CONF.get("oidc_access_token"),
        metavar="token",
    )
    @optgroup.option(
        "--mytoken",
        help="Mytoken string",
        default=CONF.get("mytoken"),
        metavar="mytoken",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):

        # If locker token is given, ignore OIDC token options
        locker_token = kwargs.pop("locker_token")
        vault_token = kwargs.pop("vault_token")
        access_token = kwargs.pop("oidc_access_token")
        oidc_agent_account = kwargs.pop("oidc_agent_account")
        mytoken = kwargs.pop("mytoken")

        if locker_token:
            token = LockerToken(locker_token=locker_token)
        elif vault_token:
            token = VaultToken(vault_token=vault_token)
        else:
            token = VaultToken()
            try:
                token.multiple_token(access_token, oidc_agent_account, mytoken)
            except TokenError:
                error_msg=f"Can not access to the ACCESS_TOKEN: {TokenError}"
                log_and_raise(error_msg, TokenError)
                SystemExit(1)

        kwargs["token"] = token
        return func(*args, **kwargs)

    return wrapper
