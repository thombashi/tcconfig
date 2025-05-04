#!/usr/bin/env python3

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import errno
import sys

import subprocrunner as spr

from .__version__ import __version__
from ._argparse_wrapper import ArgparseWrapper
from ._capabilities import check_execution_authority
from ._command import TcDelMain
from ._common import initialize_cli, is_execute_tc_command
from ._error import NetworkInterfaceNotFoundError
from ._logger import logger, set_logger
from ._network import verify_network_interface


def parse_option():
    parser = ArgparseWrapper(__version__)

    group = parser.parser.add_argument_group("Traffic Control")
    if {"-d", "--device"}.intersection(set(sys.argv)):
        # deprecated: remain for backward compatibility
        group.add_argument("-d", "--device", required=True, help="network device name (e.g. eth0)")
    else:
        group.add_argument("device", help="network device name (e.g. eth0)")
    group.add_argument(
        "-a",
        "--all",
        dest="is_delete_all",
        action="store_true",
        help="delete all of the shaping rules.",
    )
    group.add_argument(
        "--id",
        dest="filter_id",
        help="""delete a shaping rule that has a specific id. you can get an id (filter_id)
        by tcshow command output.
        e.g. "filter_id": "800::801"
        """,
    )

    parser.add_routing_group()
    parser.add_docker_group()

    return parser.parser.parse_args()


def main():
    options = parse_option()

    initialize_cli(options)

    if is_execute_tc_command(options.tc_command_output):
        check_execution_authority("tc")

        if not options.use_docker:
            try:
                verify_network_interface(options.device, options.tc_command_output)
            except NetworkInterfaceNotFoundError as e:
                logger.error(e)
                return errno.EINVAL

        is_delete_all = options.is_delete_all
    else:
        spr.SubprocessRunner.default_is_dry_run = True
        is_delete_all = True
        set_logger(False)

    spr.SubprocessRunner.clear_history()

    return TcDelMain(options).run(is_delete_all)


if __name__ == "__main__":
    sys.exit(main())
