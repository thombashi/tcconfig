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
    parser.make(version="0.3.0")

    group = parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--device", required=True,
        help="network device name (e.g. eth0)")
    group.add_argument(
        "--direction", choices=tcconfig.TrafficDirection.LIST,
        default=tcconfig.TrafficDirection.OUTGOING,
        help="""direction of network communication that impose traffic control.
        default=%(default)s
        """)
    group.add_argument(
        "--rate",
        help="network bandwidth [K|M|G bps]")
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
        help="overwrite existing settings")

    return parser.parse_args()


@thutils.main.Main
def main():
    options = parse_option()

    thutils.initialize_library(__file__, options)
    thutils.common.verify_install_command(["tc"])

    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()
    tc = tcconfig.TrafficControl(subproc_wrapper, options.device)
    tc.direction = options.direction
    tc.rate = options.rate
    tc.delay_ms = options.delay
    tc.loss_percent = options.loss
    tc.network = options.network
    tc.port = options.port

    tc.validate()

    if options.overwrite:
        tc.delete_tc()

    tc.set_tc()
    #tc.set_tc(options.rate, options.delay, options.loss, options.network)

    return 0


if __name__ == '__main__':
    sys.exit(main())
