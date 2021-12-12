"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import ipaddress
import re

import pyparsing as pp
import typepy

from .._const import Tc, TcSubCommand
from .._logger import logger
from .._network import sanitize_network
from ._interface import AbstractParser
from ._model import Filter


class TcFilterParser(AbstractParser):
    class FilterMatchIdIpv4:
        INCOMING_NETWORK = 12
        OUTGOING_NETWORK = 16
        PORT = 20

    class FilterMatchIdIpv6:
        INCOMING_NETWORK_LIST = [8, 12, 16, 20]
        OUTGOING_NETWORK_LIST = [24, 28, 32, 36]
        PORT = 40

    __FILTER_FLOWID_PATTERN = (
        pp.Literal("filter parent") + pp.SkipTo("flowid", include=True) + pp.Word(pp.hexnums + ":")
    )
    __FILTER_PROTOCOL_PATTERN = (
        pp.Literal("filter parent") + pp.SkipTo("protocol", include=True) + pp.Word(pp.alphanums)
    )
    __FILTER_PRIORITY_PATTERN = (
        pp.Literal("filter parent") + pp.SkipTo("pref", include=True) + pp.Word(pp.nums)
    )
    __FILTER_ID_PATTERN = (
        pp.Literal("filter parent") + pp.SkipTo("fh", include=True) + pp.Word(pp.hexnums + ":")
    )
    __FILTER_MATCH_PATTERN = (
        pp.Literal("match") + pp.Word(pp.alphanums + "/") + pp.Literal("at") + pp.Word(pp.nums)
    )
    __FILTER_MANGLE_MARK_PATTERN = (
        pp.Literal("filter parent")
        + pp.SkipTo("handle", include=True)
        + pp.Word(pp.hexnums)
        + pp.SkipTo("classid", include=True)
        + pp.Word(pp.hexnums + ":")
    )

    @property
    def protocol(self):
        return self.__protocol

    @property
    def _tc_subcommand(self):
        return TcSubCommand.FILTER.value

    def __init__(self, con, ip_version):
        super().__init__(con)

        self.__ip_version = ip_version
        self.__buffer = None
        self.__parse_idx = 0

        self.__protocol = None

        self._clear()

    def parse(self, device, text):
        self._clear()

        if typepy.is_null_string(text):
            return []

        self.__buffer = self._to_unicode(text).splitlines()
        self.__parse_idx = 0

        while self.__parse_idx < len(self.__buffer):
            line = self._to_unicode(self.__buffer[self.__parse_idx].strip())
            self.__parse_idx += 1

            if typepy.is_null_string(line):
                continue

            self.__device = device

            try:
                self.__parse_mangle_mark(line)
            except pp.ParseException:
                logger.debug("failed to parse mangle: {}".format(line))
            else:
                Filter.insert(
                    Filter(
                        **{
                            Tc.Param.DEVICE: self.__device,
                            Tc.Param.CLASS_ID: self.__classid,
                            Tc.Param.HANDLE: self.__handle,
                        }
                    )
                )
                self._clear()
                continue

            tc_filter = self.__get_filter()

            try:
                self.__parse_flow_id(line)
                self.__parse_protocol(line)
                self.__parse_priority(line)
                self.__parse_filter_id(line)

                if tc_filter.flowid:
                    logger.debug("store filter: {}".format(tc_filter))
                    Filter.insert(tc_filter)
                    self._clear()

                    self.__device = device
                    self.__parse_flow_id(line)
                    self.__parse_protocol(line)
                    self.__parse_priority(line)
                    self.__parse_filter_id(line)

                continue
            except pp.ParseException:
                logger.debug("failed to parse flow id: {}".format(line))

            try:
                if self.__ip_version == 4:
                    self.__parse_filter_ipv4(line)
                elif self.__ip_version == 6:
                    self.__parse_filter_ipv6(line)
                else:
                    raise ValueError("unknown ip version: {}".format(self.__ip_version))
            except pp.ParseException:
                logger.debug("failed to parse filter: {}".format(line))

        if self.__flow_id:
            Filter.insert(self.__get_filter())

    def parse_incoming_device(self, text):
        if typepy.is_null_string(text):
            return None

        match = re.search(
            r"Egress Redirect to device ifb[\d]+", self._to_unicode(text), re.MULTILINE
        )
        if match is None:
            return None

        return re.search(r"ifb[\d]+", match.group()).group()

    def _clear(self):
        self.__device = None
        self.__filter_id = None
        self.__flow_id = None
        self.__protocol = None
        self.__priority = None
        self.__filter_src_network = None
        self.__filter_dst_network = None
        self.__filter_src_port = None
        self.__filter_dst_port = None

        self.__handle = None
        self.__classid = None

    def __get_filter(self):
        return Filter(
            device=self.__device,
            filter_id=self.__filter_id,
            flowid=self.__flow_id,
            protocol=self.protocol,
            priority=self.__priority,
            src_network=sanitize_network(self.__filter_src_network, self.__ip_version),
            dst_network=sanitize_network(self.__filter_dst_network, self.__ip_version),
            src_port=self.__filter_src_port,
            dst_port=self.__filter_dst_port,
        )

    def __parse_flow_id(self, line):
        parsed_list = self.__FILTER_FLOWID_PATTERN.parseString(line)
        self.__flow_id = parsed_list[-1]
        logger.debug("succeed to parse flow id: flow-id={}, line={}".format(self.__flow_id, line))

    def __parse_protocol(self, line):
        parsed_list = self.__FILTER_PROTOCOL_PATTERN.parseString(line)
        self.__protocol = parsed_list[-1]
        logger.debug(
            "succeed to parse protocol: protocol={}, line={}".format(self.__protocol, line)
        )

    def __parse_priority(self, line):
        parsed_list = self.__FILTER_PRIORITY_PATTERN.parseString(line)
        self.__priority = int(parsed_list[-1])
        logger.debug(
            "succeed to parse priority: priority={}, line={}".format(self.__priority, line)
        )

    def __parse_filter_id(self, line):
        parsed_list = self.__FILTER_ID_PATTERN.parseString(line)
        self.__filter_id = parsed_list[-1]
        logger.debug(
            "succeed to parse filter id: filter-id={}, line={}".format(self.__filter_id, line)
        )

    def __parse_mangle_mark(self, line):
        parsed_list = self.__FILTER_MANGLE_MARK_PATTERN.parseString(line)
        self.__classid = parsed_list[-1]
        self.__handle = int("0" + parsed_list[-3], 16)
        logger.debug(
            "succeed to parse mangle mark: "
            "classid={}, handle={}, line={}".format(self.__classid, self.__handle, line)
        )

    def __parse_filter_ip_line(self, line):
        parsed_list = self.__FILTER_MATCH_PATTERN.parseString(line)
        value_hex, mask_hex = parsed_list[1].split("/")
        match_id = int(parsed_list[3])

        return (value_hex, mask_hex, match_id)

    def __parse_filter_ipv4_network(self, value_hex, mask_hex, match_id):
        ipaddr = ".".join([str(int(value_hex[i : i + 2], 16)) for i in range(0, len(value_hex), 2)])
        netmask = bin(int(mask_hex, 16)).count("1")
        network = "{:s}/{:d}".format(ipaddr, netmask)

        if match_id == self.FilterMatchIdIpv4.INCOMING_NETWORK:
            self.__filter_src_network = network
        elif match_id == self.FilterMatchIdIpv4.OUTGOING_NETWORK:
            self.__filter_dst_network = network
        else:
            logger.warning("unknown match id: {}".format(match_id))

    def __parse_filter_ipv6_network(self, value_hex, mask_hex, match_id):
        from collections import namedtuple

        Ipv6Entry = namedtuple("Ipv6Entry", "match_id octet_list mask_hex")

        OCTET_LEN = 4
        ipv6_entry_list = [
            Ipv6Entry(
                match_id=match_id,
                octet_list=[
                    value_hex[i : i + OCTET_LEN] for i in range(0, len(value_hex), OCTET_LEN)
                ],
                mask_hex=mask_hex,
            )
        ]

        while True:
            try:
                line = self.__buffer[self.__parse_idx].strip()
            except IndexError:
                break

            try:
                value_hex, mask_hex, match_id = self.__parse_filter_ip_line(line)
            except pp.ParseException:
                break

            if (
                match_id in self.FilterMatchIdIpv6.INCOMING_NETWORK_LIST
                or match_id in self.FilterMatchIdIpv6.OUTGOING_NETWORK_LIST
            ):
                ipv6_entry_list.append(
                    Ipv6Entry(
                        match_id=match_id,
                        octet_list=[
                            value_hex[i : i + OCTET_LEN]
                            for i in range(0, len(value_hex), OCTET_LEN)
                        ],
                        mask_hex=mask_hex,
                    )
                )
            else:
                break

            self.__parse_idx += 1

        src_octet_list = []
        dst_octet_list = []
        src_netmask = 0
        dst_netmask = 0

        for ipv6_entry in ipv6_entry_list:
            part_netmask = bin(int(ipv6_entry.mask_hex, 16)).count("1")

            if ipv6_entry.match_id in self.FilterMatchIdIpv6.INCOMING_NETWORK_LIST:
                src_octet_list.extend(ipv6_entry.octet_list)
                src_netmask += part_netmask
            elif ipv6_entry.match_id in self.FilterMatchIdIpv6.OUTGOING_NETWORK_LIST:
                dst_octet_list.extend(ipv6_entry.octet_list)
                dst_netmask += part_netmask
            else:
                raise ValueError("unexpected ipv6 entry: {}".format(ipv6_entry))

        while len(src_octet_list) < 8:
            src_octet_list.append("0000")
        while len(dst_octet_list) < 8:
            dst_octet_list.append("0000")

        self.__filter_dst_network = ipaddress.IPv6Network(
            "{:s}/{:d}".format(":".join(dst_octet_list), dst_netmask), strict=False
        ).compressed
        self.__filter_src_network = ipaddress.IPv6Network(
            "{:s}/{:d}".format(":".join(src_octet_list), src_netmask), strict=False
        ).compressed

    def __parse_filter_port(self, value_hex):
        # Port filter consists eight hex digits.
        # The upper-half represents source port filter and
        # the bottom-half represents destination port filter.

        if len(value_hex) != 8:
            raise ValueError("invalid port filter value: {}".format(value_hex))

        src_port_hex = value_hex[:4]
        dst_port_hex = value_hex[4:]

        logger.debug(
            "parse ipv4 port: src-port-hex={}, dst-port-hex={}".format(src_port_hex, dst_port_hex)
        )

        src_port_decimal = int(src_port_hex, 16)
        self.__filter_src_port = src_port_decimal if src_port_decimal != 0 else None

        dst_port_decimal = int(dst_port_hex, 16)
        self.__filter_dst_port = dst_port_decimal if dst_port_decimal != 0 else None

    def __parse_filter_ipv4(self, line):
        value_hex, mask_hex, match_id = self.__parse_filter_ip_line(line)

        if match_id in [
            self.FilterMatchIdIpv4.INCOMING_NETWORK,
            self.FilterMatchIdIpv4.OUTGOING_NETWORK,
        ]:
            self.__parse_filter_ipv4_network(value_hex, mask_hex, match_id)
        elif match_id == self.FilterMatchIdIpv4.PORT:
            self.__parse_filter_port(value_hex)
        elif match_id in (
            self.FilterMatchIdIpv6.INCOMING_NETWORK_LIST
            + self.FilterMatchIdIpv6.OUTGOING_NETWORK_LIST
            + [self.FilterMatchIdIpv6.PORT]
        ):
            logger.warning(
                "unknown match id for an IPv4 filter: might be an IPv6 filter. "
                "try to use --ipv6 option. (id={})".format(match_id)
            )
            return
        else:
            logger.debug("unknown match id: {}".format(match_id))
            return

        logger.debug(
            "succeed to parse ipv4 filter: "
            + ", ".join(
                [
                    "src_network={}".format(self.__filter_src_network),
                    "dst_network={}".format(self.__filter_dst_network),
                    "src_port={}".format(self.__filter_src_port),
                    "dst_port={}".format(self.__filter_dst_port),
                    "line={}".format(line),
                ]
            )
        )

    def __parse_filter_ipv6(self, line):
        value_hex, mask_hex, match_id = self.__parse_filter_ip_line(line)

        if (
            match_id in self.FilterMatchIdIpv6.INCOMING_NETWORK_LIST
            or match_id in self.FilterMatchIdIpv6.OUTGOING_NETWORK_LIST
        ):
            self.__parse_filter_ipv6_network(value_hex, mask_hex, match_id)
        elif match_id == self.FilterMatchIdIpv6.PORT:
            self.__parse_filter_port(value_hex)
        else:
            logger.debug("unknown match id: {}".format(match_id))
            return

        logger.debug(
            "succeed to parse ipv6 filter: "
            + ", ".join(
                [
                    "src_network={}".format(self.__filter_src_network),
                    "dst_network={}".format(self.__filter_dst_network),
                    "src_port={}".format(self.__filter_src_port),
                    "dst_port={}".format(self.__filter_dst_port),
                    "line={}".format(line),
                ]
            )
        )
