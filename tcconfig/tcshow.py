#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import json
import sys
import six
import subprocrunner
import thutils

import tcconfig
from .traffic_control import TrafficControl

from ._common import verify_network_interface


def parse_option():
    parser = thutils.option.ArgumentParserObject()
    parser.make(version=tcconfig.VERSION)

    group = parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", action="append", required=True,
        help="network device name (e.g. eth0)")

    return parser.parse_args()


@thutils.main.Main
def main():
    options = parse_option()

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
