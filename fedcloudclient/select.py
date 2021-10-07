"""
Implementation of "fedcloud select" commands for selecting suitable flavors
or images on different OpenStack sites
"""
import json

import click
import yaml
from jsonpath_ng.exceptions import JSONPathError
from jsonpath_ng.ext import parse

from fedcloudclient.decorators import (
    flavor_specs_params,
    image_specs_params,
    network_specs_params,
    oidc_params,
    select_output_format_params,
    site_params,
    vo_params,
)
from fedcloudclient.openstack import fedcloud_openstack
from fedcloudclient.sites import find_endpoint_and_project_id

FILTER_TEMPLATE = "$[?( {specs} )]"
GET_FLAVOR_COMMAND = ("flavor", "list", "--long")
GET_NETWORK_COMMAND = ("network", "list", "--long")
GET_IMAGE_COMMAND = ("image", "list", "--long", "--sort", "created_at:desc")


def compare_flavors(flavor_item):
    """
    Helper function for sorting flavors.
    Sorting order: Flavors with lower resources first.
    Resource importance order: GPUs, CPUs, RAM, Disk, Ephemeral.

    :param flavor_item:

    :return:
    """
    return (
        flavor_item.get("Properties", {}).get("Accelerator:Number", "0"),
        flavor_item.get("VCPUs"),
        flavor_item.get("RAM"),
        flavor_item.get("Disk"),
        flavor_item.get("Ephemeral"),
    )


def sort_flavors(flavors):
    """
    Sorting flavors, flavors with low resources first

    :param flavors: flavor list in JSON

    :return: sorted flavor list in JSON
    """
    return sorted(flavors, key=compare_flavors)


def get_resource(oidc_access_token, site, vo, command):
    """
    Getting list of flavors for the given site and VO, using
    `openstack flavor list --long` command

    :param command:
    :param site:
    :param oidc_access_token:
    :param vo: self descriptive

    :return: list of flavors in JSON formats
    """

    error_code, resource = fedcloud_openstack(oidc_access_token, site, vo, command)
    if error_code:
        command_string = " ".join(command)
        raise SystemExit(
            "Error during executing command: "
            f"fedcloud openstack {command_string} --site {site} --vo {vo}\n"
            f"Error code: {error_code}\n"
            f"Error message: {resource}\n"
        )
    return resource


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
    Build parser according to specification.
    Raise SystemExit with error message if invalid filter string

    :param filter_string:

    :return: jsonpath parser
    """

    try:
        parser = parse(filter_string)
    except JSONPathError as exception:
        raise SystemExit(
            "Error during constructing filter\n"
            f"Filter string: {filter_string}\n"
            f"{exception}"
        )
    return parser


def do_filter(parser, input_list):
    """
    Filter flavor by applying  parser on the flavor list

    :param input_list: list of input data in JSON format
    :param parser: jsonpath parser

    :return: list of matched flavors in JSON
    """
    try:
        matched = [match.value for match in parser.find(input_list)]
    except TypeError as exception:
        raise SystemExit(
            "TypeError during filtering result\n"
            "Probably string value for numeric property in filter\n"
            f"{exception}"
        )
    return matched


def compare_network(network_item):
    """
    Helper function for sorting network
    Sorting order: public, private shared, private

    :param network_item:

    :return:
    """
    return (
        1 if network_item.get("Router Type") else 0,
        1 if network_item.get("Shared") else 0,
    )


def filter_network(networks, network_specs, project_id):
    """
    Filter network according to network specifications

    :param networks: List of all networks
    :param network_specs: Network specifications
    :param project_id: Project ID for assessment of access

    :return: List of matched network
    """
    match_networks = []

    for network_item in networks:
        if network_item.get("Shared") or network_item.get("Project") == project_id:
            if network_specs == "private":
                if not network_item.get("Router Type"):
                    match_networks.append(network_item)
            elif network_specs == "public":
                if network_item.get("Router Type"):
                    match_networks.append(network_item)
            else:
                match_networks.append(network_item)

    return sorted(match_networks, key=compare_network, reverse=True)


def print_output(resource_list, output_format):
    """
    Print resource list according to output format

    :param resource_list: resource list
    :param output_format: output format

    :return: None
    """

    if len(resource_list) == 0:
        raise SystemExit("Error: No resource matched specification")

    if output_format == "first":
        print(resource_list[0].get("Name"))
    elif output_format == "list":
        for resource_item in resource_list:
            print(resource_item.get("Name"))
    elif output_format == "YAML":
        print(yaml.dump(resource_list, sort_keys=False))
    else:
        print(json.dumps(resource_list, indent=4))


@click.group()
def select():
    """
    Select resources according to specification
    """


@select.command()
@site_params
@vo_params
@flavor_specs_params
@select_output_format_params
@oidc_params
def flavor(
    site,
    vo,
    access_token,
    flavor_specs,
    vcpus,
    ram,
    gpus,
    output_format,
):
    """
    Select suitable flavors according to flavor specifications on the given site/VO
    """

    flavor_specs = list(flavor_specs)
    if vcpus:
        flavor_specs.append(f"VCPUs=={vcpus}")
    if ram:
        flavor_specs.append(f"=={ram}")
    if gpus:
        flavor_specs.append(f"Properties.'Accelerator:Number'=~'{gpus}'")

    filter_string = construct_filter(flavor_specs, FILTER_TEMPLATE)
    parser = get_parser(filter_string)
    flavors = get_resource(access_token, site, vo, GET_FLAVOR_COMMAND)

    match_flavors = do_filter(parser, flavors)

    sorted_flavors = sort_flavors(match_flavors)
    print_output(sorted_flavors, output_format)


@select.command()
@site_params
@vo_params
@image_specs_params
@select_output_format_params
@oidc_params
def image(
    site,
    vo,
    access_token,
    image_specs,
    output_format,
):
    """
    Select suitable images according to image specifications on the given site/VO
    """

    image_specs = list(image_specs)
    filter_string = construct_filter(image_specs, FILTER_TEMPLATE)
    parser = get_parser(filter_string)
    images = get_resource(access_token, site, vo, GET_IMAGE_COMMAND)

    match_images = do_filter(parser, images)

    print_output(match_images, output_format)


@select.command()
@site_params
@vo_params
@network_specs_params
@select_output_format_params
@oidc_params
def network(
    site,
    vo,
    access_token,
    network_specs,
    output_format,
):
    """
    Select suitable network according to network specifications on the given site/VO
    """

    networks = get_resource(access_token, site, vo, GET_NETWORK_COMMAND)

    _, project_id, _ = find_endpoint_and_project_id(site, vo)
    match_network = filter_network(networks, network_specs, project_id)

    print_output(match_network, output_format)
