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
    verify_network_interface,
    write_tc_script,
)
from ._const import (
    VERSION,
    TcCoomandOutput,
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

    subprocrunner.Which("tc").verify()

    try:
        verify_network_interface(options.device)
    except NetworkInterfaceNotFoundError as e:
        logger.error(e)
        return errno.EINVAL

    tc = TrafficControl(options.device)
    if options.log_level == logbook.INFO:
        subprocrunner.set_log_level(logbook.ERROR)

    subprocrunner.SubprocessRunner.is_save_history = True
    if options.tc_command_output != TcCoomandOutput.NOT_SET:
        subprocrunner.SubprocessRunner.is_dry_run = True

    if options.tc_command_output != TcCoomandOutput.NOT_SET:
        set_logger(False)

    try:
        return_code = tc.delete_tc()
    except NetworkInterfaceNotFoundError as e:
        logger.debug(e)
        return 0

    command_history = "\n".join(tc.get_command_history())

    if options.tc_command_output == TcCoomandOutput.STDOUT:
        print(command_history)
        return return_code

    if options.tc_command_output == TcCoomandOutput.SCRIPT:
        set_logger(True)
        write_tc_script(
            "tcdel", command_history, filename_suffix=options.device)
        return return_code

    logger.debug("command history\n{}".format(command_history))

    return return_code


if __name__ == '__main__':
    sys.exit(main())
