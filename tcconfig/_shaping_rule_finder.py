#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import print_function

from ._const import (
    Tc,
    TrafficDirection,
)
from ._logger import logger
from .parser.shaping_rule import TcShapingRuleParser


class TcShapingRuleFinder(object):
    @property
    def tc(self):
        return self.__tc

    def __init__(self, device, tc):
        self.__device = device
        self.__tc = tc

    def is_exist_rule(self):
        parser = TcShapingRuleParser(
            self.__device, self.tc.ip_version, logger)

        key_param_list = (
            Tc.Param.DST_NETWORK, Tc.Param.SRC_NETWORK,
            Tc.Param.DST_PORT, Tc.Param.SRC_NETWORK,
        )

        search_filter = {
            Tc.Param.DST_NETWORK: self.tc.dst_network,
            Tc.Param.SRC_NETWORK: self.tc.src_network,
            Tc.Param.DST_PORT: self.tc.dst_port,
            Tc.Param.SRC_NETWORK: self.tc.src_port,
        }

        if self.tc.direction == TrafficDirection.OUTGOING:
            current_filter_list = parser.get_outgoing_tc_filter()
        elif self.tc.direction == TrafficDirection.INCOMING:
            current_filter_list = parser.get_incoming_tc_filter()

        logger.debug(
            "is_exist_rule: direction={}, search-filter={}, "
            "current-filters={}".format(
                self.tc.direction, search_filter, current_filter_list))

        for cuurent_filter in current_filter_list:
            if all([
                    cuurent_filter.get(
                        key_param) == search_filter.get(key_param)
                    for key_param in key_param_list
            ]):
                logger.debug("existing shaping rule found: {}".format(
                    cuurent_filter))
                return True

        return False
