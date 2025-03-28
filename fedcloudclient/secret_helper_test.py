"""
Testing secret helper functions
"""
import base64
import json
import os

from fedcloudclient.secret_helper import decrypt_data, encrypt_data, print_secrets, print_value, read_data_from_file

def save_read_binary_files():
    """
    Test save random binary data, read it again and compare
    """
    print("Testing read/write data from binary files")
    data = base64.b64encode(os.urandom(20)).decode()
    temp_file = "/tmp/test"
    print_value(output_file=temp_file, binary_file=True, value=data)
    read_data = read_data_from_file(input_format="binary", input_file=temp_file)

    print(f" Original : {data} \n from file: {read_data}")
    assert read_data == data


def save_read_dict():
    """
    Test saving dict in temp file and read it again
    """
    print("Testing read/write data from YAML/JSON files")

    data = {"key1": "value1", "key2": base64.b64encode(os.urandom(8)).decode()}
    temp_file = "/tmp/test"
    print_secrets(output_file=temp_file, output_format="JSON", secrets=data)
    save_data = read_data_from_file(input_format="JSON", input_file=temp_file)

    print(f" Original : {json.dumps(data)} \n from file: {json.dumps(save_data)}")

    assert data == save_data
    print_secrets(output_file=temp_file, output_format="YAML", secrets=data)
    save_data = read_data_from_file(input_format="YAML", input_file=temp_file)

    print(f" Original : {json.dumps(data)} \n from file: {json.dumps(save_data)}")

    assert data == save_data


def encrypt_decrypt():
    """
    Testing encrypt/decrypt
    """
    print("Testing encrypt/decrypt")
    secret = base64.b64encode(os.urandom(20)).decode()
    passphrase = base64.b64encode(os.urandom(8)).decode()
    data = {"key": secret}
    encrypt_data(encrypt_key=passphrase, secrets=data)
    print(f" Original : {secret} \n encrypted: {data['key']}")
    decrypt_data(decrypt_key=passphrase, secrets=data)
    print(f" Original : {secret} \n decrypted: {data['key']}")
    assert secret == data["key"]


if __name__ == "__main__":

    print("Test help function")

    save_read_binary_files()
    save_read_dict()
    encrypt_decrypt()
