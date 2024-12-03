"""
Testing unit for auth.py
"""
import os
print(f"Start of auth_test")

import fedcloudclient.auth as auth
from fedcloudclient.conf import CONF as CONF


def get_token_from_mytoken_decode_verify(mytoken: str, user_id: str):
    """
    Get access token from mytoken server, decode, get user ID and verify
    :return: 
    """

    token = auth.OIDCToken()
    token.multiple_token(mytoken,user_id, None)
    token_id = token.get_user_id()
    token_test=token.access_token
    print("End of: def get_token_from_mytoken_decode_verify")

    pass
    #assert token_id == user_id


if __name__ == "__main__":
    print(f"Start of main auth_test")
    
    access_token = os.environ.get("OIDC_ACCESS_TOKEN","")
    oicd_user_name = os.environ.get("OIDC_AGENT_ACCOUNT","")
    server_token = os.environ.get("FEDCLOUD_SERVERTOKEN","")

    print("OIDC_AGENT_ACCOUNT:\t Done")
    get_token_from_mytoken_decode_verify(None, oicd_user_name)

    mytoken = os.environ.get("FEDCLOUD_MYTOKEN")
    print(f"FEDCLOUD_MYTOKEN:\t Done\n {mytoken}")
    
    user_id = os.environ.get("FEDCLOUD_ID")
    print(f"FEDCLOUD_ID:\t Done\n{user_id}")

    get_token_from_mytoken_decode_verify(mytoken, user_id)


