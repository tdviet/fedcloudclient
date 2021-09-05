"""
"fedcloud endpoint" commands are complementary part of the "fedcloud site" commands.

Instead of using site configurations defined in files saved in GitHub repository or
local disk, the commands try to get site information directly from GOCDB
(Grid Operations Configuration Management Database) https://goc.egi.eu/ or make probe
test on sites
"""

import os
from urllib import parse

import click
import defusedxml.ElementTree as ElementTree
import requests
from tabulate import tabulate

from fedcloudclient.checkin import get_access_token, oidc_params
from fedcloudclient.decorators import (
    ALL_SITES_KEYWORDS,
    all_site_params,
    project_id_params,
    site_params,
)
from fedcloudclient.shell import printSetEnvCommand

GOCDB_PUBLICURL = "https://goc.egi.eu/gocdbpi/public/"


def get_sites():
    """
    Get list of sites (using GOCDB instead of site configuration)

    :return: list of site IDs
    """
    q = {"method": "get_site_list", "certification_status": "Certified"}
    url = "?".join([GOCDB_PUBLICURL, parse.urlencode(q)])
    r = requests.get(url)
    sites = []
    if r.status_code == 200:
        root = ElementTree.fromstring(r.text)
        for s in root:
            sites.append(s.attrib.get("NAME"))
    else:
        print("Something went wrong...")
        print(r.status_code)
        print(r.text)
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
    q = {"method": "get_service_endpoint", "service_type": service_type}
    if monitored:
        q["monitored"] = "Y"
    if site:
        q["sitename"] = site
        sites = [site]
    else:
        sites = get_sites()
    url = "?".join([GOCDB_PUBLICURL, parse.urlencode(q)])
    r = requests.get(url)
    endpoints = []
    if r.status_code == 200:
        root = ElementTree.fromstring(r.text)
        for sp in root:
            if production:
                prod = sp.find("IN_PRODUCTION").text.upper()
                if prod != "Y":
                    continue
            os_url = sp.find("URL").text
            ep_site = sp.find("SITENAME").text
            if ep_site not in sites:
                continue
            # os_url = urlparse.urlparse(sp.find('URL').text)
            # sites[sp.find('SITENAME').text] = urlparse.urlunparse(
            #    (os_url[0], os_url[1], os_url[2], '', '', ''))
            endpoints.append([sp.find("SITENAME").text, service_type, os_url])
    else:
        print("Something went wrong...")
        print(r.status_code)
        print(r.text)
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
    for p in protocols:
        try:
            unscoped_token = retrieve_unscoped_token(os_auth_url, access_token, p)
            return unscoped_token, p
        except RuntimeError:
            pass
    raise RuntimeError("Unable to get a scoped token")


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
    r = requests.post(url, json=body)
    # pylint: disable=no-member
    if r.status_code != requests.codes.created:
        raise RuntimeError("Unable to get a scoped token")
    else:
        return r.headers["X-Subject-Token"], protocol


def retrieve_unscoped_token(os_auth_url, access_token, protocol="openid"):
    """
    Request an unscoped token
    """
    url = get_keystone_url(
        os_auth_url,
        "/v3/OS-FEDERATION/identity_providers/egi.eu/protocols/%s/auth" % protocol,
    )
    r = requests.post(url, headers={"Authorization": "Bearer %s" % access_token})
    # pylint: disable=no-member
    if r.status_code != requests.codes.created:
        raise RuntimeError("Unable to get an unscoped token")
    else:
        return r.headers["X-Subject-Token"]


def get_projects(os_auth_url, unscoped_token):
    """
    Get list of projects from unscoped token
    """
    url = get_keystone_url(os_auth_url, "/v3/auth/projects")
    r = requests.get(url, headers={"X-Auth-Token": unscoped_token})
    r.raise_for_status()
    return r.json()["projects"]


def get_projects_from_sites(access_token, site):
    """
    Get all projects from site(s) using access token
    """
    project_list = []
    for ep in find_endpoint("org.openstack.nova", site=site):
        os_auth_url = ep[2]
        try:
            unscoped_token, _ = get_unscoped_token(os_auth_url, access_token)
            project_list.extend(
                [
                    [p["id"], p["name"], p["enabled"], ep[0]]
                    for p in get_projects(os_auth_url, unscoped_token)
                ]
            )
        except (RuntimeError, ConnectionError):
            pass
    return project_list


def get_projects_from_sites_dict(access_token, site):
    """
    Get all projects as a dictionary from site(s) using access token
    """
    project_list = []
    for ep in find_endpoint("org.openstack.nova", site=site):
        os_auth_url = ep[2]
        try:
            unscoped_token, _ = get_unscoped_token(os_auth_url, access_token)
            project_list.extend(
                [
                    {
                        "project_id": p["id"],
                        "name": p["name"],
                        "enabled": p["enabled"],
                        "site": ep[0],
                    }
                    for p in get_projects(os_auth_url, unscoped_token)
                ]
            )
        except RuntimeError:
            pass
    return project_list


@click.group()
def endpoint():
    """
    Obtain endpoint details and scoped tokens
    """
    pass


@endpoint.command()
@all_site_params
@oidc_params
def projects(
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    site,
    all_sites,
):
    """
    List projects from site(s)
    """
    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )
    if site in ALL_SITES_KEYWORDS or all_sites:
        site = None

    project_list = get_projects_from_sites(access_token, site)
    if len(project_list) > 0:
        print(tabulate(project_list, headers=["id", "Name", "enabled", "site"]))
    else:
        print("Error: You probably do not have access to any project at site %s" % site)
        print(
            'Check your access token and VO memberships using "fedcloud token list-vos"'
        )


@endpoint.command()
@site_params
@project_id_params
@oidc_params
def token(
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    site,
    project_id,
):
    """
    Get scoped Keystone token for site and project
    """
    if site in ALL_SITES_KEYWORDS:
        print("Cannot get tokens for ALL_SITES")
        raise click.Abort()

    # Get an access token
    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )
    # Getting sites from GOCDB
    # assume first one is ok
    ep = find_endpoint("org.openstack.nova", site=site).pop()
    os_auth_url = ep[2]
    try:
        scoped_token, _ = get_scoped_token(os_auth_url, access_token, project_id)
        printSetEnvCommand("OS_TOKEN", scoped_token)
    except RuntimeError:
        print("Error: Unable to get Keystone token from site %s " % site)


@endpoint.command()
@all_site_params
@click.option(
    "--service-type",
    default="org.openstack.nova",
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
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    site,
    project_id,
):
    """
    Generate OS environment variables for site and project
    """
    if site in ALL_SITES_KEYWORDS:
        print("Cannot generate environment variables for ALL_SITES")
        raise click.Abort()

    # Get an access token
    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )
    # Get the right endpoint from GOCDB
    # assume first one is ok
    ep = find_endpoint("org.openstack.nova", site=site).pop()
    os_auth_url = ep[2]

    try:
        scoped_token, protocol = get_scoped_token(os_auth_url, access_token, project_id)
        print("# environment for %s" % site)
        printSetEnvCommand("OS_PROJECT_ID", project_id)
        printSetEnvCommand("OS_AUTH_URL", os_auth_url)
        printSetEnvCommand("OS_AUTH_TYPE", "v3oidcaccesstoken")
        printSetEnvCommand("OS_IDENTITY_PROVIDER", "egi.eu")
        printSetEnvCommand("OS_PROTOCOL", protocol)
        printSetEnvCommand("OS_ACCESS_TOKEN", access_token)
    except RuntimeError:
        print("Error: Unable to get Keystone token from site %s " % site)
