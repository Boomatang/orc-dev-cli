import toml

from orc import __version__


def test_version():

    data = toml.load("../pyproject.toml")

    assert __version__ == data["tool"]["poetry"]["version"]  # nosec
