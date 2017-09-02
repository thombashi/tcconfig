#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import print_function

from simplesqlite.sqlquery import SqlQuery

from ._common import is_anywhere_network
from ._const import (
    Tc,
    TrafficDirection,
)
from .parser.shaping_rule import TcShapingRuleParser


class TcShapingRuleFinder(object):

    @property
    def _parser(self):
        self.__shaping_rule_parser.parse()

        return self.__shaping_rule_parser

    def __init__(self, logger, tc):
        self.__logger = logger
        self.__tc = tc
        self.__shaping_rule_parser = TcShapingRuleParser(
            device=self.__tc.device, ip_version=self.__tc.ip_version,
            logger=self.__logger)

    def clear(self):
        self.__shaping_rule_parser.clear()

    def find_qdisc_handle(self, parent):
        return self._parser.con.get_value(
            select=Tc.Param.HANDLE,
            table_name=Tc.Subcommand.QDISC,
            where=SqlQuery.make_where(Tc.Param.PARENT, parent))

    def find_filter_param(self):
        import simplesqlite

        where_list = self.__get_filter_where_condition_list()
        table_name = Tc.Subcommand.FILTER

        try:
            result = self._parser.con.select_as_dict(
                column_list=[
                    Tc.Param.FILTER_ID, Tc.Param.PRIORITY, Tc.Param.PROTOCOL],
                table_name=table_name,
                where=" AND ".join(where_list))
        except simplesqlite.TableNotFoundError:
            return None

        if not result:
            return None

        param = result[0]
        self.__logger.debug(
            "find filter param: result={}, table={}, where={}".format(
                param, table_name, where_list))

        return param

    def find_parent(self):
        where_list = self.__get_filter_where_condition_list()
        table_name = Tc.Subcommand.FILTER
        parent = self._parser.con.get_value(
            select=Tc.Param.FLOW_ID,
            table_name=table_name,
            where=" AND ".join(where_list))

        self.__logger.debug(
            "find parent: result={}, table={}, where={}".format(
                parent, table_name, where_list))

        return parent

    def is_exist_rule(self):
        return self.find_parent() is not None

    def is_any_filter(self):
        num_records = self._parser.con.get_num_records(
            table_name=Tc.Subcommand.FILTER)

        return num_records and num_records > 0

    def is_empty_filter_condition(self):
        from typepy import is_empty_string

        return all([
            is_anywhere_network(self.__tc.dst_network, self.__tc.ip_version),
            is_anywhere_network(self.__tc.src_network, self.__tc.ip_version),
            is_empty_string(self.__tc.dst_port),
            is_empty_string(self.__tc.src_port),
        ])

    def get_parsed_device(self):
        if self.__tc.direction == TrafficDirection.OUTGOING:
            device = self._parser.device
        elif self.__tc.direction == TrafficDirection.INCOMING:
            device = self._parser.ifb_device

        return device

    def __get_filter_where_condition_list(self):
        if self.__tc.direction == TrafficDirection.OUTGOING:
            device = self._parser.device
        elif self.__tc.direction == TrafficDirection.INCOMING:
            device = self._parser.ifb_device

        return [
            SqlQuery.make_where(Tc.Param.DEVICE, device),
            SqlQuery.make_where(Tc.Param.PROTOCOL, self.__tc.protocol),
            SqlQuery.make_where(Tc.Param.DST_NETWORK, self.__tc.dst_network),
            SqlQuery.make_where(Tc.Param.SRC_NETWORK, self.__tc.src_network),
            SqlQuery.make_where(Tc.Param.DST_PORT, self.__tc.dst_port),
            SqlQuery.make_where(Tc.Param.SRC_PORT, self.__tc.src_port),
        ]
