import json
import os
import subprocess  # nosec
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


def cli_creds(cluster):
    console, creds = get_cluster_credentials(cluster)
    print_screen(console, creds, cluster)


def cli_delete(cluster):
    click.echo("Deleting Cluster: " + click.style(cluster, fg="red"))
    cluster = get_cluster_id(cluster)
    delete_cluster(cluster)


def get_cluster_id(cluster_name):
    found_cluster = get_cluster_data(cluster_name)

    cluster_id: str = found_cluster["id"]
    return cluster_id


def get_cluster_data(cluster_name):
    output = subprocess.run(["ocm", "get", "clusters"], capture_output=True)  # nosec
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


def delete_cluster(cluster_id):
    subprocess.run(["ocm", "delete", "cluster", cluster_id])  # nosec


def print_screen(console_url, data, name):
    click.echo(click.style("Cluster: ", bold=True) + click.style(name))
    click.echo(click.style("Console: ", bold=True) + click.style(console_url))
    click.echo(
        click.style("Console Login: ", bold=True)
        + click.style(get_console_login(base_url(console_url)))
    )

    click.echo()
    click.echo(click.style("Login Command:", bold=True))
    click.echo(login_command(data))

    click.echo()
    click.echo(click.style("User: ", bold=True) + click.style(data["user"]))
    click.echo(click.style("Password: ", bold=True) + click.style(data["password"]))


def base_url(url):
    spilt = url.split("apps.")
    return spilt[1]


def login_command(creds):
    cmd = [
        "oc",
        "login",
        "-u",
        creds["user"],
        "-p",
        creds["password"],
        "--server",
        creds["api"],
    ]
    return " ".join(cmd)


def get_console_login(url):
    return (
        f"https://oauth-openshift.apps.{url}/"
        f"login?then=%2Foauth%2Fauthorize%3Fclient_id%3Dconsole%26idp%3Dkubeadmin%26"
        f"redirect_uri%3Dhttps%253A%252F%252Fconsole-openshift-console.apps."
        f"{url}%252Fauth%252Fcallback%26response_type%3Dcode%26scope%3Duser%253Afull"
    )


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


def cli_addon(name, watch, delay, prefix):
    kubeconfig = create_kubeconfig()
    _, creds = get_cluster_credentials(name)
    login_to_cluster(creds, kubeconfig)
    bearer_token = get_bearer_token(creds)
    route = get_prometheus_route(kubeconfig, prefix)

    while watch:
        get_addon_information(kubeconfig, route, bearer_token, name, prefix)
        sleep(delay)
        if route is None:
            route = get_prometheus_route(kubeconfig, prefix)
    else:
        get_addon_information(kubeconfig, route, bearer_token, name, prefix)
