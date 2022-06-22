"""
Implementation of "fedcloud secret" commands for accessing secret management service
"""
import base64
import json
import os

import click
import hvac
import yaml

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from hvac.exceptions import VaultError
from tabulate import tabulate

from fedcloudclient.checkin import get_checkin_id
from fedcloudclient.decorators import oidc_params

VAULT_ADDR = "https://vault.services.fedcloud.eu:8200"
VAULT_ROLE = "demo"
VAULT_MOUNT_POINT = "/secrets"
VAULT_SALT = "fedcloud_salt"


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
        full_path = checkin_id + "/" + path
        function_list = {
            "list_secrets": client.secrets.kv.v1.list_secrets,
            "read_secret": client.secrets.kv.v1.read_secret,
            "delete_secret": client.secrets.kv.v1.read_secret,
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
        raise SystemExit(f"Error: Error when connecting to Vault server. {e}")


def secret_params_to_dict(params):
    """
    Convert secret params "key=value" to dict {"key":"value"}
    :param params: input string in format "key=value"
    :return: dict {"key":"value"}
    """

    result = {}

    if len(params) == 0:
        raise SystemExit(
            "Error: Expecting 'key=value' arguments for secrets, None provided."
        )

    for param in params:
        try:
            key, value = param.split("=", 1)
        except ValueError:
            raise SystemExit(
                f"Error: Expecting 'key=value' arguments for secrets. '{param}' provided."
            )
        if value.startswith("@"):
            try:
                with open(value[1:]) as f:
                    value = f.read()
            except (ValueError, FileNotFoundError) as e:
                raise SystemExit(
                    f"Error: Error when reading file {value[1:]}. Error message: {e}"
                )
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


def print_secrets(output_format, secrets):
    """
    Print secrets in different formats
    :param output_format:
    :param secrets:
    :return:
    """
    if output_format == "JSON":
        print(json.dumps(secrets, indent=4))
    elif output_format == "YAML":
        print(yaml.dump(secrets, sort_keys=False))
    else:
        print(tabulate(secrets.items(), headers=["key", "value"]))


@click.group()
def secret():
    """
    Commands for accessing secrets
    """


@secret.command()
@oidc_params
@click.option(
    "--output-format",
    "-f",
    required=False,
    type=click.Choice(["text", "YAML", "JSON"], case_sensitive=False),
)
@click.option("--decrypt-key", required=False)
@click.argument("short_path", metavar="[secret path]")
@click.argument("key", metavar="[key]", required=False)
def get(
    access_token,
    short_path,
    key,
    output_format,
    decrypt_key,
):
    """
    Get a secret from the path. If a key is given, print only the value of the key
    """

    response = secret_client(access_token, "read_secret", short_path, None)
    if decrypt_key:
        decrypt_data(decrypt_key, response["data"])
    if not key:
        print_secrets(output_format, response["data"])
    else:
        if key in response["data"]:
            print(response["data"][key])
        else:
            raise SystemExit(f"Error: {key} not found in {short_path}")


@secret.command("list")
@oidc_params
@click.argument("short_path", metavar="[secret path]", required=False, default="")
def list_(
    access_token,
    short_path,
):
    """
    List secrets in the path
    """

    response = secret_client(access_token, "list_secrets", short_path, None)
    print("\n".join(map(str, response["data"]["keys"])))


@secret.command()
@oidc_params
@click.argument("short_path", metavar="[secret path]")
@click.argument("secrets", nargs=-1, metavar="[key=value...]")
@click.option("--encrypt-key", required=False)
def put(
    access_token,
    short_path,
    secrets,
    encrypt_key,
):
    """
    Put secrets to the path. Secrets are provided in form key=value
    """

    secret_dict = secret_params_to_dict(secrets)
    if encrypt_key:
        encrypt_data(encrypt_key, secret_dict)
    secret_client(access_token, "put", short_path, secret_dict)


@secret.command()
@oidc_params
@click.argument("short_path", metavar="[secret path]")
def delete(
    access_token,
    short_path,
):
    """
    Delete secret in the path
    """

    secret_client(access_token, "delete_secret", short_path, None)
