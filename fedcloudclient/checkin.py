from __future__ import print_function

import re
import time
from datetime import datetime

import click
import jwt
from tabulate import tabulate
import requests

DEFAULT_CHECKIN_URL = "https://aai.egi.eu/oidc"


def oidc_discover(checkin_url):
    """
    Discover oidc endpoints

    :param checkin_url: CheckIn URL
    :return: JSON object of OIDC configuration
    """
    r = requests.get(checkin_url + "/.well-known/openid-configuration")
    r.raise_for_status()
    return r.json()


def token_refresh(
        checkin_client_id, checkin_client_secret, checkin_refresh_token, checkin_url
):
    """
    Helper function for retrieving JSON object with access token

    :param checkin_client_id:
    :param checkin_client_secret:
    :param checkin_refresh_token:
    :param checkin_url:
    :return: JSON object with access token
    """

    oidc_ep = oidc_discover(checkin_url)

    refresh_data = {
        "client_id": checkin_client_id,
        "client_secret": checkin_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": checkin_refresh_token,
        "scope": "openid email profile offline_access",
    }

    r = requests.post(
        oidc_ep["token_endpoint"],
        auth=(checkin_client_id, checkin_client_secret),
        data=refresh_data
    )
    r.raise_for_status()
    return r.json()


def refresh_access_token(
        checkin_client_id, checkin_client_secret, checkin_refresh_token, checkin_url
):
    """
    Retrieve access token in plain text (string)

    :param checkin_client_id:
    :param checkin_client_secret:
    :param checkin_refresh_token:
    :param checkin_url:
    :return: access token
    """
    return token_refresh(
        checkin_client_id,
        checkin_client_secret,
        checkin_refresh_token,
        checkin_url,
    )["access_token"]


def get_access_token(
        checkin_access_token,
        checkin_refresh_token,
        checkin_client_id,
        checkin_client_secret,
        checkin_url
):
    """
    Getting access token.
    Generate new access token from refresh token (if given) or use existing token
    Check expiration time of access token
    Raise error if no valid token exists

    :param checkin_access_token:
    :param checkin_refresh_token:
    :param checkin_client_id:
    :param checkin_client_secret:
    :param checkin_url:
    :return: access token
    """

    if (checkin_refresh_token and checkin_client_id
            and checkin_client_secret and checkin_url):

        # Always getting new access token if refresh token exist
        return token_refresh(
            checkin_client_id,
            checkin_client_secret,
            checkin_refresh_token,
            checkin_url)["access_token"]
    elif checkin_access_token:

        # Check expiration time of access token
        try:
            payload = jwt.decode(checkin_access_token, verify=False)
        except jwt.exceptions.InvalidTokenError:
            raise SystemExit("Error: Invalid access token.")

        expiration_timestamp = int(payload['exp'])
        current_timestamp = int(time.time())
        if current_timestamp > expiration_timestamp - 10:
            raise SystemExit("The given access token has expired."
                             + " Get new access token before continuing on operation")
        return checkin_access_token
    else:
        raise SystemExit("Error: Either access token OR refresh token + client ID"
                         + " + client secret are expected")


def token_list_vos(checkin_access_token, checkin_url):
    """
    List VO memberships in EGI Check-in

    :param checkin_access_token:
    :param checkin_url:
    :return: list of VO names
    """
    oidc_ep = oidc_discover(checkin_url)
    r = requests.get(
        oidc_ep["userinfo_endpoint"],
        headers={"Authorization": "Bearer %s" % checkin_access_token})

    r.raise_for_status()
    vos = []
    m = re.compile("urn:mace:egi.eu:group:(.*.):role=member#aai.egi.eu")
    for claim in r.json().get("eduperson_entitlement", []):
        vo = m.match(claim)
        if vo:
            vos.append(vo.groups()[0])
    return vos


@click.group()
def token():
    """
    Token command group for manipulation with tokens
    """
    pass


@token.command()
@click.option(
    "--checkin-client-id",
    help="Check-in client id",
    required=True,
    envvar="CHECKIN_CLIENT_ID",
)
@click.option(
    "--checkin-client-secret",
    help="Check-in client secret",
    required=True,
    envvar="CHECKIN_CLIENT_SECRET",
)
@click.option(
    "--checkin-refresh-token",
    help="Check-in refresh token",
    required=True,
    envvar="CHECKIN_REFRESH_TOKEN",
)
@click.option(
    "--checkin-url",
    help="Check-in OIDC URL",
    envvar="CHECKIN_OIDC_URL",
    default=DEFAULT_CHECKIN_URL,
    show_default=True,
)
def refresh(
        checkin_client_id,
        checkin_client_secret,
        checkin_refresh_token,
        checkin_url,
):
    """
    CLI command for creating new access token from refresh token
    """
    output = token_refresh(
        checkin_client_id,
        checkin_client_secret,
        checkin_refresh_token,
        checkin_url
    )
    print(tabulate([(k, v) for k, v in output.items()], headers=["Field", "Value"]))


@token.command()
@click.option(
    "--checkin-refresh-token",
    help="Check-in refresh token",
    envvar="CHECKIN_REFRESH_TOKEN",
)
@click.option(
    "--checkin-access-token",
    help="Check-in access token",
    envvar="CHECKIN_ACCESS_TOKEN",
)
def check(
        checkin_refresh_token,
        checkin_access_token
):
    """
    CLI command for printing validity of access or refresh token
    """

    if checkin_refresh_token:
        try:
            payload = jwt.decode(checkin_refresh_token, verify=False)
        except jwt.exceptions.InvalidTokenError:
            raise SystemExit("Error: Invalid refresh token.")

        expiration_timestamp = int(payload['exp'])
        expiration_time = datetime.utcfromtimestamp(expiration_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print("Refresh token is valid to %s UTC" % expiration_time)
        current_timestamp = int(time.time())
        if current_timestamp < expiration_timestamp:
            print("Refresh token expires in %d days" % ((expiration_timestamp - current_timestamp)//(24*3600)))
        else:
            print("Refresh token has expired")

    elif checkin_access_token:
        try:
            payload = jwt.decode(checkin_access_token, verify=False)
        except jwt.exceptions.InvalidTokenError:
            raise SystemExit("Error: Invalid access token.")

        expiration_timestamp = int(payload['exp'])
        expiration_time = datetime.utcfromtimestamp(expiration_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print("Access token is valid to %s UTC" % expiration_time)
        current_timestamp = int(time.time())
        if current_timestamp < expiration_timestamp:
            print("Access token expires in %d seconds" % (expiration_timestamp - current_timestamp))
        else:
            print("Access token has expired")
    else:
        print("Checkin access token or refresh token required")
        exit(1)


@token.command()
@click.option(
    "--checkin-client-id",
    help="Check-in client id",
    envvar="CHECKIN_CLIENT_ID",
)
@click.option(
    "--checkin-client-secret",
    help="Check-in client secret",
    envvar="CHECKIN_CLIENT_SECRET",
)
@click.option(
    "--checkin-refresh-token",
    help="Check-in client id",
    envvar="CHECKIN_REFRESH_TOKEN",
)
@click.option(
    "--checkin-access-token",
    help="Check-in access token",
    envvar="CHECKIN_ACCESS_TOKEN",
)
@click.option(
    "--checkin-url",
    help="Check-in OIDC URL",
    envvar="CHECKIN_OIDC_URL",
    default=DEFAULT_CHECKIN_URL,
    show_default=True,
)
def list_vos(
        checkin_client_id,
        checkin_client_secret,
        checkin_refresh_token,
        checkin_access_token,
        checkin_url
):
    """
    CLI command for listing VO memberships according to access token
    """

    checkin_access_token = get_access_token(
        checkin_access_token,
        checkin_refresh_token,
        checkin_client_id,
        checkin_client_secret,
        checkin_url)

    vos = token_list_vos(checkin_access_token, checkin_url)
    print("\n".join(vos))
