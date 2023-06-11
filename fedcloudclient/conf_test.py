"""
Testing unit for auth.py
"""

import os

import fedcloudclient.conf as conf


def save_load_compare():
    """
    Save config to a temp file, load it and compare the result
    """

    config_data = {
        "env1": "value1",
        "env2": "value2",
        "env3": "value3",
    }

    config_file = "/tmp/test"

    conf.save_config(config_file, config_data)
    new_config = conf.load_config(config_file)

    assert new_config == config_data


def load_env_merge_compare():
    """
    set OS env, load, and compare the result
    """
    config_data = {
        "env1": "value1",
        "env2": "value2",
        "env3": "value3",
    }

    config_file = "/tmp/test"

    conf.save_config(config_file, config_data)
    saved_config = conf.load_config(config_file)

    os.environ["FEDCLOUD_ENV1"] = "value10"
    os.environ["FEDCLOUD_ENV4"] = "value4"

    env_config = conf.load_env()

    act_config = {**config_data, **saved_config, **env_config}

    assert act_config["env1"] == "value10"
    assert act_config["env4"] == "value4"


if __name__ == "__main__":
    save_load_compare()
    load_env_merge_compare()
