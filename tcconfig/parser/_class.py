# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import json
import re

import typepy

from .._const import (
    ShapingAlgorithm,
    Tc,
)
from .._logger import logger
from ._interface import AbstractParser


class TcClassParser(AbstractParser):

    class Pattern(object):
        CLASS_ID = "[0-9a-z:]+"
        RATE = "[0-9]+[KMGT]?"

    class Key(object):
        DEVICE = Tc.Param.DEVICE
        CLASS_ID = Tc.Param.CLASS_ID
        RATE = "rate"

        LIST = (DEVICE, CLASS_ID, RATE)

    @property
    def _tc_subcommand(self):
        return Tc.Subcommand.CLASS

    def __init__(self, con):
        super(TcClassParser, self).__init__()

        self.__con = con

    def parse(self, device, text):
        entry_list = []

        for line in text.splitlines():
            self._clear()

            if typepy.is_null_string(line):
                continue

            line = self._to_unicode(line.lstrip())

            self.__parsed_param[self.Key.DEVICE] = device
            self.__parse_classid(line)
            self.__parse_rate(line)

            logger.debug("parse a class entry: {}".format(self.__parsed_param))
            entry_list.append(self.__parsed_param)

        if entry_list:
            self.__con.create_table_from_data_matrix(
                table_name=self._tc_subcommand,
                attr_name_list=self.Key.LIST,
                data_matrix=entry_list)

        logger.debug("tc {:s} parse result: {}".format(
            self._tc_subcommand, json.dumps(entry_list, indent=4)))

        return entry_list

    def _clear(self):
        self.__parsed_param = {}

    def __parse_classid(self, line):
        self.__parsed_param[self.Key.CLASS_ID] = None
        tag = "class {:s} ".format(ShapingAlgorithm.HTB)

        match = re.search("{:s}{:s}".format(tag, self.Pattern.CLASS_ID), line)
        if match is None:
            return

        self.__parsed_param[self.Key.CLASS_ID] = re.search(
            self.Pattern.CLASS_ID, match.group().lstrip(tag)).group()

    def __parse_rate(self, line):
        self.__parsed_param[self.Key.RATE] = None

        match = re.search("rate {:s}".format(self.Pattern.RATE), line)
        if match is None:
            return

        self.__parsed_param[self.Key.RATE] = re.search(
            self.Pattern.RATE, match.group()).group()
