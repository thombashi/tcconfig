# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import re

import typepy

from .._common import (
    logging_context,
    run_command_helper,
    run_tc_show,
)
from .._const import (
    KILO_SIZE,
    Tc,
)
from .._converter import Humanreadable
from .._error import (
    TcAlreadyExist,
    EmptyParameterError,
)
from .._logger import logger
from ._interface import AbstractShaper


class HtbShaper(AbstractShaper):

    __DEFAULT_CLASS_MINOR_ID = 1

    class MinQdiscMinorId(object):
        OUTGOING = 40
        INCOMING = 20

    @property
    def algorithm_name(self):
        return "htb"

    def __init__(self, tc_obj):
        super(HtbShaper, self).__init__(tc_obj)

        self.__qdisc_minor_id = None
        self.__netem_major_id = None

    def get_qdisc_minor_id(self):
        if self.__qdisc_minor_id is None:
            self.__qdisc_minor_id = self.__get_unique_qdisc_minor_id()

        return self.__qdisc_minor_id

    def get_netem_qdisc_major_id(self, base_id):
        if self.__netem_major_id is None:
            self.__netem_major_id = self.__get_unique_netem_major_id()

        return self.__netem_major_id

    def get_no_limit_kbits(self):
        # upper rate limit of iproute2 was 34.359.738.360 bits per second
        # older than 3.14.0
        # http://git.kernel.org/cgit/linux/kernel/git/shemminger/iproute2.git/commit/?id=8334bb325d5178483a3063c5f06858b46d993dc7

        iproute2_upper_kbits = Humanreadable(
            "32G", kilo_size=KILO_SIZE).to_kilo_value()

        try:
            with open("/sys/class/net/{:s}/speed".format(self.tc_device)) as f:
                return min(
                    int(f.read().strip()) * KILO_SIZE, iproute2_upper_kbits)
        except IOError:
            return iproute2_upper_kbits

    def make_qdisc(self):
        handle = "{:s}:".format(self._tc_obj.qdisc_major_id_str)
        command = " ".join([
            "tc qdisc add",
            self.dev,
            "root",
            "handle {:s}".format(handle),
            self.algorithm_name,
            "default {:d}".format(self.__DEFAULT_CLASS_MINOR_ID),
        ])

        if self._tc_obj.is_add_shaper:
            message = None
        else:
            message = self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to add qdisc: qdisc already exists "
                "({:s}, handle={:s}, algo={:s}).".format(
                    self.dev, handle, self.algorithm_name))

        run_command_helper(
            command, self._tc_obj.REGEXP_FILE_EXISTS, message, TcAlreadyExist)

        return self.__add_default_class()

    def add_rate(self):
        parent = "{:s}:".format(self._tc_obj.qdisc_major_id_str)
        classid = "{:s}:{:d}".format(
            self._tc_obj.qdisc_major_id_str,
            self.get_qdisc_minor_id())
        no_limit_kbits = self.get_no_limit_kbits()

        try:
            self._tc_obj.validate_bandwidth_rate()
            kbits = self._tc_obj.bandwidth_rate
        except EmptyParameterError:
            kbits = no_limit_kbits

        command_list = [
            "tc class add",
            self.dev,
            "parent {:s}".format(parent),
            "classid {:s}".format(classid),
            self.algorithm_name,
            "rate {:f}Kbit".format(kbits),
            "ceil {:f}Kbit".format(kbits),
        ]

        if kbits != no_limit_kbits:
            command_list.extend([
                "burst {:f}KB".format(kbits / (10 * 8)),
                "cburst {:f}KB".format(kbits / (10 * 8)),
            ])

        command = " ".join(command_list)
        run_command_helper(
            command,
            self._tc_obj.REGEXP_FILE_EXISTS,
            self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to add class: class already exists "
                "({:s}, parent={:s}, classid={:s}, algo={:s}).".format(
                    self.dev, parent, classid, self.algorithm_name)),
            TcAlreadyExist
        )

    def set_shaping(self):
        is_add_shaper = self._tc_obj.is_add_shaper

        with logging_context("make_qdisc"):
            try:
                self.make_qdisc()
            except TcAlreadyExist:
                if not is_add_shaper:
                    return

        with logging_context("add_rate"):
            try:
                self.add_rate()
            except TcAlreadyExist:
                if not is_add_shaper:
                    return

        with logging_context("set_netem"):
            self.set_netem()

        with logging_context("add_filter"):
            self.add_filter()

    def __get_unique_qdisc_minor_id(self):
        exist_class_item_list = re.findall(
            "class htb {}".format(
                self._tc_obj.qdisc_major_id_str) + "[\:][0-9]+",
            run_tc_show(Tc.Subcommand.CLASS, self.tc_device),
            re.MULTILINE)

        exist_class_minor_id_list = []
        for class_item in exist_class_item_list:
            try:
                exist_class_minor_id_list.append(
                    typepy.type.Integer(class_item.split(":")[1]).convert())
            except typepy.TypeConversionError:
                continue

        logger.debug("existing class list with {:s}: {}".format(
            self.dev, exist_class_item_list))
        logger.debug("existing minor classid list with {:s}: {}".format(
            self.dev, exist_class_minor_id_list))

        next_minor_id = self.__DEFAULT_CLASS_MINOR_ID
        while True:
            if next_minor_id not in exist_class_minor_id_list:
                break

            next_minor_id += 1

        return next_minor_id

    def __get_unique_netem_major_id(self):
        exist_netem_item_list = re.findall(
            "qdisc [a-z]+ [a-z0-9]+",
            run_tc_show(Tc.Subcommand.QDISC, self.tc_device),
            re.MULTILINE)

        exist_netem_major_id_list = []
        for netem_item in exist_netem_item_list:
            exist_netem_major_id_list.append(int(netem_item.split()[-1], 16))

        logger.debug("existing netem list with {:s}: {}".format(
            self.dev, exist_netem_item_list))
        logger.debug("existing netem major id list with {:s}: {}".format(
            self.dev, exist_netem_major_id_list))

        next_netem_major_id = self._tc_obj.qdisc_major_id + 128
        while True:
            if next_netem_major_id not in exist_netem_major_id_list:
                break

            next_netem_major_id += 1

        return next_netem_major_id

    def __add_default_class(self):
        parent = "{:s}:".format(self._tc_obj.qdisc_major_id_str)
        classid = "{:s}:{:d}".format(
            self._tc_obj.qdisc_major_id_str, self.__DEFAULT_CLASS_MINOR_ID)
        command = " ".join([
            "tc class add",
            self.dev,
            "parent {:s}".format(parent),
            "classid {:s}".format(classid),
            self.algorithm_name,
            "rate {}kbit".format(self.get_no_limit_kbits()),
        ])

        if self._tc_obj.is_add_shaper:
            message = None
        else:
            message = self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to add default class: class already exists "
                "({}, parent={:s}, classid={:s}, algo={:s})".format(
                    self.dev, parent, classid, self.algorithm_name))

        return run_command_helper(
            command,
            self._tc_obj.REGEXP_FILE_EXISTS,
            message)
