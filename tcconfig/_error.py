# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import


class NetworkInterfaceNotFoundError(Exception):
    """
    Exception raised when network interface not found.
    """


class ModuleNotFoundError(Exception):
    """
    Exception raised when mandatory kernel module not found.
    """


class TcCommandExecutionError(Exception):
    """
    Exception raised when failed to execute a ``tc`` command.
    """


class TcAlreadyExist(TcCommandExecutionError):
    pass


class EmptyParameterError(ValueError):
    pass


class InvalidParameterError(ValueError):
    pass
