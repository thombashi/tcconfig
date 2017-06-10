# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import re

import typepy

import pyparsing as pp

from ._common import _to_unicode


class TcQdiscParser(object):

    def __init__(self):
        self.__clear()

    def parse(self, text):
        if typepy.is_null_string(text):
            raise ValueError("empty text")

        text = text.strip()

        for line in text.splitlines():
            if typepy.is_null_string(line):
                continue

            line = _to_unicode(line.lstrip())

            if re.search("qdisc netem|qdisc tbf", line) is None:
                continue

            self.__clear()

            if re.search("qdisc netem", line) is not None:
                self.__parse_netem_param(line, "parent", pp.hexnums + ":")

            self.__parse_netem_param(line, "delay", pp.nums + ".")
            self.__parse_netem_delay_distro(line)
            self.__parse_netem_param(line, "loss", pp.nums + ".")
            self.__parse_netem_param(line, "duplicate", pp.nums + ".")
            self.__parse_netem_param(line, "corrupt", pp.nums + ".")
            self.__parse_netem_param(line, "reorder", pp.nums + ".")
            self.__parse_tbf_rate(line)

            yield self.__parsed_param

    def __clear(self):
        self.__parsed_param = {}

    def __parse_netem_delay_distro(self, line):
        parse_param_name = "delay"
        pattern = (
            pp.SkipTo(parse_param_name, include=True) +
            pp.Word(pp.nums + ".") + pp.Literal("ms") +
            pp.Word(pp.nums + ".") + pp.Literal("ms"))

        try:
            parsed_list = pattern.parseString(line)
            self.__parsed_param[parse_param_name] = parsed_list[2]
            self.__parsed_param["delay-distro"] = parsed_list[4]
        except pp.ParseException:
            pass

    def __parse_netem_param(self, line, parse_param_name, word_pattern):
        pattern = (
            pp.SkipTo(parse_param_name, include=True) +
            pp.Word(word_pattern))

        try:
            result = pattern.parseString(_to_unicode(line))[-1]
            if typepy.is_not_null_string(result):
                self.__parsed_param[parse_param_name] = result
        except pp.ParseException:
            pass

    def __parse_tbf_rate(self, line):
        parse_param_name = "rate"
        pattern = (
            pp.SkipTo(parse_param_name, include=True) +
            pp.Word(pp.alphanums + "." + ":"))

        try:
            result = pattern.parseString(line)[-1]
            if typepy.is_not_null_string(result):
                result = result.rstrip("bit")
                self.__parsed_param[parse_param_name] = result
        except pp.ParseException:
            pass
