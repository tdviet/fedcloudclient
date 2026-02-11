"""
Testing vault_auth.py
"""
import os

import fedcloudclient.locker_auth as locker


def test_get_locker_secret(locker_token: str):
    """
    Test getting VO-shared secrets
    """
    token = locker.LockerToken(locker_token=locker_token)
    response = token.vault_command(command="read_secret", path="test", data={}, vo=None)
    assert response["data"]["test"] == "test"


def test_main():
    locker_token_main = os.environ.get("FEDCLOUD_LOCKER_TOKEN", "DEFAULT_TOKEN")
    test_get_locker_secret(locker_token_main)


if __name__ == "__main__":
    test_main()
