"""
Implementation of "fedcloud token" commands for interactions with EGI Check-in and
access tokens
"""

import click
from tabulate import tabulate
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
    token=OIDCToken()
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

@token.command()
@oidc_params
def conf(access_token):
    """
    print config values
    """
    token=OIDCToken(access_token)
    list_conf=list()
    for item in token.CONF:
        list_conf.append([str(item), str(token.CONF[item])])

    print(
        tabulate(
            list_conf, headers=["Key", "Value"])
        )

