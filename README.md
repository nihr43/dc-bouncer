# dc-bouncer

Safely upgrade the OS of kubernetes/ceph hosts, with cluster readiness checks between reboots.

## implementation

This is made for an environment where kubernetes and ceph are running on the same physical hosts, and ceph is deployed with [rook](https://rook.io/docs/rook/v1.9/ceph-storage.html).
The nodes are running debian, and kubernetes is installed seperately of apt packaging.

The goal is to have an unattended process that will perform OS upgrades and reboot the entire cluster, while doing the appropriate kubernetes and ceph cluster health checks in-between actions.  The effect is that k8s nodes will be rebooted one at a time, and ceph will be given time to rebalance if needed.  It is assumed that applications running on the cluster will have appropriate replicasets and disruption budgets where necessary.  It is also assumed that the nodes are capable of rebooting within the configured rook and ceph failover grace-periods.  For rook, the mon timeout [defaults to 10 minutes](https://rook.io/docs/rook/v1.9/Storage-Configuration/Advanced/ceph-mon-health/#failing-over-a-monitor).  For ceph, the `mon osd down out interval` [defaults to 600 seconds](https://docs.ceph.com/en/quincy/rados/operations/monitoring-osd-pg/).

This is done using the [ansible_runner](https://ansible-runner.readthedocs.io/en/stable/index.html) library for upgrades and rebooting, and the kubernetes api for checking the status of k8s and ceph.  Since ceph is deployed on kubernetes using rook, its own basic health is available within the kubernetes api under the CephCluster crd.

It is expected that `~/.kube/config` is configured, and that some high-availability mechanism exists for the kubernetes api endpoint itself - as we will have rebooted the entire control plane when finished.

## example

```
~/git/dc-bouncer$ ./main.py 
INFO:root:found k8s node x470d4u-zen-420c2 at 10.0.200.1
INFO:root:found k8s node x470d4u-zen-9679c at 10.0.200.3
INFO:root:found k8s node x7spahf-atom-6aef0 at 10.0.254.253
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:x470d4u-zen-9679c ready state is True
INFO:root:x7spahf-atom-6aef0 ready state is True
INFO:root:ceph state is HEALTH_OK

PLAY [all] *********************************************************************

TASK [Gathering Facts] *********************************************************
ok: [10.0.200.1]

TASK [apt update] **************************************************************
ok: [10.0.200.1]

TASK [apt upgrade] *************************************************************
changed: [10.0.200.1]

TASK [reboot] ******************************************************************
changed: [10.0.200.1]

TASK [apt autoremove --purge] **************************************************
ok: [10.0.200.1]

PLAY RECAP *********************************************************************
10.0.200.1                 : ok=5    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
INFO:root:x470d4u-zen-9679c ready state is True
INFO:root:x7spahf-atom-6aef0 ready state is True
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_OK

PLAY [all] *********************************************************************

TASK [Gathering Facts] *********************************************************
ok: [10.0.200.3]

TASK [apt update] **************************************************************
ok: [10.0.200.3]

TASK [apt upgrade] *************************************************************
changed: [10.0.200.3]

TASK [reboot] ******************************************************************
changed: [10.0.200.3]

TASK [apt autoremove --purge] **************************************************
ok: [10.0.200.3]

PLAY RECAP *********************************************************************
10.0.200.3                 : ok=5    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
INFO:root:x470d4u-zen-9679c ready state is Unknown
INFO:root:x7spahf-atom-6aef0 ready state is True
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:waiting
INFO:root:x7spahf-atom-6aef0 ready state is True
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:x470d4u-zen-9679c ready state is False
INFO:root:waiting
INFO:root:x7spahf-atom-6aef0 ready state is True
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:x470d4u-zen-9679c ready state is True
INFO:root:ceph state is HEALTH_OK

PLAY [all] *********************************************************************

TASK [Gathering Facts] *********************************************************
ok: [10.0.254.253]

TASK [apt update] **************************************************************
ok: [10.0.254.253]

TASK [apt upgrade] *************************************************************
changed: [10.0.254.253]

TASK [reboot] ******************************************************************
changed: [10.0.254.253]

TASK [apt autoremove --purge] **************************************************
ok: [10.0.254.253]

PLAY RECAP *********************************************************************
10.0.254.253               : ok=5    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
INFO:root:x470d4u-zen-9679c ready state is True
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:x7spahf-atom-6aef0 ready state is Unknown
INFO:root:waiting
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:x7spahf-atom-6aef0 ready state is Unknown
INFO:root:x470d4u-zen-9679c ready state is True
INFO:root:waiting
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:x470d4u-zen-9679c ready state is True
INFO:root:x7spahf-atom-6aef0 ready state is False
INFO:root:waiting
INFO:root:x470d4u-zen-420c2 ready state is True
INFO:root:x470d4u-zen-9679c ready state is True
INFO:root:x7spahf-atom-6aef0 ready state is True
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_WARN
INFO:root:waiting
INFO:root:ceph state is HEALTH_OK
```
