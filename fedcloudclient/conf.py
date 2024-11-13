"""
Read/write configuration files
"""
import json
import os
import sys
from pathlib import Path

import click
import yaml
from tabulate import tabulate

#from fedcloudclient.exception import ConfigError

DEFAULT_CONFIG_LOCATION = Path.home() / ".config/fedcloud/config.yaml"
DEFAULT_SETTINGS = {
    "site": "IISAS-FedCloud",
    "vo": "vo.access.egi.eu",
    "site_list_url": "https://raw.githubusercontent.com/tdviet/fedcloudclient/master/config/sites.yaml",
    "site_dir": str(Path.home() / ".config/fedcloud/site-config/"),
    "oidc_url": "https://aai.egi.eu/auth/realms/egi",
    "gocdb_public_url": "https://goc.egi.eu/gocdbpi/public/",
    "gocdb_service_group": "org.openstack.nova",
    "vault_endpoint": "https://vault.services.fedcloud.eu:8200",
    "vault_role": "",
    "vault_mount_point": "/secrets/",
    "vault_locker_mount_point": "/v1/cubbyhole/",
    "vault_salt": "fedcloud_salt",
    "log_file": str(Path.home() / ".config/fedcloud/logs/fedcloud.log"),
    "log_level": "DEBUG",
    "log_config_file": str(Path.home() / ".config/fedcloud/logging.conf"),
    "requests_cert_file": str(Path.home() / ".config/fedcloud/cert/certs.pem"),
    "oidc_agent_account": "egi",
    "min_access_token_time": 30,
    "mytoken_server": "https://mytoken.data.kit.edu",
    "os_protocol": "openid",
    "os_auth_type": "v3oidcaccesstoken",
    "os_identity_provider": "egi.eu",
}


def save_config(filename: str, config_data: dict):
    """
    Save configuration to file
    :param filename: name of config file
    :param config_data: dict containing configuration
    :return: None
    """
    config_file = Path(filename).resolve()
    try:
        with config_file.open(mode="w+", encoding="utf-8") as file:
            yaml.dump(config_data, file)
    except yaml.YAMLError as exception:
        error_msg = f"Error during saving configuration to {filename}: {exception}"
        raise ConfigError(error_msg)


def load_config(filename: str) -> dict:
    """
    Load configuration file
    :param filename:
    :return: configuration data
    """

    config_file = Path(filename).resolve()

    if config_file.is_file():
        try:
            with config_file.open(mode="r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except yaml.YAMLError as exception:
            error_msg = f"Error during loading configuration from {filename}: {exception}"
            raise ConfigError(error_msg)
    else:
        return {}


def load_env() -> dict:
    """
    Load configs from environment variables
    :return: config
    """
    env_config = dict()
    for env in os.environ:
        if env.startswith("FEDCLOUD_"):
            config_key = env[9:].lower()
            env_config[config_key] = os.environ[env]
    return env_config


def init_config() -> dict:
    """
    Init config moduls
    :return: actual config
    """
    env_config = load_env()
    config_file = env_config.get("config_file", DEFAULT_CONFIG_LOCATION)

    try:
        saved_config = load_config(config_file)
    except ConfigError as exception:
        print(f"Error while loading config: {exception}")
        saved_config = {}

    act_config = {**DEFAULT_SETTINGS, **saved_config, **env_config}
    return act_config


@click.group()
def config():
    """
    Managing fedcloud configurations
    """


@config.command()
@click.option(
    "--config-file",
    type=click.Path(dir_okay=False),
    default=DEFAULT_CONFIG_LOCATION,
    help="configuration file",
    envvar="FEDCLOUD_CONFIG_FILE",
    show_default=True,
)
def create(config_file: str):
    """Create default configuration file"""
    save_config(config_file, CONF)
    print(f"Current configuration is saved in {config_file}")


@config.command()
@click.option(
    "--config-file",
    type=click.Path(dir_okay=False),
    default=DEFAULT_CONFIG_LOCATION,
    help="configuration file",
    envvar="FEDCLOUD_CONFIG_FILE",
    show_default=True,
)

@click.option(
    "--output-format",
    "-f",
    required=False,
    help="Output format",
    type=click.Choice(["text", "YAML", "JSON"], case_sensitive=False),
)

def show(config_file: str, output_format: str):
    """Show actual client configuration """
    saved_config = load_config(config_file)
    env_config = load_env()
    act_config = {**DEFAULT_SETTINGS, **saved_config, **env_config}
    if output_format == "YAML":
        yaml.dump(act_config, sys.stdout, sort_keys=False)
    elif output_format == "JSON":
        json.dump(act_config, sys.stdout, indent=4)
    else:
        print(tabulate(act_config.items(), headers=["parameter", "value"]))


CONF = init_config()
show()


for env in os.environ:
    #print(f"\n {env} \t {type(env)}")
    pass

#print(f"Test of config: {None}")
#print(f"Done")

if __name__=="__main__":
    config()
    CONF


