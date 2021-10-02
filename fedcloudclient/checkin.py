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
        "scope": "openid email profile offline_access",
    }

    request = requests.post(
        oidc_ep["token_endpoint"],
        auth=(oidc_client_id, oidc_client_secret),
        data=refresh_data,
    )
    request.raise_for_status()
    return request.json()


def refresh_access_token(
    oidc_client_id, oidc_client_secret, oidc_refresh_token, oidc_url
):
    """
    Retrieve access token in plain text (string)

    :param oidc_client_id:
    :param oidc_client_secret:
    :param oidc_refresh_token:
    :param oidc_url:
    :return: access token
    """
    return token_refresh(
        oidc_client_id,
        oidc_client_secret,
        oidc_refresh_token,
        oidc_url,
    )["access_token"]


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
    if oidc_agent_account:
        try:
            access_token = agent.get_access_token(
                oidc_agent_account,
                min_valid_period=_MIN_ACCESS_TOKEN_TIME,
                application_hint="fedcloudclient",
            )
            return access_token
        except agent.OidcAgentError as exception:
            print(f"ERROR oidc-agent: {exception}", file=sys.stderr,)

    # Then try refresh token
    if oidc_refresh_token and oidc_client_id and oidc_client_secret and oidc_url:
        print(
            "Warning: Exposing refresh tokens is insecure and will be deprecated!",
            file=sys.stderr,
        )
        return token_refresh(
            oidc_client_id, oidc_client_secret, oidc_refresh_token, oidc_url
        )["access_token"]

    # Then finally access token
    if oidc_access_token:

        # Check expiration time of access token
        try:
            payload = jwt.decode(oidc_access_token, options={"verify_signature": False})
        except jwt.exceptions.InvalidTokenError:
            raise SystemExit("Error: Invalid access token.")

        expiration_timestamp = int(payload["exp"])
        current_timestamp = int(time.time())
        if current_timestamp > expiration_timestamp - _MIN_ACCESS_TOKEN_TIME:
            raise SystemExit(
                "The given access token has expired."
                " Get new access token before continuing on operation"
            )
        if current_timestamp < expiration_timestamp - _MAX_ACCESS_TOKEN_TIME:
            raise SystemExit(
                "You probably use refresh tokens as access tokens."
                " Get access tokens via `curl -X POST -u ...` command"
                " in the last row of the page https://aai.egi.eu/fedcloud."
            )
        return oidc_access_token

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
        try:
            payload = jwt.decode(
                oidc_refresh_token, options={"verify_signature": False}
            )
        except jwt.exceptions.InvalidTokenError:
            raise SystemExit("Error: Invalid refresh token")

        expiration_timestamp = int(payload["exp"])
        expiration_time_str = datetime.utcfromtimestamp(expiration_timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print(f"Refresh token is valid until {expiration_time_str} UTC")

        current_timestamp = int(time.time())
        if current_timestamp < expiration_timestamp:
            expiration_time_in_days = (expiration_timestamp - current_timestamp) // (24 * 3600)
            print(f"Refresh token expires in {expiration_time_in_days} days")
        else:
            print("Refresh token has expired")

    elif oidc_access_token:
        try:
            payload = jwt.decode(oidc_access_token, options={"verify_signature": False})
        except jwt.exceptions.InvalidTokenError:
            raise SystemExit("Error: Invalid access token")

        expiration_timestamp = int(payload["exp"])
        expiration_time_str = datetime.utcfromtimestamp(expiration_timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print(f"Access token is valid until {expiration_time_str} UTC")

        current_timestamp = int(time.time())
        if current_timestamp < expiration_timestamp:
            expiration_time_in_sec = expiration_timestamp - current_timestamp
            print(f"Access token expires in {expiration_time_in_sec} seconds")
        else:
            print("Access token has expired")
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
