from time import sleep

import click

from orc_dev_cli import __version__
from orc_dev_cli.code import (
    cli_addon,
    cli_cluster_state,
    cli_creds,
    cli_delete,
    state_exit_condition,
)
from orc_dev_cli.config import configuration_file, load_config, try_function_defined

CONFIG = load_config()


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Dev tooling for creating, loging into, deleting OSD cluster and watching RHOAM addons

    Configuration file location: ~/.config/orc/config.toml
    """
    pass


@cli.command()
@click.option(
    "-c",
    "--cluster",
    default=try_function_defined(CONFIG, "login", "cluster"),
    show_default=True,
    help="Name of cluster. Config: cluster",
)
def login(cluster):
    """
    Get cluster kubeadmin login details.
    """
    cli_creds(cluster)


@cli.command()
@click.option(
    "-c",
    "--cluster",
    default=try_function_defined(CONFIG, "osd", "cluster"),
    show_default=True,
    help="Name of cluster. Config: cluster",
)
@click.option(
    "-w/-x",
    "--watch/--no-watch",
    default=try_function_defined(CONFIG, "osd", "watch"),
    help="Watch the current state of a cluster, Config: watch [boolean]",
    show_default=True,
)
@click.option(
    "-d",
    "--delay",
    type=int,
    default=try_function_defined(CONFIG, "osd", "delay"),
    help="Refresh delay in seconds. Config: delay",
    show_default=True,
)
@click.option(
    "-e",
    "--exit",
    "_exit",
    type=click.Choice(["State", "Health"], case_sensitive=False),
    help="Set condition for watch exit.",
)
def osd(cluster, watch, delay, _exit):
    """
    Get basic state information on osd cluster
    """

    while watch:
        message = cli_cluster_state(cluster)
        click.clear()
        click.echo(message)
        state_exit_condition(_exit, message)
        sleep(delay)
    else:
        message = cli_cluster_state(cluster)
        click.echo(message)


@cli.command()
@click.argument("cluster")
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Are you sure you want to delete this cluster?",
    help="Confirm deletion on command execution.",
)
def delete(cluster):
    """
    Delete cluster.
    """
    cli_delete(cluster)


@cli.command()
def config():
    """
    Open configuration file
    """
    configuration_file()


@cli.command()
@click.option(
    "-c",
    "--cluster",
    default=try_function_defined(CONFIG, "addon", "cluster"),
    show_default=True,
    help="Name of cluster. Config: cluster",
)
@click.option(
    "-w/-x",
    "--watch/--no-watch",
    default=try_function_defined(CONFIG, "addon", "watch"),
    help="Watch the current state of a cluster. Config: watch [boolean]",
    show_default=True,
)
@click.option(
    "-d",
    "--delay",
    type=int,
    default=try_function_defined(CONFIG, "addon", "delay"),
    help="Refresh delay in seconds. Config: delay",
    show_default=True,
)
@click.option(
    "-p",
    "--prefix",
    type=str,
    help="Namespace prefix for addon. Config: prefix",
    default=try_function_defined(CONFIG, "addon", "prefix"),
    show_default=True,
)
def addon(cluster, watch, delay, prefix):
    """
    Get the current state of an installed addon instances
    """
    cli_addon(cluster, watch, delay, prefix)


if __name__ == "__main__":
    cli()
