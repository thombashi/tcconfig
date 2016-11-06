# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
import re

import dataproperty
from dataproperty import (
    IntegerType,
    FloatType
)
import six
from subprocrunner import logger
from subprocrunner import SubprocessRunner

from ._common import (
    ANYWHERE_NETWORK,
    sanitize_network,
    verify_network_interface
)
from ._converter import Humanreadable
from ._error import (
    TcCommandExecutionError,
    NetworkInterfaceNotFoundError
)
from ._iptables import (
    IptablesMangleController,
    IptablesMangleMark
)
from ._traffic_direction import TrafficDirection


def _validate_within_min_max(param_name, value, min_value, max_value):
    if value is None:
        return

    if value > max_value:
        raise ValueError(
            "{:s} is too high: expected<={:f}[%], value={:f}[%]".format(
                param_name, max_value, value))

    if value < min_value:
        raise ValueError(
            "{:s} is too low: expected>={:f}[%], value={:f}[%]".format(
                param_name, min_value, value))


class TrafficControl(object):
    __NETEM_QDISC_MAJOR_ID_OFFSET = 10
    __FILTER_IPTABLES_MARK_ID_OFFSET = 100

    __OUT_DEVICE_QDISC_MINOR_ID = 1
    __IN_DEVICE_QDISC_MINOR_ID = 3

    __MIN_PACKET_LOSS_RATE = 0  # [%]
    __MAX_PACKET_LOSS_RATE = 99  # [%]

    __MIN_LATENCY_MS = 0  # [millisecond]
    __MAX_LATENCY_MS = 10000  # [millisecond]

    __MIN_CORRUPTION_RATE = 0  # [%]
    __MAX_CORRUPTION_RATE = 99  # [%]

    __MIN_BUFFER_BYTE = 1600

    __MIN_PORT = 0
    __MAX_PORT = 65535

    __REGEXP_FILE_EXISTS = re.compile("RTNETLINK answers: File exists")

    __EXISTS_MSG_TEMPLATE = (
        "{:s} "
        "execute with --overwrite option if you want to overwrite "
        "the existing settings.")

    @property
    def ifb_device(self):
        return "ifb{:d}".format(self.__get_device_qdisc_major_id())

    @property
    def direction(self):
        return self.__direction

    @property
    def bandwidth_rate(self):
        return self.__bandwidth_rate

    @property
    def latency_ms(self):
        return self.__latency_ms

    @property
    def latency_distro_ms(self):
        return self.__latency_distro_ms

    @property
    def packet_loss_rate(self):
        return self.__packet_loss_rate

    @property
    def corruption_rate(self):
        return self.__corruption_rate

    @property
    def network(self):
        return self.__network

    @property
    def src_network(self):
        return self.__src_network

    @property
    def port(self):
        return self.__port

    @property
    def is_enable_iptables(self):
        return self.__is_enable_iptables

    def __init__(
            self, device,
            direction=None, bandwidth_rate=None,
            latency_ms=None, latency_distro_ms=None,
            packet_loss_rate=None, corruption_rate=None,
            network=None, port=None,
            src_network=None,
            is_enable_iptables=True,
    ):
        self.__device = device

        self.__direction = direction
        self.__bandwidth_rate = bandwidth_rate  # bandwidth string [G/M/K bps]
        self.__latency_ms = latency_ms  # [milliseconds]
        self.__latency_distro_ms = latency_distro_ms  # [milliseconds]
        self.__packet_loss_rate = packet_loss_rate  # [%]
        self.__corruption_rate = corruption_rate  # [%]
        self.__network = network
        self.__src_network = src_network
        self.__port = port
        self.__is_enable_iptables = is_enable_iptables

        IptablesMangleController.enable = is_enable_iptables

    def validate(self):
        verify_network_interface(self.__device)
        self.__validate_netem_parameter()
        self.__network = sanitize_network(self.network)
        self.__src_network = sanitize_network(self.src_network)
        self.__validate_port()

    def set_tc(self):
        self.__setup_ifb()

        qdisc_major_id = self.__get_device_qdisc_major_id()
        self.__make_qdisc(qdisc_major_id)
        self.__set_pre_network_filter(qdisc_major_id)
        self.__set_netem(qdisc_major_id)
        self.__set_network_filter(qdisc_major_id)
        self.__set_rate(qdisc_major_id)

    def delete_tc(self):
        result_list = []

        returncode = self.__run(
            "tc qdisc del dev {:s} root".format(self.__device),
            re.compile("RTNETLINK answers: No such file or directory"),
            "failed to delete qdisc: no qdisc for outgoing packets")
        result_list.append(returncode == 0)

        returncode = self.__run(
            "tc qdisc del dev {:s} ingress".format(self.__device),
            re.compile("|".join([
                "RTNETLINK answers: Invalid argument",
                "RTNETLINK answers: No such file or directory",
            ])),
            "failed to delete qdisc: no qdisc for incomming packets")
        result_list.append(returncode == 0)

        try:
            result_list.append(self.__delete_ifb_device() == 0)
        except NetworkInterfaceNotFoundError as e:
            logger.debug(e)
            result_list.append(False)

        IptablesMangleController.clear()

        return any(result_list)

    def __is_use_iptables(self):
        return all([
            self.is_enable_iptables,
            self.direction == TrafficDirection.OUTGOING,
        ])

    def __validate_bandwidth_rate(self):
        if dataproperty.is_empty_string(self.bandwidth_rate):
            return

        rate = Humanreadable().humanreadable_to_byte(self.bandwidth_rate)
        if rate <= 0:
            raise ValueError("rate must be greater than zero")

    def __validate_network_delay(self):
        _validate_within_min_max(
            "latency_ms",
            self.latency_ms,
            self.__MIN_LATENCY_MS, self.__MAX_LATENCY_MS)

        _validate_within_min_max(
            "latency_distro_ms",
            self.latency_distro_ms,
            self.__MIN_LATENCY_MS, self.__MAX_LATENCY_MS)

    def __validate_packet_loss_rate(self):
        _validate_within_min_max(
            "packet_loss_rate",
            self.packet_loss_rate,
            self.__MIN_PACKET_LOSS_RATE, self.__MAX_PACKET_LOSS_RATE)

    def __validate_curruption_rate(self):
        _validate_within_min_max(
            "corruption_rate",
            self.corruption_rate,
            self.__MIN_CORRUPTION_RATE, self.__MAX_CORRUPTION_RATE)

    def __validate_netem_parameter(self):
        self.__validate_bandwidth_rate()
        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.__validate_curruption_rate()

        param_list = [
            self.bandwidth_rate,
            self.latency_ms,
            self.packet_loss_rate,
            self.corruption_rate,
        ]

        if all([
            not FloatType(value).is_type() or value == 0
            for value in param_list
        ]):
            raise ValueError("there is no valid net emulation parameter")

    def __validate_port(self):
        _validate_within_min_max(
            "port", self.port, self.__MIN_PORT, self.__MAX_PORT)

    def __make_qdisc(self, qdisc_major_id):
        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "root",
            "handle {:x}:".format(qdisc_major_id),
            "prio",
        ]

        return self.__run(
            " ".join(command_list), self.__REGEXP_FILE_EXISTS,
            self.__EXISTS_MSG_TEMPLATE.format(
                "failed to add qdisc: prio qdisc already exists."))

    def __get_tc_device(self):
        if self.direction == TrafficDirection.OUTGOING:
            return self.__device

        if self.direction == TrafficDirection.INCOMING:
            return self.ifb_device

        raise ValueError("unknown direction: " + self.direction)

    def __get_network_direction_str(self):
        if self.direction == TrafficDirection.OUTGOING:
            return "dst"

        if self.direction == TrafficDirection.INCOMING:
            return "src"

        raise ValueError("unknown direction: " + self.direction)

    def __get_device_qdisc_major_id(self):
        import hashlib

        base_device_hash = hashlib.md5(six.b(self.__device)).hexdigest()[:3]
        device_hash_prefix = "1"

        return int(device_hash_prefix + base_device_hash, 16)

    def __get_netem_qdisc_major_id(self, base_qdisc_major_id):
        if self.direction == TrafficDirection.OUTGOING:
            direction_offset = 0
        elif self.direction == TrafficDirection.INCOMING:
            direction_offset = 1

        return (
            base_qdisc_major_id +
            self.__NETEM_QDISC_MAJOR_ID_OFFSET +
            direction_offset)

    def __get_qdisc_minor_id(self):
        if self.direction == TrafficDirection.OUTGOING:
            return self.__OUT_DEVICE_QDISC_MINOR_ID

        if self.direction == TrafficDirection.INCOMING:
            return self.__IN_DEVICE_QDISC_MINOR_ID

        raise ValueError("unknown direction: " + self.direction)

    def __setup_ifb(self):
        if self.direction != TrafficDirection.INCOMING:
            return 0

        if dataproperty.is_empty_string(self.ifb_device):
            return -1

        return_code = 0

        command = "modprobe ifb"
        return_code |= SubprocessRunner(command).run()

        return_code |= self.__run(
            "ip link add {:s} type ifb".format(self.ifb_device),
            self.__REGEXP_FILE_EXISTS,
            self.__EXISTS_MSG_TEMPLATE.format(
                "failed to add ip link: ip link already exists."))

        command = "ip link set dev {:s} up".format(self.ifb_device)
        return_code |= SubprocessRunner(command).run()

        return_code |= self.__run(
            "tc qdisc add dev {:s} ingress".format(self.__device),
            self.__REGEXP_FILE_EXISTS,
            self.__EXISTS_MSG_TEMPLATE.format(
                "failed to add qdisc: ingress qdisc already exists."))

        command_list = [
            "tc filter add",
            "dev " + self.__device,
            "parent ffff: protocol ip u32 match u32 0 0",
            "flowid {:x}:".format(self.__get_device_qdisc_major_id()),
            "action mirred egress redirect",
            "dev " + self.ifb_device,
        ]
        return_code |= SubprocessRunner(" ".join(command_list)).run()

        return return_code

    def __set_pre_network_filter(self, qdisc_major_id):
        if self.__is_use_iptables():
            return 0

        if all([
            dataproperty.is_empty_string(self.network),
            not IntegerType(self.port).is_type(),
        ]):
            flowid = "{:x}:{:d}".format(
                qdisc_major_id, self.__get_qdisc_minor_id())
        else:
            flowid = "{:x}:2".format(qdisc_major_id)

        command_list = [
            "tc filter add",
            "dev " + self.__get_tc_device(),
            "protocol ip",
            "parent {:x}:".format(qdisc_major_id),
            "prio 2 u32 match ip {:s} {:s}".format(
                self.__get_network_direction_str(),
                ANYWHERE_NETWORK),
            "flowid " + flowid,
        ]

        return SubprocessRunner(" ".join(command_list)).run()

    def __set_netem(self, qdisc_major_id):
        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "parent {:x}:{:d}".format(
                qdisc_major_id, self.__get_qdisc_minor_id()),
            "handle {:x}:".format(
                self.__get_netem_qdisc_major_id(qdisc_major_id)),
            "netem",
        ]
        if self.packet_loss_rate > 0:
            command_list.append("loss {:f}%".format(self.packet_loss_rate))
        if self.latency_ms > 0:
            command_list.append("delay {:f}ms".format(self.latency_ms))

            if self.latency_distro_ms > 0:
                command_list.append("{:f}ms distribution normal".format(
                    self.latency_distro_ms))

        if self.corruption_rate > 0:
            command_list.append("corrupt {:f}%".format(self.corruption_rate))

        return self.__run(
            " ".join(command_list), self.__REGEXP_FILE_EXISTS,
            self.__EXISTS_MSG_TEMPLATE.format(
                "failed to add qdisc: netem qdisc already exists."))

    def __set_network_filter(self, qdisc_major_id):
        command_list = [
            "tc filter add",
            "dev " + self.__get_tc_device(),
            "protocol ip",
            "parent {:x}:".format(qdisc_major_id),
            "prio 1",
        ]

        if self.__is_use_iptables():
            mark_id = (
                IptablesMangleController.get_unique_mark_id() +
                self.__FILTER_IPTABLES_MARK_ID_OFFSET)
            command_list.append("handle {:d} fw".format(mark_id))

            self.__add_mangle_mark(mark_id)
        else:
            if all([
                dataproperty.is_empty_string(self.network),
                self.port is None,
            ]):
                return 0

            command_list.append("u32")
            if dataproperty.is_not_empty_string(self.network):
                command_list.append("match ip {:s} {:s}".format(
                    self.__get_network_direction_str(), self.network))
            if self.port is not None:
                command_list.append(
                    "match ip dport {:d} 0xffff".format(self.port))

        command_list.append("flowid {:x}:{:d}".format(
            qdisc_major_id, self.__get_qdisc_minor_id()))

        return SubprocessRunner(" ".join(command_list)).run()

    def __add_mangle_mark(self, mark_id):
        dst_network = None
        src_network = None

        if self.direction == TrafficDirection.OUTGOING:
            dst_network = self.network
            if dataproperty.is_empty_string(self.src_network):
                chain = "OUTPUT"
            else:
                src_network = self.src_network
                chain = "PREROUTING"
        elif self.direction == TrafficDirection.INCOMING:
            src_network = self.network
            chain = "INPUT"

        IptablesMangleController.add(IptablesMangleMark(
            mark_id=mark_id, source=src_network, destination=dst_network,
            chain=chain))

    def __set_rate(self, qdisc_major_id):
        if dataproperty.is_empty_string(self.bandwidth_rate):
            return 0

        rate_kbps = Humanreadable(kilo_size=1000).humanreadable_to_kilobyte(
            self.bandwidth_rate)
        if rate_kbps <= 0:
            raise ValueError("rate must be greater than zero")

        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "parent {:x}:{:d}".format(
                self.__get_netem_qdisc_major_id(qdisc_major_id),
                self.__get_qdisc_minor_id()),
            "handle 20:",
            "tbf",
            "rate {:f}kbit".format(rate_kbps),
            "buffer {:d}".format(
                max(rate_kbps, self.__MIN_BUFFER_BYTE)),  # [byte]
            "limit 10000",
        ]

        return SubprocessRunner(" ".join(command_list)).run()

    def __delete_ifb_device(self):
        verify_network_interface(self.ifb_device)

        command_list = [
            "tc qdisc del dev {:s} root".format(self.ifb_device),
            "ip link set dev {:s} down".format(self.ifb_device),
            "ip link delete {:s} type ifb".format(self.ifb_device),
        ]

        if all([
            SubprocessRunner(command).run() != 0
            for command in command_list
        ]):
            return 2

        return 0

    @staticmethod
    def __run(command, regexp, message):
        proc = SubprocessRunner(command, regexp)
        if proc.run() == 0:
            return 0

        match = regexp.search(proc.stderr)
        if match is None:
            return proc.returncode

        logger.notice(message)

        return proc.returncode
