import sys
from pathlib import Path

if sys.version_info.minor < 11:
    import toml
else:
    import tomllib as toml

from orc_dev_cli import __version__


def test_version():
    try:
        fp = Path("../pyproject.toml")
        if not fp.is_file():
            raise FileNotFoundError
        with open(fp, "rb") as f:
            data = toml.load(f)
    except FileNotFoundError:
        with open("pyproject.toml", "rb") as f:
            data = toml.load(f)

    assert __version__ == data["tool"]["poetry"]["version"]
