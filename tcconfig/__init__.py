# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

import dataproperty
import ipaddress
import six
import thutils


class TrafficControl(object):
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

        self.rate = None
        self.delay_ms = None
        self.loss_percent = None
        self.network = None
        self.port = None

    def validate(self):
        if dataproperty.is_empty_string(self.__device):
            raise ValueError("device name is empty")

        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.network = self.__validate_network()
        self.__validate_port()

    def set_tc(self):
        self.__make_qdisc()
        self.__set_pre_network_filter()
        self.__set_delay_and_loss()
        self.__set_network_filter()
        self.__set_rate()

    def delete_tc(self):
        command = "tc qdisc del dev %s root" % (self.__device)

        return self.__subproc_wrapper.run(command)

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

    def __make_qdisc(self):
        command_list = [
            "tc qdisc add",
            "dev " + self.__device,
            "root handle 1: prio",
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __set_pre_network_filter(self):
        if dataproperty.is_empty_string(self.network):
            flowid = "1:1"
        else:
            flowid = "1:2"

        command_list = [
            "tc filter add",
            "dev " + self.__device,
            "protocol ip parent 1: prio 2 u32 match ip dst 0.0.0.0/0",
            "flowid " + flowid
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __set_delay_and_loss(self):
        command_list = [
            "tc qdisc add",
            "dev " + self.__device,
            "parent 1:1 handle 10: netem",
        ]
        if self.loss_percent > 0:
            command_list.append("loss %s%%" % (self.loss_percent))
        if self.delay_ms > 0:
            command_list.append("delay %dms" % (self.delay_ms))

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __set_network_filter(self):
        if all([
            dataproperty.is_empty_string(self.network),
            self.port is None,
        ]):
            return 0

        command_list = [
            "tc filter add",
            "dev " + self.__device,
            "protocol ip parent 1: prio 1 u32",
            "flowid 1:1",
        ]
        if dataproperty.is_not_empty_string(self.network):
            command_list.append("match ip dst " + self.network)
        if self.port is not None:
            command_list.append("match ip dport %d" % (self.port))

        return self.__subproc_wrapper.run(" ".join(command_list))

    def __set_rate(self):
        if dataproperty.is_empty_string(self.rate):
            return 0

        rate_kbps = thutils.common.humanreadable_to_byte(
            self.rate, kilo_size=1000) / 1000.0
        if rate_kbps <= 0:
            raise ValueError("rate must be greater than zero")

        command_list = [
            "tc qdisc add",
            "dev " + self.__device,
            "parent 10:1",
            "handle 20:",
            "tbf",
            "rate %dkbit" % (rate_kbps),
            "buffer %d" % (max(rate_kbps, self.__MIN_BUFFER_BYTE)),  # [byte]
            "limit 10000",
        ]

        return self.__subproc_wrapper.run(" ".join(command_list))
