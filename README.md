# dc-bouncer

Safely upgrade the OS of kubernetes/ceph hosts, with cluster readiness checks between reboots.

## implementation

This is made for an environment where kubernetes and ceph are running on the same physical hosts, and ceph is deployed with rook.
The nodes are running debian, and kubernetes is installed/managed seperately of any apt packaging.

The goal is to have an unattended process that will perform OS upgrades and reboot the entire datacenter, while doing the appropriate kuberetes and ceph cluster health checks in-between actions.

This is done using the ansible client library for upgrades and rebooting, and the kubernetes api for checking the status of k8s and ceph.
Since ceph is deployed on kubernetes using rook, its own basic health is available within the kubernetes api under the CephCluster crd.

No other health checks are planned; in this environment it is assumed everything else is "ok" as long as the compute and storage is "ok".
