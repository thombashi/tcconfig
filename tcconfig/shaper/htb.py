# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import re

import dataproperty
from subprocrunner import SubprocessRunner

from .._common import (
    logging_context,
    run_command_helper,
)
from .._converter import Humanreadable
from .._error import (
    TcAlreadyExist,
    EmptyParameterError,
)
from .._logger import logger
from ._interface import AbstractShaper


class HtbShaper(AbstractShaper):

    __NO_LIMIT = "1000G"
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
        no_limit_bits = Humanreadable(
            self.__NO_LIMIT, kilo_size=1000).to_kilo_value()

        try:
            self._tc_obj.validate_bandwidth_rate()
            kbitps = self._tc_obj.bandwidth_rate
        except EmptyParameterError:
            kbitps = no_limit_bits

        command_list = [
            "tc class add",
            self.dev,
            "parent {:s}".format(parent),
            "classid {:s}".format(classid),
            self.algorithm_name,
            "rate {:f}Kbit".format(kbitps),
            "ceil {:f}Kbit".format(kbitps),
        ]

        if kbitps != no_limit_bits:
            command_list.extend([
                "burst {:f}KB".format(kbitps / (10 * 8)),
                "cburst {:f}KB".format(kbitps / (10 * 8)),
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
        runner = SubprocessRunner("tc class show {:s}".format(self.dev))
        runner.run()
        exist_class_item_list = re.findall(
            "class htb {}".format(
                self._tc_obj.qdisc_major_id_str) + "[\:][0-9]+",
            runner.stdout,
            re.MULTILINE)

        exist_class_minor_id_list = []
        for class_item in exist_class_item_list:
            inttype = dataproperty.IntegerType(class_item.split(":")[1])
            if not inttype.is_convertible_type():
                continue

            exist_class_minor_id_list.append(inttype.convert())

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
        runner = SubprocessRunner("tc qdisc show {:s}".format(self.dev))
        runner.run()
        exist_netem_item_list = re.findall(
            "qdisc [a-z]+ [a-z0-9]+", runner.stdout, re.MULTILINE)

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
            "rate {}bit".format(self.__NO_LIMIT),
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
