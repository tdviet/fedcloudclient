"""
Read/write configuration files
"""
import json
import os
import sys
from pathlib import Path
import textwrap

import click
import yaml
from tabulate import tabulate
from fedcloudclient.exception import ConfigError



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
    "_MIN_ACCESS_TOKEN_TIME": 30
}

def init_default_config():
    """
    Initialize the default configuration settings.

    :return:  
        A dictionary containing the default settings as defined by `DEFAULT_SETTINGS`.
    :rtype: dict
    """
    default_config_init=DEFAULT_SETTINGS
    return default_config_init

def save_config(filename: str, config_data: dict):
    """
    Save a configuration dictionary to a YAML file.

    :param filename:  
        Path to the configuration file to write.
    :type filename: str

    :param config_data:  
        A mapping of configuration keys to values to be serialized.
    :type config_data: dict

    :raises ConfigError:  
        If writing the YAML fails (wraps `yaml.YAMLError`).
    """
    config_file = Path(filename).resolve()
    try:
        with config_file.open(mode="w+", encoding="utf-8") as file:
            yaml.dump(config_data, file)
    except yaml.YAMLError as exception:
        error_msg = f"Error during saving configuration to {filename}: {exception}"
        raise ConfigError(error_msg) from exception


def load_config(filename: str) -> dict:
    """
    Load configuration data from a YAML file.

    :param filename:  
        Path to the configuration file to read.
    :type filename: str

    :return:  
        A dictionary of configuration values parsed from the file.  
        Returns an empty dict if the file does not exist.
    :rtype: dict

    :raises ConfigError:  
        If the file exists but cannot be parsed as valid YAML.
    """

    config_file = Path(filename).resolve()

    if config_file.is_file():
        try:
            with config_file.open(mode="r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except yaml.YAMLError as exception:
            error_msg = f"Error during loading configuration from {filename}: {exception}"
            raise ConfigError(error_msg) from exception
    else:
        return {}


def load_env() -> dict:
    """
    Load FedCloud client configuration from environment variables.

    Scans the current process environment for variables prefixed with
    `FEDCLOUD_`, strips that prefix, converts the remainder to lowercase,
    and returns them as configuration entries.

    :return:  
        A dictionary mapping config keys (lowercased, prefix removed) to
        their string values from the environment.
    :rtype: dict[str, str]
    """
    env_config = {}
    for env in os.environ:
        if env.startswith("FEDCLOUD_"):
            config_key = env[9:].lower()
            env_config[config_key] = os.environ[env]
    return env_config


def init_config() -> dict:
    """
    Initialize the FedCloud client configuration.

    This function merges three sources of configuration, in order of precedence:
    
    1. `DEFAULT_SETTINGS` (hard-coded defaults).  
    2. Environment variables prefixed with `FEDCLOUD_` (stripped of the prefix and lower-cased).  
    3. Values loaded from a YAML config file (path can be overridden via `FEDCLOUD_CONFIG_FILE`).

    :return:  
        A dict containing the merged configuration settings.  
        Later sources override earlier ones.
    :rtype: dict[str, Any]
    """
    env_config = load_env()
    config_file = env_config.get("config_file", DEFAULT_CONFIG_LOCATION)

    try:
        saved_config = load_config(config_file)
    except ConfigError:
        saved_config = {}

    act_config = {**DEFAULT_SETTINGS, **env_config, **saved_config}
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

@click.option(
    "--source", "-s",
    required=False,
    help="Source of configuration data",
    type=click.Choice(["DEFAULT_SETTINGS", "env_config", "saved_config"], case_sensitive=False),
)

def show(config_file: str, output_format: str, source: str):
    """
    Display the FedCloud client configuration.

    Merges three layers of configuration—defaults, environment, and on-disk—
    then prints one of:

      - the defaults only  
      - the env-vars only  
      - the saved file only  
      - the full merged config

    :param config_file:  
        Path to the YAML config file on disk.
    :type config_file: str

    :param output_format:  
        One of `"text"`, `"YAML"`, or `"JSON"` (case-insensitive) for the
        desired output format.
    :type output_format: str

    :param source:  
        If provided, limits display to one of `"DEFAULT_SETTINGS"`,  
        `"env_config"`, or `"saved_config"`.  Otherwise shows the full merge.
    :type source: Optional[str]

    :return:  
        None
    :rtype: None
    """
    saved_config = load_config(config_file)
    env_config = load_env()
    default_settings=init_default_config()
    if source is not None:
        act_config = vars()[source]
    else:
        act_config = {**default_settings, **env_config, **saved_config}
    if output_format == "YAML":
        yaml.dump(act_config, sys.stdout, sort_keys=False)
    elif output_format == "JSON":
        json.dump(act_config, sys.stdout, indent=4)
    else:
        wrapped_data = [
        ["\n".join(textwrap.wrap(cell, width=200)) if isinstance(cell, str) else cell for cell in row]
        for row in act_config.items()]

        #print(tabulate(act_config.items(), headers=["parameter", "value"]))
        print(tabulate(wrapped_data, headers=["parameter", "value"]))

CONF = init_config()
