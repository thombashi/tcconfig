# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import

import abc


class TargetNotFoundError(Exception):
    @abc.abstractproperty
    def _target_type(self):
        return None

    def __init__(self, *args, **kwargs):
        self._target = kwargs.pop("target", None)

        super(TargetNotFoundError, self).__init__(*args, **kwargs)

    def __str__(self, *args, **kwargs):
        item_list = [Exception.__str__(self, *args, **kwargs)]

        if self._target:
            item_list.append("{} not found: {}".format(self._target_type, self._target))

        return " ".join(item_list).strip()

    def __repr__(self, *args, **kwargs):
        return self.__str__(*args, **kwargs)


class NetworkInterfaceNotFoundError(TargetNotFoundError):
    """
    Exception raised when network interface not found.
    """

    @property
    def _target_type(self):
        return "network interface"

    def __str__(self, *args, **kwargs):
        item_list = [super(NetworkInterfaceNotFoundError, self).__str__(*args, **kwargs)]

        try:
            import netifaces

            item_list.append("(available interfaces: {})".format(", ".join(netifaces.interfaces())))
        except ImportError:
            pass

        return " ".join(item_list).strip()


class ContainerNotFoundError(TargetNotFoundError):
    """
    Exception raised when container not found.
    """

    @property
    def _target_type(self):
        return "container"

    def __str__(self, *args, **kwargs):
        from ._docker import DockerClient

        dclient = DockerClient()
        container_list = dclient.extract_running_container_name_list()
        item_list = [super(ContainerNotFoundError, self).__str__(*args, **kwargs)]

        if container_list:
            item_list.append("(available running containers: {})".format(", ".join(container_list)))
        else:
            item_list.append("(running container not found)")

        return " ".join(item_list).strip()


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


class ParameterError(ValueError):
    """
    Exception raised when an invalid parameter specified for
    a traffic shaping rule.
    """

    def __init__(self, *args, **kwargs):
        self.__value = kwargs.pop("value", None)
        self.__expected = kwargs.pop("expected", None)

        super(ParameterError, self).__init__(*args, **kwargs)

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


class UnitNotFoundError(ParameterError):
    """
    """

    def __init__(self, *args, **kwargs):
        self.__available_unit = kwargs.pop("available_unit", None)

        super(UnitNotFoundError, self).__init__(*args, **kwargs)

    def _get_extra_msg_list(self):
        extra_msg_list = []

        if self.__available_unit:
            extra_msg_list.append("available-units={}".format(self.__available_unit))

        return super(UnitNotFoundError, self)._get_extra_msg_list() + extra_msg_list
