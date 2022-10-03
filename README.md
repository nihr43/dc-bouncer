# dc-bouncer

Safely upgrade the OS of kubernetes/ceph hosts, with cluster readiness checks between reboots.

## implementation

This is made for an environment where kubernetes and ceph are running on the same physical hosts, and ceph is deployed with rook.
The nodes are running debian, and kubernetes is installed/managed seperately of any apt packaging.

The goal is to have an unattended process that will perform OS upgrades and reboot the entire cluster, while doing the appropriate kubernetes and ceph cluster health checks in-between actions.  The effect is that ceph will be given time to rebalance if needed.

This is done using the ansible client library for upgrades and rebooting, and the kubernetes api for checking the status of k8s and ceph.
Since ceph is deployed on kubernetes using rook, its own basic health is available within the kubernetes api under the CephCluster crd.

It is expected that `~/.kube/config` is configured, and that some high-availability mechanism exists for the kubernetes endpoint itself, as we will have rebooted the entire control plane.
