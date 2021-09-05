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

from fedcloudclient.checkin import get_access_token
from fedcloudclient.decorators import (
    ALL_SITES_KEYWORDS,
    DEFAULT_PROTOCOL,
    all_site_params,
    oidc_params,
    site_vo_params,
)
from fedcloudclient.shell import printComment, printSetEnvCommand

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
    if isinstance(url, str) and url.lower().startswith(
        "https://"
    ):  # Only read from HTTPS location
        req = Request(url)
    else:
        raise SystemExit("Error: remote filename not starting with https:// : %s" % url)

    # URLs already checked, so ignore bandit test
    data = None
    try:
        with urlopen(req) as yaml_file:  # nosec
            if int(yaml_file.headers["Content-Length"]) > max_length:
                raise SystemExit(
                    "Error: remote file %s is larger than limit %d " % (url, max_length)
                )
            data = yaml.safe_load(yaml_file)
    except Exception as e:
        print("Error during reading data from %s" % url)
        raise SystemExit("Exception: %s" % e)
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
        except Exception as e:
            print("Site config in file %s is in wrong format" % filename)
            raise SystemExit("Exception: %s" % e)

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
    for f in sorted(config_dir.glob("*.yaml")):
        try:
            yaml_file = f.open()
            site_info = yaml.safe_load(yaml_file)
            validate(instance=site_info, schema=schema)
            __site_config_data.append(site_info)
        except Exception as e:
            print("Error during reading site config from %s" % f)
            raise SystemExit("Exception: %s" % e)


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
        with config_file.open("w", encoding="utf-8") as f:
            yaml.dump(site_info, f)


def delete_site_config(config_dir):
    """
    Delete site configs to local directory specified in config_dir

    :param config_dir: path to directory containing site configuration
    :return: None
    """
    shutil.rmtree(config_dir, ignore_errors=True)


def list_sites():
    """
    List of all sites IDs in site configurations

    :return: list of site IDs
    """
    read_site_config()
    result = []
    for site_info in __site_config_data:
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


@click.group()
def site():
    """
    Obtain site configurations
    """
    pass


@site.command()
@all_site_params
def show(site, all_sites):
    """
    Print configuration of specified site(s)
    """
    if site in ALL_SITES_KEYWORDS or all_sites:
        read_site_config()
        for site_info in __site_config_data:
            site_info_str = yaml.dump(site_info, sort_keys=True)
            print(site_info_str)
        return 0

    site_info = find_site_data(site)
    if site_info:
        print(yaml.dump(site_info, sort_keys=True))
    else:
        print("Site %s not found" % site)
        return 1


@site.command()
@site_vo_params
def show_project_id(site, vo):
    """
    Print Keystone endpoint and project ID
    """
    if site in ALL_SITES_KEYWORDS:
        print("Cannot get project ID for ALL_SITES")
        raise click.Abort()

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    if endpoint:
        printSetEnvCommand("OS_AUTH_URL", endpoint)
        printSetEnvCommand("OS_PROJECT_ID", project_id)
    else:
        print("VO %s not found on site %s" % (vo, site))
        return 1


@site.command()
def save_config():
    """
    Load site configs from GitHub, save them to local folder in $HOME
    Overwrite local configs if exist.
    """
    read_default_site_config()
    config_dir = Path.home() / __LOCAL_CONFIG_DIR
    print("Saving site configs to directory %s" % config_dir)
    delete_site_config(config_dir)
    save_site_config(config_dir)


@site.command()
def list():
    """
    List all sites
    """
    read_site_config()
    for site_info in __site_config_data:
        print(site_info["gocdb"])


@site.command()
@site_vo_params
@oidc_params
def env(
    site,
    vo,
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
):
    """
    Generate OS environment variables for site.
    May set also environment variable OS_ACCESS_TOKEN,
    if access token is provided, otherwise print notification
    """
    if site in ALL_SITES_KEYWORDS:
        print("Cannot generate environment variables for ALL_SITES")
        raise click.Abort()

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    if endpoint:
        if protocol is None:
            protocol = DEFAULT_PROTOCOL
        printSetEnvCommand("OS_AUTH_URL", endpoint)
        printSetEnvCommand("OS_AUTH_TYPE", "v3oidcaccesstoken")
        printSetEnvCommand("OS_IDENTITY_PROVIDER", "egi.eu")
        printSetEnvCommand("OS_PROTOCOL", protocol)
        printSetEnvCommand("OS_PROJECT_ID", project_id)
        if (
            oidc_agent_account
            or oidc_access_token
            or (oidc_refresh_token and oidc_client_id and oidc_client_secret)
        ):
            access_token = get_access_token(
                oidc_access_token,
                oidc_refresh_token,
                oidc_client_id,
                oidc_client_secret,
                oidc_url,
                oidc_agent_account,
            )
            printSetEnvCommand("OS_ACCESS_TOKEN", access_token)
        else:
            printComment("Remember to set also OS_ACCESS_TOKEN")
    else:
        print("VO %s not found to have access to site %s" % (vo, site))
    return 1
