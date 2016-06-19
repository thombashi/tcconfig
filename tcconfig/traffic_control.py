# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import

import dataproperty
import ipaddress
import six
import thutils

import tcconfig.parser


class TrafficDirection:
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
        return "ifb%d" % (self.__get_device_qdisc_major_id())

    def __init__(self, subproc_wrapper, device):
        self.__subproc_wrapper = subproc_wrapper
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
        tcconfig.verify_network_interface(self.__device)
        self.__validate_bandwidth_rate()
        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.__validate_curruption_rate()
        self.network = self.__validate_network()
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
            "tc qdisc del dev %s root" % (self.__device),
            "tc qdisc del dev %s ingress" % (self.__device),
            "tc qdisc del dev %s root" % (self.ifb_device),
            "ip link set dev %s down" % (self.ifb_device),
            "ip link delete %s type ifb" % (self.ifb_device),
        ]

        for command in command_list:
            proc = self.__subproc_wrapper.popen_command(command)
            _stdout, _stderr = proc.communicate()
            return_code_list.append(proc.returncode != 0)

        return -1 if all(return_code_list) else 0

    def get_tc_parameter(self):
        return {
            self.__device: {
                "outgoing": self.__get_filter(self.__device),
                "incoming": self.__get_filter(
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
        return_code |= self.__subproc_wrapper.run(command)

        command = "ip link add %s type ifb" % (self.ifb_device)
        return_code |= self.__subproc_wrapper.run(command)

        command = "ip link set dev %s up" % (self.ifb_device)
        return_code |= self.__subproc_wrapper.run(command)

        command = "tc qdisc add dev %s ingress" % (self.__device)
        return_code |= self.__subproc_wrapper.run(command)

        command_list = [
            "tc filter add",
            "dev " + self.__device,
            "parent ffff: protocol ip u32 match u32 0 0",
            "flowid %x:" % (self.__get_device_qdisc_major_id()),
            "action mirred egress redirect",
            "dev " + self.ifb_device,
        ]
        return_code |= self.__subproc_wrapper.run(" ".join(command_list))

        return return_code

    def __validate_within_min_max(self, param_name, value, min_value, max_value):
        if value is None:
            return

        if value > max_value:
            raise ValueError(
                "%s is too high: expected<=%f[%%], value=%f[%%]" % (
                    param_name, max_value, value))

        if value < min_value:
            raise ValueError(
                "%s is too low: expected>=%f[%%], value=%f[%%]" % (
                    param_name, min_value, value))

    def __validate_bandwidth_rate(self):
        if dataproperty.is_empty_string(self.bandwidth_rate):
            return

        rate = thutils.common.humanreadable_to_byte(self.bandwidth_rate)
        if rate <= 0:
            raise ValueError("rate must be greater than zero")

    def __validate_network_delay(self):
        self.__validate_within_min_max(
            thutils.common.get_var_name(self.latency_ms, locals()),
            self.latency_ms,
            self.__MIN_LATENCY_MS, self.__MAX_LATENCY_MS)

        self.__validate_within_min_max(
            thutils.common.get_var_name(self.latency_distro_ms, locals()),
            self.latency_distro_ms,
            self.__MIN_LATENCY_MS, self.__MAX_LATENCY_MS)

    def __validate_packet_loss_rate(self):
        self.__validate_within_min_max(
            thutils.common.get_var_name(self.packet_loss_rate, locals()),
            self.packet_loss_rate,
            self.__MIN_PACKET_LOSS_RATE, self.__MAX_PACKET_LOSS_RATE)

    def __validate_curruption_rate(self):
        self.__validate_within_min_max(
            thutils.common.get_var_name(self.curruption_rate, locals()),
            self.curruption_rate,
            self.__MIN_CORRUPTION_RATE, self.__MAX_CORRUPTION_RATE)

    def __validate_network(self):
        if dataproperty.is_empty_string(self.network):
            return ""

        try:
            ipaddress.IPv4Address(six.u(self.network))
            return self.network + "/32"
        except ipaddress.AddressValueError:
            pass

        ipaddress.IPv4Network(six.u(self.network))
        return self.network

        raise ValueError("unrecognizable network: " + self.network)

    def __validate_port(self):
        self.__validate_within_min_max(
            thutils.common.get_var_name(self.port, locals()),
            self.port, self.__MIN_PORT, self.__MAX_PORT)

    def __make_qdisc(self, qdisc_major_id):
        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "root",
            "handle %x:" % (qdisc_major_id),
            "prio",
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __get_tc_device(self):
        if self.direction == TrafficDirection.OUTGOING:
            return self.__device

        if self.direction == TrafficDirection.INCOMING:
            return self.ifb_device

        raise ValueError("unknown direction: " + self.direction)

    def __get_ifb_from_device(self, device):
        filter_parser = tcconfig.parser.TcFilterParser()
        command = "tc filter show dev %s root" % (device)
        proc = self.__subproc_wrapper.popen_command(command)
        filter_stdout, _stderr = proc.communicate()

        return filter_parser.parse_incoming_device(filter_stdout)

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
        qdisc_parser = tcconfig.parser.TcQdiscParser()
        filter_parser = tcconfig.parser.TcFilterParser()

        # parse qdisc ---
        command = "tc qdisc show dev %s" % (device)
        proc = self.__subproc_wrapper.popen_command(command)
        qdisc_stdout, _stderr = proc.communicate()
        qdisc_param = qdisc_parser.parse(qdisc_stdout)

        # parse filter ---
        command = "tc filter show dev %s" % (device)
        proc = self.__subproc_wrapper.popen_command(command)
        filter_stdout, _stderr = proc.communicate()

        filter_table = {}

        for filter_param in filter_parser.parse_filter(filter_stdout):
            key_item_list = []

            if dataproperty.is_not_empty_string(filter_param.get("network")):
                key_item_list.append("network=" + filter_param.get("network"))

            if dataproperty.is_integer(filter_param.get("port")):
                key_item_list.append("port=%d" % (filter_param.get("port")))

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
            flowid = "%x:%d" % (qdisc_major_id, self.__get_qdisc_minor_id())
        else:
            flowid = "%x:2" % (qdisc_major_id)

        command_list = [
            "tc filter add",
            "dev " + self.__get_tc_device(),
            "protocol ip",
            "parent %x:" % (qdisc_major_id),
            "prio 2 u32 match ip %s 0.0.0.0/0" % (
                self.__get_network_direction_str()),
            "flowid " + flowid
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __set_netem(self, qdisc_major_id):
        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "parent %x:%d" % (qdisc_major_id, self.__get_qdisc_minor_id()),
            "handle %x:" % (self.__get_netem_qdisc_major_id(qdisc_major_id)),
            "netem",
        ]
        if self.packet_loss_rate > 0:
            command_list.append("loss %s%%" % (self.packet_loss_rate))
        if self.latency_ms > 0:
            command_list.append("delay %fms" % (self.latency_ms))

            if self.latency_distro_ms > 0:
                command_list.append(
                    "%fms distribution normal" % (self.latency_distro_ms))

        if self.corruption_rate > 0:
            command_list.append("corrupt %s%%" % (self.corruption_rate))

        return self.__subproc_wrapper.run(" ".join(command_list))

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
            "parent %x:" % (qdisc_major_id),
            "prio 1 u32",
            "flowid %x:%d" % (qdisc_major_id, self.__get_qdisc_minor_id()),
        ]
        if dataproperty.is_not_empty_string(self.network):
            command_list.append("match ip %s %s" % (
                self.__get_network_direction_str(), self.network))
        if self.port is not None:
            command_list.append("match ip dport %d 0xffff" % (self.port))

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __set_rate(self, qdisc_major_id):
        if dataproperty.is_empty_string(self.bandwidth_rate):
            return 0

        rate_kbps = thutils.common.humanreadable_to_byte(
            self.bandwidth_rate, kilo_size=1000) / 1000.0
        if rate_kbps <= 0:
            raise ValueError("rate must be greater than zero")

        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "parent %x:%d" % (
                self.__get_netem_qdisc_major_id(qdisc_major_id),
                self.__get_qdisc_minor_id()),
            "handle 20:",
            "tbf",
            "rate %dkbit" % (rate_kbps),
            "buffer %d" % (max(rate_kbps, self.__MIN_BUFFER_BYTE)),  # [byte]
            "limit 10000",
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))
