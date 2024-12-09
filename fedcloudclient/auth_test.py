"""
Testing unit for auth.py
"""
import os
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

import fedcloudclient.auth as auth
from fedcloudclient.conf import CONF as CONF



def verify_MYTOKEN(mytoken: str) -> str:
    """
    Get access token from mytoken server, decode, get user ID and verify
    """

    token = auth.OIDCToken()
    try:
        access_token_mytoken=token.get_token_from_mytoken(mytoken, None)
        return access_token_mytoken
    except:
        return print(f"No MYTOKEN")

    
def verify_OIDC_AGENT(user_id:str) -> str:
    token = auth.OIDCToken()
    try:
        access_token_oidc=token.get_token_from_oidc_agent(user_id) 
        return access_token_oidc
    except:
        return print(f"No OIDC_AGENT_ACCOUNT") 



def verify_ACCESS_TOKEN(access_token:str) -> str:
    token = auth.OIDCToken()
    try:
        token.access_token=access_token
        return token.access_token
    except:
        return print(f"Error with ACCESS_TOKEN") 

def verify_user_id(access_token:str) -> str:
    token = auth.OIDCToken()
    token.access_token=access_token
    try:
        user_id=token.get_user_id()
        return user_id
    except:
        print("No user_id!")
    
def verify_pyload(access_token:str) -> dict:
    token = auth.OIDCToken()
    token.access_token=access_token
    #try:
    user_id=token.get_user_id()
    payload=token.payload
    request_json=token.oidc_discover()
    list_vos=token.token_list_vos()
    return payload,request_json,list_vos
    #except:
    #    print("No user_id!")


def printing_dict(var_dict:dict):
    for idx, item in enumerate(var_dict):
        print(f"{item}:\t {var_dict[item]}")


if __name__ == "__main__":
    print(f"Start of verifying auth.py")
    mytoken=os.environ.get("FEDCLOUD_MYTOKEN","")
    access_token_mytok=verify_MYTOKEN(mytoken)

    oidc_agent_name=os.environ.get("OIDC_AGENT_ACCOUNT","")
    access_token_oidca=verify_OIDC_AGENT(oidc_agent_name)

    access_token= os.environ.get("ACCESS_TOKEN","")
    access_token_check=verify_ACCESS_TOKEN(access_token)

    user_id=verify_user_id(access_token_check)
    payload,request_json,list_vos=verify_pyload(access_token_check)




    print(f"{type(payload)}")
    printing_dict(payload)
    print("-------------------------------------------------")
    printing_dict(request_json)
    print(f"Break")







    


