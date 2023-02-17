import subprocess  # nosec

import click

from orc_dev_cli.cluster import get_cluster_id


def cli_delete(cluster):
    click.echo("Deleting Cluster: " + click.style(cluster, fg="red"))
    cluster = get_cluster_id(cluster)
    delete_cluster(cluster)


def delete_cluster(cluster_id):
    subprocess.run(["ocm", "delete", "cluster", cluster_id])  # nosec
