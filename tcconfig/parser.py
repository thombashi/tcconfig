# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import re

import dataproperty
import pyparsing as pp


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

        if dataproperty.is_empty_string(text):
            return []

        filter_data_matrix = []

        for line in text.splitlines():
            if dataproperty.is_empty_string(line):
                continue

            try:
                self.__parse_mangle_mark(line)
            except pp.ParseException:
                pass
            else:
                filter_data_matrix.append({
                    "classid": self.classid,
                    "handle": self.handle,
                })
                continue

            try:
                self.__parse_flow_id(line)
                continue
            except pp.ParseException:
                pass

            try:
                self.__parse_filter(line)
                continue
            except pp.ParseException:
                pass

            if self.flow_id is not None:
                filter_data_matrix.append(self.__get_filter())

            self.__clear()

        if self.flow_id is not None:
            filter_data_matrix.append(self.__get_filter())

        return filter_data_matrix

    def parse_incoming_device(self, text):
        if dataproperty.is_empty_string(text):
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
        return {
            "flowid": self.flow_id,
            "network": self.filter_network,
            "port": self.filter_port,
        }

    def __parse_flow_id(self, line):
        parsed_list = self.__FILTER_FLOWID_PATTERN.parseString(
            _to_unicode(line.lstrip()))
        self.__flow_id = parsed_list[-1]

    def __parse_mangle_mark(self, line):
        parsed_list = self.__FILTER_MANGLE_MARK_PATTERN.parseString(
            _to_unicode(line.lstrip()))
        self.__classid = parsed_list[-1]
        self.__handle = int(u"0" + parsed_list[-3], 16)

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


class TcQdiscParser(object):

    def __init__(self):
        self.__parsed_param = {}

    def parse(self, text):
        for line in text.splitlines():
            if dataproperty.is_empty_string(line):
                continue

            line = _to_unicode(line.lstrip())

            if re.search("qdisc netem|qdisc tbf", line) is None:
                continue

            if re.search("qdisc netem", line) is not None:
                self.__parse_netem_param(line, "parent", pp.hexnums + ":")

            self.__parse_netem_param(line, "delay", pp.nums + ".")
            self.__parse_netem_delay_distro(line)
            self.__parse_netem_param(line, "loss", pp.nums + ".")
            self.__parse_netem_param(line, "corrupt", pp.nums + ".")
            self.__parse_tbf_rate(line)

        return self.__parsed_param

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
            if dataproperty.is_not_empty_string(result):
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
            if dataproperty.is_not_empty_string(result):
                result = result.rstrip("bit")
                self.__parsed_param[parse_param_name] = result
        except pp.ParseException:
            pass
