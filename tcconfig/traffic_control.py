# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division

import re

from dataproperty import DataProperty
import six
from subprocrunner import SubprocessRunner
import typepy
from typepy.type import RealNumber

from ._common import (
    logging_context,
    sanitize_network,
    verify_network_interface,
    run_command_helper,
)
from ._const import KILO_SIZE
from ._converter import Humanreadable
from ._error import (
    NetworkInterfaceNotFoundError,
    EmptyParameterError,
    InvalidParameterError
)
from ._iptables import IptablesMangleController
from ._logger import logger
from ._traffic_direction import TrafficDirection
from .shaper.htb import HtbShaper
from .shaper.tbf import TbfShaper


def _validate_within_min_max(param_name, value, min_value, max_value, unit):
    if value is None:
        return

    if unit is None:
        unit = ""
    else:
        unit = "[{:s}]".format(unit)

    if value > max_value:
        raise ValueError(
            "'{0:s}' is too high: expected<={1:s}{3:s}, actual={2:s}{3:s}".format(
                param_name, DataProperty(max_value).to_str(),
                DataProperty(value).to_str(), unit))

    if value < min_value:
        raise ValueError(
            "'{0:s}' is too low: expected>={1:s}{3:s}, actual={2:s}{3:s}".format(
                param_name, DataProperty(min_value).to_str(),
                DataProperty(value).to_str(), unit))


class TrafficControl(object):

    MIN_PACKET_LOSS_RATE = 0  # [%]
    MAX_PACKET_LOSS_RATE = 100  # [%]

    MIN_LATENCY_MS = 0  # [millisecond]
    MAX_LATENCY_MS = 3600000  # [millisecond]

    MIN_CORRUPTION_RATE = 0  # [%]
    MAX_CORRUPTION_RATE = 100  # [%]

    __MIN_PORT = 0
    __MAX_PORT = 65535

    REGEXP_FILE_EXISTS = re.compile("RTNETLINK answers: File exists")

    EXISTS_MSG_TEMPLATE = (
        "{:s} "
        "execute with --overwrite option if you want to overwrite "
        "the existing rules."
        "execute with --add option if you want to add a new rule in addition "
        "to the existing rules."
    )

    @property
    def ifb_device(self):
        return "ifb{:d}".format(self.__qdisc_major_id)

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
    def is_add_shaper(self):
        return self.__is_add_shaper

    @property
    def is_enable_iptables(self):
        return self.__is_enable_iptables

    @property
    def qdisc_major_id(self):
        return self.__qdisc_major_id

    @property
    def qdisc_major_id_str(self):
        return "{:x}".format(self.__qdisc_major_id)

    def __init__(
            self, device,
            direction=None, bandwidth_rate=None,
            latency_ms=None, latency_distro_ms=None,
            packet_loss_rate=None, corruption_rate=None,
            network=None, port=None,
            src_network=None,
            is_add_shaper=False,
            is_enable_iptables=True,
            shaping_algorithm=None,
    ):
        self.__device = device

        self.__direction = direction
        self.__latency_ms = latency_ms  # [milliseconds]
        self.__latency_distro_ms = latency_distro_ms  # [milliseconds]
        self.__packet_loss_rate = packet_loss_rate  # [%]
        self.__corruption_rate = corruption_rate  # [%]
        self.__network = network
        self.__src_network = src_network
        self.__port = port
        self.__is_add_shaper = is_add_shaper
        self.__is_enable_iptables = is_enable_iptables

        self.__qdisc_major_id = self.__get_device_qdisc_major_id()

        # bandwidth string [G/M/K bit per second]
        try:
            self.__bandwidth_rate = Humanreadable(
                bandwidth_rate, kilo_size=KILO_SIZE).to_kilo_value()
        except (TypeError, ValueError):
            self.__bandwidth_rate = None

        IptablesMangleController.enable = is_enable_iptables

        self.__init_shaper(shaping_algorithm)

    def validate(self):
        verify_network_interface(self.__device)
        self.__validate_netem_parameter()
        self.__validate_src_network()

        self.__network = sanitize_network(self.network)
        self.__src_network = sanitize_network(self.src_network)
        self.__validate_port()

    def __validate_src_network(self):
        if typepy.is_null_string(self.src_network):
            return

        if not self.is_enable_iptables:
            raise InvalidParameterError(
                "--iptables option will be required to use --src-network option")

    def validate_bandwidth_rate(self):
        if not RealNumber(self.bandwidth_rate).is_type():
            raise EmptyParameterError("bandwidth_rate is empty")

        if self.bandwidth_rate <= 0:
            raise InvalidParameterError(
                "rate must be greater than zero: actual={}".format(
                    self.bandwidth_rate))

    def get_tc_device(self):
        if self.direction == TrafficDirection.OUTGOING:
            return self.__device

        if self.direction == TrafficDirection.INCOMING:
            return self.ifb_device

        raise ValueError("unknown direction: " + self.direction)

    def set_tc(self):
        self.__setup_ifb()
        self.__shaper.set_shaping()

    def delete_tc(self):
        result_list = []

        with logging_context("delete qdisc"):
            returncode = run_command_helper(
                "tc qdisc del dev {:s} root".format(self.__device),
                re.compile("RTNETLINK answers: No such file or directory"),
                "failed to delete qdisc: no qdisc for outgoing packets")
            result_list.append(returncode == 0)

        with logging_context("delete ingress qdisc"):
            returncode = run_command_helper(
                "tc qdisc del dev {:s} ingress".format(self.__device),
                re.compile("|".join([
                    "RTNETLINK answers: Invalid argument",
                    "RTNETLINK answers: No such file or directory",
                ])),
                "failed to delete qdisc: no qdisc for incomming packets")
            result_list.append(returncode == 0)

        with logging_context("delete ifb device"):
            try:
                result_list.append(self.__delete_ifb_device() == 0)
            except NetworkInterfaceNotFoundError as e:
                logger.debug(e)
                result_list.append(False)

        with logging_context("delete iptables mangle table entries"):
            IptablesMangleController.clear()

        return any(result_list)

    def __init_shaper(self, shaping_algorithm):
        if shaping_algorithm is None:
            self.__shaper = None
            return

        if shaping_algorithm == "htb":
            self.__shaper = HtbShaper(self)
            return

        if shaping_algorithm == "tbf":
            self.__shaper = TbfShaper(self)
            return

        raise ValueError(
            "unknown shaping algorithm: {}".format(shaping_algorithm))

    def __validate_network_delay(self):
        _validate_within_min_max(
            "delay", self.latency_ms,
            self.MIN_LATENCY_MS, self.MAX_LATENCY_MS, unit="ms")

        _validate_within_min_max(
            "delay-distro", self.latency_distro_ms,
            self.MIN_LATENCY_MS, self.MAX_LATENCY_MS, unit="ms")

    def __validate_packet_loss_rate(self):
        _validate_within_min_max(
            "loss (packet loss rate)", self.packet_loss_rate,
            self.MIN_PACKET_LOSS_RATE, self.MAX_PACKET_LOSS_RATE, unit="%")

    def __validate_corruption_rate(self):
        _validate_within_min_max(
            "corruption (packet corruption rate)", self.corruption_rate,
            self.MIN_CORRUPTION_RATE, self.MAX_CORRUPTION_RATE, unit="%")

    def __validate_netem_parameter(self):
        try:
            self.validate_bandwidth_rate()
        except EmptyParameterError:
            pass

        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.__validate_corruption_rate()

        netem_param_value_list = [
            self.bandwidth_rate,
            self.latency_ms,
            self.packet_loss_rate,
            self.corruption_rate,
        ]

        if all([
            not RealNumber(
                netem_param_value).is_type() or netem_param_value == 0
            for netem_param_value in netem_param_value_list
        ]):
            raise ValueError("there is no valid net emulation parameter value")

    def __validate_port(self):
        _validate_within_min_max(
            "port", self.port, self.__MIN_PORT, self.__MAX_PORT, unit=None)

    def __get_device_qdisc_major_id(self):
        import hashlib

        base_device_hash = hashlib.md5(six.b(self.__device)).hexdigest()[:3]
        device_hash_prefix = "1"

        return int(device_hash_prefix + base_device_hash, 16)

    def __setup_ifb(self):
        if self.direction != TrafficDirection.INCOMING:
            return 0

        if typepy.is_null_string(self.ifb_device):
            return -1

        return_code = 0

        command = "modprobe ifb"
        return_code |= SubprocessRunner(command).run()

        return_code |= run_command_helper(
            "ip link add {:s} type ifb".format(self.ifb_device),
            self.REGEXP_FILE_EXISTS,
            self.EXISTS_MSG_TEMPLATE.format(
                "failed to add ip link: ip link already exists."))

        command = "ip link set dev {:s} up".format(self.ifb_device)
        return_code |= SubprocessRunner(command).run()

        return_code |= run_command_helper(
            "tc qdisc add dev {:s} ingress".format(self.__device),
            self.REGEXP_FILE_EXISTS,
            self.EXISTS_MSG_TEMPLATE.format(
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
