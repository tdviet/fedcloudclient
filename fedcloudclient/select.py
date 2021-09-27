"""
Implementation of "fedcloud select" commands for selecting suitable flavors
or images on different OpenStack sites
"""
import json

import click
import yaml
from jsonpath_ng.exceptions import JSONPathError
from jsonpath_ng.ext import parse

from fedcloudclient.checkin import get_access_token
from fedcloudclient.decorators import (
    flavor_output_params,
    flavor_specs_params,
    image_output_params,
    image_specs_params,
    network_output_params,
    network_specs_params,
    oidc_params,
    site_params,
    vo_params,
)
from fedcloudclient.openstack import fedcloud_openstack
from fedcloudclient.sites import find_endpoint_and_project_id

filter_template = "$[?( {specs} )]"
get_flavor_command = ("flavor", "list", "--long")
get_network_command = ("network", "list", "--long")
get_image_command = ("image", "list", "--long", "--sort", "created_at:desc")


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


@click.group()
def select():
    """
    Select resources according to specification
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

    filter_string = construct_filter(flavor_specs, filter_template)
    try:
        parser = get_parser(filter_string)
    except JSONPathError as exception:
        print("Error during constructing filter")
        print("Filter string: ", filter_string)
        print(str(exception))
        exit(1)

    error_code, flavors = get_resource(access_token, site, vo, get_flavor_command)
    if error_code:
        print("Error during getting flavor list")
        print("Error code: ", error_code)
        print("Error message: ", flavors)
        exit(2)

    match_flavors = do_filter(parser, flavors)
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
        print(yaml.dump(sorted_flavors, sort_keys=False))
    else:
        print(json.dumps(sorted_flavors, indent=4))


@select.command()
@site_params
@vo_params
@image_specs_params
@image_output_params
@oidc_params
def image(
    site,
    vo,
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    image_specs,
    image_output,
):
    """
    Select suitable images according to image specifications on the given site/VO
    """
    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )

    image_specs = list(image_specs)
    filter_string = construct_filter(image_specs, filter_template)
    try:
        parser = get_parser(filter_string)
    except JSONPathError as exception:
        print("Error during constructing filter")
        print("Filter string: ", filter_string)
        print(str(exception))
        exit(1)

    error_code, images = get_resource(access_token, site, vo, get_image_command)
    if error_code:
        print("Error during getting image list")
        print("Error code: ", error_code)
        print("Error message: ", images)
        exit(2)

    match_images = do_filter(parser, images)
    if len(match_images) == 0:
        print("Error: No image matched specifications")
        exit(3)

    if image_output == "first":
        print(match_images[0].get("Name"))
    elif image_output == "list":
        for image_item in match_images:
            print(image_item.get("Name"))
    elif image_output == "YAML":
        print(yaml.dump(match_images, sort_keys=False))
    else:
        print(json.dumps(match_images, indent=4))


@select.command()
@site_params
@vo_params
@network_specs_params
@network_output_params
@oidc_params
def network(
    site,
    vo,
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    network_specs,
    network_output,
):
    """
    Select suitable network according to network specifications on the given site/VO
    """
    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )

    error_code, networks = get_resource(access_token, site, vo, get_network_command)
    if error_code:
        print("Error during getting network list")
        print("Error code: ", error_code)
        print("Error message: ", networks)
        exit(2)

    _, project_id, _ = find_endpoint_and_project_id(site, vo)
    match_network = filter_network(networks, network_specs, project_id)

    if len(match_network) == 0:
        print("Error: No network matched specifications")
        exit(3)

    if network_output == "first":
        print(match_network[0].get("Name"))
    elif network_output == "list":
        for network_object in match_network:
            print(network_object.get("Name"))
    elif network_output == "YAML":
        print(yaml.dump(match_network, sort_keys=False))
    else:
        print(json.dumps(match_network, indent=4))
