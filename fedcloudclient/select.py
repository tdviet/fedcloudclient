"""
Implementation of "fedcloud select" commands for selecting suitable flavors
or images on different OpenStack sites
"""
import json

import click
import yaml
from jsonpath_ng.exceptions import JsonPathParserError
from jsonpath_ng.ext import parse

from fedcloudclient.checkin import get_access_token
from fedcloudclient.decorators import (
    flavor_output_params,
    flavor_specs_params,
    oidc_params,
    site_params,
    vo_params,
)
from fedcloudclient.openstack import fedcloud_openstack

flavor_match_template = "$[?( {specs} )]"


def compare_flavors(flavor_object):
    """
    Helper function for sorting flavors.
    Sorting order: Flavors with lower resources first.
    Resource importance order: GPUs, CPUs, RAM, Disk, Ephemeral.

    :param flavor_object:
    :return:
    """
    return (
        flavor_object.get("Properties", {}).get("Accelerator:Number", "0"),
        flavor_object.get("VCPUs"),
        flavor_object.get("RAM"),
        flavor_object.get("Disk"),
        flavor_object.get("Ephemeral"),
    )


def sort_flavors(flavors):
    """
    Sorting flavors, flavors with low resources first

    :param flavors: flavor list in JSON
    :return: sorted flavor list in JSON
    """
    return sorted(flavors, key=compare_flavors)


def get_flavors(oidc_access_token, site, vo):
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


def construct_filter(specs, match_template):
    """
    Build parser according to specification

    :param match_template:
    :param specs: list of strings of specifications
    :return: filter string
    """

    spec_string = " & ".join(specs)
    return match_template.format(specs=spec_string)


def get_parser(filter_string):
    """
    Build parser according to specification

    :param filter_string:

    :return: jsonpath parser
    """
    return parse(filter_string)


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
@flavor_specs_params
@flavor_output_params
@oidc_params
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
    flavor_output,
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

    filter_string = construct_filter(flavor_specs, flavor_match_template)
    try:
        flavor_parser = get_parser(filter_string)
    except JsonPathParserError as exception:
        print("Error during constructing filter")
        print("Filter string: ", filter_string)
        print(str(exception))
        exit(1)

    error_code, flavors = get_flavors(access_token, site, vo)
    if error_code:
        print("Error during getting flavor list")
        print("Error code: ", error_code)
        print("Error message: ", flavors)
        exit(2)

    match_flavors = do_filter(flavor_parser, flavors)
    if len(match_flavors) == 0:
        print("Error: No flavor matched specifications")
        exit(3)

    sorted_flavors = sort_flavors(match_flavors)

    if flavor_output == "first":
        print(sorted_flavors[0].get("Name"))
    elif flavor_output == "list":
        for flavor_object in sorted_flavors:
            print(flavor_object.get("Name"))
    elif flavor_output == "YAML":
        print(yaml.dump(sorted_flavors))
    else:
        print(json.dumps(sorted_flavors, indent=4))
