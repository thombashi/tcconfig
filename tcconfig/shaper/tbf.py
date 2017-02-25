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
    run_command_helper,
)
from .._const import ANYWHERE_NETWORK
from .._error import EmptyParameterError
from .._traffic_direction import TrafficDirection
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
        handle = "{:s}:".format(self._tc_obj.qdisc_major_id_str)
        command = " ".join([
            "tc qdisc add", self.dev, "root",
            "handle {:s}".format(handle), "prio",
        ])

        return run_command_helper(
            command,
            self._tc_obj.REGEXP_FILE_EXISTS,
            self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to add qdisc: prio qdisc already exists "
                "({:s}, algo={:s}, handle={:s}).".format(
                    self.dev, self.algorithm_name, handle))
        )

    def add_rate(self):
        try:
            self._tc_obj.validate_bandwidth_rate()
        except EmptyParameterError:
            return 0

        parent = "{:x}:{:d}".format(
            self.get_netem_qdisc_major_id(self._tc_obj.qdisc_major_id),
            self.get_qdisc_minor_id())
        handle = "{:d}:".format(20)

        command = " ".join([
            "tc qdisc add",
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
                "failed to add qdisc: qdisc already exists "
                "({:s}, algo={:s}, parent={:s}, handle={:s}).".format(
                    self.dev, self.algorithm_name, parent, handle))
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

    def __set_pre_network_filter(self):
        if self._is_use_iptables():
            return 0

        if all([
            typepy.is_null_string(self._tc_obj.network),
            not typepy.type.Integer(self._tc_obj.port).is_type(),
        ]):
            flowid = "{:s}:{:d}".format(
                self._tc_obj.qdisc_major_id_str,
                self.get_qdisc_minor_id())
        else:
            flowid = "{:s}:2".format(self._tc_obj.qdisc_major_id_str)

        command = " ".join([
            "tc filter add",
            self.dev,
            "protocol ip",
            "parent {:s}:".format(self._tc_obj.qdisc_major_id_str),
            "prio 2 u32 match ip {:s} {:s}".format(
                self._get_network_direction_str(),
                ANYWHERE_NETWORK),
            "flowid {:s}".format(flowid),
        ])

        return SubprocessRunner(command).run()
