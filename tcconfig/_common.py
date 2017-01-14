# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import

import dataproperty
import six

from ._error import NetworkInterfaceNotFoundError


ANYWHERE_NETWORK = "0.0.0.0/0"


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

    if dataproperty.is_empty_string(network):
        return ""

    if network.lower() == "anywhere":
        return ANYWHERE_NETWORK

    try:
        ipaddress.IPv4Address(six.u(network))
        return network + "/32"
    except ipaddress.AddressValueError:
        pass

    ipaddress.IPv4Network(six.u(network))  # validate network str

    return network


def run_command_helper(command, error_regexp, message):
    from subprocrunner import SubprocessRunner
    from ._logger import logger

    proc = SubprocessRunner(command)
    if proc.run() == 0:
        return 0

    match = error_regexp.search(proc.stderr)
    if match is None:
        return proc.returncode

    logger.notice(message)

    return proc.returncode
