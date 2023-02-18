# RHOAM
Commands for interacting with the RHOAM installation.

## delete
Remove RHOAM CR from cluster.

| Flag         | Description                              | Type    | Default       | Configable |
|--------------|------------------------------------------|---------|---------------|------------|
| -c/--cluster | Name of cluster                          | str     | None          | yes        |
| -p/--prefix  | Set prefix for RHOAM CR namespace        | str     | redhat-rhoam  | yes        |

Example:
```shell
orc rhoam delete -c <cluster> -p <prefix>
```


## index
Builds and pushes operator, bundle and index images for installing of RHOAM via OLM.
The build tool is podman and a podman socket is required to be running as user not root.
It has not been tested on system that has both podman and docker installed. 
Some side effects may happen in this case.

As this functionality makes use of scripts and tools used by the integreatly operator if you can follow the [Manual approach](https://integreatly-operator.readthedocs.io/en/latest/installation_guides/olm_installation/#manual-approach) outlined in the OLM installation section of integreatly documentation then this command should work fine for you.

To enable the podman socket on start up use the following command.
```shell
systemctl --user enable podman.socket
```

To start the socket without the need to restart use the following.
```shell
systemctl --user start podman.socket
```

To check that the socket is running using. The socket should be active and listening.
```shell
systemctl --user status podman.socket
```
A configuration file is required for building the chain.
The format of the configuration file is in toml.
You can read more about toml at [toml.io](https://toml.io)

| Flag        | Description                                            | Type    | Default | Configable |
|-------------|--------------------------------------------------------|---------|---------|------------|
| -c/--config | Path to toml configuration file for building the chain | Path    | None    | yes        |
| --template  | Prints a detailed list of all configuration options    | output  |         |            |

In the main configuration file a default can be set under a `[index]` section.
Some general configuration expected in the input toml file can be configured in the main configuration file under `[index.configuration]` and `[index.chain]`.

Below is a sample configuration file which will build from the current released version to a feature branch.
The first time this configuration runs, it will build the operator, bundle and index for the three versions, current release (current), master branch (latest) and feature branch (new).
After the initial run it will only build the operator image for the feature branch (new).

```toml
[configuration]
local = "path/to/integreatly-operator"
org = "<quay.io org>"

[chain]
start = "current"
pre_release = "123"
operator = "reuse"
bundle = "reuse"
index = "reuse"

[new]
branch = "demo"
operator = "build"
```
Please read the output from `orc rhoam index --template` to get a better understanding of what the different field do.

## status
The addon command displays a range of information taken from the RHMI CR and information about alerts.
Alerts are related to the addon and not the cluster.

A temporary kube config is used to log into the cluster for this command.
This means that multi clusters can have the addons check at the sametime while not affecting the user's login.

| Flag         | Description                              | Type    | Default       | Configable |
|--------------|------------------------------------------|---------|---------------|------------|
| -c/--cluster | Name of cluster                          | str     | None          | yes        |
| -w/--watch   | Keep refreshing the state of the cluster | Boolean | False         | yes        |
| -d/--delay   | Delay between refreshing the state       | int     | 10            | yes        |  
| -p/--prefix  | Set prefix for RHOAM CR namespace        | str     | redhat-rhoam  | yes        |

Example:
```shell
orc rhoam status -c <cluster> -w 
```