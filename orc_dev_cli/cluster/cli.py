import click

from orc_dev_cli.cluster.list import cli_list


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
