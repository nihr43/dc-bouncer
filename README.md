# dc-bouncer

Safely upgrade the OS of kubernetes/ceph hosts, with cluster readiness checks between reboots.

## implementation

This is made for an environment where kubernetes and ceph are running on the same physical hosts, and ceph is deployed with [rook](https://rook.io/docs/rook/v1.9/ceph-storage.html).
The nodes are running debian, and kubernetes is installed seperately of apt packaging.

The goal is to have an unattended process that will perform OS upgrades and reboot the entire cluster, while doing the appropriate kubernetes and ceph cluster health checks in-between actions.  The effect is that k8s nodes will be rebooted one at a time, and ceph will be given time to rebalance if needed.  It is assumed that applications running on the cluster will have appropriate replicasets and disruption budgets where necessary.

This is done using the [ansible_runner](https://ansible-runner.readthedocs.io/en/stable/index.html) library for upgrades and rebooting, and the kubernetes api for checking the status of k8s and ceph.  By accessing some ansible functionality from within python, we are able to do things not easily done with ansible alone, such as dynamic inventory handling - but we don't have to re-immplement things ansible already does well.
Since ceph is deployed on kubernetes using rook, its own basic health is available within the kubernetes api under the CephCluster crd.

It is expected that `~/.kube/config` is configured, and that some high-availability mechanism exists for the kubernetes api endpoint itself, as we will have rebooted the entire control plane when finished.
