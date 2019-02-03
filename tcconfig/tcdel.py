#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, print_function

import errno
import sys

import logbook
import subprocrunner as spr

from .__version__ import __version__
from ._argparse_wrapper import ArgparseWrapper
from ._capabilities import check_execution_authority
from ._common import initialize_cli, is_execute_tc_command, normalize_tc_value
from ._const import Tc, TcSubCommand
from ._error import NetworkInterfaceNotFoundError
from ._logger import logger, set_logger
from ._main import Main
from ._network import verify_network_interface
from .traffic_control import TrafficControl


def parse_option():
    parser = ArgparseWrapper(__version__)

    group = parser.parser.add_argument_group("Traffic Control")
    if set(["-d", "--device"]).intersection(set(sys.argv)):
        # deprecated: remain for backward compatibility
        group.add_argument("-d", "--device", required=True, help="network device name (e.g. eth0)")
    else:
        group.add_argument("device", help="network device name (e.g. eth0)")
    group.add_argument(
        "-a",
        "--all",
        dest="is_delete_all",
        action="store_true",
        help="delete all of the shaping rules.",
    )
    group.add_argument(
        "--id",
        dest="filter_id",
        help="""delete a shaping rule which has a specific id. you can get an id (filter_id)
        by tcshow command output.
        e.g. "filter_id": "800::801"
        """,
    )

    parser.add_routing_group()
    parser.add_docker_group()

    return parser.parser.parse_args()


class TcDelMain(Main):
    def run(self, is_delete_all):
        return_code_list = []

        for tc_target in self._fetch_tc_targets():
            tc = self.__create_tc_obj(tc_target)
            if self._options.log_level == logbook.INFO:
                spr.set_log_level(logbook.ERROR)
            normalize_tc_value(tc)

            try:
                if is_delete_all:
                    return_code_list.append(tc.delete_all_tc())
                else:
                    return_code_list.append(tc.delete_tc())
            except NetworkInterfaceNotFoundError as e:
                logger.error(e)
                return errno.EINVAL

            self._dump_history(tc, Tc.Command.TCDEL)

        return self._get_return_code(return_code_list)

    def __create_tc_obj(self, tc_target):
        from .parser.shaping_rule import TcShapingRuleParser
        from simplesqlite.query import Where

        options = self._options

        if options.filter_id:
            ip_version = 6 if options.is_ipv6 else 4
            shaping_rule_parser = TcShapingRuleParser(
                device=tc_target,
                ip_version=ip_version,
                tc_command_output=options.tc_command_output,
                logger=logger,
            )
            shaping_rule_parser.parse()
            result = shaping_rule_parser.con.select_as_dict(
                table_name=TcSubCommand.FILTER.value,
                columns=[
                    Tc.Param.SRC_NETWORK,
                    Tc.Param.DST_NETWORK,
                    Tc.Param.SRC_PORT,
                    Tc.Param.DST_PORT,
                ],
                where=Where(Tc.Param.FILTER_ID, options.filter_id),
            )
            if not result:
                logger.error(
                    "shaping rule not found associated with the id ({}).".format(options.filter_id)
                )
                sys.exit(1)

            filter_param = result[0]
            dst_network = filter_param.get(Tc.Param.DST_NETWORK)
            src_network = filter_param.get(Tc.Param.SRC_NETWORK)
            dst_port = filter_param.get(Tc.Param.DST_PORT)
            src_port = filter_param.get(Tc.Param.SRC_PORT)
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


def main():
    options = parse_option()

    initialize_cli(options)

    if is_execute_tc_command(options.tc_command_output):
        check_execution_authority("tc")

        if not options.use_docker:
            try:
                verify_network_interface(options.device, options.tc_command_output)
            except NetworkInterfaceNotFoundError as e:
                logger.error(e)
                return errno.EINVAL

        is_delete_all = options.is_delete_all
    else:
        spr.SubprocessRunner.default_is_dry_run = True
        is_delete_all = True
        set_logger(False)

    spr.SubprocessRunner.clear_history()

    return TcDelMain(options).run(is_delete_all)


if __name__ == "__main__":
    sys.exit(main())
