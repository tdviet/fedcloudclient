"""
Testing unit for auth.py
"""
import os
print(f"Start of auth_test")

import fedcloudclient.auth as auth



def get_token_from_mytoken_decode_verify(mytoken: str, user_id: str):
    """
    Get access token from mytoken server, decode, get user ID and verify
    :return: 
    """

    token = auth.OIDCToken()
    token.get_token_from_mytoken(mytoken)
    token_id = token.get_user_id()
    assert token_id == user_id


if __name__ == "__main__":
    print(f"Start of main auth_test")
    mytoken = os.environ["FEDCLOUD_MYTOKEN"]
    user_id = os.environ["FEDCLOUD_ID"]
    get_token_from_mytoken_decode_verify(mytoken, user_id)
