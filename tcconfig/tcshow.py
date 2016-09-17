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


def _get_ifb_from_device(device):
    filter_parser = TcFilterParser()
    command = "tc filter show dev {:s} root".format(device)
    filter_runner = SubprocessRunner(command)
    filter_runner.run()

    return filter_parser.parse_incoming_device(filter_runner.stdout)


def _get_filter(device):
    if dataproperty.is_empty_string(device):
        return {}

    qdisc_parser = TcQdiscParser()
    filter_parser = TcFilterParser()

    # parse qdisc ---
    command = "tc qdisc show dev {:s}".format(device)
    qdisk_show_runner = SubprocessRunner(command)
    qdisk_show_runner.run()
    qdisc_param = qdisc_parser.parse(qdisk_show_runner.stdout)

    # parse filter ---
    command = "tc filter show dev {:s}".format(device)
    filter_show_runner = SubprocessRunner(command)
    filter_show_runner.run()

    filter_table = {}
    for filter_param in filter_parser.parse_filter(filter_show_runner.stdout):
        key_item_list = []

        if dataproperty.is_not_empty_string(filter_param.get("network")):
            key_item_list.append("network=" + filter_param.get("network"))

        if dataproperty.is_integer(filter_param.get("port")):
            key_item_list.append(
                "port={:d}".format(filter_param.get("port")))

        filter_key = ", ".join(key_item_list)
        filter_table[filter_key] = {}
        if filter_param.get("flowid") == qdisc_param.get("parent"):
            work_qdisc_param = dict(qdisc_param)
            del work_qdisc_param["parent"]
            filter_table[filter_key] = work_qdisc_param

    return filter_table


def get_tc_parameter(device):
    return {
        device: {
            TrafficDirection.OUTGOING: _get_filter(device),
            TrafficDirection.INCOMING: _get_filter(
                _get_ifb_from_device(device)),
        },
    }


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

        tc_param.update(get_tc_parameter(device))

    six.print_(json.dumps(tc_param, indent=4))

    return 0


if __name__ == '__main__':
    sys.exit(main())
