#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import copy
import json
import sys

import logbook
import six
from subprocrunner import SubprocessRunner
import subprocrunner
import typepy
from typepy.type import Integer

from ._argparse_wrapper import ArgparseWrapper
from ._common import (
    verify_network_interface,
    run_tc_show,
)
from ._const import (
    VERSION,
    Tc,
)
from ._error import NetworkInterfaceNotFoundError
from ._iptables import IptablesMangleController
from ._logger import (
    LOG_FORMAT_STRING,
    logger,
    set_log_level,
)
from ._traffic_direction import TrafficDirection
from .parser import (
    TcFilterParser,
    TcQdiscParser,
    TcClassParser,
)


logbook.StderrHandler(
    level=logbook.DEBUG, format_string=LOG_FORMAT_STRING).push_application()


def parse_option():
    parser = ArgparseWrapper(VERSION)

    group = parser.parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", action="append", required=True,
        help="network device name (e.g. eth0)")

    return parser.parser.parse_args()


class TcShapingRuleParser(object):

    @property
    def device(self):
        return self.__device

    def __init__(self, device, logger):
        self.__device = device
        self.__logger = logger

    def get_tc_parameter(self):
        return {
            self.device: {
                TrafficDirection.OUTGOING: self.__get_shaping_rule(
                    self.device),
                TrafficDirection.INCOMING: self.__get_shaping_rule(
                    self.__get_ifb_from_device()),
            },
        }

    def __get_ifb_from_device(self):
        filter_runner = SubprocessRunner(
            "tc filter show dev {:s} root".format(self.device))
        filter_runner.run()

        return TcFilterParser().parse_incoming_device(filter_runner.stdout)

    def __get_filter_key(self, filter_param):
        network_format = "network={:s}"
        port_format = "port={:d}"
        key_item_list = []

        if Tc.Param.HANDLE in filter_param:
            handle = filter_param.get(Tc.Param.HANDLE)
            Integer(handle).validate()
            handle = int(handle)

            for mangle in IptablesMangleController.parse():
                if mangle.mark_id != handle:
                    continue

                key_item_list.append(network_format.format(mangle.destination))
                if typepy.is_not_null_string(mangle.source):
                    key_item_list.append("source={:s}".format(mangle.source))
                key_item_list.append("protocol={}".format(mangle.protocol))

                break
            else:
                raise ValueError("mangle mark not found: {}".format(mangle))
        else:
            network = filter_param.get(Tc.Param.NETWORK)
            if typepy.is_not_null_string(network):
                key_item_list.append(network_format.format(network))

            port = filter_param.get(Tc.Param.PORT)
            if Integer(port).is_type():
                key_item_list.append(port_format.format(port))

        return ", ".join(key_item_list)

    def __get_shaping_rule(self, device):
        if typepy.is_null_string(device):
            return {}

        class_param_list = self.__parse_tc_class(device)
        filter_param_list = self.__parse_tc_filter(device)
        qdisc_param_list = self.__parse_tc_qdisc(device)

        shaping_rule_mapping = {}

        for filter_param in filter_param_list:
            logger.debug(
                "{:s} param: {}".format(Tc.Subcommand.FILTER, filter_param))
            shaping_rule = {}

            filter_key = self.__get_filter_key(filter_param)
            if typepy.is_null_string(filter_key):
                logger.debug("empty filter key: {}".format(filter_param))
                continue

            for qdisc_param in qdisc_param_list:
                logger.debug(
                    "{:s} param: {}".format(Tc.Subcommand.QDISC, qdisc_param))

                if qdisc_param.get(Tc.Param.PARENT) not in (
                        filter_param.get(Tc.Param.FLOW_ID),
                        filter_param.get(Tc.Param.CLASS_ID)):
                    continue

                work_qdisc_param = copy.deepcopy(qdisc_param)
                del work_qdisc_param[Tc.Param.PARENT]
                shaping_rule.update(work_qdisc_param)

            for class_param in class_param_list:
                logger.debug(
                    "{:s} param: {}".format(Tc.Subcommand.CLASS, class_param))

                if class_param.get(Tc.Param.CLASS_ID) not in (
                        filter_param.get(Tc.Param.FLOW_ID),
                        filter_param.get(Tc.Param.CLASS_ID)):
                    continue

                work_class_param = copy.deepcopy(class_param)
                del work_class_param[Tc.Param.CLASS_ID]
                shaping_rule.update(work_class_param)

            if not shaping_rule:
                continue

            logger.debug(
                "rule found: {} {}".format(filter_key, shaping_rule))

            shaping_rule_mapping[filter_key] = shaping_rule

        return shaping_rule_mapping

    def __parse_tc_qdisc(self, device):
        try:
            param_list = list(TcQdiscParser().parse(
                run_tc_show(Tc.Subcommand.QDISC, device)))
        except ValueError:
            return []

        logger.debug("tc qdisc parse result: {}".format(param_list))

        return param_list

    def __parse_tc_filter(self, device):
        param_list = list(TcFilterParser().parse_filter(
            run_tc_show(Tc.Subcommand.FILTER, device)))
        logger.debug("tc filter parse result: {}".format(param_list))

        return param_list

    def __parse_tc_class(self, device):
        param_list = list(TcClassParser().parse(
            run_tc_show(Tc.Subcommand.CLASS, device)))
        logger.debug("tc class parse result: {}".format(param_list))

        return param_list


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

        tc_param.update(TcShapingRuleParser(device, logger).get_tc_parameter())

    six.print_(json.dumps(tc_param, indent=4))

    return 0


if __name__ == '__main__':
    sys.exit(main())
