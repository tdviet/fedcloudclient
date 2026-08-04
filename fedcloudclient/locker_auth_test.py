"""
Testing vault_auth.py
"""
import os
import pytest
import fedcloudclient.locker_auth as locker


@pytest.fixture
def locker_token():
    token = os.environ.get("FEDCLOUD_LOCKER_TOKEN", "FEDCLOUD_LOCKER_TOKEN_DEFAULT")
    return token


def test_get_locker_secret(mocker, locker_token: str):
    """
    Test getting VO-shared secrets
    """

    # Mock the vault_command method
    mocker.patch(
        "fedcloudclient.locker_auth.LockerToken.vault_command",
        return_value={"data": {"test": "test"}}
    )

    token = locker.LockerToken(locker_token=locker_token)
    response = token.vault_command(command="read_secret", path="test", data={}, vo=None)

    assert response["data"]["test"] == "test"
