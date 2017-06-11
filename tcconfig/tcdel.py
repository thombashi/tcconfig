#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
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
    is_execute_tc_command,
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
    set_logger,
    set_log_level,
)
from .traffic_control import TrafficControl


logbook.StderrHandler(
    level=logbook.DEBUG, format_string=LOG_FORMAT_STRING).push_application()


def parse_option():
    parser = ArgparseWrapper(VERSION)

    group = parser.parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", required=True,
        help="network device name (e.g. eth0)")

    return parser.parser.parse_args()


def main():
    options = parse_option()

    set_log_level(options.log_level)

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

    subprocrunner.SubprocessRunner.is_save_history = True

    tc = TrafficControl(options.device)
    if options.log_level == logbook.INFO:
        subprocrunner.set_log_level(logbook.ERROR)

    try:
        return_code = tc.delete_tc()
    except NetworkInterfaceNotFoundError as e:
        logger.debug(e)
        return 0

    command_history = "\n".join(tc.get_command_history())

    if options.tc_command_output == TcCommandOutput.STDOUT:
        print(command_history)
        return return_code

    if options.tc_command_output == TcCommandOutput.SCRIPT:
        set_logger(True)
        write_tc_script(
            TcCommand.TCDEL, command_history, filename_suffix=options.device)
        return return_code

    logger.debug("command history\n{}".format(command_history))

    return return_code


if __name__ == '__main__':
    sys.exit(main())
