from time import sleep

from orc_dev_cli.addon_state import (
    create_kubeconfig,
    get_addon_information,
    get_bearer_token,
    get_prometheus_route,
    login_to_cluster,
)
from orc_dev_cli.cluster import credentials


def cli_addon(name, watch, delay, prefix, insecure):
    kubeconfig = create_kubeconfig()
    _, creds = credentials(name)
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
