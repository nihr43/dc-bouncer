# dc-bouncer

Upgrade or bounce kubernetes/ceph hosts with node, ceph, deployment, and daemon readiness checks between reboots.

## implementation

This is made for Debian kubernetes hosts, with ceph deployed on kubernetes using [rook](https://rook.io/docs/rook/v1.9/ceph-storage.html).

The goal is to have an unattended process that will perform OS upgrades and reboot the entire cluster, while doing the appropriate kubernetes and ceph cluster health checks in-between actions.  The effect is that k8s nodes will be rebooted one at a time, and ceph will be given time to rebalance if needed.  It is assumed that applications running on the cluster will have appropriate replicasets and disruption budgets where necessary.  It is also assumed that the nodes are capable of rebooting within the configured rook and ceph failover grace-periods.  For rook, the mon timeout [defaults to 10 minutes](https://rook.io/docs/rook/v1.9/Storage-Configuration/Advanced/ceph-mon-health/#failing-over-a-monitor).  For ceph, the `mon osd down out interval` [defaults to 600 seconds](https://docs.ceph.com/en/quincy/rados/operations/monitoring-osd-pg/).

This is done using the [ansible_runner](https://ansible-runner.readthedocs.io/en/stable/index.html) library for upgrades and rebooting, and the kubernetes api for checking the status of k8s and ceph.  Since ceph is deployed on kubernetes using rook, its own basic health is available within the kubernetes api under the CephCluster crd.

It is expected that `~/.kube/config` is configured, and that some high-availability mechanism exists for the kubernetes api endpoint itself - as we will have rebooted the entire control plane when finished.

File `config.yml` specifies extra hosts to upgrade, as well as deployments to be health-checked between reboots.

```
---
extra_hosts:
 - 10.0.0.10
 - 10.0.0.11
```

## example

```
[nix-shell:~/git/dc-bouncer]$ python main.py --reboot
found k8s node x470d4u-zen-43c5a at 10.0.200.1
found k8s node 66e3b444-3349-46af-b56e-feb1cc0aee3c at 10.0.200.3
found k8s node x470d4u-zen-3700f at 10.0.200.2
found k8s node x10slhf-xeon-9c3ab at 10.0.200.4
found extra node 10.0.0.10
found extra node 10.0.0.11
x470d4u-zen-43c5a ready state is True
66e3b444-3349-46af-b56e-feb1cc0aee3c ready state is True
x470d4u-zen-3700f ready state is True
x10slhf-xeon-9c3ab ready state is True
ceph state is HEALTH_OK
ceph state is HEALTH_OK
ceph state is HEALTH_OK
46 deployments healthy
5 daemonsets healthy

PLAY [reboot] ******************************************************************

TASK [Gathering Facts] *********************************************************
ok: [10.0.200.1]

TASK [reboot] ******************************************************************
changed: [10.0.200.1]

PLAY RECAP *********************************************************************
10.0.200.1                 : ok=2    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
x470d4u-zen-43c5a ready state is Unknown
66e3b444-3349-46af-b56e-feb1cc0aee3c ready state is True
x10slhf-xeon-9c3ab ready state is True
x470d4u-zen-3700f ready state is True
x10slhf-xeon-9c3ab ready state is True
x470d4u-zen-3700f ready state is True
66e3b444-3349-46af-b56e-feb1cc0aee3c ready state is True
x470d4u-zen-43c5a ready state is True
ceph state is HEALTH_WARN
ceph state is HEALTH_WARN
ceph state is HEALTH_OK
ceph state is HEALTH_OK
ceph state is HEALTH_OK
rook-ceph-mds-home-a has unavailable replicas
rook-ceph-mds-home-a has unavailable replicas
rook-ceph-mds-home-a has unavailable replicas
argocd-redis has unavailable replicas
argocd-redis has unavailable replicas
domain-index has unavailable replicas
domain-index has unavailable replicas
domain-index has unavailable replicas
argocd-notifications-controller has unavailable replicas
argocd-notifications-controller has unavailable replicas
argocd-notifications-controller has unavailable replicas
argocd-applicationset-controller has unavailable replicas
argocd-server has unavailable replicas
argocd-server has unavailable replicas
argocd-repo-server has unavailable replicas
argocd-repo-server has unavailable replicas
46 deployments healthy
5 daemonsets healthy

PLAY [reboot] ******************************************************************

TASK [Gathering Facts] *********************************************************
ok: [10.0.200.2]

TASK [reboot] ******************************************************************
changed: [10.0.200.2]
...
```
