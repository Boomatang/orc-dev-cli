import json
import os
import subprocess  # nosec

import click

from orc_dev_cli.helper import safe_string


def get_cluster_id(cluster_name):
    found_cluster = get_cluster_data(cluster_name)

    cluster_id: str = found_cluster["id"]
    return cluster_id


def get_cluster_data(cluster_name):

    n = safe_string(cluster_name)
    s = f"search=\"name='{n}'\""

    output = subprocess.run(
        [f"ocm get clusters -p {s}"], shell=True, capture_output=True  # nosec
    )

    data = json.loads(output.stdout)
    data = data["items"]
    found_cluster = None
    for item in data:
        if item["name"] == cluster_name:
            found_cluster = item
            break
    if found_cluster is None:
        click.echo(f'No cluster with display name "{cluster_name}" was found')
        exit(1)
    return found_cluster


def credentials(cluster_name):
    """
    Get the login details for the cluster admin
    :param cluster_name:
    :return: console url, {'user': <user>, 'password': <password>, 'api': <api>}
    """

    found_cluster = get_cluster_data(cluster_name)
    cluster_id: str = found_cluster["id"]
    cluster_console = found_cluster["console"]["url"]
    api = found_cluster["api"]["url"]
    cmd = f"ocm get /api/clusters_mgmt/v1/clusters/{cluster_id}/credentials"
    data = os.popen(  # nosec
        cmd
    )  # don't know why I can't get this to run in subprocess.run
    data = json.loads(data.read())["admin"]
    data["api"] = api
    return cluster_console, data
