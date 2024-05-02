"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import errno
import re
from typing import List

import typepy

from .._common import is_execute_tc_command, logging_context, run_command_helper
from .._const import ShapingAlgorithm, TcSubCommand
from .._error import TcAlreadyExist
from .._logger import logger
from .._network import get_upper_limit_rate
from .._tc_command_helper import run_tc_show
from ._interface import AbstractShaper


class HtbShaper(AbstractShaper):
    __DEFAULT_CLASS_MINOR_ID = 1

    class MinQdiscMinorId:
        OUTGOING = 40
        INCOMING = 20

    @property
    def algorithm_name(self):
        return ShapingAlgorithm.HTB

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

        if bandwidth != upper_limit_rate:
            command_item_list.extend(
                [
                    f"burst {bandwidth.kilo_byte_per_sec}KB",
                    f"cburst {bandwidth.kilo_byte_per_sec}KB",
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
                algorithm=ShapingAlgorithm.HTB,
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

    def __extract_exist_netem_major_ids(self) -> List[int]:
        tcshow_out = run_tc_show(
            TcSubCommand.QDISC, self._tc_device, self._tc_obj.tc_command_output
        )
        assert tcshow_out
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
