# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division

import dataproperty
import ipaddress
import six
from subprocrunner import SubprocessRunner

from .parser import TcFilterParser
from .parser import TcQdiscParser
from ._common import verify_network_interface
from ._converter import Humanreadable
from ._error import TcCommandExecutionError


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


class TrafficDirection(object):
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    LIST = [OUTGOING, INCOMING]


class TrafficControl(object):
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

    @property
    def ifb_device(self):
        return "ifb{:d}".format(self.__get_device_qdisc_major_id())

    def __init__(self, device):
        self.__device = device

        self.direction = None
        self.bandwidth_rate = None  # bandwidth string [G/M/K bps]
        self.latency_ms = None  # [milliseconds]
        self.latency_distro_ms = None  # [milliseconds]
        self.packet_loss_rate = None  # [%]
        self.curruption_rate = None  # [%]
        self.network = None
        self.port = None

    def validate(self):
        verify_network_interface(self.__device)
        self.__validate_bandwidth_rate()
        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.__validate_curruption_rate()
        self.network = self.__sanitize_network(self.network)
        self.__validate_port()

    def __get_device_qdisc_major_id(self):
        import hashlib

        base_device_hash = hashlib.md5(six.b(self.__device)).hexdigest()[:3]
        device_hash_prefix = "1"

        return int(device_hash_prefix + base_device_hash, 16)

    def set_tc(self):
        self.__setup_ifb()

        qdisc_major_id = self.__get_device_qdisc_major_id()
        self.__make_qdisc(qdisc_major_id)
        self.__set_pre_network_filter(qdisc_major_id)
        self.__set_netem(qdisc_major_id)
        self.__set_network_filter(qdisc_major_id)
        self.__set_rate(qdisc_major_id)

    def delete_tc(self):
        return_code_list = []
        command_list = [
            "tc qdisc del dev {:s} root".format(self.__device),
            "tc qdisc del dev {:s} ingress".format(self.__device),
            "tc qdisc del dev {:s} root".format(self.ifb_device),
            "ip link set dev {:s} down".format(self.ifb_device),
            "ip link delete {:s} type ifb".format(self.ifb_device),
        ]

        for command in command_list:
            return_code_list.append(SubprocessRunner(command).run() != 0)

        return -1 if all(return_code_list) else 0

    def get_tc_parameter(self):
        return {
            self.__device: {
                TrafficDirection.OUTGOING: self.__get_filter(self.__device),
                TrafficDirection.INCOMING: self.__get_filter(
                    self.__get_ifb_from_device(self.__device)),
            },
        }

    def __setup_ifb(self):
        if self.direction != TrafficDirection.INCOMING:
            return

        if dataproperty.is_empty_string(self.ifb_device):
            return

        return_code = 0

        command = "modprobe ifb"
        return_code |= SubprocessRunner(command).run()

        command = "ip link add {:s} type ifb".format(self.ifb_device)
        return_code |= SubprocessRunner(command).run()

        command = "ip link set dev {:s} up".format(self.ifb_device)
        return_code |= SubprocessRunner(command).run()

        command = "tc qdisc add dev {:s} ingress".format(self.__device)
        return_code |= SubprocessRunner(command).run()

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
            "curruption_rate",
            self.curruption_rate,
            self.__MIN_CORRUPTION_RATE, self.__MAX_CORRUPTION_RATE)

    @staticmethod
    def __sanitize_network(network):
        """
        :return: Network string
        :rtype: str
        :raises ValueError: if the network string is invalid.
        """

        if dataproperty.is_empty_string(network):
            return ""

        try:
            ipaddress.IPv4Address(six.u(network))
            return network + "/32"
        except ipaddress.AddressValueError:
            pass

        ipaddress.IPv4Network(six.u(network))  # validate network str

        return network

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

        return SubprocessRunner(" ".join(command_list)).run()

    def __get_tc_device(self):
        if self.direction == TrafficDirection.OUTGOING:
            return self.__device

        if self.direction == TrafficDirection.INCOMING:
            return self.ifb_device

        raise ValueError("unknown direction: " + self.direction)

    def __get_ifb_from_device(self, device):
        filter_parser = TcFilterParser()
        command = "tc filter show dev {:s} root".format(device)
        filter_runner = SubprocessRunner(command)
        filter_runner.run()

        return filter_parser.parse_incoming_device(filter_runner.stdout)

    def __get_network_direction_str(self):
        if self.direction == TrafficDirection.OUTGOING:
            return "dst"

        if self.direction == TrafficDirection.INCOMING:
            return "src"

        raise ValueError("unknown direction: " + self.direction)

    def __get_netem_qdisc_major_id(self, base_qdisc_major_id):
        base_offset = 10

        if self.direction == TrafficDirection.OUTGOING:
            direction_offset = 0
        elif self.direction == TrafficDirection.INCOMING:
            direction_offset = 1

        return base_qdisc_major_id + base_offset + direction_offset

    def __get_qdisc_minor_id(self):
        if self.direction == TrafficDirection.OUTGOING:
            return self.__OUT_DEVICE_QDISC_MINOR_ID

        if self.direction == TrafficDirection.INCOMING:
            return self.__IN_DEVICE_QDISC_MINOR_ID

        raise ValueError("unknown direction: " + self.direction)

    def __get_filter(self, device):
        if dataproperty.is_empty_string(device):
            return {}

        qdisc_parser = TcQdiscParser()
        filter_parser = TcFilterParser()

        # parse qdisc ---
        command = "tc qdisc show dev {:s}".format(device)
        qdisk_show_runner = SubprocessRunner(command)
        qdisk_show_runner.run()
        qdisc_param = qdisc_parser.parse(qdisk_show_runner.stdout)

        # parse filter ---
        command = "tc filter show dev {:s}".format(device)
        filter_show_runner = SubprocessRunner(command)
        filter_show_runner.run()

        filter_table = {}
        for filter_param in filter_parser.parse_filter(filter_show_runner.stdout):
            key_item_list = []

            if dataproperty.is_not_empty_string(filter_param.get("network")):
                key_item_list.append("network=" + filter_param.get("network"))

            if dataproperty.is_integer(filter_param.get("port")):
                key_item_list.append(
                    "port={:d}".format(filter_param.get("port")))

            filter_key = ", ".join(key_item_list)
            filter_table[filter_key] = {}
            if filter_param.get("flowid") == qdisc_param.get("parent"):
                work_qdisc_param = dict(qdisc_param)
                del work_qdisc_param["parent"]
                filter_table[filter_key] = work_qdisc_param

        return filter_table

    def __set_pre_network_filter(self, qdisc_major_id):
        if all([
            dataproperty.is_empty_string(self.network),
            not dataproperty.is_integer(self.port),
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
            "prio 2 u32 match ip {:s} 0.0.0.0/0".format(
                self.__get_network_direction_str()),
            "flowid " + flowid
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

        return SubprocessRunner(" ".join(command_list)).run()

    def __set_network_filter(self, qdisc_major_id):
        if all([
            dataproperty.is_empty_string(self.network),
            self.port is None,
        ]):
            return 0

        command_list = [
            "tc filter add",
            "dev " + self.__get_tc_device(),
            "protocol ip",
            "parent {:x}:".format(qdisc_major_id),
            "prio 1 u32",
            "flowid {:x}:{:d}".format(
                qdisc_major_id, self.__get_qdisc_minor_id()),
        ]
        if dataproperty.is_not_empty_string(self.network):
            command_list.append("match ip {:s} {:s}".format(
                self.__get_network_direction_str(), self.network))
        if self.port is not None:
            command_list.append("match ip dport {:d} 0xffff".format(self.port))

        return SubprocessRunner(" ".join(command_list)).run()

    def __set_rate(self, qdisc_major_id):
        if dataproperty.is_empty_string(self.bandwidth_rate):
            return 0

        rate_kbps = Humanreadable(kilo_size=1000).humanreadable_to_byte(
            self.bandwidth_rate) / 1000.0
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
