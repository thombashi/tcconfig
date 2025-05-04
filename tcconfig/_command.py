"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import errno
import sys

import subprocrunner as spr

from ._common import normalize_tc_value
from ._const import Tc
from ._error import NetworkInterfaceNotFoundError
from ._logger import LogLevel, logger
from ._main import Main
from .parser._model import Filter
from .traffic_control import TrafficControl


class TcDelMain(Main):
    def run(self, is_delete_all: bool) -> int:
        return_code_list: list[int] = []

        for tc_target in self._fetch_tc_targets():
            tc: TrafficControl = self.__create_tc_obj(tc_target)
            if self._options.log_level == LogLevel.INFO:
                spr.set_log_level("ERROR")
            normalize_tc_value(tc)

            try:
                if is_delete_all:
                    return_code_list.append(0 if tc.delete_all_rules() is True else 1)
                else:
                    return_code_list.append(tc.delete_tc())
            except NetworkInterfaceNotFoundError as e:
                logger.error(e)
                return errno.EINVAL

            self._dump_history(tc, Tc.Command.TCDEL)

        return self._get_return_code(return_code_list)

    def __create_tc_obj(self, tc_target: str) -> TrafficControl:
        from simplesqlite.query import Where

        from .parser.shaping_rule import TcShapingRuleParser

        options = self._options

        if options.filter_id:
            ip_version: int = 6 if options.is_ipv6 else 4
            shaping_rule_parser = TcShapingRuleParser(
                device=tc_target,
                ip_version=ip_version,
                tc_command_output=options.tc_command_output,
                logger=logger,
            )
            shaping_rule_parser.parse()
            for record in Filter.select(where=Where(Tc.Param.FILTER_ID, options.filter_id)):
                dst_network: str = record.dst_network
                src_network: str = record.src_network
                dst_port: int = record.dst_port
                src_port: int = record.src_port
                break
            else:
                logger.error(
                    f"shaping rule not found associated with the id ({options.filter_id})."
                )
                sys.exit(1)
        else:
            dst_network = self._extract_dst_network()
            src_network = self._extract_src_network()
            dst_port = options.dst_port
            src_port = options.src_port

        return TrafficControl(
            tc_target,
            direction=options.direction,
            dst_network=dst_network,
            src_network=src_network,
            dst_port=dst_port,
            src_port=src_port,
            is_ipv6=options.is_ipv6,
            tc_command_output=options.tc_command_output,
        )
