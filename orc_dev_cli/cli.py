import click

from orc_dev_cli import __version__
from orc_dev_cli.cluster.cli import cluster
from orc_dev_cli.config import configuration_file, load_config
from orc_dev_cli.rhoam.cli import rhoam

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


cli.add_command(cluster)
cli.add_command(rhoam)


if __name__ == "__main__":
    cli()
