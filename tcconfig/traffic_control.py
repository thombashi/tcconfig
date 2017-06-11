# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division

import re

from dataproperty import DataProperty
import six
import typepy
from typepy.type import RealNumber

import subprocrunner as spr

from ._common import (
    logging_context,
    get_anywhere_network,
    get_no_limit_kbits,
    sanitize_network,
    verify_network_interface,
    run_command_helper,
)
from ._const import (
    KILO_SIZE,
    LIST_MANGLE_TABLE_COMMAND,
    Tc,
    TcCommandOutput,
    TrafficDirection,
)
from ._converter import Humanreadable
from ._error import (
    NetworkInterfaceNotFoundError,
    InvalidParameterError,
    UnitNotFoundError,
)
from ._iptables import IptablesMangleController
from ._logger import logger
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

    MIN_PACKET_DUPLICATE_RATE = 0  # [%]
    MAX_PACKET_DUPLICATE_RATE = 100  # [%]

    MIN_LATENCY_MS = 0  # [millisecond]
    MAX_LATENCY_MS = 3600000  # [millisecond] (60 minutes)

    MIN_CORRUPTION_RATE = 0  # [%]
    MAX_CORRUPTION_RATE = 100  # [%]

    MIN_REORDERING_RATE = 0  # [%]
    MAX_REORDERING_RATE = 100  # [%]

    __MIN_PORT = 0
    __MAX_PORT = 65535

    REGEXP_FILE_EXISTS = re.compile("RTNETLINK answers: File exists")

    EXISTS_MSG_TEMPLATE = (
        "{:s} "
        "execute with --overwrite option if you want to overwrite "
        "the existing rules. "
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
        # convert bandwidth string [K/M/G bit per second] to a number
        try:
            return Humanreadable(
                self.__bandwidth_rate, kilo_size=KILO_SIZE).to_kilo_bit()
        except (InvalidParameterError, UnitNotFoundError, TypeError, ValueError):
            return None

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
    def packet_duplicate_rate(self):
        return self.__packet_duplicate_rate

    @property
    def corruption_rate(self):
        return self.__corruption_rate

    @property
    def reordering_rate(self):
        return self.__reordering_rate

    @property
    def dst_network(self):
        return self.__dst_network

    @property
    def src_network(self):
        return self.__src_network

    @property
    def src_port(self):
        return self.__src_port

    @property
    def dst_port(self):
        return self.__dst_port

    @property
    def is_change_shaper(self):
        return self.__is_change_shaper

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

    @property
    def ip_version(self):
        return 6 if self.__is_ipv6 else 4

    @property
    def protocol(self):
        return "ipv6" if self.__is_ipv6 else "ip"

    @property
    def protocol_match(self):
        return "ip6" if self.__is_ipv6 else "ip"

    @property
    def tc_command_output(self):
        return self.__tc_command_output

    @property
    def iptables_ctrl(self):
        return self.__iptables_ctrl

    def __init__(
            self, device,
            direction=None, bandwidth_rate=None,
            latency_ms=None, latency_distro_ms=None,
            packet_loss_rate=None, packet_duplicate_rate=None,
            corruption_rate=None, reordering_rate=None,
            dst_network=None, src_network=None,
            dst_port=None, src_port=None,
            is_ipv6=False, is_change_shaper=False, is_add_shaper=False,
            is_enable_iptables=True,
            shaping_algorithm=None,
            tc_command_output=TcCommandOutput.NOT_SET,
    ):
        self.__device = device

        self.__direction = direction
        self.__bandwidth_rate = bandwidth_rate
        self.__latency_ms = latency_ms  # [milliseconds]
        self.__latency_distro_ms = latency_distro_ms  # [milliseconds]
        self.__packet_loss_rate = packet_loss_rate  # [%]
        self.__packet_duplicate_rate = packet_duplicate_rate  # [%]
        self.__corruption_rate = corruption_rate  # [%]
        self.__reordering_rate = reordering_rate
        self.__dst_network = dst_network
        self.__src_network = src_network
        self.__src_port = src_port
        self.__dst_port = dst_port
        self.__is_ipv6 = is_ipv6
        self.__is_change_shaper = is_change_shaper
        self.__is_add_shaper = is_add_shaper
        self.__is_enable_iptables = is_enable_iptables
        self.__tc_command_output = tc_command_output

        self.__qdisc_major_id = self.__get_device_qdisc_major_id()

        self.__iptables_ctrl = IptablesMangleController(
            is_enable_iptables, self.ip_version)

        self.__init_shaper(shaping_algorithm)

    def validate(self):
        verify_network_interface(self.__device)
        self.__validate_netem_parameter()
        self.__validate_src_network()
        self.__validate_port()

    def __validate_src_network(self):
        if typepy.is_null_string(self.src_network):
            return

        if not self.is_enable_iptables:
            raise InvalidParameterError(
                "--iptables option will be required to use --src-network option")

    def validate_bandwidth_rate(self):
        if typepy.is_null_string(self.__bandwidth_rate):
            return

        # convert bandwidth string [K/M/G bit per second] to a number
        bandwidth_rate = Humanreadable(
            self.__bandwidth_rate, kilo_size=KILO_SIZE).to_kilo_bit()

        if not RealNumber(bandwidth_rate).is_type():
            raise InvalidParameterError(
                "bandwidth_rate must be number: actual={}".format(
                    bandwidth_rate))

        if bandwidth_rate <= 0:
            raise InvalidParameterError(
                "bandwidth_rate must be greater than zero: actual={}".format(
                    bandwidth_rate))

        no_limit_kbits = get_no_limit_kbits(self.get_tc_device())
        if bandwidth_rate > no_limit_kbits:
            raise InvalidParameterError(
                "bandwidth_rate must be less than {}: actual={}".format(
                    no_limit_kbits, bandwidth_rate))

    def sanitize(self):
        self.__dst_network = sanitize_network(
            self.dst_network, self.ip_version)
        self.__src_network = sanitize_network(
            self.src_network, self.ip_version)

    def get_tc_device(self):
        if self.direction == TrafficDirection.OUTGOING:
            return self.__device

        if self.direction == TrafficDirection.INCOMING:
            return self.ifb_device

        raise ValueError("unknown direction: {}".format(self.direction))

    def get_tc_command(self, sub_command):
        valid_sub_command_list = (
            Tc.Subcommand.CLASS, Tc.Subcommand.FILTER, Tc.Subcommand.QDISC)
        if sub_command not in valid_sub_command_list:
            raise ValueError("unknown sub command: {}".format(sub_command))

        if (self.is_change_shaper and
                sub_command in (Tc.Subcommand.QDISC, Tc.Subcommand.FILTER)):
            # no need to execute
            return None

        return "tc {:s} {:s}".format(
            sub_command, "change" if self.is_change_shaper else "add")

    def get_anywhere_network(self):
        return get_anywhere_network(self, )

    def get_command_history(self):
        def tc_filter(command):
            if command == LIST_MANGLE_TABLE_COMMAND:
                return False

            if re.search("^tc .* show dev", command):
                return False

            return True

        return filter(tc_filter, spr.SubprocessRunner.get_history())

    def set_tc(self):
        self.__setup_ifb()

        return self.__shaper.set_shaping()

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
                "failed to delete qdisc: no qdisc for incoming packets")
            result_list.append(returncode == 0)

        with logging_context("delete ifb device"):
            try:
                result_list.append(self.__delete_ifb_device() == 0)
            except NetworkInterfaceNotFoundError as e:
                logger.debug(e)
                result_list.append(False)

        with logging_context("delete iptables mangle table entries"):
            self.iptables_ctrl.clear()
            # IptablesMangleController.clear()

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

    def __validate_packet_duplicate_rate(self):
        _validate_within_min_max(
            "duplicate (packet duplicate rate)", self.packet_duplicate_rate,
            self.MIN_PACKET_DUPLICATE_RATE, self.MAX_PACKET_DUPLICATE_RATE,
            unit="%")

    def __validate_corruption_rate(self):
        _validate_within_min_max(
            "corruption (packet corruption rate)", self.corruption_rate,
            self.MIN_CORRUPTION_RATE, self.MAX_CORRUPTION_RATE, unit="%")

    def __validate_reordering_rate(self):
        _validate_within_min_max(
            "reordering (packet reordering rate)", self.reordering_rate,
            self.MIN_REORDERING_RATE, self.MAX_REORDERING_RATE, unit="%")

    def __validate_reordering_and_delay(self):
        if self.reordering_rate and not self.latency_ms:
            raise ValueError(
                'reordering needs latency to be specified: set latency > 0')

    def __validate_netem_parameter(self):
        self.validate_bandwidth_rate()
        self.__validate_network_delay()
        self.__validate_packet_loss_rate()
        self.__validate_packet_duplicate_rate()
        self.__validate_corruption_rate()
        self.__validate_reordering_rate()
        self.__validate_reordering_and_delay()

        netem_param_value_list = [
            self.bandwidth_rate,
            self.latency_ms,
            self.packet_loss_rate,
            self.packet_duplicate_rate,
            self.corruption_rate,
            self.reordering_rate,
        ]

        if all([
            not RealNumber(netem_param_value).is_type()
            or netem_param_value <= 0
            for netem_param_value in netem_param_value_list
        ]):
            raise ValueError(
                "there is no valid net emulation parameter value. "
                "at least one or more following parameters are required: "
                "--rate, --delay, --loss, --duplicate, --corrupt, --reordering"
            )

    def __validate_port(self):
        _validate_within_min_max(
            "src_port", self.src_port, self.__MIN_PORT, self.__MAX_PORT,
            unit=None)

        _validate_within_min_max(
            "dst_port", self.dst_port, self.__MIN_PORT, self.__MAX_PORT,
            unit=None)

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

        return_code |= spr.SubprocessRunner("modprobe ifb").run()

        return_code |= run_command_helper(
            "ip link add {:s} type ifb".format(self.ifb_device),
            self.REGEXP_FILE_EXISTS,
            self.EXISTS_MSG_TEMPLATE.format(
                "failed to add ip link: ip link already exists."))

        return_code |= spr.SubprocessRunner(
            "ip link set dev {:s} up".format(self.ifb_device)).run()

        base_command = "tc qdisc add"
        return_code |= run_command_helper(
            "{:s} dev {:s} ingress".format(base_command, self.__device),
            self.REGEXP_FILE_EXISTS,
            self.EXISTS_MSG_TEMPLATE.format(
                "failed to '{:s}': ingress qdisc already exists.".format(
                    base_command)))

        return_code |= spr.SubprocessRunner(" ".join([
            "tc filter add",
            "dev {:s}".format(self.__device),
            "parent ffff: protocol {:s} u32 match u32 0 0".format(
                self.protocol),
            "flowid {:x}:".format(self.__get_device_qdisc_major_id()),
            "action mirred egress redirect",
            "dev {:s}".format(self.ifb_device),
        ])).run()

        return return_code

    def __delete_ifb_device(self):
        verify_network_interface(self.ifb_device)

        command_list = [
            "tc qdisc del dev {:s} root".format(self.ifb_device),
            "ip link set dev {:s} down".format(self.ifb_device),
            "ip link delete {:s} type ifb".format(self.ifb_device),
        ]

        if all([spr.SubprocessRunner(command).run() != 0 for command in
                command_list]):
            return 2

        return 0
