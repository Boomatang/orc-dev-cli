import logging
import shutil
import tempfile
from pathlib import Path
from pprint import pprint

import git
import semver
import toml

from orc_dev_cli.config import merge
from orc_dev_cli.index_build.default import build, required

log = logging.getLogger("indexing")
log.addHandler(logging.StreamHandler())
log.setLevel("DEBUG")


def cli_template():
    with open("samples/index_build.toml") as f:
        print(f.read())


def valid_config(config: dict, must_have: dict) -> (bool, list):
    # TODO this function needs to be filled out
    return True, []


def clone_repo(repo: str, location: Path):
    if not repo.startswith("git") or not repo.endswith(".git"):
        log.warning(
            f"Repo clone url seems to be in correct please check configuration. {repo}"
        )
        exit(1)

    log.info(f"Cloning repo: {repo} to {location}")
    r = git.Repo.clone_from(repo, location)
    return r


def existing_repo(location: Path):
    return git.Repo(location)


def get_release(repo: git.Repo, prefix):
    tags = repo.tags
    releases = (t for t in tags if t.name.lower().startswith(prefix))
    versions = {}

    for release in releases:
        version = get_semver(release, prefix)
        versions[version] = release

    return versions


def sort_releases(releases):

    keys = list(releases.keys())
    keys = sorted(keys)

    versions = []
    prerelease = []
    prerelease_rc = {}
    for key in keys:
        if not key.prerelease:
            versions.append(key)
        else:
            prerelease.append(key)

    for release in prerelease:
        a = semver.VersionInfo(
            major=release.major, minor=release.minor, patch=release.patch
        )
        if a not in versions:
            if a in prerelease_rc.keys():
                prerelease_rc[a].append(release)
            else:
                prerelease_rc.setdefault(
                    a,
                    [
                        release,
                    ],
                )

    for rcs in prerelease_rc:
        high = None
        for r in prerelease_rc[rcs]:
            if high is None:
                high = r
            else:
                if high.prerelease < r.prerelease:
                    high = r
        versions.append(high)

    versions = sorted(versions)
    return versions


def none_semver(config):
    """
    This function will return the latest and new markers if the version are in the config
    """
    result = []

    if config is None:
        return result

    keys = [k.lower() for k in config]

    if "latest" in keys:
        result.append("latest")

    if "new" in keys:
        result.append("new")

    return result


def get_working_release(chain_start, data):

    match chain_start:
        case None:
            return {"tags": [], "other": []}
        case "new":
            return {"tags": [], "other": ["new"]}
        case "latest":
            return {"tags": [], "other": ["latest", "new"]}
        case "current":
            return {"tags": [data["tags"][-1]], "other": data["other"]}
        case _:
            base = semver.VersionInfo.parse(chain_start)
            index = data["tags"].index(base)
            tags = data["tags"][index:]
            return {"tags": tags, "other": data["other"]}


def cli_index(configuration):
    configuration = Path(configuration)
    config = load_config(configuration)
    ok, errors = valid_config(config, required)
    if not ok:
        for error in errors:
            print(error)
        exit(1)
    log.debug(f"Configuration Data: {config}")
    temp_location = Path(tempfile.gettempdir(), config["configuration"]["operator"])
    config["configuration"]["temporary"]["location"] = temp_location

    if config["configuration"]["temporary"]["reuse"] and temp_location.exists():
        log.info("Using existing temporary repo")
        repo = existing_repo(temp_location)
    else:
        if temp_location.exists():
            log.info("Removing existing temporary repo")
            shutil.rmtree(temp_location)
        repo = clone_repo(config["configuration"]["remote"], temp_location)

    releases = get_release(repo, config["configuration"]["tag_marker"])
    versions = sort_releases(releases)
    other = none_semver(config)
    data = {"tags": versions, "other": other}
    data = get_working_release(config["chain"]["start"], data)
    log.debug(f"Version Data: {data}")

    print(
        """
    Next Steps:
        for version
            build operator
            build bundle
            build index
            push images
            update the json file
    """
    )


def get_semver(tag: git.TagReference, prefix=None):
    if prefix is None:
        name = tag.name
    else:
        name = tag.name.strip(prefix)

    return semver.VersionInfo.parse(str(name))


def load_config(config_file: Path):
    data = {}

    if config_file.is_file():
        with open(config_file, "r") as f:
            data = toml.loads(f.read())

    output = merge(build, data)

    return output
