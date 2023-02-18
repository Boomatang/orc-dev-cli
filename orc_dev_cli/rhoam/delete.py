import subprocess  # nosec

import click

from orc_dev_cli.addon_state import create_kubeconfig, login_to_cluster
from orc_dev_cli.cluster import credentials


def delete_rhmi_cr(kube_config, prefix):
    cmd = [
        "oc",
        "--kubeconfig",
        kube_config,
        "delete",
        "rhmi",
        "rhoam",
        "-n",
        f"{prefix}-operator",
    ]
    data = subprocess.run(cmd, capture_output=True)  # nosec
    if data.stderr != b"":
        return data.stderr.decode()
    return data.stdout.decode()


def action(cluster, prefix):
    kubeconfig = create_kubeconfig()
    _, creds = credentials(cluster)
    login_to_cluster(creds, kubeconfig, False)
    result = delete_rhmi_cr(kubeconfig, prefix)
    click.echo(result)
