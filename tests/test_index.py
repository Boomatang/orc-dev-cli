from unittest.mock import Mock

import git

# from mock import Mock, patch
import pytest
import semver

from orc_dev_cli.index_build.index import (
    get_release,
    get_semver,
    get_working_release,
    none_semver,
    sort_releases,
)

test_data = [
    ("1.2.3", "1.2.3", None),
    ("1.2.3", "1.2.3", ""),
    ("1.2.3", "1.2.3", "v"),
    ("1.2.3", "v1.2.3", "v"),
    ("1.2.3-rc1", "v1.2.3-rc1", "v"),
]


@pytest.mark.parametrize("expected,name,prefix", test_data)
def test_get_semver(expected, name, prefix):
    expected = semver.VersionInfo.parse(expected)

    tag = type("obj", (object,), {"name": name})()

    result = get_semver(tag, prefix)

    assert result == expected


test_data = [
    (
        {semver.VersionInfo.parse("1.2.3"): "tag-1.2.3"},
        [type("obj", (object,), {"name": "tag-1.2.3"})()],
        "tag-",
    ),
    ({}, [type("obj", (object,), {"name": "1.2.3"})()], "tag-"),
    (
        {
            semver.VersionInfo.parse("1.2.3"): "tag-1.2.3",
            semver.VersionInfo.parse("1.2.4"): "tag-1.2.4",
        },
        [
            type("obj", (object,), {"name": "tag-1.2.3"})(),
            type("obj", (object,), {"name": "tag-1.2.4"})(),
            type("obj", (object,), {"name": "1.2.3"})(),
        ],
        "tag-",
    ),
]


@pytest.mark.parametrize("expected,tags, marker", test_data)
def test_get_release(expected, tags, marker):
    repo = type("obj", (object,), {"tags": tags})()
    result = get_release(repo, marker)
    assert result.keys() == expected.keys()


test_data = [
    (
        [
            semver.VersionInfo.parse("1.2.3"),
            semver.VersionInfo.parse("1.2.4"),
        ],
        {
            semver.VersionInfo.parse("1.2.3"): type(
                "obj", (object,), {"prerelease": None}
            )(),
            semver.VersionInfo.parse("1.2.4"): type(
                "obj", (object,), {"prerelease": None}
            )(),
        },
    ),
    (
        [
            semver.VersionInfo.parse("1.2.2"),
            semver.VersionInfo.parse("1.2.3-rc1"),
        ],
        {
            semver.VersionInfo.parse("1.2.3-rc1"): type(
                "obj", (object,), {"prerelease": "rc1"}
            )(),
            semver.VersionInfo.parse("1.2.2"): type(
                "obj", (object,), {"prerelease": "rc2"}
            )(),
        },
    ),
    (
        [
            semver.VersionInfo.parse("1.2.2"),
            semver.VersionInfo.parse("1.2.3-rc2"),
        ],
        {
            semver.VersionInfo.parse("1.2.3-rc1"): type(
                "obj", (object,), {"prerelease": "rc1"}
            )(),
            semver.VersionInfo.parse("1.2.3-rc2"): type(
                "obj", (object,), {"prerelease": "rc2"}
            )(),
            semver.VersionInfo.parse("1.2.2"): type(
                "obj", (object,), {"prerelease": "rc2"}
            )(),
        },
    ),
    (
        [
            semver.VersionInfo.parse("1.2.2"),
            semver.VersionInfo.parse("1.2.3-rc2"),
            semver.VersionInfo.parse("1.2.4"),
            semver.VersionInfo.parse("1.2.5"),
        ],
        {
            semver.VersionInfo.parse("1.2.5-rc1"): type(
                "obj", (object,), {"prerelease": "rc1"}
            )(),
            semver.VersionInfo.parse("1.2.5"): type(
                "obj", (object,), {"prerelease": "rc2"}
            )(),
            semver.VersionInfo.parse("1.2.4"): type(
                "obj", (object,), {"prerelease": "rc2"}
            )(),
            semver.VersionInfo.parse("1.2.3-rc1"): type(
                "obj", (object,), {"prerelease": "rc1"}
            )(),
            semver.VersionInfo.parse("1.2.3-rc2"): type(
                "obj", (object,), {"prerelease": "rc2"}
            )(),
            semver.VersionInfo.parse("1.2.2"): type(
                "obj", (object,), {"prerelease": "rc2"}
            )(),
        },
    ),
]


@pytest.mark.parametrize("expected,release", test_data)
def test_sort_releases(expected, release):
    result = sort_releases(release)
    assert result == expected


test_data = [
    (None, []),
    ({"key": "wrong"}, []),
    ({"latest": {}}, ["latest"]),
    ({"new": {}}, ["new"]),
    ({"new": {}, "latest": {}}, ["latest", "new"]),
    ({"NEW": {}, "LATEST": {}}, ["latest", "new"]),
]


@pytest.mark.parametrize("config,result", test_data)
def test_none_semver(result, config):
    data = none_semver(config)

    assert data == result


data1 = {
    "tags": [
        semver.VersionInfo.parse("1.2.0"),
        semver.VersionInfo.parse("1.2.1"),
        semver.VersionInfo.parse("1.2.2"),
        semver.VersionInfo.parse("1.2.3"),
        semver.VersionInfo.parse("1.2.4"),
        semver.VersionInfo.parse("1.2.5"),
    ],
    "other": ["latest", "new"],
}

test_data = [
    (
        {"start": None, "data": data1},
        {"result": {"tags": [], "other": []}},
    ),
    (
        {"start": "1.2.2", "data": data1},
        {
            "result": {
                "tags": [
                    semver.VersionInfo.parse("1.2.2"),
                    semver.VersionInfo.parse("1.2.3"),
                    semver.VersionInfo.parse("1.2.4"),
                    semver.VersionInfo.parse("1.2.5"),
                ],
                "other": ["latest", "new"],
            }
        },
    ),
    (
        {"start": "current", "data": data1},
        {
            "result": {
                "tags": [semver.VersionInfo.parse("1.2.5")],
                "other": ["latest", "new"],
            }
        },
    ),
    (
        {"start": "latest", "data": data1},
        {"result": {"tags": [], "other": ["latest", "new"]}},
    ),
    (
        {"start": "new", "data": data1},
        {"result": {"tags": [], "other": ["new"]}},
    ),
]


@pytest.mark.parametrize("data,expected", test_data)
def test_get_working_release(data, expected):
    result = get_working_release(data["start"], data["data"])

    assert result == expected["result"]
