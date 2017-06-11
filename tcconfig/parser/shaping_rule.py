# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import copy

import subprocrunner
import typepy
from typepy.type import Integer

from .._common import run_tc_show
from .._const import (
    Tc,
    TrafficDirection,
)
from .._iptables import IptablesMangleController
from .._logger import logger
from ._class import TcClassParser
from ._filter import TcFilterParser
from ._qdisc import TcQdiscParser


class TcShapingRuleParser(object):
    @property
    def device(self):
        return self.__device

    def __init__(self, device, ip_version, logger):
        self.__device = device
        self.__ip_version = ip_version
        self.__logger = logger

        self.__iptables_ctrl = IptablesMangleController(True, ip_version)

    def get_tc_parameter(self):
        return {
            self.device: {
                TrafficDirection.OUTGOING: self.__get_shaping_rule(
                    self.device),
                TrafficDirection.INCOMING: self.__get_shaping_rule(
                    self.__get_ifb_from_device()),
            },
        }

    def get_outgoing_tc_filter(self):
        return self.__parse_tc_filter(self.device)

    def get_incoming_tc_filter(self):
        ifb_device = self.__get_ifb_from_device()
        if ifb_device is None:
            return []

        return self.__parse_tc_filter(ifb_device)

    def __get_ifb_from_device(self):
        filter_runner = subprocrunner.SubprocessRunner(
            "tc filter show dev {:s} root".format(self.device), dry_run=False)
        filter_runner.run()

        return TcFilterParser(self.__ip_version).parse_incoming_device(
            filter_runner.stdout)

    def __get_filter_key(self, filter_param):
        network_format = Tc.Param.DST_NETWORK + "={:s}"
        protocol_format = Tc.Param.PROTOCOL + "={:s}"
        key_item_list = []

        if Tc.Param.HANDLE in filter_param:
            handle = filter_param.get(Tc.Param.HANDLE)
            Integer(handle).validate()
            handle = int(handle)

            for mangle in self.__iptables_ctrl.parse():
                if mangle.mark_id != handle:
                    continue

                key_item_list.append(network_format.format(mangle.destination))
                if typepy.is_not_null_string(mangle.source):
                    key_item_list.append("{:s}={:s}".format(
                        Tc.Param.SRC_NETWORK, mangle.source))
                key_item_list.append(protocol_format.format(mangle.protocol))

                break
            else:
                raise ValueError("mangle mark not found: {}".format(mangle))
        else:
            network = filter_param.get(Tc.Param.DST_NETWORK)
            if typepy.is_not_null_string(network):
                key_item_list.append(network_format.format(network))

            src_port = filter_param.get(Tc.Param.SRC_PORT)
            if Integer(src_port).is_type():
                port_format = Tc.Param.SRC_PORT + "={:d}"
                key_item_list.append(port_format.format(src_port))

            dst_port = filter_param.get(Tc.Param.DST_PORT)
            if Integer(dst_port).is_type():
                port_format = Tc.Param.DST_PORT + "={:d}"
                key_item_list.append(port_format.format(dst_port))

            protocol = filter_param.get(Tc.Param.PROTOCOL)
            if typepy.is_not_null_string(protocol):
                key_item_list.append(protocol_format.format(protocol))

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
        param_list = list(TcFilterParser(self.__ip_version).parse_filter(
            run_tc_show(Tc.Subcommand.FILTER, device)))
        logger.debug("tc filter parse result: {}".format(param_list))

        return param_list

    def __parse_tc_class(self, device):
        param_list = list(TcClassParser().parse(
            run_tc_show(Tc.Subcommand.CLASS, device)))
        logger.debug("tc class parse result: {}".format(param_list))

        return param_list
