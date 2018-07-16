# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <>
"""

from __future__ import absolute_import, unicode_literals

import errno
import os
import re
import sys

import subprocrunner as spr

from ._common import find_bin_path
from ._logger import logger


def get_required_capabilities(command):
    required_capabilities_map = {
        "tc": ["cap_net_admin"],
        "ip": ["cap_net_raw", "cap_net_admin"],
        "iptables": ["cap_net_raw", "cap_net_admin"],
    }

    return required_capabilities_map[command]


def get_permission_error_message(command):
    PERMISSION_ERROR_MSG_FORMAT = "\n".join(
        [
            "Permission denied: you must be root or set Linux capabilities to execute the command.",
            "  How to setup Linux capabilities for the {command:s} command:",
            "    $ sudo setcap {capabilities:s}+ep {bin_path:s}",
        ]
    )

    return PERMISSION_ERROR_MSG_FORMAT.format(
        command=command,
        capabilities=",".join(get_required_capabilities(command)),
        bin_path=find_bin_path(command),
    )


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
    from ._common import check_command_installation

    check_command_installation(command)

    if os.getuid() == 0:
        return True

    return _has_capabilies(find_bin_path(command), get_required_capabilities(command))


def check_execution_authority(command):
    if has_execution_authority(command):
        return

    logger.error(get_permission_error_message(command))
    sys.exit(errno.EPERM)
