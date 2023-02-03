import subprocess  # nosec
from typing import Optional

import click
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

from orc_dev_cli.config import load_config

CONFIG = load_config()


class Cluster(BaseModel):
    id: Optional[str]
    name: Optional[str]
    api_url: Optional[str]
    openshift_version: Optional[str]
    product_id: Optional[str]
    cloud_provider: Optional[str]
    region_id: Optional[str]
    state: Optional[str]


def exclude_starts_with(cluster: Cluster) -> bool:
    starts_with = CONFIG["cluster"]["list"]["exclude"]["name_starts_with"]

    for start in starts_with:
        if cluster.name.startswith(start):
            return True

    return False


def exclude_state(cluster: Cluster) -> bool:
    states = CONFIG["cluster"]["list"]["exclude"]["states"]

    for state in states:
        if cluster.state == state:
            return True

    return False


def highlight_on_name(cluster: Cluster) -> bool:
    starts_with = CONFIG["cluster"]["list"]["highlight"]["name_starts_with"]

    for start in starts_with:
        if cluster.name.startswith(start):
            return True
    return False


def filter_exclude(
    clusters: list[Cluster], exclude_filters: tuple
) -> (list[Cluster], list[Cluster], list[Cluster]):
    display_clusters = []
    exclude_clusters = []
    highlight_clusters = []

    if len(exclude_filters) == 0:
        exclude_filters = CONFIG["cluster"]["list"]["exclude"]["filter"]

    filter_ = True if "none" not in exclude_filters else False
    uuid = True if "all" in exclude_filters or "uuid" in exclude_filters else False
    starts_with = (
        True if "all" in exclude_filters or "name" in exclude_filters else False
    )
    state = True if "all" in exclude_filters or "states" in exclude_filters else False

    for cluster in clusters:
        if filter_:
            if uuid and len(cluster.name) == 28:
                exclude_clusters.append(cluster)
                continue
            elif starts_with and exclude_starts_with(cluster):
                exclude_clusters.append(cluster)
                continue
            elif state and exclude_state(cluster):
                exclude_clusters.append(cluster)
                continue

        if highlight_on_name(cluster):
            highlight_clusters.append(cluster)

        display_clusters.append(cluster)

    return display_clusters, highlight_clusters, exclude_clusters


def cli_list(exclude_filters):
    data = subprocess.run(["ocm", "list", "cluster"], capture_output=True)  # nosec
    if data.stderr == b"":
        data = data.stdout.decode()
    else:
        click.echo(data.stderr.decode())

    # with open("samples/mock_ocm_list_cluster.txt") as f:
    #     data = f.read()

    data = data.split("\n")

    clusters = []

    for d in data:
        if d.startswith("ID "):
            continue

        v = d.split(" ")
        b = []
        for i in v:
            if i:
                b.append(i)
        if b:
            c = Cluster()
            c.id = b[0].strip()
            c.name = b[1].strip()
            c.api_url = b[2].strip()
            c.openshift_version = b[3].strip()
            c.product_id = b[4].strip()
            c.cloud_provider = b[5].strip()
            c.region_id = b[6].strip()
            c.state = b[7].strip()

            clusters.append(c)

    display_clusters, highlight_clusters, exclude_clusters = filter_exclude(
        clusters, exclude_filters
    )

    display_clusters = sorted(display_clusters, key=lambda dc: dc.name)

    table = Table(
        "ID",
        "NAME",
        "API URL",
        "OPENSHIFT_VERSION",
        "PRODUCT_ID",
        "CLOUD_PROVIDER",
        "REGION ID",
        "STATE",
        box=None,
    )

    for cluster in display_clusters:
        if cluster in highlight_clusters:
            table.add_row(
                f"[bold green]{cluster.id}",
                f"[bold green]{cluster.name}",
                f"[bold green]{cluster.api_url}",
                f"[bold green]{cluster.openshift_version}",
                f"[bold green]{cluster.product_id}",
                f"[bold green]{cluster.cloud_provider}",
                f"[bold green]{cluster.region_id}",
                f"[bold green]{cluster.state}",
            )
        else:
            table.add_row(
                cluster.id,
                cluster.name,
                cluster.api_url,
                cluster.openshift_version,
                cluster.product_id,
                cluster.cloud_provider,
                cluster.region_id,
                cluster.state,
            )

    console = Console()
    console.print(table)


if __name__ == "__main__":
    cli_list(())
