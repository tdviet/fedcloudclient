"""
Main CLI module
"""

import click
from fedcloudclient.checkin import token
from fedcloudclient.ec3 import ec3
from fedcloudclient.endpoint import endpoint
from fedcloudclient.openstack import openstack, openstack_int
from fedcloudclient.sites import site


@click.group()
@click.version_option()
def cli():
    pass


cli.add_command(token)
cli.add_command(endpoint)
cli.add_command(ec3)
cli.add_command(site)

cli.add_command(openstack)
cli.add_command(openstack_int)

if __name__ == "__main__":
    cli()
