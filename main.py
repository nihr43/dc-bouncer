#!/usr/bin/python3

import time


def get_nodes(client, logging) -> list:
    '''
    get list of strings of node ips
    '''

    api = client.CoreV1Api()
    node_list = api.list_node()
    ip_list = []

    for node in node_list.items:
        for i in node.status.addresses:
            if i.type == 'InternalIP':
                ip_list.append(i.address)
                logging.info('found k8s node ' + node.metadata.name + ' at ' + i.address)

    return ip_list


def k8s_ok(client, logging) -> bool:
    '''
    check readiness of each kubernetes node
    '''
    api = client.CoreV1Api()
    node_list = api.list_node()

    not_ready = []

    for node in node_list.items:
        for i in node.status.conditions:
            if i.type == 'Ready':        # these dont appear to be more easily addressable # noqa
                node_status = i.status
                if node_status != 'True':
                    not_ready.append(node.metadata.name)
        logging.info(node.metadata.name + ' ready state is ' + node_status)

    if len(not_ready) == 0:
        return True
    else:
        return False


def ceph_ok(client, logging) -> bool:
    '''
    check readiness of cephcluster crd in kubernetes
    '''
    api = client.CustomObjectsApi()

    # CephCluster crd defined at https://github.com/rook/rook/blob/master/deploy/examples/crds.yaml line 841 # noqa
    resource = api.get_namespaced_custom_object(
        group="ceph.rook.io",
        version="v1",
        name="rook-ceph",
        namespace="rook-ceph",
        plural="cephclusters",
    )

    health = resource.get('status').get('ceph').get('health')
    logging.info('ceph state is ' + health)

    if health == "HEALTH_OK":
        return True
    else:
        return False


def upgrade_node(ansible_runner, host, os):
    '''
    upgrade and reboot a given node
    '''
    # ansible-runner apppears to leave behind a non-writable artifact:
    if os.path.isfile("./inventory/hosts"):
        os.remove("./inventory/hosts")

    ansible_runner.run(
        private_data_dir='./',
        inventory=host,
        playbook='apt_upgrade.yml'
    )


def wait_until(fn, logging):
    '''
    given a function, attempt a number of retries
    '''
    count = 100
    for i in range(count):
        if fn():
            break
        if i == count-1:
            logging.info('timed out waiting')
            exit(1)
        logging.info('waiting')
        time.sleep(10)


if __name__ == '__main__':
    def privileged_main():
        from kubernetes import client, config
        import ansible_runner

        import logging
        import os
        from functools import partial

        logging.basicConfig(level=logging.INFO)
        config.load_kube_config()

        hosts = get_nodes(client, logging)
        k8s_ok_partial = partial(k8s_ok, client, logging)
        ceph_ok_partial = partial(ceph_ok, client, logging)

        wait_until(k8s_ok_partial, logging)
        wait_until(ceph_ok_partial, logging)

        for n in hosts:
            upgrade_node(ansible_runner, n, os)
            wait_until(k8s_ok_partial, logging)
            wait_until(ceph_ok_partial, logging)

    privileged_main()
