# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import, division

import errno
import re

import msgfy
import six
import subprocrunner as spr
import typepy
from humanreadable import ParameterError

from ._common import find_bin_path, logging_context, run_command_helper, validate_within_min_max
from ._const import (
    LIST_MANGLE_TABLE_OPTION,
    ShapingAlgorithm,
    Tc,
    TcCommandOutput,
    TcSubCommand,
    TrafficDirection,
)
from ._error import NetworkInterfaceNotFoundError
from ._iptables import IptablesMangleController, get_iptables_base_command
from ._logger import logger
from ._network import sanitize_network, verify_network_interface
from ._shaping_rule_finder import TcShapingRuleFinder
from ._tc_command_helper import get_tc_base_command
from .shaper.htb import HtbShaper
from .shaper.tbf import TbfShaper


class TrafficControl(object):
    __MIN_PORT = 0
    __MAX_PORT = 65535

    REGEXP_FILE_EXISTS = re.compile("RTNETLINK answers: File exists")

    EXISTS_MSG_TEMPLATE = "\n".join(
        [
            "{:s} try to execute with: ",
            "  (a) --overwrite option if you want to overwrite the existing rule.",
            "  (b) --add option if you want to add a new rule in addition to the existing rules.",
            "  (c) --change option if you want to change the existing rule parameter.",
        ]
    )

    @property
    def device(self):
        return self.__device

    @property
    def tc_target(self):
        return self.__device

    @property
    def ifb_device(self):
        return "ifb{:d}".format(self.__qdisc_major_id)

    @property
    def direction(self):
        return self.__direction

    @property
    def netem_param(self):
        return self.__netem_param

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
        self,
        device,
        direction=None,
        netem_param=None,
        dst_network=None,
        exclude_dst_network=None,
        src_network=None,
        exclude_src_network=None,
        dst_port=None,
        exclude_dst_port=None,
        src_port=None,
        exclude_src_port=None,
        is_ipv6=False,
        is_change_shaping_rule=False,
        is_add_shaping_rule=False,
        is_enable_iptables=True,
        shaping_algorithm=None,
        tc_command_output=TcCommandOutput.NOT_SET,
    ):
        self.__device = device

        self.__direction = direction
        self.__netem_param = netem_param
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

        self.__iptables_ctrl = IptablesMangleController(is_enable_iptables, self.ip_version)

        self.__init_shaper(shaping_algorithm)

    def validate(self):
        verify_network_interface(self.device, self.__tc_command_output)
        self.__netem_param.validate_netem_parameter()
        self.__validate_src_network()
        self.__validate_port()

    def __validate_src_network(self):
        if any(
            [
                typepy.is_null_string(self.src_network),
                self.__shaper.algorithm_name == ShapingAlgorithm.HTB,
            ]
        ):
            return

        if not self.is_enable_iptables:
            raise ParameterError(
                "--iptables option required to use --src-network option",
                value=self.is_enable_iptables,
            )

    def sanitize(self):
        self.__dst_network = sanitize_network(self.dst_network, self.ip_version)
        self.__src_network = sanitize_network(self.src_network, self.ip_version)

    def get_tc_device(self):
        """
        Return a device name that associated network communication direction.
        """

        if self.direction == TrafficDirection.OUTGOING:
            return self.device

        if self.direction == TrafficDirection.INCOMING:
            return self.ifb_device

        raise ParameterError(
            "unknown direction", expected=TrafficDirection.LIST, value=self.direction
        )

    def get_tc_command(self, subcommand):
        return "{:s} {:s}".format(
            get_tc_base_command(subcommand), "change" if self.is_change_shaping_rule else "add"
        )

    def get_command_history(self):
        def tc_command_filter(command):
            if get_iptables_base_command():
                if re.search(
                    "^{:s} {:s}".format(
                        get_iptables_base_command(), re.escape(LIST_MANGLE_TABLE_OPTION)
                    ),
                    command,
                ):
                    return False

            if re.search("^{:s} .* show dev".format(find_bin_path("tc")), command):
                return False

            if re.search("^ip (netns exec |link show )", command):
                return False

            if find_bin_path("getcap"):
                if re.search("^{:s}".format(find_bin_path("getcap")), command):
                    return False

            return True

        return filter(tc_command_filter, spr.SubprocessRunner.get_history())

    def make_srcdst_text(self):
        return "".join(
            [
                six.text_type(item)
                for item in [
                    self.dst_network,
                    self.exclude_dst_network,
                    self.src_network,
                    self.exclude_src_network,
                    self.src_port,
                    self.exclude_src_port,
                    self.dst_port,
                    self.exclude_dst_port,
                ]
            ]
        )

    def set_tc(self):
        rule_finder = TcShapingRuleFinder(logger=logger, tc=self)
        if self.__is_change_shaping_rule and self.tc_command_output == TcCommandOutput.NOT_SET:
            if rule_finder.find_filter_param() is not None:
                self.__is_change_shaping_rule = True
            else:
                self.__is_change_shaping_rule = False
                self.__is_add_shaping_rule = True

        self.__setup_ifb()

        return self.__shaper.set_shaping()

    def delete_all_tc(self):
        result_list = []

        result_list.append(self.__delete_qdisc())
        result_list.append(self.__delete_ingress_qdisc())

        try:
            result_list.append(self.__delete_ifb_device() == 0)
        except NetworkInterfaceNotFoundError as e:
            logger.debug(msgfy.to_debug_message(e))
            result_list.append(False)

        with logging_context("delete iptables mangle table entries"):
            try:
                self.iptables_ctrl.clear()
            except OSError as e:
                logger.warn("{} (can not delete iptables entries)".format(e))

        return any(result_list)

    def delete_tc(self):
        """
        Delete a specific shaping rule.
        """

        rule_finder = TcShapingRuleFinder(logger=logger, tc=self)
        filter_param = rule_finder.find_filter_param()

        if not filter_param:
            message = "shaping rule not found ({}).".format(rule_finder.get_filter_string())
            if rule_finder.is_empty_filter_condition():
                message += " you can delete all of the shaping rules with --all option."
            logger.error(message)

            return 1

        logger.info("delete a shaping rule: {}".format(dict(filter_param)))

        filter_del_command = (
            "{command:s} del dev {dev:s} protocol {protocol:s} "
            "parent {parent:} handle {handle:s} prio {prio:} u32".format(
                command=get_tc_base_command(TcSubCommand.FILTER),
                dev=rule_finder.get_parsed_device(),
                protocol=filter_param.get(Tc.Param.PROTOCOL),
                parent="{:s}:".format(rule_finder.find_parent().split(":")[0]),
                handle=filter_param.get(Tc.Param.FILTER_ID),
                prio=filter_param.get(Tc.Param.PRIORITY),
            )
        )

        result = run_command_helper(
            command=filter_del_command, ignore_error_msg_regexp=None, notice_msg=None
        )

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

        raise ParameterError(
            "unknown shaping algorithm", expected=ShapingAlgorithm.LIST, value=shaping_algorithm
        )

    def __validate_port(self):
        validate_within_min_max(
            "src_port", self.src_port, self.__MIN_PORT, self.__MAX_PORT, unit=None
        )

        validate_within_min_max(
            "dst_port", self.dst_port, self.__MIN_PORT, self.__MAX_PORT, unit=None
        )

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
        modprobe_proc = spr.SubprocessRunner("modprobe ifb")

        try:
            if modprobe_proc.run() != 0:
                logger.error(modprobe_proc.stderr)
        except spr.CommandError as e:
            logger.debug(msgfy.to_debug_message(e))

        if self.is_add_shaping_rule or self.is_change_shaping_rule:
            notice_message = None
        else:
            notice_message = self.EXISTS_MSG_TEMPLATE.format(
                "failed to add ip link: ip link already exists."
            )

        return_code |= run_command_helper(
            "{:s} link add {:s} type ifb".format(find_bin_path("ip"), self.ifb_device),
            ignore_error_msg_regexp=self.REGEXP_FILE_EXISTS,
            notice_msg=notice_message,
        )

        return_code |= spr.SubprocessRunner(
            "{:s} link set dev {:s} up".format(find_bin_path("ip"), self.ifb_device)
        ).run()

        base_command = "{:s} add".format(get_tc_base_command(TcSubCommand.QDISC))
        if self.is_add_shaping_rule or self.is_change_shaping_rule:
            notice_message = None
        else:
            notice_message = self.EXISTS_MSG_TEMPLATE.format(
                "failed to '{:s}': ingress qdisc already exists.".format(base_command)
            )
        return_code |= run_command_helper(
            "{:s} dev {:s} ingress".format(base_command, self.device),
            ignore_error_msg_regexp=self.REGEXP_FILE_EXISTS,
            notice_msg=notice_message,
        )

        return_code |= spr.SubprocessRunner(
            " ".join(
                [
                    "{:s} add".format(get_tc_base_command(TcSubCommand.FILTER)),
                    "dev {:s}".format(self.device),
                    "parent ffff: protocol {:s} u32 match u32 0 0".format(self.protocol),
                    "flowid {:x}:".format(self.__qdisc_major_id),
                    "action mirred egress redirect",
                    "dev {:s}".format(self.ifb_device),
                ]
            )
        ).run()

        return return_code

    def __delete_qdisc(self):
        logging_msg = "delete {} qdisc".format(self.device)

        with logging_context(logging_msg):
            runner = spr.SubprocessRunner(
                "{:s} del dev {:s} root".format(
                    get_tc_base_command(TcSubCommand.QDISC), self.device
                )
            )
            runner.run()
            if re.search("RTNETLINK answers: No such file or directory", runner.stderr):
                logger.notice("no qdisc to delete for the outgoing device.")
                return False
            elif re.search("Cannot find device", runner.stderr):
                raise NetworkInterfaceNotFoundError(target=self.device)
            else:
                is_success = runner.returncode == 0
                if is_success:
                    logger.info(logging_msg)
                return is_success

    def __delete_ingress_qdisc(self):
        logging_msg = "delete {} ingress qdisc".format(self.device)

        with logging_context(logging_msg):
            returncode = run_command_helper(
                "{:s} del dev {:s} ingress".format(
                    get_tc_base_command(TcSubCommand.QDISC), self.device
                ),
                ignore_error_msg_regexp=re.compile(
                    "|".join(
                        [
                            "RTNETLINK answers: Invalid argument",  # debian/ubuntu
                            "RTNETLINK answers: No such file or directory",  # debian/ubuntu
                            "Error: Cannot find specified qdisc on specified device",  # RHEL/fedora
                        ]
                    )
                ),
                notice_msg="no qdisc to delete for the incoming device.",
            )
            is_success = returncode == 0
            if is_success:
                logger.info(logging_msg)

            return is_success

    def __delete_ifb_device(self):
        from ._capabilities import has_execution_authority, get_permission_error_message

        logging_msg = "delete {} ifb device ({})".format(self.device, self.ifb_device)
        with logging_context(logging_msg):
            verify_network_interface(self.ifb_device, self.__tc_command_output)

            if not has_execution_authority("ip"):
                logger.warn(get_permission_error_message("ip"))

                return errno.EPERM

            commands = [
                "{:s} del dev {:s} root".format(
                    get_tc_base_command(TcSubCommand.QDISC), self.ifb_device
                ),
                "{:s} link set dev {:s} down".format(find_bin_path("ip"), self.ifb_device),
                "{:s} link delete {:s} type ifb".format(find_bin_path("ip"), self.ifb_device),
            ]

            if all([spr.SubprocessRunner(command).run() != 0 for command in commands]):
                return 2

        logger.info(logging_msg)

        return 0
