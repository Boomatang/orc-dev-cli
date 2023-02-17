import click

from orc_dev_cli import __version__
from orc_dev_cli.cluster.cli import cluster
from orc_dev_cli.code import cli_addon
from orc_dev_cli.config import configuration_file, load_config, try_function_defined
from orc_dev_cli.index_build.index import cli_index, cli_template

CONFIG = load_config()


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Dev tooling for creating, loging into, deleting OSD cluster and watching RHOAM addons

    Configuration file location: ~/.config/orc/config.toml
    """
    pass


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
def addon(cluster_, watch, delay, prefix, insecure):
    """
    Get the current state of an installed addon instances
    """
    cli_addon(cluster_, watch, delay, prefix, insecure)


@cli.command()
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


cli.add_command(cluster)


if __name__ == "__main__":
    cli()
