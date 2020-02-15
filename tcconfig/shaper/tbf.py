"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import typepy
from humanreadable import ParameterError
from subprocrunner import SubprocessRunner

from .._common import logging_context, run_command_helper
from .._const import ShapingAlgorithm, TcSubCommand, TrafficDirection
from .._network import get_anywhere_network, get_upper_limit_rate
from ._interface import AbstractShaper


class TbfShaper(AbstractShaper):

    __NETEM_QDISC_MAJOR_ID_OFFSET = 10

    __MIN_BUFFER_BYTE = 1600

    __OUT_DEVICE_QDISC_MINOR_ID = 1
    __IN_DEVICE_QDISC_MINOR_ID = 3

    @property
    def algorithm_name(self):
        return ShapingAlgorithm.TBF

    def _get_qdisc_minor_id(self):
        if self._tc_obj.direction == TrafficDirection.OUTGOING:
            return self.__OUT_DEVICE_QDISC_MINOR_ID

        if self._tc_obj.direction == TrafficDirection.INCOMING:
            return self.__IN_DEVICE_QDISC_MINOR_ID

        raise ParameterError(
            "unknown direction", expected=TrafficDirection.LIST, value=self._tc_obj.direction
        )

    def _get_netem_qdisc_major_id(self, base_id):
        if self._tc_obj.direction == TrafficDirection.OUTGOING:
            direction_offset = 0
        elif self._tc_obj.direction == TrafficDirection.INCOMING:
            direction_offset = 1

        return base_id + self.__NETEM_QDISC_MAJOR_ID_OFFSET + direction_offset

    def _make_qdisc(self):
        base_command = self._tc_obj.get_tc_command(TcSubCommand.QDISC)
        handle = "{:s}:".format(self._tc_obj.qdisc_major_id_str)

        return run_command_helper(
            " ".join([base_command, self._dev, "root", "handle {:s}".format(handle), "prio"]),
            ignore_error_msg_regexp=self._tc_obj.REGEXP_FILE_EXISTS,
            notice_msg=self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': prio qdisc already exists "
                "({dev:s}, algo={algorithm:s}, handle={handle:s}).".format(
                    command=base_command,
                    dev=self._dev,
                    algorithm=self.algorithm_name,
                    handle=handle,
                )
            ),
        )

    def _add_rate(self):
        try:
            self._tc_obj.netem_param.validate_bandwidth_rate()
        except ParameterError:
            return 0

        base_command = self._tc_obj.get_tc_command(TcSubCommand.QDISC)
        parent = "{:x}:{:d}".format(
            self._get_netem_qdisc_major_id(self._tc_obj.qdisc_major_id), self._get_qdisc_minor_id()
        )
        handle = "{:d}:".format(20)
        upper_limit_rate = get_upper_limit_rate(self._tc_device)

        bandwidth = self._tc_obj.netem_param.bandwidth_rate
        if bandwidth is None:
            bandwidth = upper_limit_rate

        command = " ".join(
            [
                base_command,
                self._dev,
                "parent {:s}".format(parent),
                "handle {:s}".format(handle),
                self.algorithm_name,
                "rate {}kbit".format(bandwidth.kilo_bps),
                "buffer {:d}".format(
                    max(int(bandwidth.kilo_bps), self.__MIN_BUFFER_BYTE)
                ),  # [byte]
                "limit 10000",
            ]
        )

        run_command_helper(
            command,
            ignore_error_msg_regexp=self._tc_obj.REGEXP_FILE_EXISTS,
            notice_msg=self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': qdisc already exists ({dev:s}, algo={algorithm:s}, "
                "parent={parent:s}, handle={handle:s}).".format(
                    command=base_command,
                    dev=self._dev,
                    algorithm=self.algorithm_name,
                    parent=parent,
                    handle=handle,
                )
            ),
        )

        self.__set_pre_network_filter()

    def set_shaping(self):
        with logging_context("_make_qdisc"):
            self._make_qdisc()

        with logging_context("_set_netem"):
            self._set_netem()

        with logging_context("_add_rate"):
            self._add_rate()

        with logging_context("_add_filter"):
            self._add_filter()

        return 0

    def __set_pre_network_filter(self):
        if self._is_use_iptables():
            return 0

        if all(
            [
                typepy.is_null_string(self._tc_obj.dst_network),
                not typepy.Integer(self._tc_obj.dst_port).is_type(),
            ]
        ):
            flowid = "{:s}:{:d}".format(self._tc_obj.qdisc_major_id_str, self._get_qdisc_minor_id())
        else:
            flowid = "{:s}:2".format(self._tc_obj.qdisc_major_id_str)

        return SubprocessRunner(
            " ".join(
                [
                    self._tc_obj.get_tc_command(TcSubCommand.FILTER),
                    self._dev,
                    "protocol {:s}".format(self._tc_obj.protocol),
                    "parent {:s}:".format(self._tc_obj.qdisc_major_id_str),
                    "prio 2 u32 match {:s} {:s} {:s}".format(
                        self._tc_obj.protocol,
                        self._get_network_direction_str(),
                        get_anywhere_network(self._tc_obj.ip_version),
                    ),
                    "flowid {:s}".format(flowid),
                ]
            )
        ).run()
