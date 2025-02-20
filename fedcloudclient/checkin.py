"""
Implementation of "fedcloud token" commands for interactions with EGI Check-in and
access tokens
"""

import click
from fedcloudclient.auth import OIDCToken
from fedcloudclient.decorators import oidc_params


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
    token=OIDCToken(access_token)
    token.check_token(access_token, verbose=True)


@token.command()
@oidc_params
def list_vos(access_token):
    """
    List VO membership(s) of access token
    """
    token=OIDCToken(access_token)
    vos = token.token_list_vos(access_token)
    print("\n".join(vos))


@token.command()
@oidc_params
def issue(access_token):
    """
    print access token (from mytoken or oidc-agent)
    """
    print(access_token)
