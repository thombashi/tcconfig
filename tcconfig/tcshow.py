#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import errno
import json
import sys

import logbook
import subprocrunner

from ._argparse_wrapper import ArgparseWrapper
from ._common import (
    verify_network_interface,
    write_tc_script,
)
from ._const import (
    VERSION,
    TcCommand,
    TcCommandOutput,
)
from ._error import NetworkInterfaceNotFoundError
from ._logger import (
    LOG_FORMAT_STRING,
    logger,
    set_log_level,
)
from .parser.shaping_rule import TcShapingRuleParser


logbook.StderrHandler(
    level=logbook.DEBUG, format_string=LOG_FORMAT_STRING).push_application()


def parse_option():
    parser = ArgparseWrapper(VERSION)

    group = parser.parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", action="append", required=True,
        help="network device name (e.g. eth0)")
    group.add_argument(
        "--ipv6", dest="ip_version", action="store_const",
        const=6, default=4,
        help="""
        Display IPv6 shaping rules.
        Defaults to show IPv4 shaping rules.
        """)

    return parser.parser.parse_args()


def main():
    options = parse_option()

    set_log_level(options.log_level)

    try:
        subprocrunner.Which("tc").verify()
    except subprocrunner.CommandNotFoundError as e:
        logger.error(e)
        return errno.ENOENT

    subprocrunner.SubprocessRunner.is_save_history = True
    if options.tc_command_output != TcCommandOutput.NOT_SET:
        subprocrunner.SubprocessRunner.default_is_dry_run = True

    tc_param = {}
    for device in options.device:
        try:
            verify_network_interface(device)
        except NetworkInterfaceNotFoundError as e:
            logger.debug(str(e))
            continue

        tc_param.update(TcShapingRuleParser(device, options.ip_version,
                                            logger).get_tc_parameter())

    command_history = "\n".join(subprocrunner.SubprocessRunner.get_history())

    if options.tc_command_output == TcCommandOutput.STDOUT:
        print(command_history)
        return 0

    if options.tc_command_output == TcCommandOutput.SCRIPT:
        write_tc_script(
            TcCommand.TCSHOW,
            command_history,
            filename_suffix="-".join(options.device))
        return 0

    logger.debug("command history\n{}".format(command_history))
    print(json.dumps(tc_param, indent=4))

    return 0


if __name__ == '__main__':
    sys.exit(main())
