# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import


class ModuleNotFoundError(Exception):
    """
    Raised when mandatory kernel module not found.
    """


class TcCommandExecutionError(Exception):
    """
    Raised when a tc command failed.
    """
