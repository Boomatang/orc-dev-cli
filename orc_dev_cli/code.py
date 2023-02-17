import json
import os
import sys
from time import sleep

import click

from orc_dev_cli.addon_state import (
    create_kubeconfig,
    get_addon_information,
    get_bearer_token,
    get_prometheus_route,
    login_to_cluster,
)
from orc_dev_cli.cluster import get_cluster_data


def get_cluster_credentials(cluster_name):
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


def state_exit_condition(state, message):

    if state is None:
        return

    state = state.lower()
    data = message.split("\n")

    if len(data) > 2:
        status = {"state": data[1], "health": data[2]}
    else:
        status = {"state": data[1], "health": ""}

    if state == "state" and "READY" in status[state]:
        sys.exit()

    if state == "health" and "HEALTHY" in status[state]:
        sys.exit()

    return


def cli_create_cluster(name, version, region, node, num):
    click.echo("create a cluster")
    click.echo(f"name: {name}")
    click.echo(f"version: {version}")
    click.echo(f"region: {region}")
    click.echo(f"node: {node}")
    click.echo(f"num: {num}")


def cli_addon(name, watch, delay, prefix, insecure):
    kubeconfig = create_kubeconfig()
    _, creds = get_cluster_credentials(name)
    login_to_cluster(creds, kubeconfig, insecure)
    bearer_token = get_bearer_token(creds)
    route = get_prometheus_route(kubeconfig, prefix)

    while watch:
        get_addon_information(kubeconfig, route, bearer_token, name, prefix)
        sleep(delay)
        if route is None:
            route = get_prometheus_route(kubeconfig, prefix)
    else:
        get_addon_information(kubeconfig, route, bearer_token, name, prefix)
