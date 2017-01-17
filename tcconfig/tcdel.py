#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import sys

import logbook
import subprocrunner

from .traffic_control import TrafficControl
from ._argparse_wrapper import ArgparseWrapper
from ._common import verify_network_interface
from ._const import VERSION
from ._error import NetworkInterfaceNotFoundError
from ._logger import (
    LOG_FORMAT_STRING,
    logger,
    set_log_level,
)


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
        return 1

    tc = TrafficControl(options.device)
    if options.log_level == logbook.INFO:
        subprocrunner.set_log_level(logbook.ERROR)

    try:
        return tc.delete_tc()
    except NetworkInterfaceNotFoundError as e:
        logger.debug(e)
        return 0

    return 1


if __name__ == '__main__':
    sys.exit(main())
