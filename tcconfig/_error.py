# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
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
    """
    Exception raised when a traffic shaping rule already exist.
    """


class EmptyParameterError(ValueError):
    """
    Exception raised when a parameter value is empty value.
    """


class InvalidParameterError(ValueError):
    """
    Exception raised when an invalid parameter specified for
    a traffic shaping rule.
    """

    def __init__(self, *args, **kwargs):
        self.__value = kwargs.pop("value", None)
        self.__expected = kwargs.pop("expected", None)

        super(ValueError, self).__init__(*args)

    def __str__(self, *args, **kwargs):
        item_list = [ValueError.__str__(self, *args, **kwargs)]
        extra_item_list = []

        if self.__expected:
            extra_item_list.append("expected={}".format(self.__expected))

        if self.__value:
            extra_item_list.append("value={}".format(self.__value))

        if extra_item_list:
            item_list.extend([":", ", ".join(extra_item_list)])

        return " ".join(item_list)

    def __repr__(self, *args, **kwargs):
        return self.__str__(*args, **kwargs)


class UnitNotFoundError(InvalidParameterError):
    """
    """
