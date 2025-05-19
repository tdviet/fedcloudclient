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
    Abstract base class for token management.
    """
    
    def __init__(self):
        pass

# pylint: disable=too-few-public-methods
class OIDCToken(Token):
    """
    OIDC token handler.

    This class manages access tokens from various sources (OIDC agent,
    Mytoken server), decodes them, and exposes user and VO membership
    information.

    :param access_token:  
        Optional initial access token to decode and discover metadata from.
    :type access_token: str, optional

    :ivar str access_token: The raw access token string.
    :ivar dict payload: The decoded JWT payload.
    :ivar str oidc_agent_account: The account name used with oidc-agent.
    :ivar str mytoken: The Mytoken identifier used to fetch a token.
    :ivar str user_id: The `sub` claim extracted from the token payload.
    :ivar str _vo_pattern: Regex pattern for extracting VO names.
    :ivar dict request_json: OIDC discovery metadata.
    :ivar int _min_access_token_time: Minimum required lifetime for a token.
    :ivar dict conf: Reference to global CONF dict for defaults.
    """

    def __init__(self, access_token=None):
        """
        Initialize the OIDC token handler.

        :param access_token:  
            A JWT or opaque token string. If provided, the token is immediately
            decoded and OIDC discovery is performed.
        :type access_token: str, optional
        """
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
        Decode the stored access token into its JWT payload.

        This method will decode `self.access_token` without verifying the
        signature (i.e. `verify_signature=False`), extract the `sub` claim
        into `self.user_id`, and cache the payload in `self.payload`.

        :return:  
            The decoded JWT payload as a dictionary.
        :rtype: dict

        :raises TokenError:  
            If `self.access_token` is missing or invalid.
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
        Retrieve the user ID from the decoded token payload.

        If the payload hasn’t been decoded yet, this will trigger a decode
        (via `self.decode_token()`) and may still return `None` if decoding fails.

        :return:  
            The `user_id` string extracted from the token payload, or `None` if
            no payload is available.
        :rtype: str or None
        """
        self.access_token=access_token
        payload = self.decode_token()
        if payload is None:
            return None
        return payload["sub"]

    def get_user_id(self) -> str:
        """
        Return use ID
        
        :return: user_id
        
        """

        if not self.payload:
            self.decode_token()
            return None
        return self.user_id

    def get_token_from_oidc_agent(self, oidc_agent_account: str) -> str:
        """
        Obtain an access token from a local OIDC agent.

        :param oidc_agent_account:  
            The name of the account registered with your local `oidc-agent`.
        :type oidc_agent_account: str

        :return:  
            The retrieved access token string.  
        :rtype: str

        :raises TokenError:  
            If `oidc_agent_account` is not provided or if the agent fails to return a token.
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
        Obtain an access token by exchanging a Mytoken identifier.

        :param mytoken:  
            The Mytoken identifier (a one-time code or token name) to exchange for an access token.
        :type mytoken: str

        :param mytoken_server:  
            Optional base URL of the Mytoken server.  
            If not provided, defaults to `CONF["mytoken_server"]`.
        :type mytoken_server: str, optional

        :return:  
            The access token string retrieved from the Mytoken server, or `None` if an error occurred.
        :rtype: str or None

        :raises TokenError:  
            If no `mytoken` is provided, or if the server returns an HTTP error.
        :raises requests.exceptions.Timeout:  
            If the HTTP request to the Mytoken server times out.
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
        Select a valid token from multiple sources.

        :param access_token:  
            An existing access token to try first. If it’s valid, it will be returned.
        :type access_token: str

        :param oidc_agent_account:  
            The account name for your local OIDC agent.  
            If provided, we’ll ask the agent for a token.
        :type oidc_agent_account: str

        :param mytoken:  
            A Mytoken identifier (e.g. a token name) to exchange for an access token.
        :type mytoken: str

        :param mytoken_server:  
            Optional URL of the Mytoken server to contact (defaults to your configured server).
        :type mytoken_server: str, optional

        :returns:  
            A valid access token string.
        :rtype: str

        :raises TokenError:  
            If none of the methods yields a valid token.
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
        """Perform OpenID Connect discovery.

        Reads the issuer URL from `self.payload["iss"]` and fetches the
        provider metadata from `<issuer>/.well-known/openid-configuration`.

        Returns:
            dict: OIDC provider metadata as a JSON-like dict.

        Raises:
            requests.HTTPError: If fetching the discovery document fails.
        """
        oidc_url=self.payload["iss"]
        request = requests.get(oidc_url + "/.well-known/openid-configuration")
        request.raise_for_status()
        self.request_json=request.json()
        return self.request_json

    def check_token(self, access_token, verbose=False):
        """
        Check validity of an access token.

        :param access_token:  
            The JWT or opaque token string to validate.
        :type access_token: str

        :param verbose:  
            If `True`, print human‐readable expiration information.  
            Defaults to `False`.
        :type verbose: bool

        :return:  
            The same `access_token` if it’s still valid, otherwise `None`.
        :rtype: str or None

        :raises TokenError:  
            If the token is expired (or fails other validation checks).
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
        List VO memberships in EGI Check-in.

        :param access_token:  
            A valid access token (JWT or opaque string) to authenticate the request.  
        :type access_token: str

        :return:  
            A sorted list of VO names parsed from the `eduperson_entitlement` claims.  
        :rtype: list[str]

        :raises requests.exceptions.Timeout:  
            If the HTTP request to the userinfo endpoint times out.
        :raises requests.HTTPError:  
            If the HTTP response status code indicates an error.
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
