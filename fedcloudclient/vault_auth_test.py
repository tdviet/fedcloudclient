"""
Testing vault_auth.py
"""
import os
import pytest
import fedcloudclient.vault_auth as vault
from fedcloudclient.exception import TokenError


@pytest.fixture
def mytoken():
    token = os.environ.get("FEDCLOUD_MYTOKEN", "FEDCLOUD_MYTOKEN_DEFAULT")
    return token


@pytest.fixture
def vault_token():
    token = os.environ.get("FEDCLOUD_VAULT_TOKEN", "FEDCLOUD_VAULT_TOKEN_DEFAULT")
    return token


@pytest.fixture
def user_id():
    token = os.environ.get("FEDCLOUD_ID", "FEDCLOUD_ID_DEFAULT")
    return token


@pytest.fixture
def vo_secret():
    return "vo.access.egi.eu"


def test_vault_login(mocker, mytoken: str):
    """
    test vault login with mytoken
    """

    # Mock
    mocker.patch("fedcloudclient.vault_auth.VaultToken.get_token_from_mytoken",
        return_value = "token")
    mocker.patch("fedcloudclient.vault_auth.VaultToken.get_vault_client",
        return_value = "client"
    )

    token = vault.VaultToken()
    token.get_token_from_mytoken(mytoken)
    vault_client = token.get_vault_client()

    assert vault_client


def test_user_id_from_vault_token(mocker, vault_token: str, user_id: str):
    """
    Test user id from OIDC vault token
    """

    # Mock get_user_id to return the expected user_id
    mocker.patch("fedcloudclient.vault_auth.VaultToken.get_user_id",
        return_value = user_id)

    token = vault.VaultToken(vault_token=vault_token)
    vault_id = token.get_user_id()

    assert vault_id == user_id


def test_get_personal_secret(mocker, vault_token: str):
    """
    Test getting personal secrets
    """

    # Mock vault_command for personal secrets
    mocker.patch("fedcloudclient.vault_auth.VaultToken.vault_command",
        return_value = {"data": {"test": "test"}})

    token = vault.VaultToken(vault_token=vault_token)
    response = token.vault_command(command="get", path="test", data={}, vo=None)

    assert response["data"]["test"] == "test"


def test_get_vo_secret(mocker, vault_token: str, vo_secret: str):
    """
    Test getting VO-shared secrets
    """

    # Mock vault_command for VO-shared secrets
    mocker.patch("fedcloudclient.vault_auth.VaultToken.vault_command",
        return_value = {"data": {"test": "test"}})

    token = vault.VaultToken(vault_token=vault_token)
    response = token.vault_command(command="get", path="test", data={}, vo=vo_secret)

    assert response["data"]["test"] == "test"
