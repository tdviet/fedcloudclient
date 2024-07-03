"""
Decorators for command-line parameters
"""
from functools import wraps

import click
from click_option_group import (
    RequiredAnyOptionGroup,
    RequiredMutuallyExclusiveOptionGroup,
    optgroup,
)

DEFAULT_MYTOKEN_SERVER = "https://mytoken.data.kit.edu"
DEFAULT_PROTOCOL = "openid"
DEFAULT_AUTH_TYPE = "v3oidcaccesstoken"
DEFAULT_IDENTITY_PROVIDER = "egi.eu"

ALL_SITES_KEYWORDS = {"ALL_SITES", "ALL-SITES"}

# Decorator for --oidc-access-token
oidc_access_token_params = click.option(
    "--oidc-access-token",
    help="OIDC access token",
    envvar="OIDC_ACCESS_TOKEN",
    metavar="token",
)

# Decorator for --site
site_params = click.option(
    "--site",
    help="Name of the site",
    required=True,
    envvar="EGI_SITE",
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
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


# Decorator for --project-id
project_id_params = click.option(
    "--project-id",
    help="Project ID",
    required=True,
    envvar="OS_PROJECT_ID",
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
    required=True,
    envvar="EGI_VO",
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
        "--mytoken",
        help="Mytoken string",
        envvar="FEDCLOUD_MYTOKEN",
        metavar="mytoken",
    )
    @optgroup.option(
        "--mytoken-server",
        help="Mytoken sever",
        envvar="FEDCLOUD_MYTOKEN_SERVER",
        default=DEFAULT_MYTOKEN_SERVER,
        show_default=True,
        metavar="mytoken-server",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        from fedcloudclient.checkin import get_access_token

        access_token = get_access_token(
            kwargs.pop("oidc_access_token"),
            kwargs.pop("oidc_agent_account"),
            kwargs.pop("mytoken"),
            kwargs.pop("mytoken_server"),
        )
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
        envvar="FEDCLOUD_LOCKER_TOKEN",
        metavar="locker_token",
    )
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
        "--mytoken",
        help="Mytoken string",
        envvar="FEDCLOUD_MYTOKEN",
        metavar="mytoken",
    )
    @optgroup.option(
        "--mytoken-server",
        help="Mytoken sever",
        envvar="FEDCLOUD_MYTOKEN_SERVER",
        default=DEFAULT_MYTOKEN_SERVER,
        show_default=True,
        metavar="mytoken-server",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        from fedcloudclient.checkin import get_access_token

        # If locker token is given, ignore OIDC token options
        locker_token = kwargs.pop("locker_token")
        if locker_token:
            kwargs.pop("oidc_access_token")
            kwargs.pop("oidc_agent_account")
            kwargs.pop("mytoken")
            kwargs.pop("mytoken_server")
            kwargs["access_token"] = None
            kwargs["locker_token"] = locker_token
            return func(*args, **kwargs)

        access_token = get_access_token(
            kwargs.pop("oidc_access_token"),
            kwargs.pop("oidc_agent_account"),
            kwargs.pop("mytoken"),
            kwargs.pop("mytoken_server"),
        )
        kwargs["access_token"] = access_token
        kwargs["locker_token"] = None
        return func(*args, **kwargs)

    return wrapper
