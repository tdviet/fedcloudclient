"""
Testing vault_auth.py
"""
import os

import fedcloudclient.vault_auth as vault
from fedcloudclient.exception import TokenError


def test_vault_login(mytoken: str):
    """
    test vault login with mytoken
    """

    token = vault.VaultToken()
    token.get_token_from_mytoken(mytoken)
    vault_client = token.get_vault_client()

    assert vault_client


def test_user_id_from_vault_token(vault_token: str, user_id: str):
    """
    Test user id from OIDC vault token
    """
    token = vault.VaultToken(vault_token=vault_token)
    vault_id = None
    try:
        vault_id = token.get_user_id()
    except TokenError:
        print("Please check validity of your OIDC Vault token")
    assert vault_id == user_id


def test_get_personal_secret(vault_token: str):
    """
    Test getting personal secrets
    """
    token = vault.VaultToken(vault_token=vault_token)
    response = token.vault_command(command="get", path="test", data={}, vo=None)
    assert response["data"]["test"] == "test"


def test_get_vo_secret(vault_token: str, vo_secret: str):
    """
    Test getting VO-shared secrets
    """
    token = vault.VaultToken(vault_token=vault_token)
    response = token.vault_command(command="get", path="test", data={}, vo=vo_secret)
    assert response["data"]["test"] == "test"


if __name__ == "__main__":
    #Before testing, setup testing environment with
    #export  FEDCLOUD_MYTOKEN=<mytoken>
    #export  FEDCLOUD_ID=<your Checkin ID>
    #export  FEDCLOUD_VAULT_TOKEN=<Vault token exported from GUI>

    os_mytoken = os.environ["FEDCLOUD_MYTOKEN"]
    os_user_id = os.environ["FEDCLOUD_ID"]
    oidc_vault_token = os.environ["FEDCLOUD_VAULT_TOKEN"]
    test_vault_login(os_mytoken)
    test_user_id_from_vault_token(oidc_vault_token, os_user_id)
    test_get_personal_secret(oidc_vault_token)
    test_get_vo_secret(oidc_vault_token, "vo.access.egi.eu")
