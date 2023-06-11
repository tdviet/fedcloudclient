"""
Class for managing Vault locker tokens
"""
import requests

from fedcloudclient.conf import CONF
from fedcloudclient.exception import ConfigError, ServiceError, TokenError
from fedcloudclient.logger import log_and_raise
from fedcloudclient.vault_auth import VaultToken


class LockerToken(VaultToken):
    """
    Managing Vault locker token
    """

    def __init__(self, locker_token: str):
        """
        Init Locker token
        :param locker_token:
        """
        if locker_token:
            super().__init__(vault_token=locker_token)
        else:
            log_and_raise("Locker token cannot be empty", TokenError)

    def get_user_id(self):
        """
        User ID is not available for locker token
        :return:
        """
        log_and_raise("User ID is not available for locker token", TokenError)

    def get_vault_user_id(self):
        """
        Get Vault user ID from Vault token
        :return:
        """
        log_and_raise("User ID is not available for locker token", TokenError)

    def get_vault_auth_method(self):
        """
        Get Vault user ID from Vault token
        :return:
        """
        log_and_raise("Auth method is not available for locker token", TokenError)

    def vault_command(self, command: str, path: str, data: dict, vo: str = None):
        """
        Perform Vault command
        :param command:
        :param path:
        :param data:
        :param vo:
        :return:
        """
        if vo:
            log_and_raise("VO-shared is not supported by locker token", TokenError)

        try:
            headers = {"X-Vault-Token": self.vault_token}
            url = CONF.get("vault_endpoint") + CONF.get("vault_locker_mount_point") + path
            if command == "list":
                response = requests.get(url, headers=headers, params={"list": "true"})
            elif command == "get":
                response = requests.get(url, headers=headers)
            elif command == "delete":
                response = requests.delete(url, headers=headers)
            elif command == "put":
                response = requests.post(url, headers=headers, data=data)
            else:
                log_and_raise(f"Invalid command {command}", ConfigError)

            response.raise_for_status()
            if command in ["list", "get"]:
                response_json = response.json()
                return dict(response_json)
            else:
                return None
        except requests.exceptions.HTTPError as exception:
            error_msg = f"Error: Error when accessing secrets on server. Server response: {type(exception).__name__}: {exception}"
            log_and_raise(error_msg, ServiceError)
