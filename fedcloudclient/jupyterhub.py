"""
Implementation of "fedcloud jupyterhub" for communicating with JupyterHub instances
in OpenStack CLI like fashion
"""

import json
from functools import wraps

import click

from fedcloudclient.jupyterhub_lib import (
    get_servers,
    get_user,
    start_server,
    stop_server,
    add_token,
    list_tokens,
    get_token,
    delete_token,
    exec_command,
    upload_file,
    add_path,
    get_path,
    delete_path,
    add_shared_access,
    remove_shared_access,
    list_shared_access,
)


# Main function calling lib functions
def jupyterhub_full(callback_func, **kwargs):
    """
    Calls provided callback func
    """
    response_output = callback_func(**kwargs)

    if response_output is not None:
        if "output" in kwargs and kwargs["output"] == "text":
            print(response_output, end="")
        else:
            print(json.dumps(response_output, indent=4))


# Decorator for required Jupyterhub hub param
def common_hub_params(func):
    """
    Common Hub params func wrapper
    """

    @click.option(
        "--hub-api-endpoint",
        "-e",
        required=True,
        help="JupyterHub API endpoint",
    )
    @click.option(
        "--token",
        "-t",
        required=True,
        help="JupyterHub API token",
    )
    @click.option(
        "--user",
        help="ID of Jupyterhub user, if not specified token's owner ID is used",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return wrapper


# Decorator for server name param
def server_name(func):
    """
    Server name param func wrapper
    """

    @click.option(
        "--server",
        required=True,
        help='Name of the Jupyter server. For a nameless server use: --server ""',
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return wrapper


# Decorator for include_stopped_servers param
def include_stopped_servers(func):
    """
    Include stopped server param func wrapper
    """

    @click.option(
        "--include-stopped-servers",
        is_flag=True,
        flag_value=True,
        default=False,
        help="Include stopped servers",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return wrapper


# Decorator for token_id param
def api_token_id(func):
    """
    Api token param func wrapper
    """

    @click.option(
        "--api-token-id",
        required=True,
        help="API token ID",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return wrapper


@click.group()
def jupyterhub():
    """
    Communicate with Jupyterhub
    """


@jupyterhub.group()
def user():
    """
    JupyterHub user subcommand
    """


@user.command("show")
@include_stopped_servers
@common_hub_params
def show_user(**kwargs):
    """
    Get user details
    """
    jupyterhub_full(get_user, **kwargs)


@jupyterhub.group()
def server():
    """
    JupyterHub server subcommand
    """


@server.command("list")
@include_stopped_servers
@common_hub_params
def list_servers(**kwargs):
    """
    JupyterHub server subcommand
    """
    jupyterhub_full(get_servers, **kwargs)


@server.command("start")
@click.option(
    "--options",
    help="""
    User options JSON to be passed to the server, e.g. different image, 
    spawner profile, etc., must valid json!!""",
)
@common_hub_params
@server_name
def start_user_server(**kwargs):
    """
    Start named server
    """
    jupyterhub_full(start_server, **kwargs)


@server.command("stop")
@common_hub_params
@server_name
def stop_user_server(**kwargs):
    """
    Stop named server
    """
    jupyterhub_full(stop_server, **kwargs)


@jupyterhub.group()
def token():
    """
    JupyterHub token subcommand
    """


@token.command("add")
@click.option(
    "--expiration",
    type=int,
    help="API token duration before it expires in seconds, 0 or ommitting means no expiration",
)
@click.option(
    "--note",
    help="API token description note for a new token",
)
@click.option(
    "--role",
    "-r",
    multiple=True,
    help="""
    Scopes from a role for new token, can be specified multiple times, e.g. -r user -r admin
    Cannot be specified together with --scope options""",
)
@click.option(
    "--scope",
    "-s",
    multiple=True,
    help="""
    Scope for new token, can be specified multiple times, e.g. -s access:servers -s inherit
    Cannot be specified together with --role options""",
)
@common_hub_params
def generate_api_token(**kwargs):
    """
    Generate API token
    """
    jupyterhub_full(add_token, **kwargs)


@token.command("list")
@common_hub_params
def list_api_tokens(**kwargs):
    """
    Lists existing API token
    """
    jupyterhub_full(list_tokens, **kwargs)


@token.command("show")
@common_hub_params
@api_token_id
def show_api_token(**kwargs):
    """
    Shows existing API token
    """
    jupyterhub_full(get_token, **kwargs)


@token.command("rm")
@common_hub_params
@api_token_id
def delete_api_token(**kwargs):
    """
    Deletes existing API token
    """
    jupyterhub_full(delete_token, **kwargs)


@jupyterhub.group()
def sharing():
    """
    JupyterHub user share-access subcommand
    """


@sharing.command("add")
@click.option(
    "--scope",
    "-s",
    multiple=True,
    help="""
    Scope for granted access, can be specified multiple times, e.g. -s access:servers -s inherit
    If no scopes are specified, access:servers!server=:username/:servername is going to be used.
    """,
)
@click.option(
    "--grant-to-user",
    help="""ID of user to grant a shared access to the specified server, only one at the time,
    cannot be specified when --grant-to-group is used""",
)
@click.option(
    "--grant-to-group",
    help="""ID of group to grant a shared access to the specified server, only one at the time,
    cannot be specified when --grant-to-user is used""",
)
@server_name
@common_hub_params
def add_sharing(**kwargs):
    """
    Add server share
    """
    jupyterhub_full(add_shared_access, **kwargs)


@sharing.command("rm")
@click.option(
    "--all",
    is_flag=True,
    flag_value=True,
    default=False,
    help="If specified, all shared access of all invitied users will be removed, regardless of specified scopes",
)
@click.option(
    "--remove-from-user",
    help="ID of user to remove a shared access from to the specified server, only one at the time",
)
@click.option(
    "--remove-from-group",
    help="ID of group to grant a shared access from to the specified server, only one at the time",
)
@click.option(
    "--scope",
    "-s",
    multiple=True,
    help="""
    Scopes, can be specified multiple times, e.g. -s access:servers -s inherit
    If no scopes are specified, all scopes will be removed""",
)
@server_name
@common_hub_params
def remove_sharing(**kwargs):
    """
    Remove server share
    """
    jupyterhub_full(remove_shared_access, **kwargs)


@sharing.command("list")
@server_name
@common_hub_params
def list_sharing(**kwargs):
    """
    List server shares
    """
    jupyterhub_full(list_shared_access, **kwargs)


@jupyterhub.group()
def path():
    """
    Jupyterhub path subcommand
    """


@path.command("show")
@click.option(
    "--path",
    "-p",
    required=True,
    type=click.Path(readable=False),
    help="Path to the file or directory to show",
)
@click.option(
    "--show-content",
    is_flag=True,
    flag_value=True,
    default=False,
    help="If specified, path contents are displayed",
)
@server_name
@common_hub_params
def path_show(**kwargs):
    """
    Lists file/directory contents on specified path
    """
    jupyterhub_full(get_path, **kwargs)


@path.command("add")
@click.option(
    "--destination",
    "-d",
    required=True,
    type=click.Path(
        readable=False,
    ),
    help="Path where new file/directory will be created on the running server",
)
@click.option(
    "--name",
    "-n",
    type=click.Path(
        readable=False,
    ),
    help="Name of the new file/directory to create, if not specified, default is used",
)
@click.option(
    "--copy-from",
    type=click.Path(
        readable=False,
    ),
    help="Path on the server to copy content to the path on the running server",
)
@click.option(
    "--type",
    required=True,
    type=click.Choice(["file", "directory"]),
    help="Type of the item to create",
)
@server_name
@common_hub_params
def path_add(**kwargs):
    """
    Add file or directory at the specified path on running server
    """
    jupyterhub_full(add_path, **kwargs)


@path.command("rm")
@click.option(
    "--path",
    "-p",
    required=True,
    type=click.Path(
        readable=False,
    ),
    help="Path to file to delete",
)
@server_name
@common_hub_params
def path_remove(**kwargs):
    """
    Remove file or directory at the specified path on running server,
    directory must be empty
    """
    jupyterhub_full(delete_path, **kwargs)


@jupyterhub.group()
def file():
    """
    Jupyterhub file subcommand
    """


@file.command("add")
@click.option(
    "--file",
    "-f",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the file to be uploaded on the running server",
)
@click.option(
    "--destination",
    "-d",
    required=True,
    type=click.Path(readable=False),
    help="""Path to the file to be uploaded on the running server.
    Important!, the root dir is the root dir used by Jupyter server process!!,
    If the destination is file, it will be overwritten""",
)
@server_name
@common_hub_params
def file_add(**kwargs):
    """
    Uploads and/or overwrites file at the specified path on running server
    """
    jupyterhub_full(upload_file, **kwargs)


@jupyterhub.command("exec")
@click.option(
    "--output",
    "-o",
    default="text",
    type=click.Choice(["json", "text"]),
    help="Type out the output to provide",
)
@click.argument("command", nargs=-1)
@server_name
@common_hub_params
def execute(**kwargs):
    """
    JupyterHub exec subcommand
    """
    jupyterhub_full(exec_command, **kwargs)
