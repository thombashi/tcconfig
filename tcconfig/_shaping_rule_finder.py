"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


from simplesqlite.query import And, Where

from ._const import Tc, TrafficDirection
from ._network import is_anywhere_network
from .parser._model import Filter, Qdisc
from .parser.shaping_rule import TcShapingRuleParser


class TcShapingRuleFinder:
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
        for qdisc in Qdisc.select(where=Where(Tc.Param.PARENT, parent)):
            return qdisc.handle

        return None

    def find_filter_param(self):
        where_query = And(self.__get_filter_conditions())
        table_name = Filter.get_table_name()
        self.__logger.debug("find filter param: table={}, where={}".format(table_name, where_query))

        for record in Filter.select(where=where_query):
            return record.as_dict()

        self.__logger.debug(
            "find filter param: empty result (table={}, where={})".format(table_name, where_query)
        )

        return None

    def find_parent(self):
        for record in Filter.select(where=And(self.__get_filter_conditions())):
            return record.flowid

        return None

    def is_exist_rule(self):
        return self.find_parent() is not None

    def is_any_filter(self):
        return Filter.fetch_num_records() > 0

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
