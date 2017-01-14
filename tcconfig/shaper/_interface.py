# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import abc

import dataproperty
import six

from .._iptables import (
    IptablesMangleController,
    IptablesMangleMark
)
from .._traffic_direction import TrafficDirection


@six.add_metaclass(abc.ABCMeta)
class ShaperInterface(object):

    @abc.abstractproperty
    def algorithm_name(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def make_qdisc(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def add_rate(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def add_filter(self):  # pragma: no cover
        pass


class AbstractShaper(ShaperInterface):

    __FILTER_IPTABLES_MARK_ID_OFFSET = 100

    @property
    def dev(self):
        return "dev {:s}".format(self._tc_obj.get_tc_device())

    def __init__(self, tc_obj):
        self._tc_obj = tc_obj

    def _is_use_iptables(self):
        return all([
            self._tc_obj.is_enable_iptables,
            self._tc_obj.direction == TrafficDirection.OUTGOING,
        ])

    def _get_network_direction_str(self):
        if self._tc_obj.direction == TrafficDirection.OUTGOING:
            return "dst"

        if self._tc_obj.direction == TrafficDirection.INCOMING:
            return "src"

        raise ValueError("unknown direction: {}".format(self.direction))

    def _get_unique_mangle_mark_id(self):
        mark_id = (
            IptablesMangleController.get_unique_mark_id() +
            self.__FILTER_IPTABLES_MARK_ID_OFFSET)

        self.__add_mangle_mark(mark_id)

        return mark_id

    def __add_mangle_mark(self, mark_id):
        dst_network = None
        src_network = None

        if self._tc_obj.direction == TrafficDirection.OUTGOING:
            dst_network = self._tc_obj.network
            if dataproperty.is_empty_string(self._tc_obj.src_network):
                chain = "OUTPUT"
            else:
                src_network = self._tc_obj.src_network
                chain = "PREROUTING"
        elif self._tc_obj.direction == TrafficDirection.INCOMING:
            src_network = self._tc_obj.network
            chain = "INPUT"

        IptablesMangleController.add(IptablesMangleMark(
            mark_id=mark_id, source=src_network, destination=dst_network,
            chain=chain))
