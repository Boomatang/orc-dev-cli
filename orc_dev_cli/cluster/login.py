import click
import pyperclip

from orc_dev_cli.code import get_cluster_credentials


def cli_creds(cluster):
    console, creds = get_cluster_credentials(cluster)
    pyperclip.copy(creds["password"])
    print_screen(console, creds, cluster)


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
    click.echo(
        click.style("Password: ", bold=True)
        + click.style(data["password"])
        + click.style(" (copied)", italic=True, dim=True)
    )


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
