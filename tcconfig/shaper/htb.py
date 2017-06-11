# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import re

import typepy

from .._common import (
    get_no_limit_kbits,
    logging_context,
    run_command_helper,
    run_tc_show,
)
from .._const import (
    Tc,
    TcCommandOutput,
)
from .._error import TcAlreadyExist
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
        self.__qdisc_minor_id_count = 0
        self.__netem_major_id = None

    def get_qdisc_minor_id(self):
        if self.__qdisc_minor_id is None:
            self.__qdisc_minor_id = self.__get_unique_qdisc_minor_id()
            logger.debug("__get_unique_qdisc_minor_id: {:d}".format(
                self.__qdisc_minor_id))

        return self.__qdisc_minor_id

    def get_netem_qdisc_major_id(self, base_id):
        if self.__netem_major_id is None:
            self.__netem_major_id = self.__get_unique_netem_major_id()

        return self.__netem_major_id

    def make_qdisc(self):
        base_command = self._tc_obj.get_tc_command(Tc.Subcommand.QDISC)
        if base_command is None:
            return 0

        handle = "{:s}:".format(self._tc_obj.qdisc_major_id_str)

        if self._tc_obj.is_add_shaper:
            message = None
        else:
            message = self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': qdisc already exists "
                "({dev:s}, handle={handle:s}, algo={algorithm:s}).".format(
                    command=base_command, dev=self.dev, handle=handle,
                    algorithm=self.algorithm_name))

        run_command_helper(
            " ".join([
                base_command,
                self.dev,
                "root",
                "handle {:s}".format(handle),
                self.algorithm_name,
                "default {:d}".format(self.__DEFAULT_CLASS_MINOR_ID),
            ]),
            self._tc_obj.REGEXP_FILE_EXISTS,
            message,
            TcAlreadyExist)

        return self.__add_default_class()

    def add_rate(self):
        base_command = self._tc_obj.get_tc_command(Tc.Subcommand.CLASS)
        parent = "{:s}:".format(self._tc_obj.qdisc_major_id_str)
        classid = "{:s}:{:d}".format(
            self._tc_obj.qdisc_major_id_str,
            self.get_qdisc_minor_id())
        no_limit_kbits = get_no_limit_kbits(self.tc_device)

        kbits = self._tc_obj.bandwidth_rate
        if kbits is None:
            kbits = no_limit_kbits

        command_item_list = [
            base_command,
            self.dev,
            "parent {:s}".format(parent),
            "classid {:s}".format(classid),
            self.algorithm_name,
            "rate {}Kbit".format(kbits),
            "ceil {}Kbit".format(kbits),
        ]

        if kbits != no_limit_kbits:
            command_item_list.extend([
                "burst {}KB".format(kbits / (10 * 8)),
                "cburst {}KB".format(kbits / (10 * 8)),
            ])

        run_command_helper(
            " ".join(command_item_list),
            self._tc_obj.REGEXP_FILE_EXISTS,
            self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to '{command:s}': class already exists "
                "({dev:s}, parent={parent:s}, classid={classid:s}, "
                "algo={algorithm:s}).".format(
                    command=base_command, dev=self.dev, parent=parent,
                    classid=classid, algorithm=self.algorithm_name)),
            TcAlreadyExist
        )

    def set_shaping(self):
        is_add_shaper = self._tc_obj.is_add_shaper

        with logging_context("make_qdisc"):
            try:
                self.make_qdisc()
            except TcAlreadyExist:
                if not is_add_shaper:
                    return errno.EINVAL

        with logging_context("add_rate"):
            try:
                self.add_rate()
            except TcAlreadyExist:
                if not is_add_shaper:
                    return errno.EINVAL

        with logging_context("set_netem"):
            self.set_netem()

        with logging_context("add_filter"):
            self.add_filter()

        return 0

    def __get_unique_qdisc_minor_id(self):
        if (self._tc_obj.tc_command_output != TcCommandOutput.NOT_SET or
                self._tc_obj.is_change_shaper):
            self.__qdisc_minor_id_count += 1

            return self.__DEFAULT_CLASS_MINOR_ID + self.__qdisc_minor_id_count

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
        base_command = self._tc_obj.get_tc_command(Tc.Subcommand.CLASS)
        parent = "{:s}:".format(self._tc_obj.qdisc_major_id_str)
        classid = "{:s}:{:d}".format(
            self._tc_obj.qdisc_major_id_str, self.__DEFAULT_CLASS_MINOR_ID)

        if self._tc_obj.is_add_shaper:
            message = None
        else:
            message = self._tc_obj.EXISTS_MSG_TEMPLATE.format(
                "failed to default '{command:s}': class already exists "
                "({dev}, parent={parent:s}, classid={classid:s}, "
                "algo={algorithm:s})".format(
                    command=base_command, dev=self.dev, parent=parent,
                    classid=classid, algorithm=self.algorithm_name))

        return run_command_helper(
            " ".join([
                base_command,
                self.dev,
                "parent {:s}".format(parent),
                "classid {:s}".format(classid),
                self.algorithm_name,
                "rate {}kbit".format(get_no_limit_kbits(self.tc_device)),
            ]),
            self._tc_obj.REGEXP_FILE_EXISTS,
            message)
