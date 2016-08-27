# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import


class NetworkInterfaceNotFoundError(Exception):
    """
    Raised when network interface not found.
    """


class ModuleNotFoundError(Exception):
    """
    Raised when mandatory kernel module not found.
    """


class TcCommandExecutionError(Exception):
    """
    Raised when failed to execute a ``tc`` command.
    """
