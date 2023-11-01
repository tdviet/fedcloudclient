"""
Logger configuration
"""

import logging
import logging.config
from pathlib import Path

from fedcloudclient.conf import CONF as CONF


def init_logger():
    """
    Init logger
    :return:
    """
    log_file = CONF.get("log_file")
    log_level = CONF.get("log_level")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    try:
        logging.config.fileConfig(
            fname=CONF.get("log_config_file"),
            disable_existing_loggers=False,
            defaults={"log_file": log_file, "log_level": log_level},
        )
    except  (ValueError, TypeError, AttributeError, ImportError, KeyError):
        logging.basicConfig(filename=log_file, level=logging.getLevelName(log_level))


def log_and_raise(error_msg: str, exception):
    """
    Log error and raise exception
    """
    LOG.error(error_msg)
    raise exception(error_msg)


init_logger()

LOG = logging.getLogger("fedcloudclient")
