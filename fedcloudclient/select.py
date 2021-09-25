"""
Implementation of "fedcloud select" commands for selecting suitable flavors
or images on different OpenStack sites
"""
import json

import click
from jsonpath_ng.ext import parse

from fedcloudclient.checkin import get_access_token
from fedcloudclient.decorators import flavor_specs_params, oidc_params, site_params, vo_params
from fedcloudclient.openstack import fedcloud_openstack

flavor_match_template = "$[?( {specs} )]"


def get_flavors(oidc_access_token, site, vo, ):
    """
    Getting list of flavors for the given site and VO, using
    `openstack flavor list --long` command

    :param site:
    :param oidc_access_token:
    :param vo: self descriptive

    :return: list of flavors in JSON formats
    """
    command = ("flavor", "list", "--long")
    return fedcloud_openstack(oidc_access_token, site, vo, command)


def get_parser(specs, match_template):
    """
    Build parser according to specification

     :param match_template:
     :param specs: list of strings of specifications

     :return: jsonpath parser
     """
    spec_string = " & ".join(specs)
    match_string = match_template.format(specs=spec_string)
    return parse(match_string)


def do_filter(parser, input_list):
    """
     Filter flavor by applying  parser on the flavor list

     :param input_list: list of input data in JSON format
     :param parser: jsonpath parser

     :return: list of matched flavors in JSON
     """
    return [match.value for match in parser.find(input_list)]


@click.group()
def select():
    """
    Obtain site configurations
    """
    pass


@select.command()
@site_params
@vo_params
@oidc_params
@flavor_specs_params
def flavor(
    site,
    vo,
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    flavor_specs,
    vcpus,
    ram,
    gpus,
):
    """
    Select suitable flavors according to flavor specifications on the given site/VO
    """
    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )

    flavor_specs = list(flavor_specs)
    if vcpus:
        flavor_specs.append("VCPUs=={cpus}".format(cpus=vcpus))
    if ram:
        flavor_specs.append("=={RAM}".format(RAM=ram))
    if gpus:
        flavor_specs.append("Properties.'Accelerator:Number'=={gpus}".format(gpus=gpus))

    error_code, flavors = get_flavors(access_token, site, vo)

    flavor_parser = get_parser(flavor_specs, flavor_match_template)
    match_flavors = do_filter(flavor_parser, flavors)

    print(json.dumps(match_flavors, indent=4))
