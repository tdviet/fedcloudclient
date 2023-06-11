"""
Secret helper functions
"""
import base64
import json
import os
import sys

import yaml
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from tabulate import tabulate

from fedcloudclient.conf import CONF as CONF

VAULT_SALT = CONF.get("vault_salt")


def read_data_from_file(input_format: str, input_file: str):
    """
    Read data from file. Format may be text, yaml, json or auto-detect according to file extension
    :param input_format:
    :param input_file:
    :return:
    """

    if input_format is None or input_format == "auto-detect":
        if input_file.endswith(".json"):
            input_format = "JSON"
        else:
            # default format
            input_format = "YAML"

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
            data = {}
            if input_format == "YAML":
                data = yaml.safe_load(f)
            elif input_format == "JSON":
                data = json.load(f)
            return dict(data)

    except (ValueError, FileNotFoundError, yaml.YAMLError) as e:
        raise SystemExit(
            f"Error: Error when reading file {input_file}. Error message: {type(e).__name__}: {e}"
        )


def secret_params_to_dict(params: list, binary_file: bool = False):
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
            data = read_data_from_file("auto-detect", param[1:])
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


def generate_derived_key(salt: bytes, passphrase: str):
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


def encrypt_data(encrypt_key: str, secrets: dict):
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
        secrets[key] = fernet.encrypt(secrets[key].encode()).decode()
    secrets[VAULT_SALT] = base64.b64encode(salt)


def decrypt_data(decrypt_key: str, secrets: dict):
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


def print_secrets(output_file: str, output_format: str, secrets: dict):
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

    except (ValueError, FileNotFoundError, yaml.YAMLError) as e:
        raise SystemExit(
            f"Error: Error when writing file {output_file}. Error message: {type(e).__name__}: {e}"
        )


def print_value(output_file: str, binary_file: bool, value: str):
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
