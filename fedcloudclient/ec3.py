"""
Implementation of ec3 commands for deploying EC3 (Elastic Cloud Computing
Cluster) in Cloud via Infrastructure Manager
"""

import os
import time

import click
import jwt

from fedcloudclient.decorators import (
    ALL_SITES_KEYWORDS,
    auth_file_params,
    oidc_params,
)
from fedcloudclient.sites import find_endpoint_and_project_id, site_vo_params

__MIN_EXPIRATION_TIME = 300

EC3_REFRESHTOKEN_TEMPLATE = """
description refreshtoken (
    kind = 'component' and
    short = 'Tool to refresh LToS access token.' and
    content = 'Tool to refresh LToS access token.'
)
configure front (
@begin
  - vars:
      CLIENT_ID: %(client_id)s
      CLIENT_SECRET: %(client_secret)s
      REFRESH_TOKEN: %(refresh_token)s
    tasks:
    - name: Check if docker is available
      command: which docker
      changed_when: false
      failed_when: docker_installed.rc not in [0,1]
      register: docker_installed
    - name: local install of fedcloudclient
      block:
      - name: Create dir /usr/local/ec3/
        file: path=/usr/local/ec3/ state=directory
      - name: install git
        package:
          name: git
          state: present
      - name: install fedcloudclient
        pip:
          name:
          - fedcloudclient
      - cron:
          name: "refresh token"
          minute: "*/5"
          job: "[ -f /usr/local/ec3/auth.dat ]
            && /usr/local/bin/fedcloudclient endpoint ec3-refresh
               --oidc-client-id {{ CLIENT_ID }}
               --oidc-client-secret {{ CLIENT_SECRET }}
               --oidc-refresh-token {{ REFRESH_TOKEN }}
               --auth-file /usr/local/ec3/auth.dat &> /var/log/refresh.log"
          user: root
          cron_file: refresh_token
          state: present
      when: docker_installed.rc not in [ 0 ]
    - name: local install of fedcloudclient
      block:
      - cron:
          name: "refresh token"
          minute: "*/5"
          job: "[ -f /usr/local/ec3/auth.dat ]
            && docker run -v /usr/local/ec3/auth.dat:/usr/local/ec3/auth.dat
               tdviet/fedcloudclient fedcloudclient endpoint ec3-refresh
               --oidc-client-id {{ CLIENT_ID }}
               --oidc-client-secret {{ CLIENT_SECRET }}
               --oidc-refresh-token {{ REFRESH_TOKEN }}
               --auth-file /usr/local/ec3/auth.dat &> /var/log/refresh.log"
          user: root
          cron_file: refresh_token
          state: present
      when: docker_installed.rc not in [ 1 ]
@end
)
"""


@click.group()
def ec3():
    """
    EC3 cluster provisioning
    """


@ec3.command()
@oidc_params
@auth_file_params
def refresh(
    access_token,
    auth_file,
):
    """
    Refresh token in EC3 authorization file
    """
    # Get the right endpoint from GOCDB
    auth_file_contents = []
    with open(auth_file, "r") as file:
        for raw_line in file.readlines():
            line = raw_line.strip()
            if "OpenStack" in line:
                auth_tokens = []
                for token in line.split(";"):
                    if token.strip().startswith("password"):
                        current_access_token = token.split("=")[1].strip()
                        if current_access_token[0] in ["'", '"']:
                            current_access_token = current_access_token[1:-1]
                        # FIXME(enolfc): add verification
                        payload = jwt.decode(
                            current_access_token, options={"verify_signature": False}
                        )
                        now = int(time.time())
                        expires = int(payload["exp"])
                        if expires - now < __MIN_EXPIRATION_TIME:
                            current_access_token = access_token
                        auth_tokens.append(f"password = {current_access_token}")
                    else:
                        auth_tokens.append(token.strip())
                auth_file_contents.append("; ".join(auth_tokens))
            elif line:
                auth_file_contents.append(line)

    with open(auth_file, "w+") as file:
        file.write("\n".join(auth_file_contents))


@ec3.command()
@site_vo_params
@oidc_params
@auth_file_params
@click.option(
    "--template-dir",
    help="EC3 templates dir",
    default="./templates",
    show_default=True,
)
@click.option("--force", is_flag=True, help="Force rewrite of files")
def init(
    access_token,
    site,
    vo,
    auth_file,
    template_dir,
    force,
):
    """
    Create EC3 authorization file and template
    """
    if os.path.exists(auth_file) and not force:
        print(
            "Auth file already exists, not replacing unless --force option is included"
        )
        raise click.Abort()

    if site in ALL_SITES_KEYWORDS:
        print("EC3 commands cannot be used with ALL_SITES")
        raise click.Abort()

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    site_auth = [
        f"id = {site}",
        "type = OpenStack",
        "username = egi.eu",
        f"tenant = {protocol}",
        "auth_version = 3.x_oidc_access_token",
        f"host = {endpoint}",
        f"domain = {project_id}",
        f"password = {access_token}",
    ]
    auth_file_contents = [";".join(site_auth)]

    if os.path.exists(auth_file):
        with open(auth_file, "r") as file:
            for line in file.readlines():
                if "OpenStack" in line:
                    continue
                auth_file_contents.append(line)

    with open(auth_file, "w+") as file:
        file.write("\n".join(auth_file_contents))

    if not os.path.exists(template_dir):
        os.mkdir(template_dir)

    # FIXME: this should not be used at all!
    with open(os.path.join(template_dir, "refresh.radl"), "w+") as file:
        token = dict(  # nosec
            client_id="ADD_CLIENT_ID_HERE",
            client_secret="ADD_CLIENT_SECRET_HERE",
            refresh_token="ADD_REFRESH_TOKEN_HERE",
        )
        file.write(EC3_REFRESHTOKEN_TEMPLATE % token)
