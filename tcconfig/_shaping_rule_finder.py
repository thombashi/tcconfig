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
from .parser.shaping_rule import TcShapingRuleParser


class TcShapingRuleFinder(object):

    def __init__(self, logger, tc):
        self.__logger = logger
        self.__tc = tc

    def is_exist_rule(self):
        parser = TcShapingRuleParser(
            device=self.__tc.device, ip_version=self.__tc.ip_version,
            logger=self.__logger)

        key_param_list = (
            Tc.Param.DST_NETWORK, Tc.Param.SRC_NETWORK,
            Tc.Param.DST_PORT, Tc.Param.SRC_NETWORK,
        )

        search_filter = {
            Tc.Param.DST_NETWORK: self.__tc.dst_network,
            Tc.Param.SRC_NETWORK: self.__tc.src_network,
            Tc.Param.DST_PORT: self.__tc.dst_port,
            Tc.Param.SRC_NETWORK: self.__tc.src_port,
        }

        if self.__tc.direction == TrafficDirection.OUTGOING:
            current_filter_list = parser.get_outgoing_tc_filter()
        elif self.__tc.direction == TrafficDirection.INCOMING:
            current_filter_list = parser.get_incoming_tc_filter()

        self.__logger.debug(
            "is_exist_rule: direction={}, search-filter={}, "
            "current-filters={}".format(
                self.__tc.direction, search_filter, current_filter_list))

        for cuurent_filter in current_filter_list:
            if all([
                    cuurent_filter.get(
                        key_param) == search_filter.get(key_param)
                    for key_param in key_param_list
            ]):
                self.__logger.debug("existing shaping rule found: {}".format(
                    cuurent_filter))
                return True

        return False
