# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import ipaddress
import re

import typepy

import pyparsing as pp

from .._const import Tc
from .._logger import logger
from ._common import _to_unicode


class TcFilterParser(object):

    class FilterMatchIdIpv4(object):
        INCOMING_NETWORK = 12
        OUTGOING_NETWORK = 16
        PORT = 20

    class FilterMatchIdIpv6(object):
        INCOMING_NETWORK_LIST = [8, 12, 16, 20]
        OUTGOING_NETWORK_LIST = [24, 28, 32, 36]
        PORT = 40

    __FILTER_FLOWID_PATTERN = (
        pp.Literal("filter parent") +
        pp.SkipTo("flowid", include=True) +
        pp.Word(pp.hexnums + ":")
    )
    __FILTER_PROTOCOL_PATTERN = (
        pp.Literal("filter parent") +
        pp.SkipTo("protocol", include=True) +
        pp.Word(pp.alphanums)
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
    def protocol(self):
        return self.__protocol

    def __init__(self, ip_version):
        self.__ip_version = ip_version
        self.__clear()

        self.__buffer = None
        self.__parse_idx = 0

        self.__protocol = None

    def parse_filter(self, text):
        self.__clear()

        if typepy.is_null_string(text):
            return []

        filter_data_matrix = []
        self.__buffer = text.splitlines()
        self.__parse_idx = 0

        while self.__parse_idx < len(self.__buffer):
            line = self.__buffer[self.__parse_idx].strip()
            self.__parse_idx += 1

            if typepy.is_null_string(line):
                continue

            try:
                self.__parse_mangle_mark(line)
            except pp.ParseException:
                logger.debug("failed to parse mangle: {}".format(line))
            else:
                filter_data_matrix.append({
                    Tc.Param.CLASS_ID: self.__classid,
                    Tc.Param.HANDLE: self.__handle,
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
                self.__parse_protocol(line)
                continue
            except pp.ParseException:
                logger.debug("failed to parse protocol: {}".format(line))

            try:
                if self.__ip_version == 4:
                    self.__parse_filter_ipv4(line)
                elif self.__ip_version == 6:
                    self.__parse_filter_ipv6(line)
                else:
                    raise ValueError(
                        "unknown ip version: {}".format(self.__ip_version))
            except pp.ParseException:
                logger.debug("failed to parse filter: {}".format(line))

        if self.__flow_id:
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
        self.__filter_src_port = None
        self.__filter_dst_port = None

        self.__handle = None
        self.__classid = None

    def __get_filter(self):
        return {
            Tc.Param.FLOW_ID: self.__flow_id,
            Tc.Param.DST_NETWORK: self.__filter_network,
            Tc.Param.SRC_PORT: self.__filter_src_port,
            Tc.Param.DST_PORT: self.__filter_dst_port,
            Tc.Param.PROTOCOL: self.protocol
        }

    def __parse_flow_id(self, line):
        parsed_list = self.__FILTER_FLOWID_PATTERN.parseString(
            _to_unicode(line.lstrip()))
        self.__flow_id = parsed_list[-1]
        logger.debug("succeed to parse flow id: flow-id={}, line={}".format(
            self.__flow_id, line))

    def __parse_protocol(self, line):
        parsed_list = self.__FILTER_PROTOCOL_PATTERN.parseString(
            _to_unicode(line.lstrip()))
        self.__protocol = parsed_list[-1]

    def __parse_mangle_mark(self, line):
        parsed_list = self.__FILTER_MANGLE_MARK_PATTERN.parseString(
            _to_unicode(line.lstrip()))
        self.__classid = parsed_list[-1]
        self.__handle = int(u"0" + parsed_list[-3], 16)
        logger.debug(
            "succeed to parse mangle mark: "
            "classid={}, handle={}, line={}".format(
                self.__classid, self.__handle, line))

    def __parse_filter_line(self, line):
        parsed_list = self.__FILTER_MATCH_PATTERN.parseString(
            _to_unicode(line))
        value_hex, mask_hex = parsed_list[1].split("/")
        match_id = int(parsed_list[3])

        return (value_hex, mask_hex, match_id)

    def __parse_filter_port(self, value_hex):
        # Port filter consists eight hex digits.
        # The upper-half represents source port filter and
        # the bottom-half represents destination port filter.

        if len(value_hex) != 8:
            raise ValueError("invalid port filter value: {}".format(value_hex))

        src_port_hex = value_hex[:4]
        dst_port_hex = value_hex[4:]

        logger.debug(
            "parse ipv4 port: src-port-hex={}, dst-port-hex={}".format(
                src_port_hex, dst_port_hex))

        src_port_decimal = int(src_port_hex, 16)
        self.__filter_src_port = (
            src_port_decimal if src_port_decimal != 0 else None)

        dst_port_decimal = int(dst_port_hex, 16)
        self.__filter_dst_port = (
            dst_port_decimal if dst_port_decimal != 0 else None)

    def __parse_filter_ipv4(self, line):
        value_hex, mask_hex, match_id = self.__parse_filter_line(line)

        if match_id in [
            self.FilterMatchIdIpv4.INCOMING_NETWORK,
            self.FilterMatchIdIpv4.OUTGOING_NETWORK,
        ]:
            ipaddr = ".".join([
                str(int(value_hex[i: i + 2], 16))
                for i in range(0, len(value_hex), 2)
            ])
            netmask = bin(int(mask_hex, 16)).count("1")

            self.__filter_network = "{:s}/{:d}".format(ipaddr, netmask)
        elif match_id == self.FilterMatchIdIpv4.PORT:
            self.__parse_filter_port(value_hex)

        logger.debug(
            "succeed to parse filter: " + ", ".join([
                "dst_network={}".format(self.__filter_network),
                "src_port={}".format(self.__filter_src_port),
                "dst_port={}".format(self.__filter_dst_port),
                "line={}".format(line)
            ]))

    def __parse_filter_ipv6(self, line):
        netmask = 0
        value_hex, mask_hex, match_id = self.__parse_filter_line(line)

        octet_list = []
        octet_len = 4

        if (
            match_id in self.FilterMatchIdIpv6.INCOMING_NETWORK_LIST or
            match_id in self.FilterMatchIdIpv6.OUTGOING_NETWORK_LIST
        ):
            octet_list.extend([
                value_hex[i: i + octet_len]
                for i in range(0, len(value_hex), octet_len)
            ])
            netmask += bin(int(mask_hex, 16)).count("1")

            while True:
                try:
                    line = self.__buffer[self.__parse_idx].strip()
                except IndexError:
                    break

                try:
                    value_hex, mask_hex, match_id = self.__parse_filter_line(
                        line)
                except pp.ParseException:
                    break

                if (
                    match_id in self.FilterMatchIdIpv6.INCOMING_NETWORK_LIST or
                    match_id in self.FilterMatchIdIpv6.OUTGOING_NETWORK_LIST
                ):
                    octet_list.extend([
                        value_hex[i: i + octet_len]
                        for i in range(0, len(value_hex), octet_len)
                    ])
                    netmask += bin(int(mask_hex, 16)).count("1")
                else:
                    break

                self.__parse_idx += 1

            while len(octet_list) < 8:
                octet_list.append("0000")

            self.__filter_network = ipaddress.IPv6Network("{:s}/{:d}".format(
                ":".join(octet_list), netmask)).compressed

        elif match_id == self.FilterMatchIdIpv6.PORT:
            self.__parse_filter_port(value_hex)

        logger.debug(
            "succeed to parse filter: " + ", ".join([
                "dst_network={}".format(self.__filter_network),
                "src_port={}".format(self.__filter_src_port),
                "dst_port={}".format(self.__filter_dst_port),
                "line={}".format(line)
            ]))
