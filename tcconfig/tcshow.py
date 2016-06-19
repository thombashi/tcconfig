#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import with_statement
import sys

try:
    import json
except ImportError:
    import simplejson as json

import six
import thutils

import tcconfig
import tcconfig.traffic_control


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

    thutils.initialize_library(__file__, options)
    thutils.common.verify_install_command(["tc"])

    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()
    tc_param = {}

    for device in options.device:
        tcconfig.verify_network_interface(device)

        tc = tcconfig.traffic_control.TrafficControl(
            subproc_wrapper, device)
        tc_param.update(tc.get_tc_parameter())

    six.print_(json.dumps(tc_param, indent=4))

    return 0


if __name__ == '__main__':
    sys.exit(main())
