# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

from subprocrunner import SubprocessRunner
import typepy

from .._common import (
    logging_context,
    get_anywhere_network,
    run_command_helper,
)
from .._const import (
    Tc,
    TrafficDirection,
)
from .._error import InvalidParameterError
from ._interface import AbstractShaper


class TbfShaper(AbstractShaper):

    __NETEM_QDISC_MAJOR_ID_OFFSET = 10

    __MIN_BUFFER_BYTE = 1600

    __OUT_DEVICE_QDISC_MINOR_ID = 1
    __IN_DEVICE_QDISC_MINOR_ID = 3

    @property
    def algorithm_name(self):
        return "tbf"

    def get_qdisc_minor_id(self):
        if self._tc_obj.direction == TrafficDirection.OUTGOING:
            return self.__OUT_DEVICE_QDISC_MINOR_ID

        if self._tc_obj.direction == TrafficDirection.INCOMING:
            return self.__IN_DEVICE_QDISC_MINOR_ID

        raise ValueError("unknown direction: {}".format(self.direction))

    def get_netem_qdisc_major_id(self, base_id):
        if self._tc_obj.direction == TrafficDirection.OUTGOING:
            direction_offset = 0
        elif self._tc_obj.direction == TrafficDirection.INCOMING:
            direction_offset = 1

        return (
            base_id +
            self.__NETEM_QDISC_MAJOR_ID_OFFSET +
            direction_offset)

    def make_qdisc(self):
        base_command = self._tc_obj.get_tc_command(Tc.Subcommand.QDISC)
        if base_command is None:
            return 0

        handle = "{:s}:".format(self._tc_obj.qdisc_major_id_str)

        return run_command_helper(
            " ".join([
                base_command, self.dev, "root",
                "handle {:s}".format(handle), "prio",
            ]),
            self._tc_obj.REGEXP_FILE_EXISTS,
            self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': prio qdisc already exists "
                "({dev:s}, algo={algorithm:s}, handle={handle:s}).".format(
                    command=base_command, dev=self.dev,
                    algorithm=self.algorithm_name, handle=handle))
        )

    def add_rate(self):
        try:
            self._tc_obj.validate_bandwidth_rate()
        except InvalidParameterError:
            return 0

        base_command = self._tc_obj.get_tc_command(Tc.Subcommand.QDISC)
        if base_command is None:
            return 0

        parent = "{:x}:{:d}".format(
            self.get_netem_qdisc_major_id(self._tc_obj.qdisc_major_id),
            self.get_qdisc_minor_id())
        handle = "{:d}:".format(20)

        command = " ".join([
            base_command,
            self.dev,
            "parent {:s}".format(parent),
            "handle {:s}".format(handle),
            self.algorithm_name,
            "rate {:f}kbit".format(self._tc_obj.bandwidth_rate),
            "buffer {:d}".format(
                max(int(self._tc_obj.bandwidth_rate), self.__MIN_BUFFER_BYTE)
            ),  # [byte]
            "limit 10000",
        ])

        run_command_helper(
            command,
            self._tc_obj.REGEXP_FILE_EXISTS,
            self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': qdisc already exists "
                "({dev:s}, algo={algorithm:s}, parent={parent:s}, "
                "handle={handle:s}).".format(
                    command=base_command, dev=self.dev,
                    algorithm=self.algorithm_name, parent=parent,
                    handle=handle))
        )

        self.__set_pre_network_filter()

    def set_shaping(self):
        with logging_context("make_qdisc"):
            self.make_qdisc()

        with logging_context("set_netem"):
            self.set_netem()

        with logging_context("add_rate"):
            self.add_rate()

        with logging_context("add_filter"):
            self.add_filter()

        return 0

    def __set_pre_network_filter(self):
        if self._is_use_iptables():
            return 0

        if all([
            typepy.is_null_string(self._tc_obj.dst_network),
            not typepy.type.Integer(self._tc_obj.dst_port).is_type(),
        ]):
            flowid = "{:s}:{:d}".format(
                self._tc_obj.qdisc_major_id_str,
                self.get_qdisc_minor_id())
        else:
            flowid = "{:s}:2".format(self._tc_obj.qdisc_major_id_str)

        return SubprocessRunner(" ".join([
            self._tc_obj.get_tc_command(Tc.Subcommand.FILTER),
            self.dev,
            "protocol {:s}".format(self._tc_obj.protocol),
            "parent {:s}:".format(self._tc_obj.qdisc_major_id_str),
            "prio 2 u32 match {:s} {:s} {:s}".format(
                self._tc_obj.protocol,
                self._get_network_direction_str(),
                get_anywhere_network(self._tc_obj.ip_version)),
            "flowid {:s}".format(flowid),
        ])).run()
