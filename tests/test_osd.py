import toml

from orc_dev_cli import __version__


def test_version():

    data = toml.load("../pyproject.toml")

    assert __version__ == data["tool"]["poetry"]["version"]  # nosec
