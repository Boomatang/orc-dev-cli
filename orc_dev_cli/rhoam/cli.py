import click

from orc_dev_cli.config import load_config, try_function_defined
from orc_dev_cli.helper import abort_if_false
from orc_dev_cli.rhoam import delete as _delete
from orc_dev_cli.rhoam.index import cli_index, cli_template
from orc_dev_cli.rhoam.status import cli_addon

CONFIG = load_config()


@click.group("rhoam")
def rhoam():
    """
    Interacting with RHOAM addon
    """
    pass


@rhoam.command()
@click.option(
    "-c",
    "--cluster",
    "cluster_",
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
@click.option(
    "-i",
    "--insecure",
    is_flag=True,
    help="Allow connection to insecure or clusters not fully ready",
)
def status(cluster_, watch, delay, prefix, insecure):
    """
    Get the current state of an installed addon instances
    """
    cli_addon(cluster_, watch, delay, prefix, insecure)


@rhoam.command()
@click.option(
    "-c",
    "--config",
    "configuration",
    help="Configuration file used in build",
    default=try_function_defined(CONFIG, "index", "config"),
    show_default=True,
)
@click.option("--template", is_flag=True, help="Prints a sample configuration file")
def index(configuration, template):
    """
    Build and push images required for the doing catalog deployments.
    Build images for bundles, indexes and operator.
    This is done for the chain that can be created.
    """

    if template:
        cli_template()
    else:
        cli_index(configuration, CONFIG)


@rhoam.command()
@click.option(
    "-c",
    "--cluster",
    "cluster_",
    default=try_function_defined(CONFIG, "addon", "cluster"),
    show_default=True,
    help="Name of cluster. Config: cluster",
)
@click.option(
    "-p",
    "--prefix",
    type=str,
    help="Namespace prefix for addon. Config: prefix",
    default=try_function_defined(CONFIG, "addon", "prefix"),
    show_default=True,
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Are you sure you want to delete this RHOAM?",
    help="Confirm deletion on command execution.",
)
def delete(cluster_, prefix):
    """
    Delete the RHOAM rhmi CR from a cluster
    """
    click.echo("This action may take sometime...")
    _delete.action(cluster_, prefix)
