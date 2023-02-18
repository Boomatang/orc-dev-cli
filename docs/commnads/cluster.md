# Cluster
Commands related to interacting with OSD clusters.

## delete
For clusters that the current ocm user is the owner of, the `delete` command allows the cluster to be deleted.
This command requires the cluster name to be stated.

For safety when executing this command there is a prompt to confirm the choice. 
This prompt can be confirmed in the command call by passing the `-y/--yes` flag.
Example is `orc delete -y <name>`.

Example usage:
```shell
orc cluster delete <cluster>
```

## list
List cluster in the ocm account.
There are configuration options that should be set to allow to improve filters.

The following configurations can be set:
* **cluster.list.exclude.names_starts_with** : This is a list of prefix that is used to remove clusters from the list
* **cluster.list.exclude.states** : List of clusters states to be filtered.
* **clust.list.exclude.filter** : Set the default filtering 
* **cluster.list.highlight.name_starts_with** : Highlight rows for clusters which starts with prefix in list.
 

| Flag                 | Description                        | Type | Default | Options                       | Configurable |
|----------------------|------------------------------------|------|---------|-------------------------------|--------------|
| -e/--exclude-filters | Change filters for listing cluster | str  | all     | all, uuid, states, name, none | yes          |

Example:
```shell
$ orc cluster list
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
The password is copied to the clipboard for easy use.


| Flag         | Description                              | Type         | Default             | Configable |
|--------------|------------------------------------------|--------------|---------------------|------------|
| -c/--cluster | Name of cluster                          | str          | None                | yes        |

Example:
```shell
$ orc cluster login -c <cluster>

Cluster: <cluster>
Console: https://some.cluster.org
Console Login: https://some.cluster.org/user/password

Login Command:
oc login -u kubeadmin -p **---** --server https://api.at.some.cluster.org

User: kubeadmin
Password: **---**
```

## status
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
orc cluster status -c <cluster> -w -e state
```