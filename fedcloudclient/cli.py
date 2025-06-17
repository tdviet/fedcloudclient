"""
Main CLI module
"""

import click

from fedcloudclient.checkin import token
<<<<<<<<< Temporary merge branch 1
from fedcloudclient.config import config
from fedcloudclient.ec3 import ec3
=========
from fedcloudclient.conf import config
>>>>>>>>> Temporary merge branch 2
from fedcloudclient.endpoint import endpoint
from fedcloudclient.openstack import openstack, openstack_int
from fedcloudclient.secret import secret
from fedcloudclient.select import select
from fedcloudclient.sites import site


@click.group()
@click.version_option()
def cli():
    """
    CLI main function. Intentionally empty
    """


cli.add_command(token)
cli.add_command(endpoint)
cli.add_command(site)
cli.add_command(secret)
cli.add_command(select)
cli.add_command(openstack)
cli.add_command(openstack_int)
cli.add_command(config)
<<<<<<<<< Temporary merge branch 1


if __name__ == "__main__":
    cli()
