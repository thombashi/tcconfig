"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import errno
import re
import sys
from bisect import bisect_left

import pyroute2
import typepy
from pyroute2.netlink.rtnl.tcmsg.common import TIME_UNITS_PER_SEC, get_hz

from .._common import is_execute_tc_command, logging_context, run_command_helper
from .._const import ShapingAlgorithm, TcSubCommand
from .._error import TcAlreadyExist
from .._logger import logger
from .._network import get_upper_limit_rate
from .._tc_command_helper import run_tc_show
from ._interface import AbstractShaper


# Make this a function, so we can mock it for testing
def tick_in_usec() -> float:
    return pyroute2.netlink.rtnl.tcmsg.common.tick_in_usec


# Emulation of tc's buggy time2tick implementation, which
# rounds to int twice
def time2tick_bug(time: int) -> int:
    return int(int(time) * tick_in_usec())


# An accurate implementation of tick2time (unlike tc's), not rounding.
def tick2time_true(tick: float) -> float:
    return tick / tick_in_usec()


def calc_xmittime_bug(rate: int, size: int) -> int:
    return int(time2tick_bug(TIME_UNITS_PER_SEC * (float(size) / rate)))


def calc_xmitsize_true(rate: int, ticks: int) -> float:
    return (float(rate) * tick2time_true(ticks)) / TIME_UNITS_PER_SEC


# tc tries to set the default burst and cburst size to (int)(rate / get_hz() + mtu),
# with the comment
#     compute minimal allowed burst from rate; mtu is added here to make
#     sure that buffer is larger than mtu and to have some safeguard space
#
# Unfortunately, in tc from iproute2 version 6.14 and earlier, there is a rounding
# bug such that the actual burst size set will often be too small, which will cause
# bandwidth limitations to be too aggressive.
#
# Calculate the minimum necessary size to set burst and cburst to, to ensure that they
# are at least the size that tc was trying to set them to.
#
# TODO: check whether tc is from iproute2 version 6.15 or later, and if so bypass the
# adjustment and don't set the default.
def default_burst_size(rate: int, mtu: int) -> int:
    return int(rate / get_hz() + mtu)


def adjusted_burst_size(desired_burst: int, rate: int) -> int:
    if sys.version_info >= (3, 10):
        return bisect_left(
            range(1 << 32),
            True,
            key=lambda b: calc_xmitsize_true(rate, calc_xmittime_bug(rate, b)) >= desired_burst,
        )
    else:
        adjusted_burst = desired_burst
        while adjusted_burst < (1 << 32):
            if calc_xmitsize_true(rate, calc_xmittime_bug(rate, adjusted_burst)) >= desired_burst:
                return adjusted_burst
            adjusted_burst += 1
        return adjusted_burst


class HtbShaper(AbstractShaper):
    __DEFAULT_CLASS_MINOR_ID = 1

    class MinQdiscMinorId:
        OUTGOING = 40
        INCOMING = 20

    @property
    def algorithm_name(self) -> str:
        return ShapingAlgorithm.HTB.value

    def __init__(self, tc_obj):
        super().__init__(tc_obj)

        self.__qdisc_minor_id = None
        self.__qdisc_minor_id_count = 0
        self.__netem_major_id = None
        self.__classid_wo_shaping = None

    def _get_qdisc_minor_id(self):
        if self.__qdisc_minor_id is None:
            self.__qdisc_minor_id = self.__get_unique_qdisc_minor_id()
            logger.debug(f"__get_unique_qdisc_minor_id: {self.__qdisc_minor_id:d}")

        return self.__qdisc_minor_id

    def _get_netem_qdisc_major_id(self, base_id):
        if self.__netem_major_id is None:
            self.__netem_major_id = self.__get_unique_netem_major_id()

        return self.__netem_major_id

    def _make_qdisc(self):
        if self._tc_obj.is_change_shaping_rule:
            return 0

        base_command = self._tc_obj.get_tc_command(TcSubCommand.QDISC)
        handle = f"{self._tc_obj.qdisc_major_id_str:s}:"

        if self._tc_obj.is_add_shaping_rule:
            message = None
        else:
            message = self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': qdisc already exists "
                "({dev:s}, handle={handle:s}, algo={algorithm:s}).".format(
                    command=base_command,
                    dev=self._dev,
                    handle=handle,
                    algorithm=self.algorithm_name,
                )
            )

        run_command_helper(
            " ".join(
                [
                    base_command,
                    self._dev,
                    "root",
                    f"handle {handle:s}",
                    self.algorithm_name,
                    f"default {self.__DEFAULT_CLASS_MINOR_ID:d}",
                ]
            ),
            ignore_error_msg_regexp=self._tc_obj.REGEXP_FILE_EXISTS,
            notice_msg=message,
            exception_class=TcAlreadyExist,
        )

        return self.__add_default_class()

    def _add_rate(self):
        base_command = self._tc_obj.get_tc_command(TcSubCommand.CLASS)
        parent = "{:s}:".format(
            self._get_tc_parent(f"{self._tc_obj.qdisc_major_id_str:s}:").split(":")[0]
        )
        classid = self._get_tc_parent(
            f"{self._tc_obj.qdisc_major_id_str:s}:{self._get_qdisc_minor_id():d}"
        )
        upper_limit_rate = get_upper_limit_rate(self._tc_device)

        bandwidth = self._tc_obj.netem_param.bandwidth_rate
        if bandwidth is None:
            bandwidth = upper_limit_rate

        command_item_list = [
            base_command,
            self._dev,
            f"parent {parent:s}",
            f"classid {classid:s}",
            self.algorithm_name,
            f"rate {bandwidth.kilo_bps}Kbit",
            f"ceil {bandwidth.kilo_bps}Kbit",
        ]

        mtu = self._tc_obj.netem_param.mtu
        if mtu:
            command_item_list.extend([f"mtu {mtu:d}"])

        if bandwidth != upper_limit_rate:
            rate = bandwidth.byte_per_sec
            desired_burst = self._tc_obj.netem_param.burst
            # TODO: check whether tc is from iproute2 version 6.15 or later, and if so bypass the default
            # and adjustment.
            if not desired_burst:
                if not mtu:
                    mtu = 1600
                desired_burst = default_burst_size(rate, mtu)
            burst = adjusted_burst_size(desired_burst, rate)

            command_item_list.extend(
                [
                    f"burst {burst}b",
                    f"cburst {burst}b",
                ]
            )

        run_command_helper(
            " ".join(command_item_list),
            ignore_error_msg_regexp=self._tc_obj.REGEXP_FILE_EXISTS,
            notice_msg=self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': class already exists "
                "({dev:s}, parent={parent:s}, classid={classid:s}, "
                "algo={algorithm:s}).".format(
                    command=base_command,
                    dev=self._dev,
                    parent=parent,
                    classid=classid,
                    algorithm=self.algorithm_name,
                )
            ),
            exception_class=TcAlreadyExist,
        )

    def _add_exclude_filter(self):
        import subprocrunner

        if all(
            [
                typepy.is_null_string(param)
                for param in (
                    self._tc_obj.exclude_dst_network,
                    self._tc_obj.exclude_src_network,
                    self._tc_obj.exclude_dst_port,
                    self._tc_obj.exclude_src_port,
                )
            ]
        ):
            logger.debug("no exclude filter found")
            return

        command_item_list = [
            self._tc_obj.get_tc_command(TcSubCommand.FILTER),
            self._dev,
            f"protocol {self._tc_obj.protocol:s}",
            f"parent {self._tc_obj.qdisc_major_id_str:s}:",
            f"prio {self._get_filter_prio(is_exclude_filter=True):d}",
            "u32",
        ]

        if typepy.is_not_null_string(self._tc_obj.exclude_dst_network):
            command_item_list.append(
                "match {:s} {:s} {:s}".format(
                    self._tc_obj.protocol_match, "dst", self._tc_obj.exclude_dst_network
                )
            )

        if typepy.is_not_null_string(self._tc_obj.exclude_src_network):
            command_item_list.append(
                "match {:s} {:s} {:s}".format(
                    self._tc_obj.protocol_match, "src", self._tc_obj.exclude_src_network
                )
            )

        if typepy.is_not_null_string(self._tc_obj.exclude_dst_port):
            command_item_list.append(
                "match {:s} {:s} {:s} 0xffff".format(
                    self._tc_obj.protocol_match, "dport", self._tc_obj.exclude_dst_port
                )
            )

        if typepy.is_not_null_string(self._tc_obj.exclude_src_port):
            command_item_list.append(
                "match {:s} {:s} {:s} 0xffff".format(
                    self._tc_obj.protocol_match, "sport", self._tc_obj.exclude_src_port
                )
            )

        command_item_list.append(f"flowid {self.__classid_wo_shaping:s}")

        return subprocrunner.SubprocessRunner(" ".join(command_item_list)).run()

    def set_shaping(self):
        is_add_shaping_rule = self._tc_obj.is_add_shaping_rule

        with logging_context("_make_qdisc"):
            try:
                self._make_qdisc()
            except TcAlreadyExist:
                if not is_add_shaping_rule:
                    return errno.EINVAL

        with logging_context("_add_rate"):
            try:
                self._add_rate()
            except TcAlreadyExist:
                if not is_add_shaping_rule:
                    return errno.EINVAL

        with logging_context("_set_netem"):
            self._set_netem()

        with logging_context("_add_exclude_filter"):
            self._add_exclude_filter()

        with logging_context("_add_filter"):
            self._add_filter()

        return 0

    def __get_unique_qdisc_minor_id(self):
        if not is_execute_tc_command(self._tc_obj.tc_command_output):
            return (
                int(
                    self._tc_obj.netem_param.calc_hash(self._tc_obj.make_srcdst_text())[-2:],
                    16,
                )
                + 1
            )

        if self._tc_obj.is_change_shaping_rule:
            self.__qdisc_minor_id_count += 1

            return self.__DEFAULT_CLASS_MINOR_ID + self.__qdisc_minor_id_count

        exist_class_item_list = re.findall(
            "class {algorithm:s} {qdisc_major_id:s}:[0-9]+".format(
                algorithm=self.algorithm_name,
                qdisc_major_id=self._tc_obj.qdisc_major_id_str,
            ),
            run_tc_show(TcSubCommand.CLASS, self._tc_device, self._tc_obj.tc_command_output),
            re.MULTILINE,
        )

        exist_class_minor_id_list = []
        for class_item in exist_class_item_list:
            try:
                exist_class_minor_id_list.append(typepy.Integer(class_item.split(":")[1]).convert())
            except typepy.TypeConversionError:
                continue

        logger.debug(f"existing class list with {self._dev:s}: {exist_class_item_list}")
        logger.debug(f"existing minor classid list with {self._dev:s}: {exist_class_minor_id_list}")

        next_minor_id = self.__DEFAULT_CLASS_MINOR_ID
        while True:
            if next_minor_id not in exist_class_minor_id_list:
                break

            next_minor_id += 1

        return next_minor_id

    def __extract_exist_netem_major_ids(self) -> list[int]:
        tcshow_out = run_tc_show(
            TcSubCommand.QDISC, self._tc_device, self._tc_obj.tc_command_output
        )
        exist_netem_items = re.findall(
            "qdisc [a-z]+ [a-z0-9]+",
            tcshow_out,
            re.MULTILINE,
        )

        logger.debug(f"existing netem list with {self._dev:s}: {exist_netem_items}")

        exist_netem_major_id_list = []
        for netem_item in exist_netem_items:
            exist_netem_major_id_list.append(int(netem_item.split()[-1], 16))

        return exist_netem_major_id_list

    def __get_unique_netem_major_id(self):
        exist_netem_major_ids = self.__extract_exist_netem_major_ids()

        logger.debug(f"existing netem major id list with {self._dev:s}: {exist_netem_major_ids}")

        next_netem_major_id = self._tc_obj.netem_param.calc_device_qdisc_major_id()
        while True:
            if next_netem_major_id not in exist_netem_major_ids:
                break

            next_netem_major_id += 1

        return next_netem_major_id

    def __add_default_class(self):
        base_command = self._tc_obj.get_tc_command(TcSubCommand.CLASS)
        parent = f"{self._tc_obj.qdisc_major_id_str:s}:"
        classid = f"{self._tc_obj.qdisc_major_id_str:s}:{self.__DEFAULT_CLASS_MINOR_ID:d}"
        self.__classid_wo_shaping = classid

        if self._tc_obj.is_add_shaping_rule:
            message = None
        else:
            message = self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to default '{command:s}': class already exists "
                "({dev}, parent={parent:s}, classid={classid:s}, "
                "algo={algorithm:s})".format(
                    command=base_command,
                    dev=self._dev,
                    parent=parent,
                    classid=classid,
                    algorithm=self.algorithm_name,
                )
            )

        return run_command_helper(
            " ".join(
                [
                    base_command,
                    self._dev,
                    f"parent {parent:s}",
                    f"classid {classid:s}",
                    self.algorithm_name,
                    f"rate {get_upper_limit_rate(self._tc_device).kilo_bps}kbit",
                ]
            ),
            ignore_error_msg_regexp=self._tc_obj.REGEXP_FILE_EXISTS,
            notice_msg=message,
        )
