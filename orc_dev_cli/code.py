import sys

import click


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
