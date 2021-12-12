"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import abc

from pr2modules.iproute import IPRoute


class TargetNotFoundError(Exception):
    @abc.abstractproperty
    def _target_type(self):
        return None

    def __init__(self, *args, **kwargs):
        self._target = kwargs.pop("target", None)

        super().__init__(*args, **kwargs)

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
        item_list = [super().__str__(*args, **kwargs)]

        with IPRoute() as ipr:
            avail_interfaces = [link.get_attr("IFLA_IFNAME") for link in ipr.get_links()]

        item_list.append("(available interfaces: {})".format(", ".join(avail_interfaces)))

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
        container_names = dclient.extract_running_container_names()
        item_list = [super().__str__(*args, **kwargs)]

        if container_names:
            item_list.append(
                "(available running containers: {})".format(", ".join(container_names))
            )
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
