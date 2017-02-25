# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import abc

import six
from subprocrunner import SubprocessRunner
import typepy

from .._common import run_command_helper
from .._const import ANYWHERE_NETWORK
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
    def get_qdisc_minor_id(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def get_netem_qdisc_major_id(self, base_id):  # pragma: no cover
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

    @abc.abstractmethod
    def set_shaping(self):  # pragma: no cover
        pass


class AbstractShaper(ShaperInterface):

    @property
    def tc_device(self):
        return "{:s}".format(self._tc_obj.get_tc_device())

    @property
    def dev(self):
        return "dev {:s}".format(self.tc_device)

    def __init__(self, tc_obj):
        self._tc_obj = tc_obj

    def set_netem(self):
        parent = "{:s}:{:d}".format(
            self._tc_obj.qdisc_major_id_str, self.get_qdisc_minor_id())
        handle = "{:x}".format(
            self.get_netem_qdisc_major_id(self._tc_obj.qdisc_major_id))
        command_list = [
            "tc qdisc add",
            "dev {:s}".format(self._tc_obj.get_tc_device()),
            "parent {:s}".format(parent),
            "handle {:s}:".format(handle),
            "netem",
        ]

        if self._tc_obj.packet_loss_rate > 0:
            command_list.append(
                "loss {:f}%".format(self._tc_obj.packet_loss_rate))

        if self._tc_obj.latency_ms > 0:
            command_list.append("delay {:f}ms".format(self._tc_obj.latency_ms))

            if self._tc_obj.latency_distro_ms > 0:
                command_list.append("{:f}ms distribution normal".format(
                    self._tc_obj.latency_distro_ms))

        if self._tc_obj.corruption_rate > 0:
            command_list.append(
                "corrupt {:f}%".format(self._tc_obj.corruption_rate))

        return run_command_helper(
            " ".join(command_list), self._tc_obj.REGEXP_FILE_EXISTS,
            self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to add qdisc: netem qdisc already exists "
                "(dev={:s}, parent={:s}, handle={:s})".format(
                    self._tc_obj.get_tc_device(), parent, handle)))

    def add_filter(self):
        command_list = [
            "tc filter add",
            self.dev,
            "protocol ip",
            "parent {:s}:".format(self._tc_obj.qdisc_major_id_str),
            "prio 1",
        ]

        if self._is_use_iptables():
            command_list.append(
                "handle {:d} fw".format(self._get_unique_mangle_mark_id()))
        else:
            if typepy.is_null_string(self._tc_obj.network):
                network = ANYWHERE_NETWORK
            else:
                network = self._tc_obj.network

            command_list.extend([
                "u32",
                "match ip {:s} {:s}".format(
                    self._get_network_direction_str(), network),
            ])

            if self._tc_obj.port is not None:
                command_list.append(
                    "match ip dport {:d} 0xffff".format(self._tc_obj.port))

        command_list.append("flowid {:s}:{:d}".format(
            self._tc_obj.qdisc_major_id_str,
            self.get_qdisc_minor_id()))

        return SubprocessRunner(" ".join(command_list)).run()

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
        mark_id = IptablesMangleController.get_unique_mark_id()

        self.__add_mangle_mark(mark_id)

        return mark_id

    def __add_mangle_mark(self, mark_id):
        dst_network = None
        src_network = None

        if self._tc_obj.direction == TrafficDirection.OUTGOING:
            dst_network = self._tc_obj.network
            if typepy.is_null_string(self._tc_obj.src_network):
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
