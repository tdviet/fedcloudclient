"""
"fedcloud endpoint" commands are complementary part of the "fedcloud site" commands.

Instead of using site configurations defined in files saved in GitHub repository or
local disk, the commands try to get site information directly from GOCDB
(Grid Operations Configuration Management Database) https://goc.egi.eu/ or make probe
test on sites
"""

import os
import sys
from urllib import parse

import click
import requests
from defusedxml import ElementTree
from tabulate import tabulate

from fedcloudclient.decorators import (
    ALL_SITES_KEYWORDS,
    all_site_params,
    oidc_params,
    project_id_params,
    site_params,
)
from fedcloudclient.shell import print_set_env_command
from fedcloudclient.sites import find_vo_from_project_id

OPENSTACK_NOVA = "org.openstack.nova"
GOCDB_PUBLICURL = "https://goc.egi.eu/gocdbpi/public/"
TIMEOUT = 10
TLS_ERROR_MSG = "TLS error. IGTF certificates may not have been installed"
CONNECTION_ERROR_MSG = "Connection error"
SCOPED_TOKEN_ERROR_MSG = "Unable to get a scoped token"
UNSCOPED_TOKEN_ERROR_MSG = "Unable to get an unscoped token"


class TokenException(Exception):
    """Exception for Token related errors"""

    # Basic exception. This should be extended


def get_sites():
    """
    Get list of sites (using GOCDB instead of site configuration)

    :return: list of site IDs
    """
    query = {"method": "get_site_list", "certification_status": "Certified"}
    url = "?".join([GOCDB_PUBLICURL, parse.urlencode(query)])
    request = requests.get(url)
    sites = []
    if request.status_code == 200:
        root = ElementTree.fromstring(request.text)
        for site_object in root:
            sites.append(site_object.attrib.get("NAME"))
    else:
        print("Something went wrong...")
        print(request.status_code)
        print(request.text)
    return sites


def find_endpoint(service_type, production=True, monitored=True, site=None):
    """
    Searching GOCDB for endpoints according to service types and status

    :param service_type:
    :param production:
    :param monitored:
    :param site: list of sites, None for searching all sites

    :return: list of endpoints
    """
    query = {"method": "get_service_endpoint", "service_type": service_type}
    if monitored:
        query["monitored"] = "Y"
    if site:
        query["sitename"] = site
        sites = [site]
    else:
        sites = get_sites()
    url = "?".join([GOCDB_PUBLICURL, parse.urlencode(query)])
    request = requests.get(url)
    endpoints = []
    if request.status_code == 200:
        root = ElementTree.fromstring(request.text)
        for site_object in root:
            if production:
                prod = site_object.find("IN_PRODUCTION").text.upper()
                if prod != "Y":
                    continue
            os_url = site_object.find("URL").text
            ep_site = site_object.find("SITENAME").text
            if ep_site not in sites:
                continue
            # os_url = urlparse.urlparse(sp.find('URL').text)
            # sites[sp.find('SITENAME').text] = urlparse.urlunparse(
            #    (os_url[0], os_url[1], os_url[2], '', '', ''))
            endpoints.append([site_object.find("SITENAME").text, service_type, os_url])
    else:
        print("Something went wrong...")
        print(request.status_code)
        print(request.text)
    return endpoints


def get_keystone_url(os_auth_url, path):
    """
    Helper function for fixing Keystone URL
    """
    url = parse.urlparse(os_auth_url)
    prefix = url.path.rstrip("/")
    if prefix.endswith("v2.0") or prefix.endswith("v3"):
        prefix = os.path.dirname(prefix)
    path = os.path.join(prefix, path)
    return parse.urlunparse((url[0], url[1], path, url[3], url[4], url[5]))


def get_unscoped_token(os_auth_url, access_token):
    """
    Get an unscoped token, will try all protocols if needed
    """
    protocols = ["openid", "oidc"]
    for protocol in protocols:
        try:
            unscoped_token = retrieve_unscoped_token(
                os_auth_url, access_token, protocol
            )
            return unscoped_token, protocol
        except RuntimeError:
            pass
    raise TokenException(SCOPED_TOKEN_ERROR_MSG)


def get_scoped_token(os_auth_url, access_token, project_id):
    """
    Get a scoped token, will try all protocols if needed
    """
    unscoped_token, protocol = get_unscoped_token(os_auth_url, access_token)
    url = get_keystone_url(os_auth_url, "/v3/auth/tokens")
    body = {
        "auth": {
            "identity": {"methods": ["token"], "token": {"id": unscoped_token}},
            "scope": {"project": {"id": project_id}},
        }
    }
    request = requests.post(url, json=body)
    # pylint: disable=no-member
    if request.status_code != requests.codes.created:
        raise TokenException(SCOPED_TOKEN_ERROR_MSG)

    return request.headers["X-Subject-Token"], protocol


def retrieve_unscoped_token(os_auth_url, access_token, protocol="openid"):
    """
    Request an unscoped token
    """
    url = get_keystone_url(
        os_auth_url,
        f"/v3/OS-FEDERATION/identity_providers/egi.eu/protocols/{protocol}/auth",
    )
    request = requests.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=TIMEOUT,
    )
    # pylint: disable=no-member
    if request.status_code != requests.codes.created:
        raise TokenException(UNSCOPED_TOKEN_ERROR_MSG)

    return request.headers["X-Subject-Token"]


def get_projects_from_single_site(os_auth_url, unscoped_token):
    """
    Get list of projects from unscoped token
    """
    url = get_keystone_url(os_auth_url, "/v3/auth/projects")
    request = requests.get(url, headers={"X-Auth-Token": unscoped_token})
    request.raise_for_status()
    return request.json()["projects"]


def format_project_as_list(site_name, project):
    """
    Format project data as a list
    """
    return [[project["id"], project["name"], project["enabled"], site_name]]


def format_project_as_dict(site_name, project):
    """
    Format project data as a dictionary
    """
    return [
        {
            "project_id": project["id"],
            "name": project["name"],
            "enabled": project["enabled"],
            "site": site_name,
        }
    ]


def get_projects_from_sites(access_token, site):
    """
    Get all projects from site(s) using access token, in the default output format (list)
    """
    return get_projects_from_sites_as_list(access_token, site)


def get_projects_from_sites_as_list(access_token, site):
    """
    Get all projects from site(s) using access token, as a list
    """
    return get_projects_from_sites_with_format(
        access_token, site, format_project_as_list
    )


def get_projects_from_sites_as_dict(access_token, site):
    """
    Get all projects from site(s) using access token, as a dictionary
    """
    return get_projects_from_sites_with_format(
        access_token, site, format_project_as_dict
    )


def get_projects_from_sites_with_format(access_token, site, output_format_function):
    """
    Get all projects from site(s) using access token
    """
    project_list = []
    project_error_list = []
    for site_ep in find_endpoint(OPENSTACK_NOVA, site=site):
        site_name = site_ep[0]
        site_os_auth_url = site_ep[2]

        try:
            unscoped_token, _ = get_unscoped_token(site_os_auth_url, access_token)
            for project in get_projects_from_single_site(
                site_os_auth_url, unscoped_token
            ):
                project_list.extend(output_format_function(site_name, project))
        except TokenException:
            # e.g. The user may have no permissions
            pass
        except requests.exceptions.SSLError:
            project_error_list.append([site_name, TLS_ERROR_MSG])
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            # The site is unavailable e.g. HTTP 500
            project_error_list.append([site_name, CONNECTION_ERROR_MSG])
        except RuntimeError:
            # Logging needed
            pass
    return project_list, project_error_list


@click.group()
def endpoint():
    """
    Obtain endpoint details and scoped tokens
    """


@endpoint.command()
@all_site_params
@oidc_params
def vos(
    access_token,
    site,
    all_sites,
):
    """
    List projects from site(s)
    """
    if site in ALL_SITES_KEYWORDS or all_sites:
        site = None

    project_list, project_error_list = get_projects_from_sites(access_token, site)
    if len(project_list) > 0:
        for p in project_list:
            vo = find_vo_from_project_id(p[3], p[0])
            p.insert(0, vo)
        print(
            tabulate(
                project_list, headers=["VO", "id", "Project name", "enabled", "site"]
            )
        )
    else:
        print(f"Error: You probably do not have access to any project at site {site}")
        print(
            'Check your access token and VO memberships using "fedcloud token list-vos"'
        )
    if len(project_error_list) > 0:
        print("[WARN] Sites not available: ", project_error_list, file=sys.stderr)


@endpoint.command()
@all_site_params
@oidc_params
def projects(
    access_token,
    site,
    all_sites,
):
    """
    List projects from site(s)
    """
    if site in ALL_SITES_KEYWORDS or all_sites:
        site = None

    project_list, project_error_list = get_projects_from_sites(access_token, site)
    if len(project_list) > 0:
        print(tabulate(project_list, headers=["id", "Name", "enabled", "site"]))
    else:
        print(f"Error: You probably do not have access to any project at site {site}")
        print(
            'Check your access token and VO memberships using "fedcloud token list-vos"'
        )
    if len(project_error_list) > 0:
        print("[WARN] Sites not available: ", project_error_list, file=sys.stderr)


@endpoint.command()
@site_params
@project_id_params
@oidc_params
def token(
    access_token,
    site,
    project_id,
):
    """
    Get scoped Keystone token for site and project
    """
    if site in ALL_SITES_KEYWORDS:
        print("Cannot get tokens for ALL_SITES")
        raise click.Abort()

    # Getting sites from GOCDB
    # assume first one is ok
    site_ep = find_endpoint(OPENSTACK_NOVA, site=site).pop()
    os_auth_url = site_ep[2]
    try:
        scoped_token, _ = get_scoped_token(os_auth_url, access_token, project_id)
        print_set_env_command("OS_TOKEN", scoped_token)
    except RuntimeError:
        print(f"Error: Unable to get Keystone token from site {site}")


@endpoint.command()
@all_site_params
@click.option(
    "--service-type",
    default=OPENSTACK_NOVA,
    help="Service type in GOCDB",
    show_default=True,
)
@click.option(
    "--production/--not-production",
    default=True,
    help="Production status",
    show_default=True,
)
@click.option(
    "--monitored/--not-monitored",
    default=True,
    help="Monitoring status",
    show_default=True,
)
def list(service_type, production, monitored, site, all_sites):
    """
    List endpoints in site(s), will query GOCDB
    """
    if site in ALL_SITES_KEYWORDS or all_sites:
        site = None

    endpoints = find_endpoint(service_type, production, monitored, site)
    print(tabulate(endpoints, headers=["Site", "type", "URL"]))


@endpoint.command()
@site_params
@project_id_params
@oidc_params
def env(
    access_token,
    site,
    project_id,
):
    """
    Generate OS environment variables for site and project
    """
    if site in ALL_SITES_KEYWORDS:
        print("Cannot generate environment variables for ALL_SITES")
        raise click.Abort()

    # Get the right endpoint from GOCDB
    # assume first one is ok
    site_ep = find_endpoint(OPENSTACK_NOVA, site=site).pop()
    os_auth_url = site_ep[2]

    try:
        _, protocol = get_scoped_token(os_auth_url, access_token, project_id)
        print(f"# environment for {site}")
        print_set_env_command("OS_PROJECT_ID", project_id)
        print_set_env_command("OS_AUTH_URL", os_auth_url)
        print_set_env_command("OS_AUTH_TYPE", "v3oidcaccesstoken")
        print_set_env_command("OS_IDENTITY_PROVIDER", "egi.eu")
        print_set_env_command("OS_PROTOCOL", protocol)
        print_set_env_command("OS_ACCESS_TOKEN", access_token)
    except RuntimeError as runtime_error:
        raise SystemExit(
            f"Error: Unable to get Keystone token from site {site}"
        ) from runtime_error
