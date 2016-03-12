#!/usr/bin/env python
# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

from __future__ import absolute_import
from __future__ import with_statement
import sys

import thutils
import tcconfig
import tcconfig.traffic_control


def parse_option():
    parser = thutils.option.ArgumentParserObject()
    parser.make(version=tcconfig.VERSION)

    group = parser.add_argument_group("Network Interface")
    group.add_argument(
        "--device", required=True,
        help="network device name (e.g. eth0)")
    group.add_argument(
        "--overwrite", action="store_true", default=False,
        help="overwrite existing settings")

    group = parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--direction", choices=tcconfig.traffic_control.TrafficDirection.LIST,
        default=tcconfig.traffic_control.TrafficDirection.OUTGOING,
        help="""direction of network communication that impose traffic control.
        "incoming" requires linux kernel version 2.6.20 or later.
        (default=%(default)s)
        """)
    group.add_argument(
        "--rate", dest="bandwidth_rate",
        help="network bandwidth rate [K|M|G bps]")
    group.add_argument(
        "--delay", dest="network_latency", type=float, default=0,
        help="round trip network delay [ms] (default=%(default)s)")
    group.add_argument(
        "--delay-distro", dest="latency_distro_ms", type=float, default=0,
        help="""
        distribution of network latency becomes X +- Y [ms]
        (normal distribution), with this option.
        (X: value of --delay option, Y: value of --delay-dist opion)
        network latency distribution will uniform without this option.
        """)
    group.add_argument(
        "--loss", dest="packet_loss_rate", type=float, default=0,
        help="round trip packet loss rate [%%] (default=%(default)s)")
    group.add_argument(
        "--corrupt", dest="corruption_rate", type=float, default=0,
        help="""
        packet corruption rate [%%].
        packet corruption means single bit error at a random offset in the packet.
        (default=%(default)s)
        """)
    group.add_argument(
        "--network",
        help="IP address/network of traffic control")
    group.add_argument(
        "--port", type=int,
        help="port number of traffic control")

    return parser.parse_args()


@thutils.main.Main
def main():
    options = parse_option()

    thutils.initialize_library(__file__, options)
    thutils.common.verify_install_command(["tc"])

    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()
    tc = tcconfig.traffic_control.TrafficControl(
        subproc_wrapper, options.device)
    tc.direction = options.direction
    tc.bandwidth_rate = options.bandwidth_rate
    tc.latency_ms = options.network_latency
    tc.latency_distro_ms = options.latency_distro_ms
    tc.packet_loss_rate = options.packet_loss_rate
    tc.corruption_rate = options.corruption_rate
    tc.network = options.network
    tc.port = options.port

    tc.validate()

    if options.overwrite:
        tc.delete_tc()

    tc.set_tc()

    return 0


if __name__ == '__main__':
    sys.exit(main())
