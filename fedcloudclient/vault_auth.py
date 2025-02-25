"""
Class for managing Vault tokens
"""
import hvac
from hvac.exceptions import VaultError

from fedcloudclient.auth import OIDCToken
from fedcloudclient.conf import CONF as CONF
from fedcloudclient.exception import TokenError
from fedcloudclient.logger import LOG, log_and_raise


class VaultToken(OIDCToken):
    """
    Managing tokens for Vault
    """

    def __init__(self, access_token: str = None, vault_token: str = None):
        """
        Init Vault token
        """
        super().__init__(access_token)
        self.vault_token = vault_token
        self.auth_method = None
        self.vault_client = None

    def get_vault_client(self) -> hvac.Client:
        """
        Init client if needed and return the client
        """
        if self.vault_client:
            # client is initialized, just return it
            return self.vault_client

        # Create the client
        client = hvac.Client(url=CONF.get("vault_endpoint"))
        if self.vault_token:
            client.token = self.vault_token
            self.vault_client = client
            return client
        elif self.access_token:
            try:
                client.auth.jwt.jwt_login(role=CONF.get("vault_role"), jwt=self.access_token)
                self.vault_token = client.token
                self.vault_client = client
                return client
            except VaultError as exception:
                error_msg = f"Cannot login to Vault via access token: {exception}"
                log_and_raise(error_msg, TokenError)
        else:
            error_msg = "Token is not initialized"
            log_and_raise(error_msg, TokenError)

    def get_vault_token(self) -> str:
        """
        Return Vault token
        """
        if self.vault_token:
            return self.vault_token
        elif self.access_token:
            self.get_vault_client()
            return self.vault_token
        else:
            error_msg = "Vault token is not initialized"
            log_and_raise(error_msg, TokenError)

    def get_user_id(self) -> str:
        """
        Get user ID (from access token or vault token)
        """
        if self.access_token:
            return super().get_user_id()
        else:
            return self.get_vault_user_id()

    def get_vault_user_id(self) -> str:
        """
        Get Vault user ID from Vault token
        """
        response = {}
        try:
            client = self.get_vault_client()
            response = client.auth.token.lookup_self()
        except VaultError as exception:
            error_msg = f"Cannot get user information via Vault token: {exception}"
            log_and_raise(error_msg, TokenError)

        display_name = response["data"]["display_name"]
        LOG.debug(f"Vault token display_name: {display_name}")
        self.auth_method, self.user_id = display_name.split("-")
        return self.user_id

    def get_vault_auth_method(self) -> str:
        """
        Get authentication method creating the token
        """
        if self.auth_method:
            return self.auth_method
        else:
            self.get_vault_user_id()
            return self.auth_method

    def vault_command(self, command: str, path: str, data: dict, vo: str = None) -> dict:
        """
        Perform Vault kv command
        """

        client = self.get_vault_client()

        full_path = ""
        if vo:
            if self.get_vault_auth_method() == "oidc":
                full_path = "vos/" + vo + "/" + path
            else:
                log_and_raise(
                    "VO-shared folders are accessible only for token created by OIDC method via GUI",
                    TokenError,
                )
        else:
            full_path = "users/" + self.get_user_id() + "/" + path

        function_list = {
            "list": client.secrets.kv.v1.list_secrets,
            "get": client.secrets.kv.v1.read_secret,
            "delete": client.secrets.kv.v1.delete_secret,
        }
        mount_point = CONF.get("vault_mount_point")
        try:
            if command == "put":
                response = client.secrets.kv.v1.create_or_update_secret(
                    path=full_path,
                    mount_point=mount_point,
                    secret=data,
                )
            else:
                response = function_list[command](
                    path=full_path,
                    mount_point=mount_point,
                )
            return response

        except VaultError as e:
            error_msg = f"Error: Error when accessing secrets on server. Server response: {type(e).__name__}: {e}"
            log_and_raise(error_msg, TokenError)
