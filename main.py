import time
import os
import argparse
import yaml
from typing import Dict, List

import ansible_runner  # type: ignore
from kubernetes import client, config  # type: ignore
from functools import partial


def get_nodes() -> list:
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
                print("found k8s node {} at {}".format(node.metadata.name, i.address))

    return ip_list


def k8s_ok() -> bool:
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
            print(node.metadata.name + " ready state is " + node_status)

    except ConnectionRefusedError:
        pass

    if len(not_ready) == 0:
        return True
    else:
        return False


def ceph_ok() -> bool:
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
    print("ceph state is " + health)

    if health == "HEALTH_OK":
        return True
    else:
        return False


def run_playbook(host: str, playbook: str) -> None:
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
        raise RuntimeError("playbook {} failed on {}".format(playbook, host))


def wait_until(fn: partial[bool], retry: int, success: int) -> None:
    """
    Given a function that returns True or False, attempt (retry) iterations for (success) successes.
    This is needed because ceph will not always immediately report unhealthy when a node is pulled.
    Example: wait_until(fn, 100, 3) will require 3 successes within 100 retries.
    """
    retry -= 1
    if retry == 0:
        raise TimeoutError("timed out waiting")

    time.sleep(5)

    if fn():
        success -= 1
    if success != 0:
        wait_until(fn, retry, success)

    return


def get_config(path: str) -> Dict[str, List[str]]:
    with open(path, "r") as file:
        yam = yaml.safe_load(file)
    return yam


def deployments_ok() -> bool:
    apps_v1 = client.AppsV1Api()

    deployments = apps_v1.list_deployment_for_all_namespaces()
    for d in deployments.items:
        try:
            assert d.status.unavailable_replicas is None
        except AssertionError:
            print(f"{d.metadata.name} has unavailable replicas")
            return False

    print(f"{len(deployments.items)} deployments healthy")
    return True


def daemonsets_ok() -> bool:
    apps_v1 = client.AppsV1Api()

    daemonsets = apps_v1.list_daemon_set_for_all_namespaces()
    for d in daemonsets.items:
        try:
            assert d.status.number_unavailable is None
        except AssertionError:
            print(f"{d.metadata.name} has unavailable replicas")
            return False

    print(f"{len(daemonsets.items)} daemonsets healthy")
    return True


if __name__ == "__main__":
    config.load_kube_config()
    cfg = get_config("config.yml")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reboot", action="store_true", help="Reboot only without upgrade"
    )
    args = parser.parse_args()

    k8s_hosts = get_nodes()
    extra_hosts = cfg.get("extra_hosts")

    if extra_hosts is not None:
        for h in extra_hosts:
            print(f"found extra node {h}")
        hosts = k8s_hosts + extra_hosts
    else:
        hosts = k8s_hosts

    k8s_ok_partial = partial(k8s_ok)
    ceph_ok_partial = partial(ceph_ok)
    deployments_ok_partial = partial(deployments_ok)
    daemonsets_ok_partial = partial(daemonsets_ok)

    wait_until(k8s_ok_partial, 120, 1)
    wait_until(ceph_ok_partial, 120, 3)
    wait_until(deployments_ok_partial, 120, 1)
    wait_until(daemonsets_ok_partial, 120, 1)

    for n in hosts:
        if args.reboot:
            run_playbook(n, "reboot.yml")
        else:
            run_playbook(n, "apt_upgrade.yml")
        wait_until(k8s_ok_partial, 120, 1)
        wait_until(ceph_ok_partial, 120, 3)
        wait_until(deployments_ok_partial, 120, 1)
        wait_until(daemonsets_ok_partial, 120, 1)
