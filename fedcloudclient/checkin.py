import functools
import re
import time
from datetime import datetime

import click
import jwt
import requests
import liboidcagent as agent

DEFAULT_OIDC_URL = "https://aai.egi.eu/oidc"


def oidc_discover(oidc_url):
    """
    Discover oidc endpoints

    :param oidc_url: CheckIn URL
    :return: JSON object of OIDC configuration
    """
    r = requests.get(oidc_url + "/.well-known/openid-configuration")
    r.raise_for_status()
    return r.json()


def token_refresh(
        oidc_client_id, oidc_client_secret, oidc_refresh_token, oidc_url
):
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

    r = requests.post(
        oidc_ep["token_endpoint"],
        auth=(oidc_client_id, oidc_client_secret),
        data=refresh_data
    )
    r.raise_for_status()
    return r.json()


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
    Getting access token.
    Generate new access token from oidc-agent or refresh token (if given)
    or use existing token

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
            access_token = agent.get_access_token(oidc_agent_account,
                                                  min_valid_period=30,
                                                  application_hint="fedcloudclient")
            return access_token
        except agent.OidcAgentError as e:
            print("ERROR oidc-agent: {}".format(e))

    # Then try refresh token
    if (oidc_refresh_token and oidc_client_id
            and oidc_client_secret and oidc_url):
        print("WARNING: exposing refresh tokens is insecure and will be disable in next version!")
        return token_refresh(
            oidc_client_id,
            oidc_client_secret,
            oidc_refresh_token,
            oidc_url)["access_token"]

    # Then finally access token
    elif oidc_access_token:

        # Check expiration time of access token
        try:
            payload = jwt.decode(oidc_access_token, options={"verify_signature": False})
        except jwt.exceptions.InvalidTokenError:
            raise SystemExit("Error: Invalid access token.")

        expiration_timestamp = int(payload['exp'])
        current_timestamp = int(time.time())
        if current_timestamp > expiration_timestamp - 10:
            raise SystemExit("The given access token has expired."
                             + " Get new access token before continuing on operation")
        return oidc_access_token
    else:
        raise SystemExit("Error: An access token is needed for the operation. You can specify access token"
                         " directly via --oidc-access-token option or use oidc-agent via --oidc-agent-account")


def token_list_vos(oidc_access_token, oidc_url):
    """
    List VO memberships in EGI Check-in

    :param oidc_access_token:
    :param oidc_url:
    :return: list of VO names
    """
    oidc_ep = oidc_discover(oidc_url)
    r = requests.get(
        oidc_ep["userinfo_endpoint"],
        headers={"Authorization": "Bearer %s" % oidc_access_token})

    r.raise_for_status()
    vos = []
    m = re.compile("urn:mace:egi.eu:group:(.+?):(.+:)*role=member#aai.egi.eu")
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


def oidc_params(func):
    """
    Decorator for OIDC parameters

    :param func:
    :return:
    """
    @click.option(
        "--oidc-client-id",
        help="OIDC client id",
        envvar="OIDC_CLIENT_ID",
    )
    @click.option(
        "--oidc-client-secret",
        help="OIDC client secret",
        envvar="OIDC_CLIENT_SECRET",
    )
    @click.option(
        "--oidc-refresh-token",
        help="OIDC refresh token",
        envvar="OIDC_REFRESH_TOKEN",
    )
    @click.option(
        "--oidc-access-token",
        help="OIDC access token",
        envvar="OIDC_ACCESS_TOKEN",
    )
    @click.option(
        "--oidc-url",
        help="OIDC URL",
        envvar="OIDC_URL",
        default=DEFAULT_OIDC_URL,
        show_default=True,
    )
    @click.option(
        "--oidc-agent-account",
        help="short account name in oidc-agent",
        envvar="OIDC_AGENT_ACCOUNT",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@token.command()
@click.option(
    "--oidc-refresh-token",
    help="OIDC refresh token",
    envvar="OIDC_REFRESH_TOKEN",
)
@click.option(
    "--oidc-access-token",
    help="OIDC access token",
    envvar="OIDC_ACCESS_TOKEN",
)
def check(
        oidc_refresh_token,
        oidc_access_token
):
    """
    CLI command for printing validity of access or refresh token
    """

    if oidc_refresh_token:
        try:
            payload = jwt.decode(oidc_refresh_token, options={"verify_signature": False})
        except jwt.exceptions.InvalidTokenError:
            raise SystemExit("Error: Invalid refresh token.")

        expiration_timestamp = int(payload['exp'])
        expiration_time = datetime.utcfromtimestamp(expiration_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print("Refresh token is valid to %s UTC" % expiration_time)
        current_timestamp = int(time.time())
        if current_timestamp < expiration_timestamp:
            print("Refresh token expires in %d days" % ((expiration_timestamp - current_timestamp) // (24 * 3600)))
        else:
            print("Refresh token has expired")

    elif oidc_access_token:
        try:
            payload = jwt.decode(oidc_access_token, options={"verify_signature": False})
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
        print("OIDC access token or refresh token required")
        exit(1)


@token.command()
@oidc_params
def list_vos(
        oidc_client_id,
        oidc_client_secret,
        oidc_refresh_token,
        oidc_access_token,
        oidc_url,
        oidc_agent_account,
):
    """
    CLI command for listing VO memberships according to access token
    """
    oidc_access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account)

    vos = token_list_vos(oidc_access_token, oidc_url)
    print("\n".join(vos))
