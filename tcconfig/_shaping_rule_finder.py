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
        parent = self.__parser.con.get_value(
            select=Tc.Param.FLOW_ID,
            table_name=Tc.Subcommand.FILTER,
            where=" AND ".join(where_list))

        self.__logger.debug(
            "find parent: result={}, where{}".format(parent, where_list))

        return parent

    def is_exist_rule(self):
        return self.find_parent() is not None
