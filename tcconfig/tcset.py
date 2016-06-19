#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import with_statement
import sys

import dataproperty
import pyparsing as pp
import six
import thutils

import tcconfig
import tcconfig.traffic_control


def parse_option():
    parser = thutils.option.ArgumentParserObject()
    parser.make(version=tcconfig.VERSION)

    group = parser.parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--device",
        help="network device name (e.g. eth0)")
    group.add_argument(
        "-f", "--config-file",
        help="""setting traffic controls from a configuration file.
        output file of the tcshow.""")

    group = parser.add_argument_group("Network Interface")
    group.add_argument(
        "--overwrite", action="store_true", default=False,
        help="overwrite existing settings")

    group = parser.add_argument_group("Traffic Control")
    group.add_argument(
        "--direction", choices=tcconfig.traffic_control.TrafficDirection.LIST,
        default=tcconfig.traffic_control.TrafficDirection.OUTGOING,
        help="""the direction of network communication that impose traffic control.
        ``incoming`` requires linux kernel version 2.6.20 or later.
        (default = ``%(default)s``)
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
        (X: value of --delay option, Y: value of --delay-dist option)
        network latency distribution will be uniform without this option.
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


def _parse_tc_filter_network(text):
    network_pattern = (
        pp.SkipTo("network=", include=True) +
        pp.Word(pp.alphanums + "." + "/"))

    return network_pattern.parseString(text)[-1]


def _parse_tc_filter_port(text):
    port_pattern = (
        pp.SkipTo("port=", include=True) +
        pp.Word(pp.nums))

    return port_pattern.parseString(text)[-1]


def load_tcconfig(config_file):
    from voluptuous import Schema, Required, Any, ALLOW_EXTRA

    schema = Schema({
        Required(six.text_type): {
            Any("outgoing", "incoming"): {
                six.text_type: {
                    six.text_type: six.text_type,
                },
            }
        },
    }, extra=ALLOW_EXTRA)

    return thutils.loader.JsonLoader.load(
        config_file, schema)


def get_tcconfig_command_list(config_table, is_overwrite):
    command_list = []

    for device, device_table in six.iteritems(config_table):
        if is_overwrite:
            command_list.append("tcdel --device " + device)

        for direction, direction_table in six.iteritems(device_table):
            for tc_filter, filter_table in six.iteritems(direction_table):
                if filter_table == {}:
                    continue

                option_list = [
                    "--device=" + device,
                    "--direction=" + direction,
                ] + [
                    "--%s=%s" % (k, v)
                    for k, v in six.iteritems(filter_table)
                ]

                try:
                    network = _parse_tc_filter_network(tc_filter)
                    if network != "0.0.0.0/0":
                        option_list.append("--network=" + network)
                except pp.ParseException:
                    pass

                try:
                    port = _parse_tc_filter_port(tc_filter)
                    option_list.append("--port=" + port)
                except pp.ParseException:
                    pass

                command_list.append(" ".join(["tcset"] + option_list))

    return command_list


@thutils.main.Main
def main():
    options = parse_option()

    thutils.initialize_library(__file__, options)
    thutils.common.verify_install_command(["tc"])

    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()

    if dataproperty.is_not_empty_string(options.config_file):
        return_code = 0

        for tcconfig_command in get_tcconfig_command_list(
                load_tcconfig(options.config_file), options.overwrite):
            return_code |= subproc_wrapper.run(tcconfig_command)

        return return_code

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
