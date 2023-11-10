"""
Implementation of "fedcloud secret" commands for accessing secret management service
"""
from urllib.error import HTTPError

import click
import hvac
import requests
from hvac.exceptions import VaultError

from fedcloudclient.checkin import get_checkin_id
from fedcloudclient.conf import CONF as CONF
from fedcloudclient.decorators import (
    oidc_params,
    secret_output_params,
    secret_token_params,
)
from fedcloudclient.logger import LOG as LOG
from fedcloudclient.secret_helper import decrypt_data, encrypt_data, print_secrets, print_value, secret_params_to_dict
from fedcloudclient.vault_auth import VaultToken

VAULT_ADDR = CONF.get("vault_endpoint")
VAULT_ROLE = CONF.get("vault_role")
VAULT_MOUNT_POINT = CONF.get("vault_mount_point")
VAULT_SALT = CONF.get("vault_salt")
VAULT_LOCKER_MOUNT_POINT = CONF.get("vault_locker_mount_point")


def secret_client(access_token, command, path, data):
    """
    Client function for accessing secrets
    :param path: path to secret
    :param access_token: access token for authentication
    :param command: the command to perform
    :param data: input data
    :return: Output data from the service
    """

    try:
        client = hvac.Client(url=VAULT_ADDR)
        client.auth.jwt.jwt_login(role=VAULT_ROLE, jwt=access_token)
        checkin_id = get_checkin_id(access_token)
        full_path = "users/" + checkin_id + "/" + path
        function_list = {
            "list_secrets": client.secrets.kv.v1.list_secrets,
            "read_secret": client.secrets.kv.v1.read_secret,
            "delete_secret": client.secrets.kv.v1.delete_secret,
        }
        if command == "put":
            response = client.secrets.kv.v1.create_or_update_secret(
                path=full_path,
                mount_point=VAULT_MOUNT_POINT,
                secret=data,
            )
        else:
            response = function_list[command](
                path=full_path,
                mount_point=VAULT_MOUNT_POINT,
            )
        return response
    except VaultError as e:
        raise SystemExit(
            f"Error: Error when accessing secrets on server. Server response: {type(e).__name__}: {e}"
        )


def locker_client(locker_token, command, path, data):
    """
    Client function for accessing secrets
    :param path: path to secret
    :param command: the command to perform
    :param data: input data
    :param locker_token: locker token
    :return: Output data from the service
    """

    try:
        headers = {"X-Vault-Token": locker_token}
        url = VAULT_ADDR + VAULT_LOCKER_MOUNT_POINT + path
        if command == "list_secrets":
            response = requests.get(url, headers=headers, params={"list": "true"})
        elif command == "read_secret":
            response = requests.get(url, headers=headers)
        elif command == "delete_secret":
            response = requests.delete(url, headers=headers)
        elif command == "put":
            response = requests.post(url, headers=headers, data=data)
        else:
            raise SystemExit(f"Invalid command {command}")
        response.raise_for_status()
        if command in ["list_secrets", "read_secret"]:
            response_json = response.json()
            return dict(response_json)
        else:
            return None
    except requests.exceptions.HTTPError as exception:
        raise SystemExit(
            f"Error: Error when accessing secrets on server. Server response: {type(exception).__name__}: {exception}"
        )


@click.group()
def secret():
    """
    Commands for accessing secret objects
    """


@secret.command()
@secret_token_params
@secret_output_params
@click.argument("short_path", metavar="[secret_path]")
@click.argument("key", metavar="[key]", required=False)
@click.option(
    "--decrypt-key",
    "-d",
    metavar="passphrase",
    required=False,
    help="Decryption key or passphrase",
)
@click.option(
    "--binary-file",
    "-b",
    required=False,
    is_flag=True,
    help="True for writing secrets to binary files",
)
@click.option(
    "--output-file",
    "-o",
    metavar="filename",
    required=False,
    help="Name of output file",
)
def get(
        token: VaultToken,
        short_path: str,
        key: str,
        output_format: str,
        decrypt_key: str,
        binary_file: bool,
        output_file: str,
):
    """
    Get the secret object in the path. If a key is given, print only the value of the key
    """

    response = token.vault_command(command="get", path=short_path, data={})
    if decrypt_key:
        decrypt_data(decrypt_key, response["data"])
    if not key:
        print_secrets(output_file, output_format, response["data"])
    else:
        if key in response["data"]:
            print_value(output_file, binary_file, response["data"][key])
        else:
            raise SystemExit(f"Error: {key} not found in {short_path}")


@secret.command("list")
@secret_token_params
@click.argument("short_path", metavar="[secret path]", required=False, default="")
def list_(
        token: VaultToken,
        short_path: str,
):
    """
    List secret objects in the path
    """
    try:
        response = token.vault_command(command="list", path=short_path, data={})
        print("\n".join(map(str, response["data"]["keys"])))
    except HTTPError as e:
        if e.code == 404:
            pass
        else:
            print(f"HTTPError occurred. Error code: {e.code}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


@secret.command()
@secret_token_params
@click.argument("short_path", metavar="[secret path]")
@click.argument("secrets", nargs=-1, metavar="[key=value...]")
@click.option(
    "--encrypt-key",
    "-e",
    metavar="passphrase",
    help="Encryption key or passphrase",
)
@click.option(
    "--binary-file",
    "-b",
    is_flag=True,
    help="True for reading secrets from binary files",
)
def put(
        token: VaultToken,
        short_path: str,
        secrets: list,
        encrypt_key: str,
        binary_file: bool,
):
    """
    Put a secret object to the path. Secrets are provided in form key=value
    """

    secret_dict = secret_params_to_dict(secrets, binary_file)
    if encrypt_key:
        encrypt_data(encrypt_key, secret_dict)
    token.vault_command(command="put", path=short_path, data=secret_dict)


@secret.command()
@secret_token_params
@click.argument("short_path", metavar="[secret path]")
def delete(
        token: VaultToken,
        short_path,
):
    """
    Delete the secret object in the path
    """
    token.vault_command(command="delete", path=short_path, data={})


@secret.group()
def locker():
    """
    Commands for creating and accessing locker objects
    """


@locker.command()
@oidc_params
@secret_output_params
@click.option("--ttl", default="24h", help="Locker's Time-to-live", show_default=True)
@click.option("--num-uses", default=10, help="Max number of uses", show_default=True)
@click.option("--verbose", is_flag=True, help="Print token details")
def create(access_token, ttl, num_uses, output_format, verbose):
    """
    Create a locker and return the locker token
    """
    LOG.debug("Creating a new locker")
    try:
        client = hvac.Client(url=VAULT_ADDR)
        client.auth.jwt.jwt_login(role=VAULT_ROLE, jwt=access_token)
        client.auth.token.renew_self(increment=ttl)
        locker_token = client.auth.token.create(
            policies=["default"], ttl=ttl, num_uses=num_uses, renewable=False
        )
        if not verbose:
            print(locker_token["auth"]["client_token"])
        else:
            print_secrets("", output_format, locker_token["auth"])
    except VaultError as e:
        raise SystemExit(
            f"Error: Error when accessing secrets on server. Server response: {type(e).__name__}: {e}"
        )


@locker.command()
@secret_output_params
@click.argument(
    "locker_token", metavar="[locker_token]", envvar="FEDCLOUD_LOCKER_TOKEN"
)
def check(locker_token, output_format):
    """
    Check status of locker token
    """

    try:
        client = hvac.Client(url=VAULT_ADDR)
        client.token = locker_token
        locker_info = client.auth.token.lookup_self()
        print_secrets("", output_format, locker_info["data"])
    except VaultError as e:
        raise SystemExit(
            f"Error: Error when accessing secrets on server. Server response: {type(e).__name__}: {e}"
        )


@locker.command()
@click.argument(
    "locker_token", metavar="[locker_token]", envvar="FEDCLOUD_LOCKER_TOKEN"
)
def revoke(locker_token):
    """
    Revoke the locker token and delete all data in the locker
    """
    try:
        client = hvac.Client(url=VAULT_ADDR)
        client.token = locker_token
        client.auth.token.revoke_self()
    except VaultError as e:
        raise SystemExit(
            f"Error: Error when accessing secrets on server. Server response: {type(e).__name__}: {e}"
        )
