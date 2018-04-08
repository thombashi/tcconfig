# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, unicode_literals

import errno
import os
import re
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


def _has_capabilies(bin_path, capabilities):
    getcap_bin_path = find_bin_path("getcap")

    if not getcap_bin_path:
        logger.error("command not found: getcap")
        return False

    bin_path = os.path.realpath(bin_path)
    proc = spr.SubprocessRunner("{:s} {:s}".format(getcap_bin_path, bin_path))
    if proc.run() != 0:
        logger.error(proc.stderr)
        sys.exit(proc.returncode)

    getcap_output = proc.stdout
    has_capabilies = True
    for capability in capabilities:
        if re.search(capability, getcap_output):
            logger.debug("{:s} has {:s} capability".format(bin_path, capability))
        else:
            logger.debug("{:s} has no {:s} capability".format(bin_path, capability))
            has_capabilies = False

    capability = "+ep"
    if re.search(re.escape(capability), getcap_output):
        logger.debug("{:s} has {:s} capability".format(bin_path, capability))
    else:
        logger.debug("{:s} has no {:s} capability".format(bin_path, capability))
        has_capabilies = False

    return has_capabilies


def has_execution_authority(command):
    if os.getuid() == 0:
        return True

    capabilities_map = {
        "tc": ["cap_net_admin"],
        "iptables": ["cap_net_raw", "cap_net_admin"],
    }

    return _has_capabilies(find_bin_path(command), capabilities_map[command])


def check_tc_execution_authority():
    if not has_execution_authority("tc"):
        logger.error("Permission denied (you must be root)")
        sys.exit(errno.EPERM)


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
