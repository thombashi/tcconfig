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

from ._const import ANYWHERE_NETWORK
from ._error import NetworkInterfaceNotFoundError
from ._logger import logger


@contextlib.contextmanager
def logging_context(name):
    logger.debug("|---- {:s}: {:s} -----".format("start", name))
    try:
        yield
    finally:
        logger.debug("----- {:s}: {:s} ----|".format("complete", name))


def verify_network_interface(device):
    try:
        import netifaces
    except ImportError:
        return

    if device not in netifaces.interfaces():
        raise NetworkInterfaceNotFoundError(
            "network interface not found: {}".format(device))


def sanitize_network(network):
    """
    :return: Network string
    :rtype: str
    :raises ValueError: if the network string is invalid.
    """

    import ipaddress

    if typepy.is_null_string(network):
        return ""

    if network.lower() == "anywhere":
        return ANYWHERE_NETWORK

    try:
        ipaddress.IPv4Address(six.text_type(network))
        return network + "/32"
    except ipaddress.AddressValueError:
        pass

    ipaddress.IPv4Network(six.text_type(network))  # validate network str

    return network


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
