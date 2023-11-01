"""
Implementation of "fedcloud secret" commands for accessing secret management service
"""
import base64
import json
import os
import sys

import click
import hvac
import requests
import yaml
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from hvac.exceptions import VaultError
from tabulate import tabulate
from yaml import YAMLError

from fedcloudclient.checkin import get_checkin_id
from fedcloudclient.decorators import (
    oidc_params,
    secret_output_params,
    secret_token_params,
)

VAULT_ADDR = "https://vault.services.fedcloud.eu:8200"
VAULT_ROLE = ""
VAULT_MOUNT_POINT = "/secrets/"
VAULT_SALT = "fedcloud_salt"
VAULT_LOCKER_MOUNT_POINT = "/v1/cubbyhole/"


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


def read_data_from_file(input_format, input_file):
    """
    Read data from file. Format may be text, yaml, json or auto-detect according to file extension
    :param input_format:
    :param input_file:
    :return:
    """

    if input_format is None or input_format == "auto-detect":
        if input_file.endswith(".json"):
            input_format = "json"
        else:
            # default format
            input_format = "yaml"

    try:

        # read text/binary files to strings
        if input_format == "binary":
            with open(input_file, "rb") if input_file else sys.stdin.buffer as f:
                return base64.b64encode(f.read()).decode()
        if input_format == "text":
            with open(input_file, "r") if input_file else sys.stdin as f:
                return f.read()

        # reading YAML or JSON to dict
        with open(input_file) if input_file else sys.stdin as f:
            if input_format == "yaml":
                data = yaml.safe_load(f)
            elif input_format == "json":
                data = json.load(f)
            return dict(data)

    except (ValueError, FileNotFoundError, YAMLError) as e:
        raise SystemExit(
            f"Error: Error when reading file {input_file}. Error message: {type(e).__name__}: {e}"
        )


def secret_params_to_dict(params, binary_file=False):
    """
    Convert secret params "key=value" to dict {"key":"value"}
    :param binary_file: if reading files as binary
    :param params: input string in format "key=value"
    :return: dict {"key":"value"}
    """

    result = {}

    if len(params) == 0:
        raise SystemExit(
            "Error: Expecting 'key=value' arguments for secrets, None provided."
        )

    for param in params:
        if param.startswith("@") or param == "-":
            data = read_data_from_file(None, param[1:])
            result.update(data)
        else:
            try:
                key, value = param.split("=", 1)
            except ValueError:
                raise SystemExit(
                    f"Error: Expecting 'key=value' arguments for secrets. '{param}' provided."
                )
            if value.startswith("@") or value == "-":
                if binary_file:
                    value = read_data_from_file("binary", value[1:])
                else:
                    value = read_data_from_file("text", value[1:])
            result[key] = value

    return result


def generate_derived_key(salt, passphrase):
    """
    Generate derived encryption/decryption key from salted passphrase
    :param salt:
    :param passphrase:
    :return: derived key
    """

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.b64encode(kdf.derive(passphrase.encode()))


def encrypt_data(encrypt_key, secrets):
    """
    Encrypt values in secrets using key
    :param encrypt_key: encryption key
    :param secrets: dict containing secrets
    :return: dict with encrypted values
    """
    salt = os.urandom(16)
    derived_key = generate_derived_key(salt, encrypt_key)
    fernet = Fernet(derived_key)
    for key in secrets:
        secrets[key] = fernet.encrypt(secrets[key].encode())
    secrets[VAULT_SALT] = base64.b64encode(salt)


def decrypt_data(decrypt_key, secrets):
    """
    Decrypt values in secrets using key
    :param decrypt_key: decryption key
    :param secrets: dict containing encrypted secrets
    :return: dict with decrypted values
    """
    try:
        salt = base64.b64decode(secrets.pop(VAULT_SALT))
        derived_key = generate_derived_key(salt, decrypt_key)
        fernet = Fernet(derived_key)
        for key in secrets:
            secrets[key] = fernet.decrypt(secrets[key].encode()).decode()
    except InvalidToken as e:
        raise SystemExit(f"Error: Error during decryption. {e}")


def print_secrets(output_file, output_format, secrets):
    """
    Print secrets in different formats
    :param output_file:
    :param output_format:
    :param secrets:
    :return:
    """

    try:
        with open(output_file, "wt") if output_file else sys.stdout as f:
            if output_format == "JSON":
                json.dump(secrets, f, indent=4)
            elif output_format == "YAML":
                yaml.dump(secrets, f, sort_keys=False)
            else:
                print(tabulate(secrets.items(), headers=["key", "value"]), file=f)

    except (ValueError, FileNotFoundError, YAMLError) as e:
        raise SystemExit(
            f"Error: Error when writing file {output_file}. Error message: {type(e).__name__}: {e}"
        )


def print_value(output_file, binary_file, value):
    """
    Print secrets in different formats
    :param output_file:
    :param binary_file:
    :param value:
    :return:
    """

    try:
        if binary_file:
            with open(output_file, "wb") if output_file else sys.stdout.buffer as f:
                f.write(base64.b64decode(value.encode()))
        else:
            with open(output_file, "wt") if output_file else sys.stdout as f:
                f.write(value)

    except (ValueError, FileNotFoundError, TypeError) as e:
        raise SystemExit(
            f"Error: Error when writing file {output_file}. Error message: {type(e).__name__}: {e}"
        )


@click.group()
def secret():
    """
    Commands for accessing secret objects
    """


@secret.command()
@secret_token_params
@secret_output_params
@click.argument("short_path", metavar="[secret path]")
@click.argument("key", metavar="[key]", required=False)
@click.option(
    "--decrypt-key",
    "-d",
    metavar="[key]",
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
    metavar="[filename]",
    required=False,
    help="Name of output file",
)
def get(
    access_token,
    locker_token,
    short_path,
    key,
    output_format,
    decrypt_key,
    binary_file,
    output_file,
):
    """
    Get the secret object in the path. If a key is given, print only the value of the key
    """
    if locker_token:
        response = locker_client(locker_token, "read_secret", short_path, None)
    else:
        response = secret_client(access_token, "read_secret", short_path, None)
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
    access_token,
    locker_token,
    short_path,
):
    """
    List secret objects in the path
    """
    if locker_token:
        response = locker_client(locker_token, "list_secrets", short_path, None)
    else:
        response = secret_client(access_token, "list_secrets", short_path, None)
    print("\n".join(map(str, response["data"]["keys"])))


@secret.command()
@secret_token_params
@click.argument("short_path", metavar="[secret path]")
@click.argument("secrets", nargs=-1, metavar="[key=value...]")
@click.option(
    "--encrypt-key",
    "-e",
    metavar="[key]",
    help="Encryption key or passphrase",
)
@click.option(
    "--binary-file",
    "-b",
    is_flag=True,
    help="True for reading secrets from binary files",
)
def put(
    access_token,
    locker_token,
    short_path,
    secrets,
    encrypt_key,
    binary_file,
):
    """
    Put a secret object to the path. Secrets are provided in form key=value
    """

    secret_dict = secret_params_to_dict(secrets, binary_file)
    if encrypt_key:
        encrypt_data(encrypt_key, secret_dict)
    if locker_token:
        locker_client(locker_token, "put", short_path, secret_dict)
    else:
        secret_client(access_token, "put", short_path, secret_dict)


@secret.command()
@secret_token_params
@click.argument("short_path", metavar="[secret path]")
def delete(
    access_token,
    locker_token,
    short_path,
):
    """
    Delete the secret object in the path
    """
    if locker_token:
        locker_client(locker_token, "delete_secret", short_path, None)
    else:
        secret_client(access_token, "delete_secret", short_path, None)


@secret.group()
def locker():
    """
    Commands for creating and accessing locker objects
    """


@locker.command()
@oidc_params
@secret_output_params
@click.option("--ttl", default="24h", help="Time-to-live for the new locker")
@click.option("--num-uses", default=10, help="Max number of uses")
@click.option("--verbose", is_flag=True, help="Print token details")
def create(access_token, ttl, num_uses, output_format, verbose):
    """
    Create a locker and return the locker token
    """
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
            print_secrets(None, output_format, locker_token["auth"])
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
        print_secrets(None, output_format, locker_info["data"])
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
