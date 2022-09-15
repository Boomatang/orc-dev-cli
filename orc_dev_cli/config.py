import pathlib
import subprocess  # nosec
import sys
import textwrap

import click
import toml

HOST = pathlib.Path.home()
CONFIG_PATH = pathlib.Path(HOST, ".config", "orc")
CONFIG_FILE = pathlib.Path(CONFIG_PATH, "config.toml")


def configuration_file():

    if not CONFIG_FILE.is_file():
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        data = textwrap.dedent(
            """\
        [default]
        cluster = ""
        delay = 10
        prefix = "redhat-rhoam"
        watch = false
        """
        )
        with open(CONFIG_FILE, "w") as f:
            f.write(data)

        click.echo(f"Configuration file created: {CONFIG_FILE}")

    cmd = None
    if sys.platform.startswith("linux"):
        cmd = "xdg-open"
    elif sys.platform.startswith("darwin"):
        cmd = "open"
    else:
        click.echo("Auto opening of configuration file failed unsupported platform")
        exit(1)

    subprocess.call([cmd, CONFIG_FILE])  # nosec


def merge(a: dict, b: dict):

    for key in a:
        if key in b:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                a[key].update(b[key])
            else:
                a[key] = b[key]

    for key in b:
        if key not in a:
            a[key] = b[key]

    return a


def load_config():
    data = {}
    config = {
        "default": {
            "cluster": "",
            "delay": 10,
            "prefix": "redhat-rhoam",
            "watch": False,
        },
    }

    if CONFIG_FILE.is_file():
        with open(CONFIG_FILE, "r") as f:
            data = toml.loads(f.read())

    output = merge(config, data)

    return output


def try_function_defined(config: dict, func: str, field: str):
    if func in config:
        if field in config[func]:
            return config[func][field]
    return config["default"][field]
