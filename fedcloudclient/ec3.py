"""
Implementation of ec3 commands for deploying EC3 (Elastic Cloud Computing
Cluster) in Cloud via Infrastructure Manager
"""

import os
import time

import click
import jwt
from fedcloudclient.checkin import get_access_token, oidc_params
from fedcloudclient.decorators import auth_file_params
from fedcloudclient.sites import find_endpoint_and_project_id, site_vo_params

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


__OPENSTACK_CLIENT = "openstack"
__MAX_WORKER_THREAD = 30


@click.group()
def ec3():
    """
    EC3 related comands
    """
    pass


@ec3.command()
@oidc_params
@auth_file_params
def refresh(
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    auth_file,
):
    """
    Refreshing token in EC3 authorization file
    """
    # Get the right endpoint from GOCDB
    auth_file_contents = []
    with open(auth_file, "r") as f:
        for raw_line in f.readlines():
            line = raw_line.strip()
            if "OpenStack" in line:
                auth_tokens = []
                for token in line.split(";"):
                    if token.strip().startswith("password"):
                        access_token = token.split("=")[1].strip()
                        if access_token[0] in ["'", '"']:
                            access_token = access_token[1:-1]
                        # FIXME(enolfc): add verification
                        payload = jwt.decode(
                            access_token, options={"verify_signature": False}
                        )
                        now = int(time.time())
                        expires = int(payload["exp"])
                        if expires - now < 300:
                            access_token = get_access_token(
                                oidc_access_token,
                                oidc_refresh_token,
                                oidc_client_id,
                                oidc_client_secret,
                                oidc_url,
                                oidc_agent_account,
                            )
                        auth_tokens.append("password = %s" % access_token)
                    else:
                        auth_tokens.append(token.strip())
                auth_file_contents.append("; ".join(auth_tokens))
            elif line:
                auth_file_contents.append(line)
    with open(auth_file, "w+") as f:
        f.write("\n".join(auth_file_contents))


@ec3.command()
@oidc_params
@site_vo_params
@auth_file_params
@click.option(
    "--template-dir",
    help="EC3 templates dir",
    default="./templates",
    show_default=True,
)
@click.option("--force", is_flag=True, help="Force rewrite of files")
def init(
    oidc_client_id,
    oidc_client_secret,
    oidc_refresh_token,
    oidc_access_token,
    oidc_url,
    oidc_agent_account,
    site,
    vo,
    auth_file,
    template_dir,
    force,
):
    """
    Creating EC3 authorization file and template
    """
    if os.path.exists(auth_file) and not force:
        print(
            "Auth file already exists, not replacing unless --force option is included"
        )
        raise click.Abort()

    access_token = get_access_token(
        oidc_access_token,
        oidc_refresh_token,
        oidc_client_id,
        oidc_client_secret,
        oidc_url,
        oidc_agent_account,
    )

    if site == "ALL_SITES":
        print("ec3 command cannot be used with ALL_SITES")
        raise click.Abort()

    endpoint, project_id, protocol = find_endpoint_and_project_id(site, vo)
    site_auth = [
        "id = %s" % site,
        "type = OpenStack",
        "username = egi.eu",
        "tenant = %s" % protocol,
        "auth_version = 3.x_oidc_access_token",
        "host = %s" % endpoint,
        "domain = %s" % project_id,
        "password = '%s'" % access_token,
    ]
    auth_file_contents = [";".join(site_auth)]
    if os.path.exists(auth_file):
        with open(auth_file, "r") as f:
            for line in f.readlines():
                if "OpenStack" in line:
                    continue
                auth_file_contents.append(line)
    with open(auth_file, "w+") as f:
        f.write("\n".join(auth_file_contents))
    if not os.path.exists(template_dir):
        os.mkdir(template_dir)
    # FIXME: this should not be used at all!
    with open(os.path.join(template_dir, "refresh.radl"), "w+") as f:
        v = dict(
            client_id=oidc_client_id,
            client_secret=oidc_client_secret,
            refresh_token=oidc_refresh_token,
        )
        f.write(EC3_REFRESHTOKEN_TEMPLATE % v)
