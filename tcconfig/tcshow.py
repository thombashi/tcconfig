#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import json
import sys
import six

import dataproperty
from dataproperty import IntegerType
import logbook
import subprocrunner
from subprocrunner import SubprocessRunner

from .parser import (
    TcFilterParser,
    TcQdiscParser,
)
from ._argparse_wrapper import ArgparseWrapper
from ._common import verify_network_interface
from ._const import VERSION
from ._error import NetworkInterfaceNotFoundError
from ._iptables import IptablesMangleController
from ._logger import (
    LOG_FORMAT_STRING,
    logger,
    set_log_level,
)
from ._traffic_direction import TrafficDirection


logbook.StderrHandler(
    level=logbook.DEBUG, format_string=LOG_FORMAT_STRING).push_application()


def parse_option():
    parser = ArgparseWrapper(VERSION)

    group = parser.parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", action="append", required=True,
        help="network device name (e.g. eth0)")

    return parser.parser.parse_args()


class TcParamParser(object):

    @property
    def device(self):
        return self.__device

    def __init__(self, device, logger):
        self.__device = device
        self.__logger = logger

    def get_tc_parameter(self):
        return {
            self.device: {
                TrafficDirection.OUTGOING: self.__get_filter(self.device),
                TrafficDirection.INCOMING: self.__get_filter(
                    self.__get_ifb_from_device()),
            },
        }

    def __get_ifb_from_device(self):
        filter_parser = TcFilterParser()
        command = "tc filter show dev {:s} root".format(self.device)
        filter_runner = SubprocessRunner(command)
        filter_runner.run()

        return filter_parser.parse_incoming_device(filter_runner.stdout)

    def __get_filter_key(self, filter_param):
        network_format = "network={:s}"
        port_format = "port={:d}"
        key_item_list = []

        if "handle" in filter_param:
            handle = filter_param.get("handle")

            IntegerType(handle).validate()

            handle = int(handle)
            for mangle in IptablesMangleController.parse():
                if mangle.mark_id != handle:
                    continue

                key_item_list.append(network_format.format(mangle.destination))
                if dataproperty.is_not_empty_string(mangle.source):
                    key_item_list.append("source={:s}".format(mangle.source))
                key_item_list.append("protocol={}".format(mangle.protocol))

                break
            else:
                raise ValueError("mangle mark not found: {}".format(mangle))
        else:
            if dataproperty.is_not_empty_string(filter_param.get("network")):
                key_item_list.append(
                    network_format.format(filter_param.get("network")))

            if IntegerType(filter_param.get("port")).is_type():
                key_item_list.append(
                    port_format.format(filter_param.get("port")))

        return ", ".join(key_item_list)

    def __get_filter(self, device):
        if dataproperty.is_empty_string(device):
            return {}

        # parse filter ---
        filter_parser = TcFilterParser()
        command = "tc filter show dev {:s}".format(device)
        filter_show_runner = SubprocessRunner(command)
        filter_show_runner.run()

        qdisc_param = self.__parse_qdisc(device)

        filter_table = {}
        for filter_param in filter_parser.parse_filter(filter_show_runner.stdout):
            filter_key = self.__get_filter_key(filter_param)
            filter_table[filter_key] = {}
            if qdisc_param.get("parent") in (
                    filter_param.get("flowid"), filter_param.get("classid")):
                work_qdisc_param = dict(qdisc_param)
                del work_qdisc_param["parent"]
                filter_table[filter_key] = work_qdisc_param

        return filter_table

    @staticmethod
    def __parse_qdisc(device):
        qdisc_parser = TcQdiscParser()
        command = "tc qdisc show dev {:s}".format(device)
        qdisk_show_runner = SubprocessRunner(command)
        qdisk_show_runner.run()

        return qdisc_parser.parse(qdisk_show_runner.stdout)


def main():
    options = parse_option()

    set_log_level(options.log_level)

    subprocrunner.Which("tc").verify()

    tc_param = {}
    for device in options.device:
        try:
            verify_network_interface(device)
        except NetworkInterfaceNotFoundError as e:
            logger.debug(str(e))
            continue

        tc_param.update(TcParamParser(device, logger).get_tc_parameter())

    six.print_(json.dumps(tc_param, indent=4))

    return 0


if __name__ == '__main__':
    sys.exit(main())
