"""
Class for managing tokens
"""

import re
import time
from datetime import datetime
import jwt
import liboidcagent as agent
import requests

from fedcloudclient.conf import CONF
from fedcloudclient.exception import TokenError
from fedcloudclient.logger import log_and_raise
from fedcloudclient.conf import save_config, DEFAULT_CONFIG_LOCATION

# pylint: disable=too-few-public-methods
class Token:
    """
    Abstract object for managing tokens
    
    """
    def __init__(self):
        pass

# pylint: disable=too-few-public-methods
class OIDCToken(Token):
    """
    OIDC tokens. Managing access tokens, oidc-agent account and mytoken
    
    """

    def __init__(self, access_token=None):
        super().__init__()
        self.access_token = access_token
        self.payload = None
        self.oidc_agent_account = None
        self.mytoken = None
        self.user_id = None
        self._vo_pattern = "urn:mace:egi.eu:group:(.+?):(.+:)*role=member#aai.egi.eu"
        self.request_json=None
        self._min_access_token_time=CONF["_MIN_ACCESS_TOKEN_TIME"]
        self.conf=CONF
        if access_token is not None:
            self.decode_token()
            self.oidc_discover()

    def decode_token(self) -> dict:
        """
        Decoding access token to payload
        :return:
        
        """
        if not self.payload:
            try:
                self.payload = jwt.decode(self.access_token, options={"verify_signature": False})
                self.user_id = self.payload["sub"]
            except jwt.exceptions.InvalidTokenError:
                error_msg = "Invalid access token"
                log_and_raise(error_msg, TokenError)

        return self.payload

    def get_checkin_id(self,access_token):
        """
        Get EGI Check-in ID from access token

        :param oidc_token: the token

        :return: Check-in ID
        
        """
        self.access_token=access_token
        payload = self.decode_token()
        if payload is None:
            return None
        return payload["sub"]

    def get_user_id(self) -> str:
        """
        Return use ID
        :return:
        
        """

        if not self.payload:
            self.decode_token()
            return None
        return self.user_id

    def get_token_from_oidc_agent(self, oidc_agent_account: str) -> str:
        """
        Get access token from oidc-agent
        :param oidc_agent_account: account name in oidc-agent
        :return: access token, and set internal token, raise TokenError on None
        """

        if oidc_agent_account:
            try:
                access_token = agent.get_access_token(
                    oidc_agent_account,
                    min_valid_period=CONF.get("_MIN_ACCESS_TOKEN_TIME"),
                    application_hint="fedcloudclient",
                    )
                self.access_token = access_token
                self.oidc_agent_account = oidc_agent_account
                self.conf["oidc_agent_account"]=str(oidc_agent_account)
                save_config(DEFAULT_CONFIG_LOCATION,self.conf)
                return access_token

            except agent.OidcAgentError as exception:
                error_msg = f"Error getting access token from oidc-agent in -def get_token_from_oidc_agent()-: {exception}"
                log_and_raise(error_msg, TokenError)
                return None
        else:
            error_msg = f"Error getting access token from oidc-agent: {oidc_agent_account}"
            log_and_raise(error_msg, TokenError)
            return None

    def get_token_from_mytoken(self, mytoken: str, mytoken_server: str = None) -> str:
        """
        Get access token from mytoken server
        :param mytoken:
        :param mytoken_server:
        :return: access token, or None on error
        
        """
        if not mytoken_server:
            mytoken_server = CONF.get("mytoken_server")

        if mytoken:
            try:
                data = {
                    "grant_type": "mytoken",
                    "mytoken": mytoken,
                }
                try:
                    req = requests.post(
                    mytoken_server + "/api/v0/token/access",
                    json=data,)

                    self.conf["mytoken"]=str(mytoken)
                    save_config(DEFAULT_CONFIG_LOCATION,self.conf)

                except requests.exceptions.Timeout as err:
                    error_msg = f"Timeout for requests in mytoken: {err}"
                    log_and_raise(error_msg, err)
                    return None
                req.raise_for_status()
                access_token = req.json().get("access_token")
                self.access_token = access_token
                self.mytoken = mytoken
                return access_token

            except requests.exceptions.HTTPError as exception:
                error_msg = f"Error getting access token from mytoken server: {exception}"
                log_and_raise(error_msg, TokenError)
                return None
        else:
            error_msg = f"Error getting access token from mytoken server: mytoken is {mytoken}"
            log_and_raise(error_msg, TokenError)
            return None

    def multiple_token(self, access_token: str, oidc_agent_account: str, mytoken: str, mytoken_server = None) -> str:
        """
        Select valid token from multiple options
        :param access_token:
        :param oidc_agent_account:
        :param mytoken:
        :return:
        
        """
        if mytoken:
            try:
                access_token=self.get_token_from_mytoken(mytoken)
                return access_token
            except TokenError:
                pass
        if oidc_agent_account:
            try:
                access_token=self.get_token_from_oidc_agent(oidc_agent_account)
                return access_token
            except TokenError:
                pass
        if mytoken_server:
            pass

        if access_token:
            self.access_token = access_token
            return access_token
        log_and_raise("Cannot get access token", TokenError)
        return None

    def oidc_discover(self) -> dict:
        """
        :param oidc_url: CheckIn URL get from payload
        :return: JSON object of OIDC configuration
        
        """
        oidc_url=self.payload["iss"]
        request = requests.get(oidc_url + "/.well-known/openid-configuration")
        request.raise_for_status()
        self.request_json=request.json()
        return self.request_json

    def check_token(self, access_token, verbose=False):
        """
        Check validity of access token

        :param verbose:
        :param oidc_token: the token to check
        :return: access token, or None on error
        
        """
        self.access_token=access_token
        payload = self.decode_token()
        if payload is None:
            return None

        exp_timestamp = int(payload["exp"])
        current_timestamp = int(time.time())
        exp_time_in_sec = exp_timestamp - current_timestamp

        if exp_time_in_sec < self._min_access_token_time:
            error_msg=f"Error: Expired access token in {exp_time_in_sec}"
            log_and_raise(error_msg,TokenError)
            return None

        if verbose:
            exp_time_str = datetime.utcfromtimestamp(exp_timestamp).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            print(f"Token is valid until {exp_time_str} UTC")
            if exp_time_in_sec < 24 * 3600:
                print(f"Token expires in {exp_time_in_sec} seconds")
            else:
                exp_time_in_days = exp_time_in_sec // (24 * 3600)
                print(f"Token expires in {exp_time_in_days} days")

        return access_token

    def token_list_vos(self,access_token):
        """
        List VO memberships in EGI Check-in
        :return: list of VO names
        
        """
        self.access_token=access_token
        oidc_ep  = self.request_json
        try:
            request = requests.get(
                oidc_ep["userinfo_endpoint"],
                headers={"Authorization": f"Bearer {self.access_token}"})

        except requests.exceptions.Timeout as err:
            error_msg = f"Timeout for requests in list-vos: {err}"
            log_and_raise(error_msg, err)
            return None

        request.raise_for_status()
        vos = set()
        pattern = re.compile(self._vo_pattern)
        for claim in request.json().get("eduperson_entitlement", []):
            vo = pattern.match(claim) # pylint: disable=invalid-name
            if vo:
                vos.add(vo.groups()[0])
            request.raise_for_status()

        return sorted(vos)
