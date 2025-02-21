"""
Testing unit for auth.py
"""
import os

from fedcloudclient.auth import OIDCToken
from fedcloudclient.logger import log_and_raise
from fedcloudclient.exception import TokenError

def verify_mytoken(mytoken: str) -> str:
    """
    Get access token from mytoken, decode them, get user ID and verify
    """
    token = OIDCToken()
    try:
        access_token_mytoken=token.get_token_from_mytoken(mytoken, None)
        return access_token_mytoken
    except TokenError:
        err_msg="No MYTOKEN"
        return log_and_raise(err_msg,TokenError)


def verify_oidc_agent(user_id: str) -> str:
    """ Verify token access from oidc-agent"""
    token = OIDCToken()
    try:
        access_token_oidc=token.get_token_from_oidc_agent(user_id)
        return access_token_oidc
    except TokenError:
        err_msg="No OIDC_AGENT_ACCOUNT"
        return log_and_raise(err_msg,TokenError)


def verify_access_token(access_token:str) -> str:
    """ Verify access_token """
    token = OIDCToken()
    try:
        token.access_token=access_token
        return token.access_token
    except TokenError:
        err_msg="Not valid ACCESS_TOKEN"
        return log_and_raise(err_msg,TokenError)

def verify_user_id(access_token:str) -> str:
    """ Check user id from access_token """
    token = OIDCToken()
    token.access_token=access_token
    try:
        user_id=token.get_user_id()
        return user_id
    except TokenError:
        err_msg="No user ID from access_token"
        return log_and_raise(err_msg,TokenError)

def verify_pyload(access_token:str) -> dict:
    """ Get payload, request_json, list_vos from access_token """
    token = OIDCToken()
    token.access_token=access_token
    try:
        token.get_user_id()
        payload=token.payload
        request_json=token.oidc_discover()
        list_vos=token.token_list_vos(access_token)
        return payload,request_json,list_vos
    except TokenError:
        err_msg="Not valid ACCESS_TOKEN"
        return log_and_raise(err_msg,TokenError)



def printing_dict(var_dict: dict) -> None:
    """ Printing dictionary """
    for item in var_dict:
        print(f"{item}:\t {var_dict[item]}")


if __name__ == "__main__":
    print("Start of verifying auth.py")

    access_token1= os.environ.get("ACCESS_TOKEN","")
    access_token_check=verify_access_token(access_token1)

    payload1,request_json1,list_vos1=verify_pyload(access_token_check)

    mytoken1=os.environ.get("FEDCLOUD_MYTOKEN","")
    access_token_mytok=verify_mytoken(mytoken1)

    oidc_agent_name=os.environ.get("OIDC_AGENT_ACCOUNT","")
    access_token_oidc1=verify_oidc_agent(oidc_agent_name)

    user_id1=verify_user_id(access_token_oidc1)
    payload1,request_json1,list_vos1=verify_pyload(access_token_oidc1)


    print(f"{type(payload1)}")
    printing_dict(payload1)
    print("-------------------------------------------------")
    printing_dict(request_json1)
    print("-------------------------------------------------")
    print(list_vos1)
    print("Break")
