"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

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
        # assume that the command has the required capabilities if getcap command is not found
        return True

    bin_path = os.path.realpath(bin_path)
    proc = spr.SubprocessRunner(f"{getcap_bin_path:s} {bin_path:s}")
    if proc.run() != 0:
        logger.error(proc.stderr)
        sys.exit(proc.returncode)

    getcap_output = proc.stdout
    has_capabilies = True

    if not getcap_output:
        logger.debug(f"no capabilities found for {bin_path:s}")
        return False

    for capability in capabilities:
        if re.search(capability, getcap_output):
            logger.debug(f"{bin_path:s} has {capability:s} capability")
        else:
            logger.debug(f"{bin_path:s} has no {capability:s} capability")
            has_capabilies = False

    # ubuntu: =ep
    # debian: +ep
    capability = "[+=]ep$"
    if re.search(capability, getcap_output):
        logger.debug(f"{bin_path:s} has {capability:s} capability")
    else:
        logger.debug(f"{bin_path:s} has no {capability:s} capability: got={getcap_output}")
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
