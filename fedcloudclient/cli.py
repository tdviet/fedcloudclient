import click

from fedcloudclient.sites import site
from fedcloudclient.checkin import token
from fedcloudclient.endpoint import endpoint
from fedcloudclient.openstack import openstack, openstack_int


@click.group()
def cli():
    pass


cli.add_command(token)
cli.add_command(endpoint)
cli.add_command(site)

cli.add_command(openstack)
cli.add_command(openstack_int)

if __name__ == "__main__":
    cli()
