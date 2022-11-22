"""
Implementation of "fedcloud token" commands for interactions with EGI Check-in and
access tokens
"""
import re
import sys
import time
from datetime import datetime

import click
import jwt
import liboidcagent as agent
import requests

from fedcloudclient.decorators import (
    oidc_params,
)

# Minimal lifetime of the access token is 30s and max 24h
_MIN_ACCESS_TOKEN_TIME = 30

VO_PATTERN = "urn:mace:egi.eu:group:(.+?):(.+:)*role=member#aai.egi.eu"


def print_error(message, quiet):
    """
    Print error message to stderr if not quiet
    """
    if not quiet:
        print(message, file=sys.stderr)


def decode_token(oidc_access_token):
    """
    Decoding access token to a dict
    :param oidc_access_token:
    :return: dict with token info
    """
    try:
        payload = jwt.decode(oidc_access_token, options={"verify_signature": False})
    except jwt.exceptions.InvalidTokenError:
        print_error("Error: Invalid access token.", False)
        return None
    return payload


def oidc_discover(oidc_url):
    """
    Discover OIDC endpoints

    :param oidc_url: CheckIn URL

    :return: JSON object of OIDC configuration
    """
    request = requests.get(oidc_url + "/.well-known/openid-configuration")
    request.raise_for_status()
    return request.json()


def get_token_from_oidc_agent(oidc_agent_account, quiet=False):
    """
    Get access token from oidc-agent
    :param quiet:
    :param oidc_agent_account: account name in oidc-agent
    :return: access token, or None on error
    """

    if oidc_agent_account:
        try:
            access_token = agent.get_access_token(
                oidc_agent_account,
                min_valid_period=_MIN_ACCESS_TOKEN_TIME,
                application_hint="fedcloudclient",
            )
            return access_token
        except agent.OidcAgentError as exception:
            print_error(
                "Error getting access token from oidc-agent\n"
                f"Error message: {exception}",
                quiet,
            )
    return None


def get_token_from_mytoken_server(mytoken, mytoken_server, quiet=False):
    """
    Get access token from mytoken server
    :param quiet:
    :param mytoken:
    :param mytoken_server:
    :return: access token, or None on error
    """

    if mytoken:
        try:
            data = {
                "grant_type": "mytoken",
                "mytoken": mytoken,
            }
            req = requests.post(
                mytoken_server + "/api/v0/token/access",
                json=data,
            )
            req.raise_for_status()
            return req.json().get("access_token")
        except requests.exceptions.HTTPError as exception:
            print_error(
                "Error getting access token from mytoken\n"
                f"Error message: {exception}",
                quiet,
            )
    return None


def check_token(oidc_token, verbose=False):
    """
    Check validity of access token

    :param verbose:
    :param oidc_token: the token to check
    :return: access token, or None on error
    """

    payload = decode_token(oidc_token)
    if payload is None:
        return None

    exp_timestamp = int(payload["exp"])
    current_timestamp = int(time.time())
    exp_time_in_sec = exp_timestamp - current_timestamp

    if exp_time_in_sec < _MIN_ACCESS_TOKEN_TIME:
        print_error("Error: Expired access token.", False)
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

    return oidc_token


def get_checkin_id(
    oidc_token,
):
    """
    Get EGI Check-in ID from access token

    :param oidc_token: the token

    :return: Check-in ID
    """
    payload = decode_token(oidc_token)
    if payload is None:
        return None
    return payload["sub"]


def get_access_token(
    oidc_access_token,
    oidc_agent_account,
    mytoken,
    mytoken_server,
):
    """
    Get access token
    Generates new access token from oidc-agent
    or mytoken

    Check expiration time of access token
    Raise error if no valid token exists

    :param oidc_access_token:
    :param oidc_agent_account:
    :param mytoken:
    :param mytoken_server:
    :return: access token
    """

    access_token = None

    # access token via parameter has the highest priority
    if oidc_access_token:
        access_token = check_token(oidc_access_token)

    # then try to get access token from mytoken server
    if mytoken and access_token is None:
        access_token = get_token_from_mytoken_server(
            mytoken, mytoken_server, quiet=False
        )

    # then, try to get access token from oidc-agent
    if oidc_agent_account and access_token is None:
        access_token = get_token_from_oidc_agent(oidc_agent_account, quiet=False)

    if access_token is None:
        # Nothing available
        raise SystemExit(
            "Error: An access token is needed for the operation. You can specify "
            "access token directly via --oidc-access-token option or use oidc-agent "
            "via --oidc-agent-account or mytoken via --mytoken"
        )

    return access_token


def token_list_vos(oidc_access_token):
    """
    List VO memberships in EGI Check-in

    :param oidc_access_token:

    :return: list of VO names
    """
    oidc_url = decode_token(oidc_access_token)["iss"]
    oidc_ep = oidc_discover(oidc_url)
    request = requests.get(
        oidc_ep["userinfo_endpoint"],
        headers={"Authorization": f"Bearer {oidc_access_token}"},
    )

    request.raise_for_status()
    vos = set()
    pattern = re.compile(VO_PATTERN)
    for claim in request.json().get("eduperson_entitlement", []):
        vo = pattern.match(claim)
        if vo:
            vos.add(vo.groups()[0])
    return sorted(vos)


@click.group()
def token():
    """
    Get details of access token
    """


@token.command()
@oidc_params
def check(access_token):
    """
    Check validity of access token
    """
    check_token(access_token, verbose=True)


@token.command()
@oidc_params
def list_vos(access_token):
    """
    List VO membership(s) of access token
    """
    vos = token_list_vos(access_token)
    print("\n".join(vos))


@token.command()
@oidc_params
def issue(access_token):
    """
    print access token (from mytoken or oidc-agent)
    """
    print(access_token)
