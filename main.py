#!/usr/bin/python3

import json
import time
import os

def k8s_ok(client, logging) -> bool:
    '''
    check readiness of kubernetes
    '''
    api = client.CoreV1Api()
    node_list = api.list_node()

    not_ready = []

    for node in node_list.items:
        for i in node.status.conditions:
            if i.type == 'Ready':        # these dont appear to be more easily addresable
                node_status = i.status
                if node_status != 'True':
                    not_ready.append(node.metadata.name)
        logging.info(node.metadata.name + ' Ready is ' + node_status)

    if len(not_ready) == 0:
        return True
    else:
        return False


def ceph_ok(client, logging) -> bool:
    '''
    check readiness of cephcluster crd in kubernetes
    '''
    api = client.CustomObjectsApi()

    # CephCluster crd defined at https://github.com/rook/rook/blob/master/deploy/examples/crds.yaml line 841
    resource = api.get_namespaced_custom_object(
        group="ceph.rook.io",
        version="v1",
        name="rook-ceph", # or cephcluster?
        namespace="rook-ceph",
        plural="cephclusters",
    )

    health = resource.get('status').get('ceph').get('health')
    logging.info('ceph state is ' + health)

    if health == "HEALTH_OK":
        return True
    else:
        return False


def upgrade_node(ansible_runner, host):
    '''
    upgrade and reboot a given node
    '''
    ansible_runner.run(
        private_data_dir='./',
        inventory = host,
        playbook = 'apt_upgrade.yml'
    )


if __name__ == '__main__':
    def privileged_main():
        from kubernetes import client, config, watch
        import ansible_runner

        import logging

        hosts = ['10.0.200.1','10.0.200.3','10.0.254.253']

        logging.basicConfig(level=logging.INFO)
        config.load_kube_config()

        notready = []

        if k8s_ok(client, logging) == False:
            notready.append('k8s')
        if ceph_ok(client, logging) == False:
            notready.append('ceph')
        if len(notready) != 0:
            exit()

        for n in hosts:
            upgrade_node(ansible_runner, n)
            os.remove("./inventory/hosts")
            for i in range(20): # wait up to 10 minutes
                time.sleep(30)
                if k8s_ok(client, logging) == False:
                    notready.append('k8s')
                if ceph_ok(client, logging) == False:
                    notready.append('ceph')
                if len(notready) == 0:
                    break

    privileged_main()
