"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import re

import typepy

from .._const import ShapingAlgorithm, Tc, TcSubCommand
from .._logger import logger
from ._interface import AbstractParser


try:
    import ujson as json
except ImportError:
    import json  # type: ignore


class TcClassParser(AbstractParser):
    class Pattern:
        CLASS_ID = "[0-9a-z:]+"
        RATE = "[0-9]+[KMGT]?"

    class Key:
        DEVICE = Tc.Param.DEVICE
        CLASS_ID = Tc.Param.CLASS_ID
        RATE = "rate"

        LIST = (DEVICE, CLASS_ID, RATE)

    @property
    def _tc_subcommand(self):
        return TcSubCommand.CLASS.value

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

            logger.debug(f"parse a class entry: {self.__parsed_param}")
            entry_list.append(self.__parsed_param)

        if entry_list:
            self._con.create_table_from_data_matrix(self._tc_subcommand, self.Key.LIST, entry_list)

        logger.debug(f"tc {self._tc_subcommand:s} parse result: {json.dumps(entry_list, indent=4)}")

        return entry_list

    def _clear(self):
        self.__parsed_param = {}

    def __parse_classid(self, line):
        self.__parsed_param[self.Key.CLASS_ID] = None
        tag = f"class {ShapingAlgorithm.HTB:s} "

        match = re.search(f"{tag:s}{self.Pattern.CLASS_ID:s}", line)
        if match is None:
            return

        self.__parsed_param[self.Key.CLASS_ID] = re.search(
            self.Pattern.CLASS_ID, match.group().lstrip(tag)
        ).group()

    def __parse_rate(self, line):
        self.__parsed_param[self.Key.RATE] = None

        match = re.search(f"rate {self.Pattern.RATE:s}", line)
        if match is None:
            return

        self.__parsed_param[self.Key.RATE] = (
            re.search(self.Pattern.RATE, match.group()).group() + "bps"
        )
