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
    DEFAULT_OIDC_URL,
    oidc_access_token_params,
    oidc_params,
    oidc_refresh_token_params,
)

# Minimal lifetime of the access token is 30s and max 24h
_MIN_ACCESS_TOKEN_TIME = 30
_MAX_ACCESS_TOKEN_TIME = 24 * 3600

VO_PATTERN = "urn:mace:egi.eu:group:(.+?):(.+:)*role=member#aai.egi.eu"


def print_error(message, quiet):
    """
    Print error message to stderr if not quiet
    """
    if not quiet:
        print(message, file=sys.stderr)


def oidc_discover(oidc_url):
    """
    Discover OIDC endpoints

    :param oidc_url: CheckIn URL

    :return: JSON object of OIDC configuration
    """
    request = requests.get(oidc_url + "/.well-known/openid-configuration")
    request.raise_for_status()
    return request.json()


def token_refresh(oidc_client_id, oidc_client_secret, oidc_refresh_token, oidc_url):
    """
    Helper function for retrieving JSON object with access token

    :param oidc_client_id:
    :param oidc_client_secret:
    :param oidc_refresh_token:
    :param oidc_url:

    :return: JSON object with access token
    """

    oidc_ep = oidc_discover(oidc_url)

    refresh_data = {
        "client_id": oidc_client_id,
        "client_secret": oidc_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": oidc_refresh_token,
        "scope": "openid email profile eduperson_entitlement",
    }

    request = requests.post(
        oidc_ep["token_endpoint"],
        auth=(oidc_client_id, oidc_client_secret),
        data=refresh_data,
    )
    request.raise_for_status()
    return request.json()


def refresh_access_token(
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_url,
    quiet=False,
):
    """
    Retrieve access token in plain text (string)

    :param oidc_client_id:
    :param oidc_client_secret:
    :param oidc_refresh_token:
    :param oidc_url:
    :param quiet: If true, print no error message

    :return: access token or None on error
    """
    if oidc_refresh_token:
        if not (oidc_client_id and oidc_client_secret and oidc_url):
            print_error(
                "Error: Client ID and secret required together with refresh token",
                quiet,
            )
            return None

        print_error(
            "Warning: Exposing refresh tokens is insecure and will be deprecated!",
            quiet,
        )
        try:
            access_token = token_refresh(
                oidc_client_id, oidc_client_secret, oidc_refresh_token, oidc_url
            )
            return access_token["access_token"]
        except requests.exceptions.RequestException as exception:
            print_error(
                "Error during getting access token from refresh token\n"
                f"Error message: {exception}",
                quiet,
            )
    return None


def get_token_from_oidc_agent(oidc_agent_account, quiet=False):
    """
    Get access token from oidc-agent

    :param quiet: If true, print no error message
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
                "Error during getting access token from oidc-agent\n"
                f"Error message: {exception}",
                quiet,
            )
    return None


def check_token(oidc_token, quiet=False, verbose=False, refresh_token=False):
    """
    Check validity of access token

    :param oidc_token: the token to check
    :param refresh_token: the provided token is refresh token
    :param verbose: If true, print additional info
    :param quiet: If true, print no error message

    :return:
    """
    if oidc_token:
        # Check expiration time of access token
        try:
            payload = jwt.decode(oidc_token, options={"verify_signature": False})
        except jwt.exceptions.InvalidTokenError:
            print_error("Error: Invalid access token.", quiet)
            return None

        exp_timestamp = int(payload["exp"])
        current_timestamp = int(time.time())
        exp_time_in_sec = exp_timestamp - current_timestamp

        if exp_time_in_sec < _MIN_ACCESS_TOKEN_TIME:
            print_error("Error: Expired access token.", quiet)
            return None

        if exp_time_in_sec > _MAX_ACCESS_TOKEN_TIME and not refresh_token:
            print_error(
                "Warning: You probably use refresh tokens as access tokens.",
                quiet,
            )
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
    quiet=False,
):
    """
    Get EGI Check-in ID from access token

    :param oidc_token: the token
    :param quiet: If true, print no error message

    :return: Check-in ID
    """
    try:
        payload = jwt.decode(oidc_token, options={"verify_signature": False})
    except jwt.exceptions.InvalidTokenError:
        print_error("Error: Invalid access token.", quiet)
        return None

    return payload["sub"]


def get_access_token(
    oidc_access_token,
    oidc_refresh_token,
    oidc_client_id,
    oidc_client_secret,
    oidc_url,
    oidc_agent_account,
):
    """
    Get access token
    Generates new access token from oidc-agent or
    refresh token (if given), or use existing token

    Check expiration time of access token
    Raise error if no valid token exists

    :param oidc_access_token:
    :param oidc_refresh_token:
    :param oidc_client_id:
    :param oidc_client_secret:
    :param oidc_url:
    :param oidc_agent_account:

    :return: access token
    """

    # First, try to get access token from oidc-agent
    access_token = get_token_from_oidc_agent(oidc_agent_account)
    if access_token:
        return access_token

    # Then try refresh token
    access_token = refresh_access_token(
        oidc_client_id, oidc_client_secret, oidc_refresh_token, oidc_url
    )
    if access_token:
        return access_token

    # Then finally access token
    access_token = check_token(oidc_access_token)
    if access_token:
        return access_token

    # Nothing available
    raise SystemExit(
        "Error: An access token is needed for the operation. You can specify "
        "access token directly via --oidc-access-token option or use oidc-agent "
        "via --oidc-agent-account"
    )


def token_list_vos(oidc_access_token, oidc_url):
    """
    List VO memberships in EGI Check-in

    :param oidc_access_token:
    :param oidc_url:

    :return: list of VO names
    """
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
    Get details of access/refresh tokens
    """


@token.command()
@oidc_refresh_token_params
@oidc_access_token_params
def check(oidc_refresh_token, oidc_access_token):
    """
    Check validity of access/refresh token
    """

    if oidc_refresh_token:
        check_token(oidc_refresh_token, verbose=True, refresh_token=True)
    elif oidc_access_token:
        check_token(oidc_access_token, verbose=True)
    else:
        raise SystemExit("OIDC access token or refresh token required")


@token.command()
@oidc_params
def list_vos(access_token):
    """
    List VO membership(s) of access token
    """

    vos = token_list_vos(access_token, DEFAULT_OIDC_URL)
    print("\n".join(vos))
