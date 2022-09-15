import json
import pathlib
import secrets
import string
import subprocess  # nosec
import tempfile

import click
import requests


def create_kubeconfig():
    """
    creates a temporary kubeconfig in /tmp to be used for the script
    :return: str: path to file
    """

    suffix = []
    suffix_length = 7
    while suffix_length:
        suffix.append(secrets.choice(string.ascii_uppercase + string.digits))
        suffix_length -= 1

    suffix = "".join(suffix)
    kubeconfig = pathlib.Path(tempfile.gettempdir(), f"kudeconfig-{suffix}")

    with open(kubeconfig, "w"):
        if not kubeconfig.is_file():
            click.echo("Kubeconfig file not created")
            exit(1)
    return kubeconfig.absolute()


def get_addon_information(kube_config, route, bearer_token, name, prefix):
    cr = get_rhoam_cr(kube_config, prefix)
    if cr is None:
        click.secho("failed to get the rhmi cr", fg="red")
        exit(1)
    try:
        alert_data = get_addon_alerts(
            route, bearer_token
        )  # TODO alerts might not be there when start the script
    except requests.exceptions.ConnectionError:
        alert_data = None

    subprocess.call("clear")  # nosec
    rhoam_details(cr, name)
    click.echo()
    process_alerts(alert_data)


def login_to_cluster(creds, kube_config):
    data = subprocess.run(  # nosec
        [
            "oc",
            "login",
            "--kubeconfig",
            kube_config,
            "-u",
            creds["user"],
            "-p",
            creds["password"],
            "--server",
            creds["api"],
        ],
        capture_output=True,
    )

    if data.stderr != b"":
        click.echo(f"Error logging into cluster, {str(data.stderr)}")


def get_bearer_token(auth):
    """
    get the bearer token for the give user and cluster
    :param auth: dict: {}
    :return: str:
    """
    base = auth["api"]
    base: str = base.split(":")[1]
    base = base.replace("//api", "https://oauth-openshift.apps")

    url = f"{base}/oauth/authorize?client_id=openshift-challenging-client&response_type=token"
    s = requests.Session()
    r = s.get(
        url,
        headers={"X-CSRF-Token": "xxx"},
        cookies={},
        auth=(auth["user"], auth["password"]),
    )

    location = r.history[0].headers["Location"]
    location = location.split("#")[1]
    location = location.split("&")

    token = None
    for item in location:
        if item.startswith("access_token"):
            token = item.split("=")[1]

    return token


def get_prometheus_route(kube_config, prefix):
    cmd = ["oc", "--kubeconfig", kube_config, "get", "routes", "-A", "-o", "json"]
    data = subprocess.run(cmd, capture_output=True)  # nosec
    data = json.loads(data.stdout)

    for item in data["items"]:
        if item["metadata"]["name"] == "prometheus" and is_namespace(
            item["metadata"]["namespace"], prefix, "observability"
        ):
            return item["spec"]["host"]


def is_namespace(namespace, prefix, suffix, separator="-"):
    ns = f"{prefix}{separator}{suffix}"
    if namespace == ns:
        return True
    else:
        return False


def get_rhoam_cr(kube_config, prefix):
    """
    Get the RHOAM CR in json format
    :param kube_config:
    :param prefix
    :return:
    """
    cmd = [
        "oc",
        "--kubeconfig",
        kube_config,
        "get",
        "rhmi",
        "rhoam",
        "-n",
        f"{prefix}-operator",
        "-o",
        "json",
    ]
    data = subprocess.run(cmd, capture_output=True)  # nosec
    if data.stdout == b"":
        return None
    return json.loads(data.stdout)


def get_addon_alerts(route, bearer_token):
    resq = requests.get(
        f"https://{route}/api/v1/alerts",
        headers={"Authorization": f"Bearer {bearer_token}"},
        cookies={},
        auth=(),
    )

    if resq.status_code == 200:
        return resq.json()["data"]["alerts"]
    else:
        return None


def rhoam_details(CR, cluster):
    """
    Print details from rhoam CR
    :param CR:
    :param cluster
    :return:
    """

    click.echo(click.style("Cluster: ", bold=True) + click.style(cluster))

    if "status" not in CR:
        click.secho("No status block in CR yet", fg="red")
        return

    status = CR["status"]["stage"]
    click.echo(click.style("Status: ", bold=True) + click.style(status))
    if "version" in CR["status"]:
        click.echo(
            click.style("Version: ", bold=True) + click.style(CR["status"]["version"])
        )
    if "toVersion" in CR["status"]:
        click.echo(
            click.style("To Version: ", bold=True)
            + click.style(CR["status"]["toVersion"])
        )
    if "quota" in CR["status"]:
        click.echo(
            click.style("Quota: ", bold=True) + click.style(CR["status"]["quota"])
        )
    if "toQuota" in CR["status"]:
        click.echo(
            click.style("To Quota: ", bold=True) + click.style(CR["status"]["toQuota"])
        )
    if "lastError" in CR["status"] and len(CR["status"]["lastError"]) > 0:
        start = click.style(f"Last Error:\n{'-' * 20}\n", bold=True)
        middle = click.style(CR["status"]["lastError"])
        end = click.style(f"\n{'-' * 20}")
        click.echo(f"{start}{middle}{end}")
    if status != "complete":
        click.echo(click.style("Current stage is: ", bold=True) + click.style(status))

        for stage in CR["status"]["stages"]:
            if stage == "bootstrap":
                continue
            for product in CR["status"]["stages"][stage]["products"]:
                if (
                    CR["status"]["stages"][stage]["products"][product]["status"]
                    != "completed"
                ):
                    current_product = CR["status"]["stages"][stage]["products"][product]

                    click.echo(
                        f"\t{current_product['name']}, {current_product['status']}"
                    )


def process_alerts(data: dict):
    if data is None:
        click.echo("No alert data found")
        return

    alerts = {}

    for point in data:
        if point["state"] in alerts:
            alerts[point["state"]].append(point)
        else:
            alerts.setdefault(point["state"], [])
            alerts[point["state"]].append(point)

    # TODO loops need to be sorted. They keep flipping
    for status in alerts:
        click.echo(
            click.style(f"{status} alerts: ", bold=True)
            + click.style(f"{len(alerts[status])}", fg="red")
        )

    click.echo()
    for status in alerts:
        click.echo(click.style(f"{status} alerts: ", bold=True))
        for item in alerts[status]:
            click.echo(f"\t{item['labels']['alertname']}")
        click.echo()
