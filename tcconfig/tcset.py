#!/usr/bin/env python
# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

from __future__ import with_statement
import sys

import thutils
import tcconfig


def parse_option():
    parser = thutils.option.ArgumentParserObject()
    parser.make(version="0.2.0")

    group = parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", required=True,
        help="network device name")
    group.add_argument(
        "--rate",
        help="network bandwidth to apply the limit [K|M|G bps]")
    group.add_argument(
        "--delay", type=float, default=0,
        help="round trip network delay [ms] (default=%(default)s)")
    group.add_argument(
        "--loss", type=float, default=0,
        help="round trip packet loss rate [%%] (default=%(default)s)")
    group.add_argument(
        "--network",
        help="destination network of traffic control")
    group.add_argument(
        "--port", type=int,
        help="destination port of traffic control")
    group.add_argument(
        "--overwrite", action="store_true", default=False,
        help="overwrite existing setting")

    return parser.parse_args()


@thutils.main.Main
def main():
    options = parse_option()

    thutils.initialize_library(__file__, options)
    thutils.common.verify_install_command(["tc"])

    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()
    tc = tcconfig.TrafficControl(subproc_wrapper, options.device)
    tc.rate = options.rate
    tc.delay_ms = options.delay
    tc.loss_percent = options.loss
    tc.network = options.network
    tc.port = options.port

    import logging
    subproc_wrapper.command_log_level = logging.DEBUG

    tc.validate()

    if options.overwrite:
        tc.delete_tc()

    tc.set_tc()
    #tc.set_tc(options.rate, options.delay, options.loss, options.network)

    return 0


if __name__ == '__main__':
    sys.exit(main())
