#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import sys

import subprocrunner
import thutils

import tcconfig
from traffic_control import TrafficControl

from ._common import verify_network_interface


def parse_option():
    parser = thutils.option.ArgumentParserObject()
    parser.make(version=tcconfig.VERSION)

    group = parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", required=True,
        help="network device name (e.g. eth0)")

    return parser.parse_args()


@thutils.main.Main
def main():
    options = parse_option()

    subprocrunner.Which("tc").verify()
    verify_network_interface(options.device)

    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()
    tc = TrafficControl(
        subproc_wrapper, options.device)

    return tc.delete_tc()


if __name__ == '__main__':
    sys.exit(main())
