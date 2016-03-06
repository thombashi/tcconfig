# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

import dataproperty
import ipaddress
import six
import thutils


class TrafficDirection:
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    LIST = [OUTGOING, INCOMING]


class TrafficControl(object):
    __OUT_DEVICE_QDISC_MAJOR_ID = 1
    __OUT_DEVICE_QDISC_MINOR_ID = 1
    __IN_DEVICE_QDISC_MAJOR_ID = 1
    __IN_DEVICE_QDISC_MINOR_ID = 3

    __MIN_LOSS_RATE = 0  # [%]
    __MAX_LOSS_RATE = 99  # [%]

    __MIN_DELAY_MS = 0  # [millisecond]
    __MAX_DELAY_MS = 10000  # [millisecond]

    __MIN_BUFFER_BYTE = 1600

    __MIN_PORT = 0
    __MAX_PORT = 65535

    def __init__(self, subproc_wrapper, device):
        self.__subproc_wrapper = subproc_wrapper
        self.__device = device

        self.ifb_device = "ifb0"
        self.direction = None
        self.rate = None
        self.delay_ms = None
        self.loss_percent = None
        self.network = None
        self.port = None

    def validate(self):
        if dataproperty.is_empty_string(self.__device):
            raise ValueError("device name is empty")

        self.__validate_rate()
        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.network = self.__validate_network()
        self.__validate_port()

    def __get_device_qdisc_major_id(self):
        if self.direction == TrafficDirection.OUTGOING:
            return self.__OUT_DEVICE_QDISC_MAJOR_ID

        if self.direction == TrafficDirection.INCOMING:
            return self.__IN_DEVICE_QDISC_MAJOR_ID

        raise ValueError("unknown traffic direction: " + self.direction)

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

        command = "tc qdisc del dev %s root" % (self.__device)
        proc = self.__subproc_wrapper.popen_command(command)
        _stdout, _stderr = proc.communicate()
        return_code_list.append(proc.returncode != 0)

        command = "tc qdisc del dev %s ingress" % (self.__device)
        proc = self.__subproc_wrapper.popen_command(command)
        _stdout, _stderr = proc.communicate()
        return_code_list.append(proc.returncode != 0)

        command = "tc qdisc del dev %s root" % (self.ifb_device)
        proc = self.__subproc_wrapper.popen_command(command)
        _stdout, _stderr = proc.communicate()
        return_code_list.append(proc.returncode != 0)

        return -1 if all(return_code_list) else 0

    def __setup_ifb(self):
        if self.direction != TrafficDirection.INCOMING:
            return

        if dataproperty.is_empty_string(self.ifb_device):
            return

        return_code = 0

        command = "modprobe ifb"
        return_code |= self.__subproc_wrapper.run(command)

        command = "ip link set dev %s up" % (self.ifb_device)
        return_code |= self.__subproc_wrapper.run(command)

        command = "tc qdisc add dev %s ingress" % (self.__device)
        return_code |= self.__subproc_wrapper.run(command)

        command_list = [
            "tc filter add",
            "dev " + self.__device,
            "parent ffff: protocol ip u32 match u32 0 0",
            "flowid %d:" % (self.__IN_DEVICE_QDISC_MAJOR_ID),
            "action mirred egress redirect",
            "dev " + self.ifb_device,
        ]
        return_code |= self.__subproc_wrapper.run(" ".join(command_list))

        return return_code

    def __validate_rate(self):
        if dataproperty.is_empty_string(self.rate):
            return

        rate = thutils.common.humanreadable_to_byte(self.rate)
        if rate <= 0:
            raise ValueError("rate must be greater than zero")

    def __validate_network_delay(self):
        if self.delay_ms is None:
            return

        if self.delay_ms > self.__MAX_DELAY_MS:
            raise ValueError(
                "network delay is too high: expected<=%d[ms], value=%d[ms]" % (
                    self.__MAX_DELAY_MS, self.delay_ms))

        if self.delay_ms < self.__MIN_DELAY_MS:
            raise ValueError(
                "delay time is too low: expected>=%d[ms], value=%d[ms]" % (
                    self.__MIN_DELAY_MS, self.delay_ms))

    def __validate_packet_loss_rate(self):
        if self.loss_percent is None:
            return

        if self.loss_percent > self.__MAX_LOSS_RATE:
            raise ValueError(
                "packet loss rate is too high: expected<=%d[%%], value=%d[%%]" % (
                    self.__MAX_LOSS_RATE, self.loss_percent))

        if self.loss_percent < self.__MIN_LOSS_RATE:
            raise ValueError(
                "packet loss rate is too low: expected>=%d[%%], value=%d[%%]" % (
                    self.__MIN_LOSS_RATE, self.loss_percent))

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
        if self.port is None:
            return

        if self.port > self.__MAX_PORT:
            raise ValueError(
                "port number is too high: expected<=%d[%%], value=%d[%%]" % (
                    self.__MAX_PORT, self.port))

        if self.port < self.__MIN_PORT:
            raise ValueError(
                "port number is too low: expected>=%d[%%], value=%d[%%]" % (
                    self.__MIN_PORT, self.port))

    def __make_qdisc(self, qdisc_major_id):
        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "root",
            "handle %d:" % (qdisc_major_id),
            "prio",
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))

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

    def __set_pre_network_filter(self, qdisc_major_id):
        if dataproperty.is_empty_string(self.network):
            flowid = "%d:%d" % (qdisc_major_id, self.__get_qdisc_minor_id())
        else:
            flowid = "%d:2" % (qdisc_major_id)

        command_list = [
            "tc filter add",
            "dev " + self.__get_tc_device(),
            "protocol ip",
            "parent %d:" % (qdisc_major_id),
            "prio 2 u32 match ip %s 0.0.0.0/0" % (
                self.__get_network_direction_str()),
            "flowid " + flowid
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __set_netem(self, qdisc_major_id):
        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "parent %d:%d" % (qdisc_major_id, self.__get_qdisc_minor_id()),
            "handle %d:" % (self.__get_netem_qdisc_major_id(qdisc_major_id)),
            "netem",
        ]
        if self.loss_percent > 0:
            command_list.append("loss %s%%" % (self.loss_percent))
        if self.delay_ms > 0:
            command_list.append("delay %dms" % (self.delay_ms))

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
            "parent %d:" % (qdisc_major_id),
            "prio 1 u32",
            "flowid %d:%d" % (qdisc_major_id, self.__get_qdisc_minor_id()),
        ]
        if dataproperty.is_not_empty_string(self.network):
            command_list.append("match ip %s %s" % (
                self.__get_network_direction_str(), self.network))
        if self.port is not None:
            command_list.append("match ip dport %d 0xffff" % (self.port))

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __set_rate(self, qdisc_major_id):
        if dataproperty.is_empty_string(self.rate):
            return 0

        rate_kbps = thutils.common.humanreadable_to_byte(
            self.rate, kilo_size=1000) / 1000.0
        if rate_kbps <= 0:
            raise ValueError("rate must be greater than zero")

        command_list = [
            "tc qdisc add",
            "dev " + self.__get_tc_device(),
            "parent %d:%d" % (
                self.__get_netem_qdisc_major_id(qdisc_major_id),
                self.__get_qdisc_minor_id()),
            "handle 20:",
            "tbf",
            "rate %dkbit" % (rate_kbps),
            "buffer %d" % (max(rate_kbps, self.__MIN_BUFFER_BYTE)),  # [byte]
            "limit 10000",
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))
