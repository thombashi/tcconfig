# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import

import argparse
from textwrap import dedent

import logbook

from ._const import TcCommandOutput, TrafficDirection


class ArgparseWrapper(object):
    """
    Wrapper class for argparse
    """

    def __init__(self, version, description=""):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=description,
            epilog=dedent(
                """\
                Documentation: https://tcconfig.rtfd.io/
                Issue tracker: https://github.com/thombashi/tcconfig/issues
                """
            ),
        )
        self.parser.add_argument(
            "-V", "--version", action="version", version="%(prog)s {}".format(version)
        )
        self._add_tc_command_arg_group()
        self._add_log_level_argument_group()

        group = self.parser.add_argument_group("Debug")
        group.add_argument(
            "--debug-query", action="store_true", default=False, help="for debug print."
        )
        group.add_argument(
            "--stacktrace",
            dest="is_output_stacktrace",
            action="store_true",
            default=False,
            help="""print stack trace for debug information.
            --debug option required to see the debug print.
            """,
        )

    def add_routing_group(self):
        group = self.parser.add_argument_group("Routing")
        group.add_argument(
            "--direction",
            choices=TrafficDirection.LIST,
            default=TrafficDirection.OUTGOING,
            help="""the direction of network communication that imposes traffic control.
            'incoming' requires ifb kernel module and Linux kernel 2.6.20 or later.
            (default = %(default)s)
            """,
        )
        group.add_argument(
            "--network",
            "--dst-network",
            dest="dst_network",
            help="""specify destination IP-address/network that applies traffic control.
            defaults to any.""",
        )
        group.add_argument(
            "--src-network",
            help="""specify source IP-address/network that applies traffic control.
            defaults to any.
            this option has no effect when executing with "--direction incoming" option.
            note: this option required to execute with the --iptables option when using tbf
            algorithm.
            """,
        )
        group.add_argument(
            "--port",
            "--dst-port",
            dest="dst_port",
            type=int,
            help="specify destination port number that applies traffic control. defaults to any.",
        )
        group.add_argument(
            "--src-port",
            type=int,
            help="specify source port number that applies traffic control. defaults to any.",
        )
        group.add_argument(
            "--ipv6",
            dest="is_ipv6",
            action="store_true",
            default=False,
            help="apply traffic control to IPv6 packets rather than IPv4.",
        )

        return group

    def _add_log_level_argument_group(self):
        dest = "log_level"

        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            "--debug",
            dest=dest,
            action="store_const",
            const=logbook.DEBUG,
            default=logbook.INFO,
            help="for debug print.",
        )
        group.add_argument(
            "--quiet",
            dest=dest,
            action="store_const",
            const=logbook.NOTSET,
            default=logbook.INFO,
            help="suppress execution log messages.",
        )

        return group

    def add_docker_group(self, is_add_srcdst=True):
        group = self.parser.add_argument_group("Docker")
        group.add_argument(
            "--docker",
            dest="use_docker",
            action="store_true",
            default=False,
            help="apply traffic control to a docker container.",
        )
        if is_add_srcdst:
            group.add_argument("--src-container", help="specify source container id or name.")
            group.add_argument("--dst-container", help="specify destination container id or name.")

        return group

    def _add_tc_command_arg_group(self):
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            "--tc-command",
            dest="tc_command_output",
            action="store_const",
            const=TcCommandOutput.STDOUT,
            default=TcCommandOutput.NOT_SET,
            help="""
            display tc commands to be executed and exit.
            these commands are not actually executed.
            """,
        )

        group.add_argument(
            "--tc-script",
            dest="tc_command_output",
            action="store_const",
            const=TcCommandOutput.SCRIPT,
            default=TcCommandOutput.NOT_SET,
            help="""
            generate a shell script file that described tc commands.
            this tc script execution result nearly equivalent with the tcconfig command.
            the script can be executed without tcconfig package installation.
            """,
        )
