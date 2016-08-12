#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import json
import sys
import six

import logbook
import subprocrunner

import tcconfig
from .traffic_control import TrafficControl
from ._argparse_wrapper import ArgparseWrapper
from ._common import verify_network_interface


handler = logbook.StderrHandler()
handler.push_application()


def parse_option():
    parser = ArgparseWrapper(tcconfig.VERSION)

    group = parser.parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", action="append", required=True,
        help="network device name (e.g. eth0)")

    return parser.parser.parse_args()


def main():
    options = parse_option()

    subprocrunner.logger.level = options.log_level
    if options.quiet:
        subprocrunner.logger.disable()
    else:
        subprocrunner.logger.enable()

    subprocrunner.Which("tc").verify()

    tc_param = {}
    for device in options.device:
        verify_network_interface(device)

        tc = TrafficControl(device)
        tc_param.update(tc.get_tc_parameter())

    six.print_(json.dumps(tc_param, indent=4))

    return 0


if __name__ == '__main__':
    sys.exit(main())
