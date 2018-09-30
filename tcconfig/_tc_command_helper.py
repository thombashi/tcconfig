# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import subprocrunner as spr

from ._common import find_bin_path
from ._const import TcSubCommand
from ._error import NetworkInterfaceNotFoundError


def get_tc_base_command(tc_subcommand):
    if not isinstance(tc_subcommand, TcSubCommand):
        raise ValueError("the argument must be a TcSubCommand value")

    return "{:s} {:s}".format(find_bin_path("tc"), tc_subcommand.value)


def run_tc_show(subcommand, device, tc_command_output):
    from ._network import verify_network_interface

    verify_network_interface(device, tc_command_output)

    runner = spr.SubprocessRunner(
        "{:s} show dev {:s}".format(get_tc_base_command(subcommand), device)
    )
    if runner.run() != 0 and runner.stderr.find("Cannot find device") != -1:
        # reach here if the device does not exist at the system and netiface
        # not installed.
        raise NetworkInterfaceNotFoundError(target=device)

    return runner.stdout
