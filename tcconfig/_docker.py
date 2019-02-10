# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, print_function, unicode_literals

import errno
import os
import re
import sys
from collections import namedtuple

import msgfy
import six
from docker import APIClient
from docker.errors import APIError, NotFound
from path import Path
from simplesqlite import OperationalError, connect_memdb
from simplesqlite.model import Integer, Model, Text
from simplesqlite.query import And, Where
from subprocrunner import SubprocessRunner

from ._common import is_execute_tc_command
from ._const import TcCommandOutput
from ._error import ContainerNotFoundError
from ._logger import logger


if six.PY2:
    PermissionError = OSError


ContainerInfo = namedtuple("ContainerInfo", "id name pid ipaddr image")


class IfIndex(Model):
    host = Text(not_null=True)
    ifindex = Integer(primary_key=True)
    ifname = Text(not_null=True)
    peer_ifindex = Integer(not_null=True, unique=True)


class DockerClient(object):
    @property
    def __netns_root_path(self):
        return Path("/var/run/netns")

    def __init__(self, tc_command_output=TcCommandOutput.NOT_SET):
        self.__client = APIClient(version="auto")
        self.__host_name = os.uname()[1]
        self.__tc_command_output = tc_command_output

        self.__con = connect_memdb()
        IfIndex.attach(self.__con)

    def exist_container(self, container):
        try:
            self.__verify_container(container)
            return True
        except ContainerNotFoundError:
            return False

    def verify_container(self, container, exit_on_exception=False):
        if not is_execute_tc_command(self.__tc_command_output):
            return

        try:
            self.__verify_container(container)
        except ContainerNotFoundError as e:
            if exit_on_exception:
                logger.error(msgfy.to_error_message(e))
                sys.exit(errno.EPERM)

            raise

    def extract_running_container_names(self):
        running_container_name_list = []

        for container in self.__get_containers():
            if container.get("State") != "running":
                continue

            running_container_name_list.append(container["Names"][0].lstrip("/"))

        return running_container_name_list

    def extract_container_info(self, container):
        try:
            container_map = self.__client.inspect_container(container=container)
        except APIError as e:
            logger.error(e)
            sys.exit(1)

        container_name = container_map["Name"].lstrip("/")
        container_state = container_map["State"]

        if not container_state["Running"]:
            logger.error("{} not running".format(container_name))
            return ContainerInfo(name=container_name)

        return ContainerInfo(
            id=container_map["Id"],
            name=container_name,
            pid=int(container_state["Pid"]),
            ipaddr=container_map["NetworkSettings"]["IPAddress"],
            image=container_map["Config"]["Image"],
        )

    def create_veth_table(self, container):
        try:
            self.__netns_root_path.makedirs_p()
        except PermissionError as e:
            logger.error(e)
            sys.exit(errno.EPERM)

        container_info = self.extract_container_info(container)
        logger.debug(
            "found container: name={}, pid={}".format(container_info.name, container_info.pid)
        )

        try:
            netns_path = self.__get_netns_path(container_info.name)

            if not os.path.lexists(netns_path):
                logger.debug("make symlink to {}".format(netns_path))

                try:
                    Path("/proc/{:d}/ns/net".format(container_info.pid)).symlink(netns_path)
                except PermissionError as e:
                    logger.error(e)
                    sys.exit(errno.EPERM)

            return_code = self.__create_ifindex_table(container_info.name)
            if return_code != 0:
                sys.exit(return_code)

            return return_code
        finally:
            netns_path.remove_p()

    def select_veth(self, container_name):
        for container_record in IfIndex.select(where=Where("host", container_name)):
            for veth_record in IfIndex.select(
                where=And(
                    [
                        Where("host", self.__host_name),
                        Where("ifindex", container_record.peer_ifindex),
                    ]
                )
            ):
                yield veth_record

    def fetch_veth_list(self, container_name):
        return [veth_record.ifname for veth_record in self.select_veth(container_name)]

    def __verify_container(self, container):
        if len(self.__get_containers()) == 0:
            raise ContainerNotFoundError()

        try:
            self.__client.inspect_container(container=container)
        except NotFound:
            raise ContainerNotFoundError(target=container)
        except APIError as e:
            logger.error(e)
            sys.exit(1)

    def __get_containers(self):
        try:
            return self.__client.containers()
        except APIError as e:
            logger.error(e)
            sys.exit(1)

    def __get_netns_path(self, container_name):
        return self.__netns_root_path / container_name

    def __create_ifindex_table(self, container_name):
        netns_path = self.__get_netns_path(container_name)

        try:
            netns_path.stat()
        except PermissionError as e:
            logger.error(e)
            return errno.EPERM

        IfIndex.create()

        proc = SubprocessRunner(
            "ip netns exec {ns} ip link show type veth".format(ns=container_name), dry_run=False
        )
        if proc.run() != 0:
            logger.error(proc.stderr)
            return proc.returncode

        veth_groups_regexp = re.compile("([0-9]+): ([a-z0-9]+)@([a-z0-9]+): ")
        peer_ifindex_prefix_regexp = re.compile("^if")

        try:
            for i, line in enumerate(proc.stdout.splitlines()):
                match = veth_groups_regexp.search(line)
                if not match:
                    continue

                logger.debug("parse veth @{} [{:02d}] {}".format(container_name, i, line))
                ifindex, ifname, peer_ifindex = match.groups()
                IfIndex.insert(
                    IfIndex(
                        host=container_name,
                        ifindex=int(ifindex),
                        ifname=ifname,
                        peer_ifindex=int(peer_ifindex_prefix_regexp.sub("", peer_ifindex)),
                    )
                )

            proc = SubprocessRunner("ip link show type veth", dry_run=False)
            if proc.run() != 0:
                logger.error(proc.stderr)
                return proc.returncode

            for line in proc.stdout.splitlines():
                logger.debug("parse veth @docker-host [{:02d}] {}".format(i, line))
                match = veth_groups_regexp.search(line)
                if not match:
                    continue

                ifindex, ifname, peer_ifindex = match.groups()
                try:
                    IfIndex.insert(
                        IfIndex(
                            host=self.__host_name,
                            ifindex=int(ifindex),
                            ifname=ifname,
                            peer_ifindex=int(peer_ifindex_prefix_regexp.sub("", peer_ifindex)),
                        )
                    )
                except OperationalError as e:
                    logger.error(msgfy.to_error_message(e))
        finally:
            IfIndex.commit()

            try:
                netns_path.remove_p()
            except PermissionError as e:
                logger.error(msgfy.to_error_message(e))
                return errno.EPERM

        return 0
