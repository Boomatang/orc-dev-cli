import json
import subprocess  # nosec
import sys

import click

from orc_dev_cli.cluster import get_cluster_data, get_cluster_id


def get_cluster_state(cluster_data):
    state = cluster_data["status"]["state"]
    return state


def get_cluster_health(cluster_data):
    try:
        health = cluster_data["items"][0]["metrics"][0]["health_state"]
    except KeyError:
        health = "Unknown"
    return health


def get_cluster_sub(cluster):
    cmd = subprocess.run(  # nosec
        ["ocm", "get", "subs", "--parameter", f"search=cluster_id='{cluster}'"],
        capture_output=True,
    )
    if cmd.stderr is None:
        click.secho("Error getting subs form cluster", fg="red")
        sys.exit(1)
    data = json.loads(cmd.stdout)
    return data


def cli_cluster_state(name):
    cluster_id = get_cluster_id(name)
    data1 = get_cluster_data(name)
    data = get_cluster_sub(cluster_id)

    state = get_cluster_state(data1)
    out = f"Cluster: {name}\nState: "
    if state == "ready":
        state = state.upper()
        out += click.style(state, fg="green")
    else:
        out += state
        return out

    out += "\nHealth: "
    health = get_cluster_health(data)
    if health == "healthy":
        health = health.upper()
        out += click.style(health, fg="green")
    else:
        out += health

    return out
