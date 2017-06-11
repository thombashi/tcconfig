# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import abc

import six
import subprocrunner
import typepy

from .._common import (
    get_anywhere_network,
    run_command_helper,
)
from .._const import (
    Tc,
    TrafficDirection,
)
from .._iptables import IptablesMangleMark


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
        base_command = self._tc_obj.get_tc_command(Tc.Subcommand.QDISC)
        if base_command is None:
            return 0

        parent = "{:s}:{:d}".format(
            self._tc_obj.qdisc_major_id_str, self.get_qdisc_minor_id())
        handle = "{:x}".format(
            self.get_netem_qdisc_major_id(self._tc_obj.qdisc_major_id))
        command_item_list = [
            base_command,
            "dev {:s}".format(self._tc_obj.get_tc_device()),
            "parent {:s}".format(parent),
            "handle {:s}:".format(handle),
            "netem",
        ]

        if self._tc_obj.packet_loss_rate > 0:
            command_item_list.append(
                "loss {:f}%".format(self._tc_obj.packet_loss_rate))

        if self._tc_obj.packet_duplicate_rate > 0:
            command_item_list.append(
                "duplicate {:f}%".format(self._tc_obj.packet_duplicate_rate))

        if self._tc_obj.latency_ms > 0:
            command_item_list.append(
                "delay {}ms".format(self._tc_obj.latency_ms))

            if self._tc_obj.latency_distro_ms > 0:
                command_item_list.append("{}ms distribution normal".format(
                    self._tc_obj.latency_distro_ms))

        if self._tc_obj.corruption_rate > 0:
            command_item_list.append(
                "corrupt {:f}%".format(self._tc_obj.corruption_rate))

        if self._tc_obj.reordering_rate > 0:
            command_item_list.append(
                "reorder {:f}%".format(self._tc_obj.reordering_rate))

        return run_command_helper(
            " ".join(command_item_list),
            self._tc_obj.REGEXP_FILE_EXISTS,
            self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': netem qdisc already exists "
                "(dev={dev:s}, parent={parent:s}, handle={handle:s})".format(
                    command=base_command, dev=self._tc_obj.get_tc_device(),
                    parent=parent, handle=handle)))

    def add_filter(self):
        base_command = self._tc_obj.get_tc_command(Tc.Subcommand.FILTER)
        if base_command is None:
            return 0

        command_item_list = [
            base_command,
            self.dev,
            "protocol {:s}".format(self._tc_obj.protocol),
            "parent {:s}:".format(self._tc_obj.qdisc_major_id_str),
            "prio 1",
        ]

        if self._is_use_iptables():
            command_item_list.append(
                "handle {:d} fw".format(self._get_unique_mangle_mark_id()))
        else:
            if typepy.is_null_string(self._tc_obj.dst_network):
                dst_network = get_anywhere_network(self._tc_obj.ip_version)
            else:
                dst_network = self._tc_obj.dst_network

            command_item_list.extend([
                "u32",
                "match {:s} {:s} {:s}".format(
                    self._tc_obj.protocol_match,
                    self._get_network_direction_str(),
                    dst_network),
            ])

            if self._tc_obj.src_port:
                command_item_list.append(
                    "match {:s} sport {:d} 0xffff".format(
                        self._tc_obj.protocol_match, self._tc_obj.src_port))

            if self._tc_obj.dst_port:
                command_item_list.append(
                    "match {:s} dport {:d} 0xffff".format(
                        self._tc_obj.protocol_match, self._tc_obj.dst_port))

        command_item_list.append("flowid {:s}:{:d}".format(
            self._tc_obj.qdisc_major_id_str,
            self.get_qdisc_minor_id()))

        return subprocrunner.SubprocessRunner(
            " ".join(command_item_list)).run()

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
        mark_id = self._tc_obj.iptables_ctrl.get_unique_mark_id()

        self.__add_mangle_mark(mark_id)

        return mark_id

    def __add_mangle_mark(self, mark_id):
        dst_network = None
        src_network = None

        if self._tc_obj.direction == TrafficDirection.OUTGOING:
            dst_network = self._tc_obj.dst_network
            if typepy.is_null_string(self._tc_obj.src_network):
                chain = "OUTPUT"
            else:
                src_network = self._tc_obj.src_network
                chain = "PREROUTING"
        elif self._tc_obj.direction == TrafficDirection.INCOMING:
            src_network = self._tc_obj.dst_network
            chain = "INPUT"

        self._tc_obj.iptables_ctrl.add(IptablesMangleMark(
            ip_version=self._tc_obj.ip_version, mark_id=mark_id,
            source=src_network, destination=dst_network, chain=chain))
