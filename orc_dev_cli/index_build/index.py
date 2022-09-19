from pathlib import Path
from pprint import pprint

import toml

from orc_dev_cli.config import merge
from orc_dev_cli.index_build.default import build, required


def cli_template():
    with open("samples/index_build.toml") as f:
        print(f.read())


def valid_config(config: dict, must_have: dict) -> (bool, list):
    # TODO this function needs to be filled out
    return True, []


def cli_index(configuration):
    print("WIP")
    print(
        """
    1. Read in configuration file
    """
    )

    configuration = Path(configuration)
    config = load_config(configuration)

    ok, errors = valid_config(config, required)
    if not ok:
        for error in errors:
            print(error)
        exit(1)

    pprint(config)
    print(
        """
    2. Clone the repo to a temp location
    3. Get all the different tags the versions that is state in the configuration
    4. Start at the oldest tag
    """
    )


def load_config(config_file: Path):
    data = {}

    if config_file.is_file():
        with open(config_file, "r") as f:
            data = toml.loads(f.read())

    output = merge(build, data)

    return output
