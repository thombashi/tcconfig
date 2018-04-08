# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import errno
import os
import sys

import subprocrunner as spr

from ._common import find_bin_path
from ._const import TcSubCommand
from ._error import NetworkInterfaceNotFoundError
from ._logger import logger


def check_tc_command_installation():
    if find_bin_path("tc"):
        return

    logger.error("command not found: tc")
    sys.exit(errno.ENOENT)


def check_tc_execution_authority():
    if os.getuid() != 0:
        # using OSError for Python2 compatibility reason.
        # (PermissionError introduced since Python 3.3)
        raise OSError("Permission denied (you must be root)")


def get_tc_base_command(tc_subcommand):
    if tc_subcommand not in TcSubCommand:
        raise ValueError("the argument must be a TcSubCommand value")

    return "{:s} {:s}".format(find_bin_path("tc"), tc_subcommand.value)


def run_tc_show(subcommand, device):
    from ._network import verify_network_interface

    verify_network_interface(device)

    runner = spr.SubprocessRunner(
        "{:s} show dev {:s}".format(get_tc_base_command(subcommand), device))
    if runner.run() != 0 and runner.stderr.find("Cannot find device") != -1:
        # reach here if the device does not exist at the system and netiface
        # not installed.
        raise NetworkInterfaceNotFoundError(device=device)

    return runner.stdout
