# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import re

import typepy

from ._common import _to_unicode


class TcClassParser(object):

    class Pattern(object):
        CLASS_ID = "[0-9a-z:]+"
        RATE = "[0-9]+[KMGT]?"

    class Key(object):
        CLASS_ID = "classid"
        RATE = "rate"

    def __init__(self):
        self.__clear()

    def parse(self, text):
        for line in text.splitlines():
            self.__clear()

            if typepy.is_null_string(line):
                continue

            line = _to_unicode(line.lstrip())

            self.__parse_classid(line)
            self.__parse_rate(line)

            yield self.__parsed_param

    def __clear(self):
        self.__parsed_param = {}

    def __parse_classid(self, line):
        self.__parsed_param[self.Key.CLASS_ID] = None
        tag = "class htb "

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
