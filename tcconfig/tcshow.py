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
import logbook
import subprocrunner
from subprocrunner import SubprocessRunner

import tcconfig
from .parser import TcFilterParser
from .parser import TcQdiscParser
from ._argparse_wrapper import ArgparseWrapper
from ._common import verify_network_interface
from ._error import NetworkInterfaceNotFoundError
from ._iptables import IptablesMangleController
from ._traffic_direction import TrafficDirection


handler = logbook.StderrHandler()
handler.push_application()


def parse_option():
    parser = ArgparseWrapper(tcconfig.VERSION)

    group = parser.parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", action="append", required=True,
        help="network device name (e.g. eth0)")

    return parser.parser.parse_args()


class TcParamParser(object):

    @property
    def device(self):
        return self.__device

    def __init__(self, device):
        self.__device = device
        self.__qdisc_param = self.__parse_qdisc(device)

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

        if dataproperty.is_not_empty_string(filter_param.get("network")):
            key_item_list.append(
                network_format.format(filter_param.get("network")))

        if dataproperty.is_integer(filter_param.get("port")):
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

        filter_table = {}
        for filter_param in filter_parser.parse_filter(filter_show_runner.stdout):
            filter_key = self.__get_filter_key(filter_param)
            filter_table[filter_key] = {}
            if filter_param.get("flowid") == self.__qdisc_param.get("parent"):
                work_qdisc_param = dict(self.__qdisc_param)
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
    logger = logbook.Logger("tcshow")
    logger.level = options.log_level

    subprocrunner.logger.level = options.log_level
    if options.quiet:
        subprocrunner.logger.disable()
    else:
        subprocrunner.logger.enable()

    subprocrunner.Which("tc").verify()

    tc_param = {}
    for device in options.device:
        try:
            verify_network_interface(device)
        except NetworkInterfaceNotFoundError as e:
            logger.debug(str(e))
            continue

        tc_param.update(TcParamParser(device).get_tc_parameter())

    six.print_(json.dumps(tc_param, indent=4))

    return 0


if __name__ == '__main__':
    sys.exit(main())
