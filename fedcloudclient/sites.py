from pathlib import Path
from urllib.request import urlopen, Request

import click
import yaml

# Default site configs from GitHub
DEFAULT_SITE_CONFIGS = (
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/100IT.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/BIFI.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/CESGA.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/CESNET-MCC.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/CETA-GRID.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/CLOUDIFIN.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/CYFRONET-CLOUD.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/DESY-HH.yaml",
    'https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/IFCA-LCG2.yaml',
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/IISAS-FedCloud-cloud.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/IISAS-GPUCloud.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/IN2P3-IRES.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/INFN-CATANIA-STACK.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/INFN-PADOVA-STACK.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/Kharkov-KIPT-LCG2.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/NCG-INGRID-PT.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/RECAS-BARI.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/SCAI.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/TR-FC1-ULAKBIM.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/UA-BITP.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/UNIV-LILLE.yaml",
    "https://raw.githubusercontent.com/EGI-Foundation/fedcloud-catchall-operations/master/sites/fedcloud.srce.hr.yaml",
)

LOCAL_CONFIG_DIR = ".fedcloud-site-config/"

site_config_data = []


def read_site_config():
    """
    Read site configurations from local config dir if exist, otherwise from default GitHub location. Storing
    site configurations in global variable, that will be used by other functions. Call read_local_site_config()
    or read_default_site_config()

    :return: None
    """
    if len(site_config_data) > 0:
        return
    config_dir = Path.home() / LOCAL_CONFIG_DIR
    if config_dir.exists():
        read_local_site_config(config_dir)
    else:
        read_default_site_config()


def read_default_site_config():
    """
    Read default site configurations from GitHub.  Storing
    site configurations in a global variable, that will be used by other functions

    :return: None
    """
    site_config_data.clear()
    for filename in DEFAULT_SITE_CONFIGS:
        if filename.lower().startswith('http'):
            req = Request(filename)
        else:
            raise ValueError from None

        # URLs already checked, so ignore bandit test
        with urlopen(req) as yaml_file:       # nosec
            site_info = yaml.safe_load(yaml_file)
            site_config_data.append(site_info)


def read_local_site_config(config_dir):
    """
    Read site configurations from local directory specified in config_dir. Storing
    site configurations in global variable, that will be used by other functions

    :param config_dir: path to directory containing site configuration

    :return: None
    """
    site_config_data.clear()
    config_dir = Path(config_dir)
    for f in sorted(config_dir.glob('*.yaml')):
        yaml_file = f.open()
        site_info = yaml.safe_load(yaml_file)
        site_config_data.append(site_info)


def save_site_config(config_dir):
    """
    Save site configs to local directory specified in config_dir. Overwrite local configs if exist

    :param config_dir: path to directory containing site configuration

    :return: None
    """
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    for site_info in site_config_data:
        config_file = config_dir / (site_info["gocdb"] + ".yaml")
        with config_file.open("w", encoding="utf-8") as f:
            yaml.dump(site_info, f)


def list_sites():
    """
    List of all sites IDs in site configurations

    :return: list of site IDs
    """
    read_site_config()
    result = []
    for site_info in site_config_data:
        result.append(site_info["gocdb"])
    return result


def find_site_data(site_name):
    """
    Return configuration of the correspondent site with site_name

    :param site_name: site ID in GOCDB
    :return: configuration of site if found, otherwise None
    """
    read_site_config()

    for site_info in site_config_data:
        if site_info["gocdb"] == site_name:
            return site_info
    return None


def find_endpoint_and_project_id(site_name, vo):
    """
    Return Keystone endpoint and project ID from site name and VO according to site configuration

    :param site_name: site ID in GOCDB
    :param vo: VO name. None if finding only site endpoint

    :return: endpoint, project_id, protocol if the VO exist on the site, otherwise None, None, None
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

    # Return None, None if VO not found
    return None, None, None


@click.group()
def site():
    """
    Site command group for manipulation with site configurations
    """
    pass


@site.command()
@click.option(
    "--site",
    help="Name of the site",
    required=True,
    envvar="EGI_SITE",
)
def show(site):
    """
    Print configuration of the specified site
    """
    site_info = find_site_data(site)
    if site_info:
        print(yaml.dump(site_info, sort_keys=True))
    else:
        print("Site %s not found" % site)


@site.command()
@click.option(
    "--site",
    help="Name of the site",
    required=True,
    envvar="EGI_SITE",
)
@click.option(
    "--vo",
    help="Name of the VO",
    required=True,
    envvar="EGI_VO",
)
def show_project_id(site, vo):
    """
    Printing Keystone endpoint and project ID of the VO on the site
    """
    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    if endpoint:
        print(" Endpoint : %s \n Project ID : %s" % (endpoint, project_id))
    else:
        print("VO %s not found on site %s" % (vo, site))


@site.command()
def show_all():
    """
    Print all site configuration
    """
    read_site_config()
    for site_info in site_config_data:
        site_info_str = yaml.dump(site_info, sort_keys=True)
        print(site_info_str)


@site.command()
def save_config():
    """
    Read default site configs from GitHub and save them to local folder in home directory
    Overwrite local configs if exist
    """
    read_default_site_config()
    config_dir = Path.home() / LOCAL_CONFIG_DIR
    print("Saving site configs to directory %s" % config_dir)
    save_site_config(config_dir)


@site.command()
def list():
    """
    List site IDs
    """
    read_site_config()
    for site_info in site_config_data:
        print(site_info["gocdb"])
