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

        super(InvalidParameterError, self).__init__(*args, **kwargs)

    def __str__(self, *args, **kwargs):
        item_list = [ValueError.__str__(self, *args, **kwargs)]
        extra_msg_list = self._get_extra_msg_list()

        if extra_msg_list:
            item_list.extend([":", ", ".join(extra_msg_list)])

        return " ".join(item_list)

    def __repr__(self, *args, **kwargs):
        return self.__str__(*args, **kwargs)

    def _get_extra_msg_list(self):
        extra_msg_list = []

        if self.__expected:
            extra_msg_list.append("expected={}".format(self.__expected))

        if self.__value:
            extra_msg_list.append("value={}".format(self.__value))

        return extra_msg_list


class UnitNotFoundError(InvalidParameterError):
    """
    """

    def __init__(self, *args, **kwargs):
        self.__available_unit = kwargs.pop("available_unit", None)

        super(UnitNotFoundError, self).__init__(*args, **kwargs)

    def _get_extra_msg_list(self):
        extra_msg_list = []

        if self.__available_unit:
            extra_msg_list.append(
                "available-units={}".format(self.__available_unit))

        return (
            super(UnitNotFoundError, self)._get_extra_msg_list() +
            extra_msg_list)
