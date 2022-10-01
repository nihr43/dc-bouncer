#!/usr/bin/python3

import ansible.runner
import ansible.playbook
import ansible.inventory
from ansible import callbacks
from ansible import utils
import json

from kubernetes import client, config, watch


def k8s_ok(api) -> bool:
    '''
    check readiness of kubernetes
    '''
    node_list = api.list_node()

    for node in node_list.items:
        print("%s\t%s" % (node.metadata.name, node.metadata.labels))

    if any node.metadata.readiness = false: # this is phony
        return false
    else:
        return true


def ceph_ok(api) -> bool:
    '''
    check readiness of cephcluster crd in kubernetes
    '''
    api = client.CustomObjectsApi() #perhaps

    # CephCluster crd defined at https://github.com/rook/rook/blob/master/deploy/examples/crds.yaml line 841
    resource = api.get_namespaced_custom_object(
        group="ceph.rook.io",
        version="v1",
        name="rook-ceph", # or cephcluster?
        namespace="rook-ceph",
        plural="cephclusters",
    )
    print("Resource details:")
    pprint(resource)

    if "HEALTH_OK" in resource: # this is phony
        return true
    else
        return false

def upgrade_node(inventory):
    '''
    upgrade and reboot a given node
    '''
    run = ansible.runner.Runner(
        module_name = 'apt_upgrade.yml',
        timeout = 5,
        inventory = inventory,
        subset = 'all'
    )

    out = pm.run()
    print json.dumps(out, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    '''
    we expect some HA cluster-wide endpoint to exist, in order to continue to
    use the k8s api while waiting for a node to reboot
    '''
    k8s_endpoint = ''
    hosts = []

    config.load_kube_config()
    k8s_v1 = client.CoreV1Api()

    for n in hosts:
        ephemeral_inventory = ansible.inventory.Inventory(hosts)
        upgrade_node(ephemeral_inventory)
        wait_until:
            k8s_ok(k8s_v1)
        wait_until:
            ceph_ok(k8s_v1)
