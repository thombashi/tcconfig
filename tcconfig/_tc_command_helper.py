# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import errno
import sys

import subprocrunner as spr

from ._common import find_bin_path
from ._const import Tc, TcSubCommand
from ._error import NetworkInterfaceNotFoundError
from ._logger import logger


def check_tc_command_installation():
    try:
        spr.Which("tc").verify()
    except spr.CommandNotFoundError as e:
        logger.error("{:s}: {}".format(e.__class__.__name__, e))
        sys.exit(errno.ENOENT)


def get_tc_base_command(tc_subcommand):
    if tc_subcommand not in TcSubCommand:
        raise ValueError("the argument must be a TcSubCommand value")

    return "{:s} {:s}".format(find_bin_path("tc"), tc_subcommand.value)


def run_tc_show(subcommand, device):
    from ._network import verify_network_interface

    if subcommand not in Tc.Subcommand.LIST:
        raise ValueError("unexpected tc sub command: {}".format(subcommand))

    verify_network_interface(device)

    runner = spr.SubprocessRunner(
        "tc {:s} show dev {:s}".format(subcommand, device))
    if runner.run() != 0 and runner.stderr.find("Cannot find device") != -1:
        # reach here if the device does not exist at the system and netiface
        # not installed.
        raise NetworkInterfaceNotFoundError(device=device)

    return runner.stdout
