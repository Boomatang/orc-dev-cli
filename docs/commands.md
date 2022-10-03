# Commands

## addon
The addon command displays a range of information taken from the RHMI CR and information about alerts.
Alerts are related to the addon and not the cluster.

A temporary kube config is used to log into the cluster for this command.
This means that multi clusters can have the addons check at the sametime while not affecting the user's login.

| Flag         | Description                              | Type         | Default             | Configable |
|--------------|------------------------------------------|--------------|---------------------|------------|
| -c/--cluster | Name of cluster                          | str          | None                | yes        |
| -w/--watch   | Keep refreshing the state of the cluster | Boolean      | False               | yes        |
| -d/--delay   | Delay between refreshing the state       | int          | 10                  | yes        |  

Example:
```shell
orc addon -c <cluster> -w 
```

## config
Creates the initial configuration file and opens the file using the systems default editor.
The command will never update or override any existing configurations.
Location of the configuration file is `/home/<user>/.config/orc/config.toml`

Example usage:
```shell
orc config
```

## delete
For clusters that the current ocm user is the owner of, the `delete` command allows the cluster to be deleted.
This command requires the cluster name to be stated.

For safety when executing this command there is a prompt to confirm the choice. 
This prompt can be confirmed in the command call by passing the `-y/--yes` flag.
Example is `orc delete -y <name>`.

Example usage:
```shell
orc delete <cluster>
```

## login
The `login` command will give login details for kubeadmin on a cluster.
For easy of use the login password is copied to the clip board for easy use later.
URL's for logging both by IDP and user/password.
If no IDP is configured on the cluster both URLs bring you to the user/password login.

The command output lists the following information.

* `Console` This is the console URL for the cluster.
If there is a IDP configured on the cluster this URL will redirect to the IDP login page if login is required.
* `Console Login` URL used to log in with kubeadmin if there is a cluster IDP configured.
* `oc login` The login command for login with the oc cli. 
The command does not auto login the user but gives a easy to copy login command.
* `user` Defaults to kubeadmin.
* `password` is the cluster password for the kubeadmin. 
This should not be shared and should only be accessible on dev clusters.


| Flag         | Description                              | Type         | Default             | Configable |
|--------------|------------------------------------------|--------------|---------------------|------------|
| -c/--cluster | Name of cluster                          | str          | None                | yes        |

Example:
```shell
$ orc osd -c <cluster>

Cluster: <cluster>
Console: https://some.cluster.org
Console Login: https://some.cluster.org/user/password

Login Command:
oc login -u kubeadmin -p **---** --server https://api.at.some.cluster.org

User: kubeadmin
Password: **---**

```

## osd
Get the current state of an openshift osd cluster.
The two state values that are returned is the cluster creation and health state.
These states can be used to check when a cluster will be become functional.

| Flag         | Description                              | Type         | Default             | Configable |
|--------------|------------------------------------------|--------------|---------------------|------------|
| -c/--cluster | Name of cluster                          | str          | None                | yes        |
| -w/--watch   | Keep refreshing the state of the cluster | Boolean      | False               | yes        |
| -d/--delay   | Delay between refreshing the state       | int          | 10                  | yes        |  
| -e/--exit    | Exit watch on matched state              | str (choice) | None (health/state) | no         |

Example:
```shell
orc osd -c <cluster> -w -e state
```

