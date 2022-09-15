# Welcome to orc-dev-cli

Orc-dev-cli gives developers a CLI tool called orc.
Orc is used to interact with openshift osd clusters and the openshift addon RHOAM.

As this is a dev tool kude-admin access to the clusters is expected.

## Installation
Easiest way to install orc is by using pip
```shell
pip install orc-dev-cli
```

## Basic Commands

* `orc addon`   Get the current state of an installed addon instances
* `orc config`  Open configuration file
* `orc delete`  Delete cluster.
* `orc login`   Get cluster kubeadmin login details.
* `orc osd`     Get basic state information on osd cluster

## Shell Completion

### Bash

1. Create temporary bash script.
2. Add `_ORC_COMPLETE=bash_source orc > ~/.orc-complete.bash`.
3. Run script.
4. Source the newly created `~/.orc-complete.bash` in `~/.bashrc` as follows `. ~/.orc-complete.bash`.
5. Restart the shell to complete.
