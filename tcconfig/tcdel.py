#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import print_function

import errno
import sys

import logbook
import subprocrunner

from ._argparse_wrapper import ArgparseWrapper
from ._common import (
    check_tc_command_installation,
    initialize,
    is_execute_tc_command,
    normalize_tc_value,
    verify_network_interface,
    write_tc_script,
)
from ._const import (
    VERSION,
    Tc,
    TcCommandOutput,
)
from ._error import NetworkInterfaceNotFoundError
from ._logger import (
    LOG_FORMAT_STRING,
    logger,
    set_logger,
)
from .traffic_control import TrafficControl


logbook.StderrHandler(
    level=logbook.DEBUG, format_string=LOG_FORMAT_STRING).push_application()


def parse_option():
    parser = ArgparseWrapper(VERSION)

    group = parser.parser.add_argument_group("Traffic Control")
    group.add_argument(
        "-d", "--device", required=True,
        help="network device name (e.g. eth0)")
    group.add_argument(
        "-a", "--all", dest="is_delete_all", action="store_true",
        help="delete all of the shaping rules.")
    group.add_argument(
        "--id", dest="filter_id",
        help="""
        delete a shaping rule which has a specific id.
        you can get an id (filter_id) by tcshow command output.
        e.g. "filter_id": "800::801"
        """)

    parser.add_routing_group()

    return parser.parser.parse_args()


def create_tc_obj(options):
    from .parser.shaping_rule import TcShapingRuleParser
    from simplesqlite.sqlquery import SqlQuery

    if options.filter_id:
        ip_version = 6 if options.is_ipv6 else 4
        shaping_rule_parser = TcShapingRuleParser(
            device=options.device, ip_version=ip_version, logger=logger)
        shaping_rule_parser.parse()
        result = shaping_rule_parser.con.select_as_dict(
            table_name=Tc.Subcommand.FILTER,
            column_list=[
                Tc.Param.SRC_NETWORK, Tc.Param.DST_NETWORK,
                Tc.Param.SRC_PORT, Tc.Param.DST_PORT],
            where=SqlQuery.make_where(Tc.Param.FILTER_ID, options.filter_id))
        if not result:
            logger.error(
                "shaping rule not found associated with the id ({}).".format(
                    options.filter_id))
            sys.exit(1)

        filter_param = result[0]
        dst_network = filter_param.get(Tc.Param.DST_NETWORK)
        src_network = filter_param.get(Tc.Param.SRC_NETWORK)
        dst_port = filter_param.get(Tc.Param.DST_PORT)
        src_port = filter_param.get(Tc.Param.SRC_PORT)
    else:
        dst_network = options.dst_network
        src_network = options.src_network
        dst_port = options.dst_port
        src_port = options.src_port

    return TrafficControl(
        options.device, direction=options.direction,
        dst_network=dst_network, src_network=src_network,
        dst_port=dst_port, src_port=src_port,
        is_ipv6=options.is_ipv6)


def main():
    options = parse_option()

    initialize(options)

    if is_execute_tc_command(options.tc_command_output):
        check_tc_command_installation()
    else:
        subprocrunner.SubprocessRunner.default_is_dry_run = True
        set_logger(False)

    try:
        verify_network_interface(options.device)
    except NetworkInterfaceNotFoundError as e:
        logger.error(e)
        return errno.EINVAL

    subprocrunner.SubprocessRunner.clear_history()
    tc = create_tc_obj(options)
    if options.log_level == logbook.INFO:
        subprocrunner.set_log_level(logbook.ERROR)
    normalize_tc_value(tc)

    return_code = 0
    if options.is_delete_all:
        return_code = tc.delete_all_tc()
    else:
        return_code = tc.delete_tc()

    command_history = "\n".join(tc.get_command_history())

    if options.tc_command_output == TcCommandOutput.STDOUT:
        print(command_history)
        return return_code
    elif options.tc_command_output == TcCommandOutput.SCRIPT:
        set_logger(True)
        write_tc_script(
            Tc.Command.TCDEL, command_history, filename_suffix=options.device)
        return return_code

    logger.debug("command history\n{}".format(command_history))

    return return_code


if __name__ == '__main__':
    sys.exit(main())
