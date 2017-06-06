# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib

import logbook
import six
import typepy

import subprocrunner as spr

from ._const import (
    Network,
    TcCoomandOutput,
)
from ._error import NetworkInterfaceNotFoundError
from ._logger import logger


@contextlib.contextmanager
def logging_context(name):
    logger.debug("|---- {:s}: {:s} -----".format("start", name))
    try:
        yield
    finally:
        logger.debug("----- {:s}: {:s} ----|".format("complete", name))


def is_anywhere_network(network, ip_version):
    try:
        return network.strip() == get_anywhere_network(ip_version)
    except AttributeError as e:
        raise ValueError(e)


def is_execute_tc_command(tc_command_output):
    return tc_command_output == TcCoomandOutput.NOT_SET


def get_anywhere_network(ip_version):
    ip_version_n = typepy.type.Integer(ip_version).try_convert()

    if ip_version_n == 4:
        return Network.Ipv4.ANYWHERE

    if ip_version_n == 6:
        return Network.Ipv6.ANYWHERE

    raise ValueError("unknown ip version: {}".format(ip_version))


def verify_network_interface(device):
    try:
        import netifaces
    except ImportError:
        return

    if device not in netifaces.interfaces():
        raise NetworkInterfaceNotFoundError(
            "network interface not found: {}".format(device))


def sanitize_network(network, ip_version):
    """
    :return: Network string
    :rtype: str
    :raises ValueError: if the network string is invalid.
    """

    import ipaddress

    if typepy.is_null_string(network):
        return ""

    if network.lower() == "anywhere":
        return get_anywhere_network(ip_version)

    try:
        if ip_version == 4:
            ipaddress.IPv4Address(network)
            return network + "/32"

        if ip_version == 6:
            return ipaddress.IPv6Address(network).compressed
    except ipaddress.AddressValueError:
        pass

    # validate network str ---

    if ip_version == 4:
        return ipaddress.IPv4Network(six.text_type(network)).compressed

    if ip_version == 6:
        return ipaddress.IPv6Network(six.text_type(network)).compressed

    raise ValueError("unexpected ip version: {}".format(ip_version))


def run_command_helper(command, error_regexp, message, exception=None):
    if logger.level != logbook.DEBUG:
        spr.set_logger(is_enable=False)

    proc = spr.SubprocessRunner(command)
    proc.run()

    if logger.level != logbook.DEBUG:
        spr.set_logger(is_enable=True)

    if proc.returncode == 0:
        return 0

    match = error_regexp.search(proc.stderr)
    if match is None:
        logger.error(proc.stderr)
        return proc.returncode

    if typepy.is_not_null_string(message):
        logger.notice(message)

    if exception is not None:
        raise exception(command)

    return proc.returncode


def run_tc_show(subcommand, device):
    runner = spr.SubprocessRunner(
        "tc {:s} show dev {:s}".format(subcommand, device))
    runner.run()

    return runner.stdout


def _get_original_tcconfig_command(tcconfig_command):
    import sys

    return " ".join([tcconfig_command] + [
        command_item for command_item in sys.argv[1:]
        if command_item != "--tc-script"
    ])


def write_tc_script(tcconfig_command, command_history, filename_suffix=None):
    import datetime
    import io
    import os

    filename_item_list = [tcconfig_command]
    if typepy.is_not_null_string(filename_suffix):
        filename_item_list.append(filename_suffix)

    filename = "_".join(filename_item_list) + ".sh"
    with io.open(filename, "w", encoding="utf8") as fp:
        fp.write("\n".join([
            "#!/bin/sh",
            "",
            "# tc script file:",
            "#   the following command sequence lead to equivalent results as",
            "#   '{:s}'.".format(
                _get_original_tcconfig_command(tcconfig_command)),
            "#   created by {:s} on {:s}.".format(
                tcconfig_command,
                datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")),
            "",
            command_history,
        ]) + "\n")

    os.chmod(filename, 0o755)
    logger.info("written a tc script to '{:s}'".format(filename))
