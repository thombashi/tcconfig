# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
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
    get_no_limit_kbits,
    sanitize_network,
    verify_network_interface,
    run_command_helper,
)
from ._const import (
    KILO_SIZE,
    LIST_MANGLE_TABLE_COMMAND,
    ShapingAlgorithm,
    Tc,
    TcCommandOutput,
    TrafficDirection,
)
from ._converter import (
    Humanreadable,
    HumanReadableTime,
)
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
        raise InvalidParameterError(
            "'{:s}' is too high".format(param_name),
            expected="<={:s}{:s}".format(
                DataProperty(max_value).to_str(), unit),
            value="{:s}{:s}".format(
                DataProperty(value).to_str(), unit))

    if value < min_value:
        raise InvalidParameterError(
            "'{:s}' is too low".format(param_name),
            expected=">={:s}{:s}".format(
                DataProperty(min_value).to_str(), unit),
            value="{:s}{:s}".format(DataProperty(value).to_str(), unit))


class TrafficControl(object):
    MIN_PACKET_LOSS_RATE = 0  # [%]
    MAX_PACKET_LOSS_RATE = 100  # [%]

    MIN_PACKET_DUPLICATE_RATE = 0  # [%]
    MAX_PACKET_DUPLICATE_RATE = 100  # [%]

    MIN_CORRUPTION_RATE = 0  # [%]
    MAX_CORRUPTION_RATE = 100  # [%]

    MIN_REORDERING_RATE = 0  # [%]
    MAX_REORDERING_RATE = 100  # [%]

    __MIN_PORT = 0
    __MAX_PORT = 65535

    REGEXP_FILE_EXISTS = re.compile("RTNETLINK answers: File exists")

    EXISTS_MSG_TEMPLATE = (
        "{:s} try to execute with: "
        "(a) --overwrite option if you want to overwrite "
        "the existing rule. "
        "(b) --add option if you want to add a new rule in addition "
        "to the existing rules. "
        "(c) --change option if you want to change the existing "
        "rule parameter."
    )

    @property
    def device(self):
        return self.__device

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
        except (InvalidParameterError, UnitNotFoundError, TypeError):
            return None

    @property
    def latency_time(self):
        return self.__latency_time

    @property
    def latency_distro_time(self):
        return self.__latency_distro_time

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
    def exclude_dst_network(self):
        return self.__exclude_dst_network

    @property
    def src_network(self):
        return self.__src_network

    @property
    def exclude_src_network(self):
        return self.__exclude_src_network

    @property
    def src_port(self):
        return self.__src_port

    @property
    def exclude_src_port(self):
        return self.__exclude_src_port

    @property
    def dst_port(self):
        return self.__dst_port

    @property
    def exclude_dst_port(self):
        return self.__exclude_dst_port

    @property
    def is_change_shaping_rule(self):
        return self.__is_change_shaping_rule

    @property
    def is_add_shaping_rule(self):
        return self.__is_add_shaping_rule

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
            latency_time=None, latency_distro_time=None,
            packet_loss_rate=None, packet_duplicate_rate=None,
            corruption_rate=None, reordering_rate=None,
            dst_network=None, exclude_dst_network=None,
            src_network=None, exclude_src_network=None,
            dst_port=None, exclude_dst_port=None,
            src_port=None, exclude_src_port=None,
            is_ipv6=False,
            is_change_shaping_rule=False, is_add_shaping_rule=False,
            is_enable_iptables=True,
            shaping_algorithm=None,
            tc_command_output=TcCommandOutput.NOT_SET,
    ):
        self.__device = device

        self.__direction = direction
        self.__bandwidth_rate = bandwidth_rate
        self.__latency_time = HumanReadableTime(latency_time)
        self.__latency_distro_time = HumanReadableTime(latency_distro_time)
        self.__packet_loss_rate = packet_loss_rate  # [%]
        self.__packet_duplicate_rate = packet_duplicate_rate  # [%]
        self.__corruption_rate = corruption_rate  # [%]
        self.__reordering_rate = reordering_rate
        self.__dst_network = dst_network
        self.__exclude_dst_network = exclude_dst_network
        self.__src_network = src_network
        self.__exclude_src_network = exclude_src_network
        self.__src_port = src_port
        self.__exclude_src_port = exclude_src_port
        self.__dst_port = dst_port
        self.__exclude_dst_port = exclude_dst_port
        self.__is_ipv6 = is_ipv6
        self.__is_change_shaping_rule = is_change_shaping_rule
        self.__is_add_shaping_rule = is_add_shaping_rule
        self.__is_enable_iptables = is_enable_iptables
        self.__tc_command_output = tc_command_output

        self.__qdisc_major_id = self.__get_device_qdisc_major_id()

        self.__iptables_ctrl = IptablesMangleController(
            is_enable_iptables, self.ip_version)

        self.__init_shaper(shaping_algorithm)

    def validate(self):
        verify_network_interface(self.device)
        self.__validate_netem_parameter()
        self.__validate_src_network()
        self.__validate_port()

    def __validate_src_network(self):
        if any([
                typepy.is_null_string(self.src_network),
                self.__shaper.algorithm_name == ShapingAlgorithm.HTB,
        ]):
            return

        if not self.is_enable_iptables:
            raise InvalidParameterError(
                "--iptables option required to use --src-network option",
                value=self.is_enable_iptables)

    def validate_bandwidth_rate(self):
        if typepy.is_null_string(self.__bandwidth_rate):
            return

        # convert bandwidth string [K/M/G bit per second] to a number
        bandwidth_rate = Humanreadable(
            self.__bandwidth_rate, kilo_size=KILO_SIZE).to_kilo_bit()

        if not RealNumber(bandwidth_rate).is_type():
            raise InvalidParameterError(
                "bandwidth_rate must be a number", value=bandwidth_rate)

        if bandwidth_rate <= 0:
            raise InvalidParameterError(
                "bandwidth_rate must be greater than zero",
                value=bandwidth_rate)

        no_limit_kbits = get_no_limit_kbits(self.get_tc_device())
        if bandwidth_rate > no_limit_kbits:
            raise InvalidParameterError(
                "bandwidth_rate must be less than {}".format(no_limit_kbits),
                value=bandwidth_rate)

    def sanitize(self):
        self.__dst_network = sanitize_network(
            self.dst_network, self.ip_version)
        self.__src_network = sanitize_network(
            self.src_network, self.ip_version)

    def get_tc_device(self):
        """
        Return a device name that associated network communication direction.
        """

        if self.direction == TrafficDirection.OUTGOING:
            return self.device

        if self.direction == TrafficDirection.INCOMING:
            return self.ifb_device

        raise InvalidParameterError(
            "unknown direction",
            expected=TrafficDirection.LIST, value=self.direction)

    def get_tc_command(self, sub_command):
        valid_sub_command_list = (
            Tc.Subcommand.CLASS, Tc.Subcommand.FILTER, Tc.Subcommand.QDISC)
        if sub_command not in valid_sub_command_list:
            raise InvalidParameterError(
                "unknown sub command",
                expected=valid_sub_command_list, value=sub_command)

        return "tc {:s} {:s}".format(
            sub_command, "change" if self.is_change_shaping_rule else "add")

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

    def delete_all_tc(self):
        result_list = []

        with logging_context("delete qdisc"):
            returncode = run_command_helper(
                "tc qdisc del dev {:s} root".format(self.device),
                re.compile("RTNETLINK answers: No such file or directory"),
                "no qdisc to delete for the outgoing device.")
            result_list.append(returncode == 0)

        with logging_context("delete ingress qdisc"):
            returncode = run_command_helper(
                "tc qdisc del dev {:s} ingress".format(self.device),
                re.compile("|".join([
                    "RTNETLINK answers: Invalid argument",
                    "RTNETLINK answers: No such file or directory",
                ])),
                "no qdisc to delete for the incoming device.")
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

    def delete_tc(self):
        """
        Delete a specific shaping rule.
        """

        from ._shaping_rule_finder import TcShapingRuleFinder

        rule_finder = TcShapingRuleFinder(logger=logger, tc=self)

        parent = rule_finder.find_parent()
        filter_param = rule_finder.find_filter_param()

        logger.debug("delete_tc: pram={}".format(filter_param))

        if not filter_param:
            message = "shaping rule not found."
            if rule_finder.is_empty_filter_condition():
                message += (
                    " you can delete all of the shaping rules "
                    "with --all option.")
            logger.error(message)

            return 1

        filter_del_command = (
            "tc filter del dev {dev:s} protocol {protocol:s} "
            "parent {parent:} handle {handle:s} prio {prio:} u32".format(
                dev=rule_finder.get_parsed_device(),
                protocol=filter_param.get(Tc.Param.PROTOCOL),
                parent="{:s}:".format(parent.split(":")[0]),
                handle=filter_param.get(Tc.Param.FILTER_ID),
                prio=filter_param.get(Tc.Param.PRIORITY),
            ))

        result = run_command_helper(
            command=filter_del_command, error_regexp=None, message=None)

        rule_finder.clear()
        if not rule_finder.is_any_filter():
            logger.debug("there are no filters remain. delete qdiscs.")
            self.delete_all_tc()

        return result

    def __init_shaper(self, shaping_algorithm):
        if shaping_algorithm is None:
            self.__shaper = None
            return

        if shaping_algorithm == ShapingAlgorithm.HTB:
            self.__shaper = HtbShaper(self)
            return

        if shaping_algorithm == ShapingAlgorithm.TBF:
            self.__shaper = TbfShaper(self)
            return

        raise InvalidParameterError(
            "unknown shaping algorithm",
            expected=ShapingAlgorithm.LIST, value=shaping_algorithm)

    def __validate_network_delay(self):
        try:
            self.latency_time.validate(
                min_value=Tc.ValueRange.LatencyTime.MIN,
                max_value=Tc.ValueRange.LatencyTime.MAX)
        except InvalidParameterError as e:
            raise InvalidParameterError("delay {}".format(str(e)))

        try:
            self.latency_distro_time.validate(
                min_value=Tc.ValueRange.LatencyTime.MIN,
                max_value=Tc.ValueRange.LatencyTime.MAX)
        except InvalidParameterError as e:
            raise InvalidParameterError("delay-distro {}".format(str(e)))

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
        if self.reordering_rate and not self.latency_time:
            raise InvalidParameterError(
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
            self.packet_loss_rate,
            self.packet_duplicate_rate,
            self.corruption_rate,
            self.reordering_rate,
        ]

        if all([
                not RealNumber(netem_param_value).is_type()
                or netem_param_value <= 0
                for netem_param_value in netem_param_value_list
        ] + [
            self.latency_time <= HumanReadableTime(
                Tc.ValueRange.LatencyTime.MIN)
        ]):
            raise InvalidParameterError(
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
        base_device_hash = hashlib.md5(six.b(self.device)).hexdigest()[:3]
        device_hash_prefix = "1"

        return int(device_hash_prefix + base_device_hash, 16)

    def __setup_ifb(self):
        if self.direction != TrafficDirection.INCOMING:
            return 0

        if typepy.is_null_string(self.ifb_device):
            return -1

        return_code = 0

        return_code |= spr.SubprocessRunner("modprobe ifb").run()

        if self.is_add_shaping_rule or self.is_change_shaping_rule:
            notice_message = None
        else:
            notice_message = self.EXISTS_MSG_TEMPLATE.format(
                "failed to add ip link: ip link already exists.")
        return_code |= run_command_helper(
            "ip link add {:s} type ifb".format(self.ifb_device),
            self.REGEXP_FILE_EXISTS, notice_message)

        return_code |= spr.SubprocessRunner(
            "ip link set dev {:s} up".format(self.ifb_device)).run()

        base_command = "tc qdisc add"
        if self.is_add_shaping_rule or self.is_change_shaping_rule:
            notice_message = None
        else:
            notice_message = self.EXISTS_MSG_TEMPLATE.format(
                "failed to '{:s}': ingress qdisc already exists.".format(
                    base_command))
        return_code |= run_command_helper(
            "{:s} dev {:s} ingress".format(base_command, self.device),
            self.REGEXP_FILE_EXISTS, notice_message)

        return_code |= spr.SubprocessRunner(" ".join([
            "tc filter add",
            "dev {:s}".format(self.device),
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
