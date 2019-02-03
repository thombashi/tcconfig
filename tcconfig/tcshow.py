#!/usr/bin/env python
# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, print_function, unicode_literals

import sys

import simplejson as json
import subprocrunner as spr

from .__version__ import __version__
from ._argparse_wrapper import ArgparseWrapper
from ._common import check_command_installation, initialize_cli
from ._const import Tc, TcCommandOutput
from ._docker import DockerClient
from ._error import TargetNotFoundError
from ._logger import logger
from ._network import verify_network_interface
from ._tc_script import write_tc_script
from .parser.shaping_rule import TcShapingRuleParser


def parse_option():
    parser = ArgparseWrapper(__version__)

    group = parser.parser.add_argument_group("Traffic Control")
    if set(["-d", "--device"]).intersection(set(sys.argv)):
        # deprecated: remain for backward compatibility
        group.add_argument(
            "-d", "--device", action="append", required=True, help="network device name (e.g. eth0)"
        )
    else:
        group.add_argument("device", nargs="+", help="network device name (e.g. eth0)")
    group.add_argument(
        "--ipv6",
        dest="ip_version",
        action="store_const",
        const=6,
        default=4,
        help="Display IPv6 shaping rules. Defaults to show IPv4 shaping rules.",
    )

    parser.add_docker_group(is_add_srcdst=False)

    parser.parser.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="colorize the output. require Pygments package.",
    )

    return parser.parser.parse_args()


def print_tc(text, is_colorize):
    try:
        from pygments import highlight
        from pygments.lexers import JsonLexer
        from pygments.formatters import TerminalTrueColorFormatter

        pygments_installed = True
    except ImportError:
        pygments_installed = False

    if is_colorize and pygments_installed:
        print(
            highlight(
                code=text, lexer=JsonLexer(), formatter=TerminalTrueColorFormatter(style="monokai")
            )
        )
    else:
        print(text)


def main():
    options = parse_option()

    initialize_cli(options)
    check_command_installation("tc")

    if options.tc_command_output != TcCommandOutput.NOT_SET:
        spr.SubprocessRunner.default_is_dry_run = True

    dclient = DockerClient(options.tc_command_output)

    tc_param = {}
    for device in options.device:
        try:
            if options.use_docker and dclient.exist_container(container=device):
                container = device

                dclient.verify_container(container)
                dclient.create_veth_table(container)
                container_info = dclient.extract_container_info(container)

                for veth in dclient.fetch_veth_list(container_info.name):
                    tc_param.update(
                        TcShapingRuleParser(
                            veth, options.ip_version, options.tc_command_output, logger
                        ).get_tc_parameter()
                    )
                    tc_param[
                        "{veth} (container_id={id}, image={image})".format(
                            veth=veth, id=container_info.id[:12], image=container_info.image
                        )
                    ] = tc_param.pop(veth)
            else:
                verify_network_interface(device, options.tc_command_output)

                tc_param.update(
                    TcShapingRuleParser(
                        device, options.ip_version, options.tc_command_output, logger
                    ).get_tc_parameter()
                )
        except TargetNotFoundError as e:
            logger.warn(e)
            continue

    command_history = "\n".join(spr.SubprocessRunner.get_history())

    if options.tc_command_output == TcCommandOutput.STDOUT:
        print(command_history)
        return 0

    if options.tc_command_output == TcCommandOutput.SCRIPT:
        write_tc_script(
            Tc.Command.TCSHOW, command_history, filename_suffix="-".join(options.device)
        )
        return 0

    logger.debug("command history\n{}".format(command_history))

    print_tc(json.dumps(tc_param, ensure_ascii=False, indent=4), options.color)

    return 0


if __name__ == "__main__":
    sys.exit(main())
