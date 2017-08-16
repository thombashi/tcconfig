#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import print_function

from simplesqlite.sqlquery import SqlQuery

from ._const import (
    Tc,
    TrafficDirection,
)
from .parser.shaping_rule import TcShapingRuleParser


class TcShapingRuleFinder(object):

    def __init__(self, logger, tc):
        self.__logger = logger
        self.__tc = tc
        self.__parser = TcShapingRuleParser(
            device=self.__tc.device, ip_version=self.__tc.ip_version,
            logger=self.__logger)

    def find_handle(self, parent):
        return self.__parser.con.get_value(
            select=Tc.Param.HANDLE,
            table_name=Tc.Subcommand.QDISC,
            where=SqlQuery.make_where(Tc.Param.PARENT, parent))

    def find_parent(self):
        self.__parser.parse()

        if self.__tc.direction == TrafficDirection.OUTGOING:
            device = self.__parser.device
        elif self.__tc.direction == TrafficDirection.INCOMING:
            device = self.__parser.ifb_device

        where_list = [
            SqlQuery.make_where(Tc.Param.DEVICE, device),
            SqlQuery.make_where(Tc.Param.PROTOCOL, self.__tc.protocol),
            SqlQuery.make_where(Tc.Param.DST_NETWORK, self.__tc.dst_network),
            SqlQuery.make_where(Tc.Param.SRC_NETWORK, self.__tc.src_network),
            SqlQuery.make_where(Tc.Param.DST_PORT, self.__tc.dst_port),
            SqlQuery.make_where(Tc.Param.SRC_PORT, self.__tc.src_port),
        ]

        return self.__parser.con.get_value(
            select=Tc.Param.FLOW_ID,
            table_name=Tc.Subcommand.FILTER,
            where=" AND ".join(where_list))

    def is_exist_rule(self):
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
            current_filter_list = self.__parser.get_outgoing_tc_filter()
        elif self.__tc.direction == TrafficDirection.INCOMING:
            current_filter_list = self.__parser.get_incoming_tc_filter()

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
