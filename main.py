#!/usr/bin/python3

import time


def get_nodes(client, logging) -> list:
    """
    get list of strings of node ips
    """

    api = client.CoreV1Api()
    node_list = api.list_node()
    ip_list = []

    for node in node_list.items:
        for i in node.status.addresses:
            if i.type == "InternalIP":
                ip_list.append(i.address)
                logging.info(
                    "found k8s node {} at {}".format(node.metadata.name, i.address)
                )

    return ip_list


def k8s_ok(client, logging) -> bool:
    """
    check readiness of each kubernetes node
    """
    api = client.CoreV1Api()

    try:
        node_list = api.list_node()
        not_ready = []

        for node in node_list.items:
            for i in node.status.conditions:
                if (
                    i.type == "Ready"
                ):  # these dont appear to be more easily addressable # noqa
                    node_status = i.status
                    if node_status != "True":
                        not_ready.append(node.metadata.name)
            logging.info(node.metadata.name + " ready state is " + node_status)

    except ConnectionRefusedError:
        pass

    if len(not_ready) == 0:
        return True
    else:
        return False


def ceph_ok(client, logging) -> bool:
    """
    check readiness of cephcluster crd in kubernetes
    """
    api = client.CustomObjectsApi()

    # CephCluster crd defined at https://github.com/rook/rook/blob/master/deploy/examples/crds.yaml line 841 # noqa
    resource = api.get_namespaced_custom_object(
        group="ceph.rook.io",
        version="v1",
        name="rook-ceph",
        namespace="rook-ceph",
        plural="cephclusters",
    )

    health = resource.get("status").get("ceph").get("health")
    logging.info("ceph state is " + health)

    if health == "HEALTH_OK":
        return True
    else:
        return False


def run_playbook(ansible_runner, host, os, playbook):
    """
    run a given playbook
    """
    # ansible-runner apppears to leave behind a non-writable artifact:
    if os.path.isfile("./inventory/hosts"):
        os.remove("./inventory/hosts")

    runner = ansible_runner.run(
        private_data_dir="./", inventory=host, playbook=playbook
    )

    if runner.status != "successful":
        exit(1)


def wait_until(fn, logging):
    """
    given a function that returns True or False, attempt a number of retries
    """
    count = 100
    for i in range(count):
        if fn():
            break
        if i == count - 1:
            logging.info("timed out waiting")
            exit(1)
        logging.info("waiting")
        time.sleep(10)


def get_snowflakes(path, logging):
    with open(path, "r") as file:
        lines = [line.strip() for line in file]
    return lines


if __name__ == "__main__":

    def privileged_main():
        from kubernetes import client, config
        import ansible_runner
        import argparse

        import logging
        import os
        from functools import partial

        logging.basicConfig(level=logging.INFO)
        config.load_kube_config()

        parser = argparse.ArgumentParser()
        parser.add_argument("--reboot", action="store_true")
        args = parser.parse_args()

        hosts = get_nodes(client, logging)
        k8s_ok_partial = partial(k8s_ok, client, logging)
        ceph_ok_partial = partial(ceph_ok, client, logging)

        wait_until(k8s_ok_partial, logging)
        wait_until(ceph_ok_partial, logging)

        for n in hosts:
            if args.reboot:
                run_playbook(ansible_runner, n, os, "reboot.yml")
            else:
                run_playbook(ansible_runner, n, os, "apt_upgrade.yml")
            wait_until(k8s_ok_partial, logging)
            wait_until(ceph_ok_partial, logging)

        logging.info("---------- continuing to miscellaneous hosts ----------")
        for n in get_snowflakes("misc_hosts", logging):
            if args.reboot:
                run_playbook(ansible_runner, n, os, "reboot.yml")
            else:
                run_playbook(ansible_runner, n, os, "apt_upgrade.yml")

    privileged_main()
