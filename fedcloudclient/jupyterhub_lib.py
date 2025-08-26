"""
JupyterHub adapter library to make requests
"""

import os
import json
import base64
import urllib

import requests


def _make_request(**kwargs):
    """
    Sends requests to Hub API endpoint
    """
    if not kwargs["hub_api_endpoint"].endswith("/"):
        kwargs["hub_api_endpoint"] = kwargs["hub_api_endpoint"] + "/"

    headers = {}
    data = None
    params = None

    if "data" in kwargs:
        headers.update({"Content-Type": "application/json; charset=utf-8"})
        data = json.dumps(kwargs.pop("data"))
    if "params" in kwargs:
        params = kwargs.pop("params")
    headers.update({"Authorization": f"Bearer {kwargs['token']}"})

    response = getattr(requests, kwargs["method"])(
        urllib.parse.urljoin(
            kwargs["hub_api_endpoint"], kwargs["api_request_endpoint"]
        ),
        headers=headers,
        params=params,
        data=data,
    )
    if not response.ok:
        try:
            decoded_response = response.json()
            print(
                f"Error - Hub responded with: {response.status_code} - {decoded_response['message']}"
            )
        except (requests.JSONDecodeError, KeyError):
            print(
                f"Error - Hub responded with: {response.status_code} - {response.reason}"
            )
        return None
    return response


def _decode_response(response):
    """
    Decodes JSON response from Hub API
    """
    try:
        return response.json()
    except requests.JSONDecodeError:
        print("Failed to decode Hub response")
    return None


def _get_user_id(**kwargs):
    """
    Gets user ID
    """
    user_output = get_user(**kwargs)

    if user_output is not None:
        try:
            return user_output["name"]
        except KeyError:
            print("Failed to acquire user ID from Hub response")
    return None


def _is_server_running(server_name, user_output):
    """
    Verifies if server is running
    """
    try:
        if not user_output["servers"][server_name]["ready"]:
            print(f'Error - "{server_name}" server is not running')
            return False
    except KeyError:
        print("Error - Failed to decode Hub response")
        return False
    return True


def _get_full_user_output(**kwargs):
    """
    Return full user output
    """
    # Stopped servers are required to get all of them
    kwargs.update({"include_stopped_servers": True})
    return get_user(**kwargs)


def _get_server_url(hub_api_endpoint, server_name, user_output):
    """
    Returns server url
    """
    try:
        if server_name not in user_output["servers"]:
            print("Error - Specified server does not exist")
            return None
        if "url" not in user_output["servers"][server_name]:
            print(f'Error - "{server_name}" server does not have specified it\'s url')
            return None
    except KeyError:
        print("Error - Failed to decode Hub response")
        return None

    server_url_path = user_output["servers"][server_name]["url"]

    if not server_url_path.endswith("/"):
        server_url_path = server_url_path + "/"
    # Required for urllib joining to work correctly
    if server_url_path.startswith("/"):
        server_url_path = server_url_path[1:]

    hub_address = urllib.parse.urlsplit(hub_api_endpoint)
    hub_address = urllib.parse.urlunsplit((hub_address[0], hub_address[1], "", "", ""))

    server_url = urllib.parse.urljoin(hub_address, server_url_path)

    return server_url


def get_user(**kwargs):
    """
    Gets specified user output
    """
    api_request_endpoint = ""

    # If specific user ID is provided, the module will request
    # details for that user ID instead of token owner
    if kwargs.get("user", None) is not None:
        api_request_endpoint = f"users/{kwargs['user']}"
    else:
        api_request_endpoint = "user"
    kwargs.update({"method": "get", "api_request_endpoint": api_request_endpoint})

    kwargs.update(
        {
            "params": {
                "include_stopped_servers": kwargs.get("include_stopped_servers", False)
            }
        }
    )
    response = _make_request(**kwargs)

    if response is not None:
        return _decode_response(response)
    return None


def _server_start_stop(**kwargs):
    """
    Starts or stops single user server
    """
    user_id = _get_user_id(**kwargs)

    if "options" in kwargs and kwargs["options"] is not None:
        try:
            user_options = json.loads(kwargs["options"])
            kwargs.update({"data": user_options})
        except json.JSONDecodeError:
            print("Error - passed user options json is invalid.")
            return None

    if user_id is not None:
        kwargs.update(
            {"api_request_endpoint": f"users/{user_id}/servers/{kwargs['server']}"}
        )
        _make_request(**kwargs)
    return None


def get_servers(**kwargs):
    """
    Lists named servers
    """
    user_output = get_user(**kwargs)
    if user_output is not None:
        return user_output["servers"]
    return None


def start_server(**kwargs):
    """
    Starts named server
    """
    kwargs.update({"method": "post"})
    _server_start_stop(**kwargs)


def stop_server(**kwargs):
    """
    Stops names server
    """
    kwargs.update({"method": "delete"})
    _server_start_stop(**kwargs)


def _shares_request(**kwargs):
    """
    Sends requests to shares API endpoint
    """
    if kwargs["method"] in ["post", "patch"]:
        data = {}
        data_items = [
            ("grant_to_group", "group"),
            ("grant_to_user", "user"),
            ("remove_from_user", "user"),
            ("remove_from_group", "group"),
            ("scope", "scopes"),
        ]
        for kwargs_key, api_item_key in data_items:
            if kwargs.get(kwargs_key, None) is not None:
                data.update({api_item_key: kwargs[kwargs_key]})
        if "user" not in data and "group" not in data:
            print(
                "Error - Either one user or group can be specified, not at the same time"
            )
            return None
        if "user" in data and "group" in data:
            print("Error - User or group cannot be specified at the same time")
            return None

        kwargs.update({"data": data})

    user_id = (
        kwargs["user"]
        if kwargs.get("user", None) is not None
        else _get_user_id(**kwargs)
    )

    if user_id is not None:
        api_request_endpoint = f"shares/{user_id}/{kwargs['server']}"
        kwargs.update({"api_request_endpoint": api_request_endpoint})

        response = _make_request(**kwargs)
        # Response output is returned apart from token deletion
        if response is not None and kwargs["method"] != "delete":
            return _decode_response(response)
    return None


def add_shared_access(**kwargs):
    """
    Adds shared access to the user server
    """
    kwargs.update({"method": "post"})
    return _shares_request(**kwargs)


def remove_shared_access(**kwargs):
    """
    Removes shared access to the user server
    """
    if kwargs.get("all", False):
        kwargs.update({"method": "delete"})
    else:
        kwargs.update({"method": "patch"})
    return _shares_request(**kwargs)


def list_shared_access(**kwargs):
    """
    Lists shared access of the user server
    """
    kwargs.update({"method": "get"})
    return _shares_request(**kwargs)


def _token_request(**kwargs):
    """
    Sends requests to token API endpoint
    """
    # This is for token generation
    if kwargs["method"] == "post":
        data = {}
        data_items = [
            ("expiration", "expires_in"),
            ("note", "note"),
            ("role", "roles"),
            ("scope", "scopes"),
        ]
        for kwargs_key, api_item_key in data_items:
            kwargs_item = kwargs.get(kwargs_key, None)
            # Empty tuple check is for role and scope as they
            # can't be specified both at the same time. Hub API
            # error will notify user in case of both being set
            if kwargs_item is not None and kwargs_item != ():
                data.update({api_item_key: kwargs[kwargs_key]})
        kwargs.update({"data": data})
    user_id = (
        kwargs["user"]
        if kwargs.get("user", None) is not None
        else _get_user_id(**kwargs)
    )

    if user_id is not None:
        if "api_token_id" in kwargs:
            api_request_endpoint = f"users/{user_id}/tokens/{kwargs['api_token_id']}"
        else:
            api_request_endpoint = f"users/{user_id}/tokens"

        kwargs.update({"api_request_endpoint": api_request_endpoint})
        response = _make_request(**kwargs)

        # Response output is returned apart from token deletion
        if response is not None and kwargs["method"] != "delete":
            return _decode_response(response)
    return None


def get_token(**kwargs):
    """
    Gets token details by token ID
    """
    kwargs.update({"method": "get"})
    return _token_request(**kwargs)


def delete_token(**kwargs):
    """
    Delete specified API token
    """
    kwargs.update({"method": "delete"})
    _token_request(**kwargs)


def list_tokens(**kwargs):
    """
    Lists existing API tokens
    """
    kwargs.update({"method": "get"})
    return _token_request(**kwargs)


def add_token(**kwargs):
    """
    Generates API token
    """
    kwargs.update({"method": "post"})
    return _token_request(**kwargs)


def _path_request(**kwargs):
    """
    Sends requests to path jupyter server API
    """
    user_output = _get_full_user_output(**kwargs)
    if user_output is None:
        return None

    server_url = _get_server_url(
        kwargs["hub_api_endpoint"], kwargs["server"], user_output
    )
    if not server_url:
        return None

    # Switching Hub API url for user server API url
    kwargs.update({"hub_api_endpoint": urllib.parse.urljoin(server_url, "api")})

    content_path = ""
    # PUT method indicates file upload request
    if kwargs["method"] == "put":
        content_path = kwargs["data"]["path"]
    else:
        # Because get_path is called from upload_file, 'destination'
        # is used, on other cases 'path' param
        content_path = kwargs["path"] if "path" in kwargs else kwargs["destination"]

    if content_path.startswith("/"):
        content_path = content_path[1:]
    kwargs.update({"api_request_endpoint": f"contents/{content_path}"})
    response = _make_request(**kwargs)

    if response is not None and kwargs["method"] != "delete":
        return _decode_response(response)
    return None


def get_path(**kwargs):
    """
    Gets path on the running server
    """
    kwargs.update({"method": "get"})
    kwargs.update(
        {"params": {"content": 1 if kwargs.get("show_content", False) else 0}}
    )
    return _path_request(**kwargs)


def add_path(**kwargs):
    """
    Adds path on the running server
    """
    data = {}

    if "copy_from" in kwargs:
        data.update({"type": kwargs["type"], "copy_from": kwargs["copy_from"]})

    kwargs.update({"method": "post"})
    data.update({"type": kwargs["type"]})
    kwargs.update({"data": data})
    add_path_response = _path_request(**kwargs)

    if add_path_response is None:
        return None

    if "name" in kwargs and kwargs["name"] is not None:
        kwargs.update({"method": "patch"})
        # New destination for API request and new destination
        # with new file/directory name must be set for renaming
        kwargs.update({"destination": add_path_response["path"]})
        kwargs.update(
            {
                "data": {
                    "path": os.path.join(
                        os.path.dirname(add_path_response["path"]), kwargs["name"]
                    )
                }
            }
        )
        return _path_request(**kwargs)

    return add_path_response


def delete_path(**kwargs):
    """
    Deletes file/directory on the running server
    """
    kwargs.update({"method": "delete"})
    return _path_request(**kwargs)


def upload_file(**kwargs):
    """
    Uploads file to the server
    """
    server_destination = get_path(**kwargs)

    if server_destination is None:
        return None

    try:
        if server_destination["type"] == "file":
            jupyter_file_dest = kwargs["destination"]

        else:
            jupyter_file_dest = os.path.join(
                kwargs["destination"], os.path.basename(kwargs["file"])
            )

    except KeyError:
        print("Error - failed to decode Jupyterhub response")
        return None

    data = {}

    try:
        with open(kwargs["file"], "rb") as f:
            content = base64.standard_b64encode(f.read()).decode("utf-8")
            data.update(
                {
                    "content": content,
                    "format": "base64",
                    "name": os.path.basename(jupyter_file_dest),
                    "type": "file",
                    "path": jupyter_file_dest,
                }
            )

    except IOError:
        print("Error - Failed to read specified file")
        return None

    # Setting new data
    kwargs.update({"data": data})
    kwargs.update({"method": "put"})

    return _path_request(**kwargs)


def exec_command(**kwargs):
    """
    Sends command to extension endpoint for execution
    """
    kwargs.update({"method": "post"})
    kwargs.update({"api_request_endpoint": "jlab-control/exec"})

    user_output = _get_full_user_output(**kwargs)
    if user_output is None:
        return None

    server_url = _get_server_url(
        kwargs["hub_api_endpoint"], kwargs["server"], user_output
    )

    # Switching Hub API url for user server url
    kwargs.update({"hub_api_endpoint": server_url})

    if len(kwargs["command"]) > 0:
        kwargs.update({"data": {"command": kwargs["command"]}})
        response = _make_request(**kwargs)

        if response is not None:
            decoded_response = _decode_response(response)
            if decoded_response is not None:
                if kwargs["output"] == "text":
                    return decoded_response["output"]
                return decoded_response
        return None
    print("No command provided, nothing to do")
    return None
