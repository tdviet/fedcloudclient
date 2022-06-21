"""
Implementation of "fedcloud secret" commands for accessing secret management service
"""
import base64
import json

import click
import hvac
import yaml

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from tabulate import tabulate

from fedcloudclient.checkin import get_checkin_id
from fedcloudclient.decorators import oidc_params

VAULT_ADDR = "https://vault.services.fedcloud.eu:8200"
VAULT_ROLE = "demo"
VAULT_MOUNT_POINT = "/secrets"
VAULT_SALT = b"e8d3af638e26ede70afc3b3755e7c093"


def secret_client(access_token, command, path, data):
    """
    Client function for accessing secrets
    :param path: path to secret
    :param access_token: access token for authentication
    :param command: the command to perform
    :param data: input data
    :return: Output data from the service
    """

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
        response = function_list[command](path=full_path, mount_point=VAULT_MOUNT_POINT)
    return response


def secret_params_to_dict(params):
    """
    Convert secret params "key=value" to dict {"key":"value"}
    :param params: input string in format "key=value"
    :return: dict {"key":"value"}
    """

    result = {}

    if len(params) == 0:
        raise click.UsageError(
            "Expecting 'key=value' arguments for secrets, None provided."
        )

    for param in params:
        try:
            key, value = param.split("=", 1)
        except ValueError:
            raise click.UsageError(
                f"Expecting 'key=value' arguments for secrets. '{param}' provided."
            )
        if value.startswith("@"):
            with open(value[1:]) as f:
                value = f.read()
        result[key] = value
    return result


def generate_derived_key(passphrase):
    """
    Generate derived encryption/decryption key from passphrase
    :param passphrase:
    :return: derived key
    """

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=VAULT_SALT,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def encrypt_data(encrypt_key, secrets):
    """
    Encrypt values in secrets using key
    :param encrypt_key: encryption key
    :param secrets: dict containing secrets
    :return: dict with encrypted values
    """

    derived_key = generate_derived_key(encrypt_key)
    fernet = Fernet(derived_key)
    for key in secrets:
        secrets[key] = fernet.encrypt(secrets[key].encode())
    return secrets


def decrypt_data(decrypt_key, secrets):
    """
    Decrypt values in secrets using key
    :param decrypt_key: decryption key
    :param secrets: dict containing encrypted secrets
    :return: dict with decrypted values
    """

    derived_key = generate_derived_key(decrypt_key)
    fernet = Fernet(derived_key)
    for key in secrets:
        secrets[key] = fernet.decrypt(secrets[key].encode()).decode()
    return secrets


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

    data = secret_client(access_token, "read_secret", short_path, None)
    if decrypt_key:
        data["data"] = decrypt_data(decrypt_key, data["data"])
    if not key:
        if output_format == "JSON":
            print(json.dumps(data["data"], indent=4))
        elif output_format == "YAML":
            print(yaml.dump(data["data"], sort_keys=False))
        else:
            print(tabulate(data["data"].items(), headers=["key", "value"]))
    else:
        if key in data["data"]:
            print(data["data"][key])
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

    data = secret_client(access_token, "list_secrets", short_path, None)
    print("\n".join(map(str, data["data"]["keys"])))


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
        secret_dict = encrypt_data(encrypt_key, secret_dict)
    secret_client(access_token, "put", short_path, secret_dict)
