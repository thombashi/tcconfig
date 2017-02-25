# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import copy
import re

import typepy

import pyparsing as pp

from ._const import Tc
from ._logger import logger


def _to_unicode(text):
    try:
        return text.decode("ascii")
    except AttributeError:
        return text


class TcFilterParser(object):

    class FilterMatchId(object):
        INCOMING_NETWORK = 12
        OUTGOING_NETWORK = 16
        PORT = 20

    __FILTER_FLOWID_PATTERN = (
        pp.Literal("filter parent") +
        pp.SkipTo("flowid", include=True) +
        pp.Word(pp.hexnums + ":")
    )
    __FILTER_MATCH_PATTERN = (
        pp.Literal("match") +
        pp.Word(pp.alphanums + "/") +
        pp.Literal("at") +
        pp.Word(pp.nums)
    )
    __FILTER_MANGLE_MARK_PATTERN = (
        pp.Literal("filter parent") +
        pp.SkipTo("handle", include=True) +
        pp.Word(pp.hexnums) +
        pp.SkipTo("classid", include=True) +
        pp.Word(pp.hexnums + ":")
    )

    @property
    def flow_id(self):
        return self.__flow_id

    @property
    def filter_network(self):
        return self.__filter_network

    @property
    def filter_port(self):
        return self.__filter_port

    @property
    def handle(self):
        return self.__handle

    @property
    def classid(self):
        return self.__classid

    def __init__(self):
        self.__clear()

    def parse_filter(self, text):
        self.__clear()

        if typepy.is_null_string(text):
            return []

        filter_data_matrix = []

        for line in text.splitlines():
            if typepy.is_null_string(line):
                continue

            try:
                self.__parse_mangle_mark(line)
            except pp.ParseException:
                logger.debug("failed to parse mangle: {}".format(line))
            else:
                filter_data_matrix.append({
                    "classid": self.classid,
                    "handle": self.handle,
                })
                self.__clear()
                continue

            tc_filter = self.__get_filter()

            try:
                self.__parse_flow_id(line)

                if tc_filter.get(Tc.Param.FLOW_ID):
                    logger.debug("store filter: {}".format(tc_filter))
                    filter_data_matrix.append(tc_filter)
                    self.__clear()
                    self.__parse_flow_id(line)

                continue
            except pp.ParseException:
                logger.debug("failed to parse flow id: {}".format(line))

            try:
                self.__parse_filter(line)
            except pp.ParseException:
                logger.debug("failed to parse filter: {}".format(line))

        if self.flow_id:
            filter_data_matrix.append(self.__get_filter())

        return filter_data_matrix

    def parse_incoming_device(self, text):
        if typepy.is_null_string(text):
            return None

        match = re.search(
            "Egress Redirect to device ifb[\d]+",
            _to_unicode(text), re.MULTILINE)
        if match is None:
            return None

        return re.search("ifb[\d]+", match.group()).group()

    def __clear(self):
        self.__flow_id = None
        self.__filter_network = None
        self.__filter_port = None

        self.__handle = None
        self.__classid = None

    def __get_filter(self):
        return copy.deepcopy({
            "flowid": self.flow_id,
            "network": self.filter_network,
            "port": self.filter_port,
        })

    def __parse_flow_id(self, line):
        parsed_list = self.__FILTER_FLOWID_PATTERN.parseString(
            _to_unicode(line.lstrip()))
        self.__flow_id = parsed_list[-1]
        logger.debug("succeed to parse flow id: flow-id={}, line={}".format(
            self.flow_id, line))

    def __parse_mangle_mark(self, line):
        parsed_list = self.__FILTER_MANGLE_MARK_PATTERN.parseString(
            _to_unicode(line.lstrip()))
        self.__classid = parsed_list[-1]
        self.__handle = int(u"0" + parsed_list[-3], 16)
        logger.debug(
            "succeed to parse mangle mark: classid={}, handle={}, line={}".format(
                self.classid, self.handle, line))

    def __parse_filter(self, line):
        parsed_list = self.__FILTER_MATCH_PATTERN.parseString(
            _to_unicode(line))
        value_hex, mask_hex = parsed_list[1].split("/")
        match_id = int(parsed_list[3])

        if match_id in [
            self.FilterMatchId.INCOMING_NETWORK,
            self.FilterMatchId.OUTGOING_NETWORK,
        ]:
            ipaddr = ".".join([
                str(int(value_hex[i: i + 2], 16))
                for i in range(0, len(value_hex), 2)
            ])
            netmask = bin(int(mask_hex, 16)).count("1")

            self.__filter_network = "{:s}/{:d}".format(ipaddr, netmask)
        elif match_id == self.FilterMatchId.PORT:
            self.__filter_port = int(value_hex, 16)

        logger.debug(
            "succeed to parse filter: filter_network={}, filter_port={}, line={}".format(
                self.filter_network, self.filter_port, line))


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
            self.__parse_netem_param(line, "corrupt", pp.nums + ".")
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
