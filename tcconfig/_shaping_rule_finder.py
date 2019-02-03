# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import

from simplesqlite.query import And, Where

from ._const import Tc, TcSubCommand, TrafficDirection
from ._network import is_anywhere_network
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
            device=self.__tc.device,
            ip_version=self.__tc.ip_version,
            tc_command_output=self.__tc.tc_command_output,
            logger=self.__logger,
        )

    def clear(self):
        self.__shaping_rule_parser.clear()

    def find_qdisc_handle(self, parent):
        return self._parser.con.fetch_value(
            select=Tc.Param.HANDLE,
            table_name=TcSubCommand.QDISC.value,
            where=Where(Tc.Param.PARENT, parent),
        )

    def find_filter_param(self):
        import simplesqlite

        where_list = self.__get_filter_conditions()
        where_query = And(where_list)
        table_name = TcSubCommand.FILTER.value
        self.__logger.debug("find filter param: table={}, where={}".format(table_name, where_query))

        try:
            result = self._parser.con.select_as_dict(
                columns=[Tc.Param.FILTER_ID, Tc.Param.PRIORITY, Tc.Param.PROTOCOL],
                table_name=table_name,
                where=where_query,
            )
        except simplesqlite.TableNotFoundError:
            return None

        if not result:
            self.__logger.debug(
                "find filter param: emptry result (table={}, where={})".format(
                    table_name, where_query
                )
            )
            return None

        param = result[0]
        self.__logger.debug(
            "find filter param: result={}, table={}, where={}".format(
                param, table_name, where_query
            )
        )

        return param

    def find_parent(self):
        where_list = self.__get_filter_conditions()
        table_name = TcSubCommand.FILTER.value
        parent = self._parser.con.fetch_value(
            select=Tc.Param.FLOW_ID, table_name=table_name, where=And(where_list)
        )

        self.__logger.debug(
            "find parent: result={}, table={}, where={}".format(parent, table_name, where_list)
        )

        return parent

    def is_exist_rule(self):
        return self.find_parent() is not None

    def is_any_filter(self):
        num_records = self._parser.con.fetch_num_records(table_name=TcSubCommand.FILTER.value)

        return num_records and num_records > 0

    def is_empty_filter_condition(self):
        from typepy import is_null_string

        return all(
            [
                is_anywhere_network(self.__tc.dst_network, self.__tc.ip_version),
                is_anywhere_network(self.__tc.src_network, self.__tc.ip_version),
                is_null_string(self.__tc.dst_port),
                is_null_string(self.__tc.src_port),
            ]
        )

    def get_parsed_device(self):
        if self.__tc.direction == TrafficDirection.OUTGOING:
            device = self._parser.device
        elif self.__tc.direction == TrafficDirection.INCOMING:
            device = self._parser.ifb_device

        return device

    def get_filter_string(self):
        return ", ".join(
            [where.to_query() for where in self.__get_filter_conditions() if where.value]
        )

    def __get_filter_conditions(self):
        if self.__tc.direction == TrafficDirection.OUTGOING:
            device = self._parser.device
        elif self.__tc.direction == TrafficDirection.INCOMING:
            device = self._parser.ifb_device

        return [
            Where(Tc.Param.DEVICE, device),
            Where(Tc.Param.PROTOCOL, self.__tc.protocol),
            Where(Tc.Param.DST_NETWORK, self.__tc.dst_network),
            Where(Tc.Param.SRC_NETWORK, self.__tc.src_network),
            Where(Tc.Param.DST_PORT, self.__tc.dst_port),
            Where(Tc.Param.SRC_PORT, self.__tc.src_port),
        ]
