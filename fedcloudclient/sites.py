"""
"fedcloud site" commands will read site configurations and manipulate with them. If
the local site configurations exist at ~/.config/fedcloud/site-config/, fedcloud will
read them from there, otherwise the commands will read from GitHub repository.

By default, fedcloud does not save anything on local disk, users have to save the
site configuration to local disk explicitly via "fedcloud site save-config" command.
The advantage of having local site configurations, beside faster loading, is to give
users ability to make customizations, e.g. add additional VOs, remove sites they
do not have access, and so on.
"""

import builtins
import json
import shutil
from pathlib import Path
from typing import List
from urllib.request import Request, urlopen

import click
import pkg_resources
import yaml
from jsonschema import validate

from fedcloudclient.conf import CONF
from fedcloudclient.decorators import (
    ALL_SITES_KEYWORDS,
    all_site_params,
    oidc_params,
    site_vo_params,
    vo_params_optional,
)
from fedcloudclient.shell import print_set_env_command

DEFAULT_PROTOCOL = CONF.get("os_protocol")

__REMOTE_CONFIG_FILE = (
    "https://raw.githubusercontent.com/tdviet/fedcloudclient/master/config/sites.yaml"
)

# WARNING:
# ALL FILES in this site-config directory WILL BE DELETED  at every execution
# of "fedcloud site save-config" command. Do not change it to a common directory
__LOCAL_CONFIG_DIR = ".config/fedcloud/site-config/"

__site_config_data: List[dict] = []

__FILE_SIZE_LIMIT = 1024 * 1024  # Max size for config files


def read_site_schema():
    """
    Read schema.json for validating site configuration

    :return: JSON object from schema.json
    """
    file = pkg_resources.resource_stream("fedcloudclient", "schema.json")
    schema = json.load(file)
    return schema


def read_site_config():
    """
    Read site configurations from local config dir if exist, otherwise from default
    GitHub location. Storing site configurations in global variable, that will be
    used by other functions. Call read_local_site_config()
    or read_default_site_config()

    :return: None
    """
    if len(__site_config_data) > 0:
        return
    config_dir = Path.home() / __LOCAL_CONFIG_DIR
    if config_dir.exists():
        read_local_site_config(config_dir)
    else:
        read_default_site_config()


def safe_read_yaml_from_url(url, max_length):
    """
    Safe reading from URL
    Check URL and size before reading

    :param url:
    :param max_length:
    :return: data from URL
    """

    # if isinstance(url, str) and url.lower().startswith(
    #     "https://"
    # ):  # Only read from HTTPS location
    #     req = Request(url)
    # else:
    #     raise SystemExit(f"Error: remote filename not starting with https:// : {url}")

    # ignore bandit test because url is taken from configuration
    req = Request(url)
    data = None
    try:
        with urlopen(req) as yaml_file:  # nosec
            if int(yaml_file.headers["Content-Length"]) > max_length:
                raise SystemExit(
                    f"Error: remote file {url} is larger than limit {max_length} "
                )
            data = yaml.safe_load(yaml_file)
    except Exception as exception:
        print(f"Error during reading data from {url}")
        raise SystemExit(f"Exception: {exception}") from exception
    return data


def read_default_site_config():
    """
    Read default site configurations from GitHub
    Storing site configurations in a global variable that will be used by other functions

    :return: None
    """
    __site_config_data.clear()
    schema = read_site_schema()

    site_list = safe_read_yaml_from_url(__REMOTE_CONFIG_FILE, __FILE_SIZE_LIMIT)

    # Check data format of site list
    if not isinstance(site_list, builtins.list):
        raise SystemExit("Error: site list is in a wrong format")

    for filename in site_list:
        site_info = safe_read_yaml_from_url(filename, __FILE_SIZE_LIMIT)

        # Validating site config after reading
        try:
            validate(instance=site_info, schema=schema)
        except Exception as exception:
            print(f"Site config in file {filename} is in wrong format")
            raise SystemExit(f"Exception: {exception}") from exception

        __site_config_data.append(site_info)


def read_local_site_config(config_dir):
    """
    Read site configurations from local directory specified in config_dir
    Storing site configurations in global variable, that will be used by other functions

    :param config_dir: path to directory containing site configuration
    :return: None
    """
    __site_config_data.clear()
    schema = read_site_schema()
    config_dir = Path(config_dir)
    for file in sorted(config_dir.glob("*.yaml")):
        try:
            yaml_file = file.open()
            site_info = yaml.safe_load(yaml_file)
            validate(instance=site_info, schema=schema)
            __site_config_data.append(site_info)
        except Exception as exception:
            print(f"Error during reading site config from {file}")
            raise SystemExit(f"Exception: {exception}") from exception


def save_site_config(config_dir):
    """
    Save site configs to local directory specified in config_dir
    Overwrite local configs if exist

    :param config_dir: path to directory containing site configuration
    :return: None
    """
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    for site_info in __site_config_data:
        config_file = config_dir / (site_info["gocdb"] + ".yaml")
        with config_file.open("w", encoding="utf-8") as file:
            yaml.dump(site_info, file)


def delete_site_config(config_dir):
    """
    Delete site configs to local directory specified in config_dir

    :param config_dir: path to directory containing site configuration
    :return: None
    """
    shutil.rmtree(config_dir, ignore_errors=True)


def list_sites(vo=None):
    """
    List all sites IDs in site configurations
    Optionally list all sites supporting a Virtual Organization

    :return: list of site IDs
    """
    read_site_config()
    result = []
    for site_info in __site_config_data:
        if vo is None:
            result.append(site_info["gocdb"])
        else:
            for vos in site_info["vos"]:
                if vo == vos["name"]:
                    result.append(site_info["gocdb"])
    return result


def find_site_data(site_name):
    """
    Return configuration of the correspondent site with site_name

    :param site_name: site ID in GOCDB
    :return: configuration of site if found, otherwise None
    """
    read_site_config()

    for site_info in __site_config_data:
        if site_info["gocdb"] == site_name:
            return site_info
    return None


def find_endpoint_and_project_id(site_name, vo):
    """
    Return Keystone endpoint and project ID from site name and VO according
    to site configuration

    :param site_name: site ID in GOCDB
    :param vo: VO name or None to find site endpoint only
    :return: endpoint, project_id, protocol if the VO has access to the site,
             otherwise None, None, None
    """
    site_info = find_site_data(site_name)
    if site_info is None:
        return None, None, None

    protocol = site_info.get("protocol")
    # If only site name is given, return endpoint without project ID
    if vo is None:
        return site_info["endpoint"], None, protocol

    for vo_info in site_info["vos"]:
        if vo_info["name"] == vo:
            return site_info["endpoint"], vo_info["auth"]["project_id"], protocol

    # Return None if VO not found among those that have access to site
    return None, None, None


def find_vo_from_project_id(site_name, project_id):
    """
    Return the VO name form the project ID and site_name according
    to site configuration

    :param site_name: site ID in GOCDB
    :param project_id: project_id configured to support the VO
    :return: vo if the VO is configured, otherwise None
    """
    site_info = find_site_data(site_name)
    if site_info is None:
        return None

    for vo_info in site_info["vos"]:
        if vo_info.get("auth", {}).get("project_id", None) == project_id:
            return vo_info["name"]

    # Return None if the project is not found
    return None


@click.group()
def site():
    """
    Obtain site configurations
    """


@site.command()
@all_site_params
def show(site_local, all_sites):
    """
    Print configuration of specified site(s)
    """
    if site_local in ALL_SITES_KEYWORDS or all_sites:
        read_site_config()
        for site_info in __site_config_data:
            site_info_str = yaml.dump(site_info, sort_keys=True)
            print(site_info_str)

    else:
        site_info = find_site_data(site_local)
        if site_info:
            print(yaml.dump(site_info, sort_keys=True))
        else:
            raise SystemExit(f"Site {site_local} not found")


@site.command()
@site_vo_params
def show_project_id(site_local, vo):
    """
    Print Keystone endpoint and project ID
    """
    if site_local in ALL_SITES_KEYWORDS:
        print("Cannot get project ID for ALL_SITES")
        raise click.Abort()

    endpoint, project_id, _ = find_endpoint_and_project_id(site_local, vo)
    if endpoint:
        print_set_env_command("OS_AUTH_URL", endpoint)
        print_set_env_command("OS_PROJECT_ID", project_id)
    else:
        raise SystemExit(f"VO {vo} not found on site {site_local}")


@site.command()
def save_config():
    """
    Load site configs from GitHub, save them to local folder in $HOME
    Overwrite local configs if existed.
    """
    read_default_site_config()
    config_dir = Path.home() / __LOCAL_CONFIG_DIR
    # delete_site_config(config_dir) # too dangerous, should check and ask for confirmation before deleting
    print(f"Saving site configs to directory {config_dir}")
    save_site_config(config_dir)


@site.command("list")
@vo_params_optional
def list_(vo=None):
    """
    List all sites. If "--vo <name>" is provided, list only sites
    supporting a Virtual Organization.
    """
    for site_local in list_sites(vo):
        print(site_local)


@site.command()
@site_vo_params
@oidc_params
def env(
    site_local,
    vo,
    access_token,
):
    """
    Generate OS environment variables for site.
    May set also environment variable OS_ACCESS_TOKEN,
    if access token is provided, otherwise print notification
    """
    if site_local in ALL_SITES_KEYWORDS:
        print("Cannot generate environment variables for ALL_SITES")
        raise click.Abort()

    endpoint, project_id, protocol = find_endpoint_and_project_id(site_local, vo)
    if endpoint:
        if protocol is None:
            protocol = DEFAULT_PROTOCOL
        print_set_env_command("OS_AUTH_URL", endpoint)
        print_set_env_command("OS_AUTH_TYPE", "v3oidcaccesstoken")
        print_set_env_command("OS_IDENTITY_PROVIDER", "egi.eu")
        print_set_env_command("OS_PROTOCOL", protocol)
        print_set_env_command("OS_PROJECT_ID", project_id)
        print_set_env_command("OS_ACCESS_TOKEN", access_token)
    else:
        print(f"VO {vo} not found to have access to site {site_local}")
    return 1
