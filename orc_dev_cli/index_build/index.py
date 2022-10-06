import logging
import os
import shutil
import subprocess  # nosec
import tempfile
from pathlib import Path
from pprint import pprint

import git
import semver
import toml
import yaml
from podman import PodmanClient

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


def build_container(image, uri, container_file, dockerfile=None, buildargs=None):
    log.info(f"Building container image: {image}")
    log.debug(f"Container File: {container_file}")
    with PodmanClient(base_url=uri) as client:
        if dockerfile is None:
            client.images.build(
                path=container_file.parent,
                dockerfile=container_file.name,
                tag=image,
                buildargs=buildargs,
            )
        else:
            log.debug(f"Building with dockerfile: {dockerfile}")
            client.images.build(
                path=container_file,
                dockerfile=dockerfile,
                tag=image,
                buildargs=buildargs,
            )
        client.images.prune()


def push_container(image, uri):
    log.info(f"Pushing container image: {image}")
    with PodmanClient(base_url=uri) as client:
        client.images.push(image)


def build_index(image, bundles):
    log.info(f"Building index image: {image}")
    log.debug(f"Bundles in index: {bundles}")
    b = []
    for bundle in bundles:
        b.append("--bundles")
        b.append(bundle)

    s = ["opm", "index", "add"]
    e = ["--build-tool", "podman", "--tag", image]
    cmd = s + b + e
    log.debug(f"opm command: {cmd}")
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

    if "pre_release" in config["chain"]:
        tag = semver.VersionInfo(
            major=tag.major,
            minor=tag.minor,
            patch=tag.patch,
            prerelease=config["chain"]["pre_release"],
        )
    else:
        tag = semver.VersionInfo(major=tag.major, minor=tag.minor, patch=tag.patch)

    data = {
        "label": label,
        "operator": f'{Path(image_site, org, operator)}:{config["configuration"]["tag_marker"]}{tag}',
        "bundle": f"{Path(image_site, org, bundle)}:{tag}",
        "index": f"{Path(image_site, org, index)}:{tag}",
    }
    bundles.append(data["bundle"])

    if csv.exists():
        service_affecting = get_service_affecting(csv)
    else:
        service_affecting = True
    data["service_affecting"] = service_affecting

    release_prepare(config, repo, service_affecting, tag)

    if first:
        remove_replaces(csv)
    data["bundles"] = bundles.copy()
    build_container(data["operator"], uri, Path(repo.working_dir, "Dockerfile"))
    push_container(data["operator"], uri)

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

    log.warning("No validation is happening on the bundles")
    build_index(data["index"], bundles)
    push_container(data["index"], uri)

    if label != "new":
        repo.git.restore("*")

    return data


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

    chain = {}
    bundles = []
    last_tag = None
    for tag in data["tags"]:
        log.info(f"Working on: {tag}")
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

        log.info(f"Working on: latest ({config['latest']['branch']})")

        if last_tag is None:
            first = True
        else:
            first = False

        branch = config["latest"]["branch"]
        checkout(repo, branch, config)
        tag = next_version(last_tag)
        chain_data = work_on_tag(repo, tag, config, bundles, first, label="latest")
        chain[tag] = chain_data
        last_tag = tag

    if "new" in data["other"]:
        log.info(f"Working on: new ({config['new']['branch']})")

        if last_tag is None:
            first = True
        else:
            first = False
        branch = config["new"]["branch"]
        local_repo = existing_repo(config["configuration"]["local"])
        checkout(local_repo, branch, config)
        tag = next_version(last_tag)

        csv = Path(
            repo.working_dir,
            "bundles",
            config["configuration"]["operator"],
            f"{tag.major}.{tag.minor}.{tag.patch}",
            "manifests",
            f"{config['configuration']['operator']}.clusterserviceversion.yaml",
        )
        if not csv.exists():
            log.info(f"Build {last_tag} to ensure the chain")
            release_prepare(config, local_repo, True, last_tag)

        chain_data = work_on_tag(local_repo, tag, config, bundles, first, label="new")
        chain[tag] = chain_data

    pprint(chain)


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
