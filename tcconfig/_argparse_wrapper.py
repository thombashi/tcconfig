#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
import argparse

import logbook

from ._const import (
    TcCommandOutput,
    TrafficDirection,
)


class ArgparseWrapper(object):
    """
    Wrapper class for argparse
    """

    def __init__(self, version, description=""):
        epilog = "Issue tracker: https://github.com/thombashi/tcconfig/issues"

        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=description, epilog=epilog)
        self.parser.add_argument(
            "--version", action="version", version="%(prog)s " + version)

        self._add_tc_command_arg_group()
        self._add_log_level_argument_group()

        group = self.parser.add_argument_group("Debug")
        group.add_argument(
            "--stacktrace", dest="is_output_stacktrace",
            action="store_true", default=False,
            help="""print stack trace for debug information.
            --debug option required to see the debug print.
            """)

    def add_routing_group(self):
        group = self.parser.add_argument_group("Routing")
        group.add_argument(
            "--direction", choices=TrafficDirection.LIST,
            default=TrafficDirection.OUTGOING,
            help="""the direction of network communication that impose traffic control.
            'incoming' requires Linux kernel version 2.6.20 or later.
            (default = %(default)s)
            """)
        group.add_argument(
            "--network", "--dst-network", dest="dst_network",
            help="target IP-address/network to control traffic")
        group.add_argument(
            "--src-network",
            help="""set a traffic shaping rule to specific packets that routed from
            --src-network to --dst-network. this option required to execute
            with the --iptables option when you use tbf.
            the shaping rule only affect to outgoing packets
            (no effect to if you execute with "--direction incoming" option)
            """)
        group.add_argument(
            "--port", "--dst-port", dest="dst_port", type=int,
            help="target destination port number to control traffic.")
        group.add_argument(
            "--src-port", type=int,
            help="target source port number to control traffic.")
        group.add_argument(
            "--ipv6", dest="is_ipv6", action="store_true", default=False,
            help="apply traffic control to IPv6 packets rather than IPv4.")

        return group

    def _add_log_level_argument_group(self):
        dest = "log_level"

        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            "--debug", dest=dest, action="store_const",
            const=logbook.DEBUG, default=logbook.INFO,
            help="for debug print.")
        group.add_argument(
            "--quiet", dest=dest, action="store_const",
            const=logbook.NOTSET, default=logbook.INFO,
            help="suppress execution log messages.")

        return group

    def _add_tc_command_arg_group(self):
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            "--tc-command", dest="tc_command_output", action="store_const",
            const=TcCommandOutput.STDOUT, default=TcCommandOutput.NOT_SET,
            help="""
            display tc commands to be executed and exit.
            these commands are not executed.
            """)

        group.add_argument(
            "--tc-script", dest="tc_command_output", action="store_const",
            const=TcCommandOutput.SCRIPT, default=TcCommandOutput.NOT_SET,
            help="""
            generate a script file that described tc commands which equivalent
            with execution tcconfig command. the script can be execute without
            tcconfig package installation.
            """)
