import json
import os
import shutil
import subprocess  # nosec
import sys
import tempfile
from pathlib import Path
from typing import Dict

import click
import git
import requests
import semver
import yaml
from podman import PodmanClient

from orc_dev_cli import config
from orc_dev_cli.config import merge
from orc_dev_cli.rhoam.index.default import build, required

if sys.version_info.minor < 11:
    import toml
else:
    import tomllib as toml


def cli_template():
    root = Path(os.path.relpath(__file__))
    template = Path(root.parent, "..", "data", "index.toml")
    with open(template) as f:
        click.echo(f.read())


def valid_config(config: dict, must_have: dict) -> (bool, list):
    # TODO this function needs to be filled out
    return True, []


def clone_repo(repo: str, location: Path):
    if not repo.startswith("git@") or not repo.endswith(".git"):
        click.secho(
            f"Repo clone url seems to be in correct please check configuration. {repo}",
            fg="red",
            bold=True,
        )
        exit(1)

    click.echo(f"Cloning repo: {repo} to {location}")
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
    other = ["latest", "new"]

    if config is None:
        return result

    for key in other:
        if key in config and config[key]["include"]:
            result.append(key)

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


def checkout(repo, tag, config):
    if type(tag) == semver.VersionInfo:
        name = f"{config['configuration']['tag_marker']}{tag}"
    else:
        name = tag

    repo.git.checkout(name)


def get_service_affecting(csv):
    with open(csv, "r") as f:
        data = yaml.safe_load(f)

        if (
            "metadata" in data
            and "annotations" in data["metadata"]
            and "serviceAffecting" in data["metadata"]["annotations"]
        ):
            return data["metadata"]["annotations"]["serviceAffecting"]
    return True


def remove_replaces(csv):
    with open(csv, "r") as f:
        data = yaml.safe_load(f)

    del data["spec"]["replaces"]
    with open(csv, "w") as f:
        f.write(yaml.dump(data))


def container_exist_remote(config, repo, tag: str):
    image_site = config["configuration"]["image_site"]
    org = config["configuration"]["org"]

    if image_site != "quay.io":
        click.secho(
            "The checking for existing containers only works with quay.io",
            fg="red",
            bold=True,
        )
        return False

    click.echo(f"Searching for tag {tag} in repository {repo}")
    url = f"https://{image_site}/api/v1/repository/{org}/{repo}/tag"
    resq = requests.get(url, timeout=30)
    data = resq.json()
    data = data["tags"]
    for t in data:
        if t["name"] == tag:
            return True
    return False


def build_container(image, uri, container_file, dockerfile=None, buildargs=None):
    click.echo(f"Building container image: {image}")
    click.secho(f"Container File: {container_file}", dim=True)
    with PodmanClient(base_url=uri) as client:
        if dockerfile is None:
            client.images.build(
                path=container_file.parent,
                dockerfile=container_file.name,
                tag=image,
                buildargs=buildargs,
            )
        else:
            click.secho(f"Building with dockerfile: {dockerfile}", dim=True)
            client.images.build(
                path=container_file,
                dockerfile=dockerfile,
                tag=image,
                buildargs=buildargs,
            )
        client.images.prune()


def push_container(image, uri):
    click.echo(f"Pushing container image: {image}")
    with PodmanClient(base_url=uri) as client:
        client.images.push(image)


def build_index(image, bundles):
    click.echo(f"Building index image: {image}")
    click.secho(f"Bundles in index: {bundles}", dim=True)
    b = []
    for bundle in bundles:
        b.append("--bundles")
        b.append(bundle)

    s = ["opm", "index", "add"]
    e = ["--build-tool", "podman", "--tag", image]
    cmd = s + b + e
    subprocess.run(cmd, check=True)  # nosec


def work_on_tag(repo, tag, config, bundles, first=False, label=None):
    uri = f"unix:/run/user/{os.getuid()}/podman/podman.sock"
    csv = Path(
        repo.working_dir,
        "bundles",
        config["configuration"]["operator"],
        f"{tag.major}.{tag.minor}.{tag.patch}",
        "manifests",
        f"{config['configuration']['operator']}.clusterserviceversion.yaml",
    )

    image_site = config["configuration"]["image_site"]
    org = config["configuration"]["org"]
    operator = config["configuration"]["operator"]
    bundle = f"{operator}-bundle"
    index = f"{operator}-index"
    config_tag = semver.VersionInfo(major=tag.major, minor=tag.minor, patch=tag.patch)

    pre_release = get_config_value("pre_release", config, config_tag, label)

    if pre_release not in [False, None]:
        tag = semver.VersionInfo(
            major=tag.major,
            minor=tag.minor,
            patch=tag.patch,
            prerelease=pre_release,
        )
    else:
        tag = semver.VersionInfo(major=tag.major, minor=tag.minor, patch=tag.patch)
    operator_tag = f'{config["configuration"]["tag_marker"]}{tag}'
    data = {
        "label": label,
        "operator": f"{Path(image_site, org, operator)}:{operator_tag}",
        "bundle": f"{Path(image_site, org, bundle)}:{tag}",
        "index": f"{Path(image_site, org, index)}:{tag}",
    }
    bundles.append(data["bundle"])

    build_operator = True
    if get_config_value("operator", config, config_tag, label) == "reuse":
        result = container_exist_remote(config, operator, str(operator_tag))
        if result:
            click.secho(
                f"Reusing existing remote operator: {data['operator']}", fg="green"
            )
            build_operator = False

    do_build_index = True
    if get_config_value("index", config, config_tag, label) == "reuse":
        result = container_exist_remote(config, index, str(tag))
        if result:
            click.secho(f"Reusing existing remote index: {data['index']}", fg="green")
            do_build_index = False

    build_bundle = True
    if get_config_value("bundle", config, config_tag, label) == "reuse":
        result = container_exist_remote(config, bundle, str(tag))
        if result:
            click.secho(f"Reusing existing remote bundle: {data['bundle']}", fg="green")
            data["service_affecting"] = "unknown"
            build_bundle = False

    if build_bundle:
        state = get_config_value("service_affecting", config, config_tag, label)
        service_affecting = is_service_affecting(csv, state)
        data["service_affecting"] = service_affecting
        release_prepare(config, repo, service_affecting, tag)

        if first:
            remove_replaces(csv)

        data["bundle_built"] = True
        config["configuration"]["temporary"]["rebuild"] = True

    data["bundles"] = bundles.copy()

    if build_operator:
        build_container(data["operator"], uri, Path(repo.working_dir, "Dockerfile"))
        push_container(data["operator"], uri)

    if build_bundle:
        build_container(
            data["bundle"],
            uri,
            repo.working_dir,
            dockerfile=Path(
                "bundles", config["configuration"]["operator"], "bundle.Dockerfile"
            ),
            buildargs={"version": f"{tag.major}.{tag.minor}.{tag.patch}"},
        )
        push_container(data["bundle"], uri)

    if do_build_index or config["configuration"]["temporary"]["rebuild"]:
        click.secho("No validation is happening on the bundles", fg="red")
        build_index(data["index"], bundles)
        push_container(data["index"], uri)

    if label != "new":
        repo.git.restore("*")

    return data


def is_service_affecting(csv, state):
    match state:
        case "existing":
            if csv.exists():
                service_affecting = get_service_affecting(csv)
            else:
                service_affecting = True
            return service_affecting
        case _:
            return state


def get_config_value(setting, config, tag=None, label=None):
    if tag is not None:
        tag = str(tag)
        if tag in config and setting in config[tag]:
            return config[tag][setting]

    if label is not None:
        if label in config and setting in config[label]:
            return config[label][setting]

    state = config["chain"][setting]
    return state


def release_prepare(config, repo, service_affecting, tag):
    subprocess.run(  # nosec
        [
            "make",
            "release/prepare",
            f"SEMVER={tag}",
            f"ORG={config['configuration']['org']}",
            f"OLM_TYPE={config['configuration']['operator']}",
            f"SERVICE_AFFECTING={service_affecting}",
        ],
        cwd=repo.working_dir,
        check=True,
    )


def next_version(tag: semver.VersionInfo):
    return tag.bump_minor()


def write_json_config(chain):
    _chain = {}
    for key in chain:
        _chain[str(key)] = chain[key]

    data = json.dumps(_chain)
    data_file = Path(tempfile.gettempdir(), "orc_index_data.json")
    with open(data_file, "w") as f:
        f.write(data)


def cli_index(configuration, main_configuration=None):
    if main_configuration is None:
        main_configuration = {}
    configuration = Path(configuration)
    config = load_config(configuration, main_configuration)
    ok, errors = valid_config(config, required)
    if not ok:
        for error in errors:
            click.secho(error, fg="red")
        exit(1)
    temp_location = Path(tempfile.gettempdir(), config["configuration"]["operator"])
    config["configuration"]["temporary"]["location"] = temp_location

    if config["configuration"]["temporary"]["reuse"] and temp_location.exists():
        click.echo("Using existing temporary repo")
        repo = existing_repo(temp_location)
    else:
        if temp_location.exists():
            click.echo("Removing existing temporary repo")
            shutil.rmtree(temp_location)
        repo = clone_repo(config["configuration"]["remote"], temp_location)

    releases = get_release(repo, config["configuration"]["tag_marker"])
    versions = sort_releases(releases)
    other = none_semver(config)
    data = {"tags": versions, "other": other}
    data = get_working_release(config["chain"]["start"], data)

    chain = {}
    bundles = []
    last_tag = None
    for tag in data["tags"]:
        click.echo(f"Working on: {tag}")
        if data["tags"].index(tag) == 0:
            first = True
        else:
            first = False
        checkout(repo, tag, config)

        label = None
        if tag == data["tags"][-1]:
            label = "current"
        chain_data = work_on_tag(repo, tag, config, bundles, first, label=label)
        chain[tag] = chain_data
        last_tag = tag

    if "latest" in data["other"]:
        click.echo(f"Working on: latest ({config['latest']['branch']})")

        if last_tag is None:
            first = True
        else:
            first = False

        branch = config["latest"]["branch"]
        checkout(repo, branch, config)

        bundle_path = Path(
            repo.working_dir, "bundles", config["configuration"]["operator"]
        )

        if config["chain"]["start"] == "latest":
            tag = get_version_latest_tag(bundle_path)
        else:
            tag = next_version(last_tag)

        chain_data = work_on_tag(repo, tag, config, bundles, first, label="latest")
        chain[tag] = chain_data
        last_tag = tag

    if "new" in data["other"]:
        chain_data, tag = build_new(bundles, config, last_tag)
        chain[tag] = chain_data

    write_json_config(chain)


def get_version_latest_tag(bundle_path):
    versions = []
    dirs = os.listdir(bundle_path)
    for parts in dirs:
        if Path(bundle_path, str(parts)).is_dir():
            versions.append(semver.VersionInfo.parse(parts))
    versions = sorted(versions)
    return versions[-1]


def build_new(bundles, _config, last_tag):
    click.echo(f"Working on: new ({_config['new']['branch']})")
    if last_tag is None:
        first = True
    else:
        first = False
    branch = _config["new"]["branch"]

    location = _config["new"]["location"]
    if location == "local":
        repo = existing_repo(_config["configuration"]["local"])
    elif location == "temp":
        repo = existing_repo(_config["configuration"]["temporary"]["location"])
    else:
        repo = None
        click.secho("Invalid location set on 'new'", fg="red")
        exit(1)

    ok = _config["new"]["checkout"]
    if ok:
        checkout(repo, branch, _config)

    ensure_branch = _config["new"]["ensure_branch"]
    if ensure_branch:
        if repo.head.is_detached:
            click.secho(
                "Current branch does not match required branch: Repo head in detached state",
                fg="red",
            )
            exit(1)
        if repo.active_branch.name != branch:
            click.secho(
                f"Current branch does not match required branch: {branch} != {repo.active_branch.name}",
                fg="red",
            )
            exit(1)

    bundle_path = Path(
        repo.working_dir, "bundles", _config["configuration"]["operator"]
    )
    if _config["chain"]["start"] == "new":
        tag = get_version_latest_tag(bundle_path)
    else:
        tag = next_version(last_tag)
        csv = Path(
            bundle_path,
            f"{tag.major}.{tag.minor}.{tag.patch}",
            "manifests",
            f"{_config['configuration']['operator']}.clusterserviceversion.yaml",
        )
        if not csv.exists():
            click.echo(f"Build {last_tag} to ensure the chain")
            release_prepare(_config, repo, True, last_tag)
    chain_data = work_on_tag(repo, tag, _config, bundles, first, label="new")
    return chain_data, tag


def get_semver(tag: git.TagReference, prefix=None):
    if prefix is None:
        name = tag.name
    else:
        name = tag.name.strip(prefix)

    return semver.VersionInfo.parse(str(name))


def load_config(config_file: Path, main_config_file: Dict):
    data = {}
    _build = build

    if "index" in main_config_file:
        if "configuration" in main_config_file["index"]:
            _build = merge(
                _build, {"configuration": main_config_file["index"]["configuration"]}
            )

        if "chain" in main_config_file["index"]:
            _build = merge(_build, {"chain": main_config_file["index"]["chain"]})

    if config_file.is_file():
        with open(config_file, "r") as f:
            data = toml.loads(f.read())

    output = merge(_build, data)

    return output


if "__main__" == __name__:
    cli_index(
        "/home/jimfitz/code/github.com/Boomatang/orc-dev-cli/samples/simple.toml",
        config.load_config(),
    )
