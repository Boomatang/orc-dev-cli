from time import sleep

import click

from orc_dev_cli.cluster.delete import cli_delete
from orc_dev_cli.cluster.list import cli_list
from orc_dev_cli.cluster.login import cli_creds
from orc_dev_cli.cluster.status import cli_cluster_state
from orc_dev_cli.code import state_exit_condition
from orc_dev_cli.config import load_config, try_function_defined
from orc_dev_cli.helper import abort_if_false

CONFIG = load_config()


@click.group("cluster")
def cluster():
    """
    Functions for interacting with clusters
    """
    pass


def not_valid_filter_selection(exclude_filters):
    if len(exclude_filters) > 1 and (
        "all" in exclude_filters or "none" in exclude_filters
    ):
        return True
    return False


@cluster.command(name="list")
@click.option(
    "-e",
    "--exclude-filters",
    "exclude_filters",
    type=click.Choice(
        ["all", "uuid", "states", "name", "none"],
        case_sensitive=False,
    ),
    multiple=True,
)
def list_(exclude_filters):
    """
    List cluster using ocm and apply custom filtering to the results.
    """

    if not_valid_filter_selection(exclude_filters):
        click.echo(
            "Exclude filter all and none can not be select with other choices or with each other.\n"
            "Please check your input"
        )
        exit(1)

    cli_list(exclude_filters)


@cluster.command()
@click.option(
    "-c",
    "--cluster",
    "cluster_",
    default=try_function_defined(CONFIG, "login", "cluster"),
    show_default=True,
    help="Name of cluster. Config: cluster",
)
def login(cluster_):
    """
    Get cluster kubeadmin login details.
    """
    cli_creds(cluster_)


@cluster.command()
@click.option(
    "-c",
    "--cluster",
    "cluster_",
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
def status(cluster_, watch, delay, _exit):
    """
    Get basic state information on osd cluster
    """

    while watch:
        message = cli_cluster_state(cluster_)
        click.clear()
        click.echo(message)
        state_exit_condition(_exit, message)
        sleep(delay)
    else:
        message = cli_cluster_state(cluster_)
        click.echo(message)


@cluster.command()
@click.argument("cluster_")
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Are you sure you want to delete this cluster?",
    help="Confirm deletion on command execution.",
)
def delete(cluster_):
    """
    Delete cluster.
    """
    cli_delete(cluster_)
