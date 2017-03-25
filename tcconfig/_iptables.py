# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import re

from subprocrunner import SubprocessRunner
import typepy
from typepy.type import Integer

from ._common import sanitize_network
from ._const import (
    LIST_MANGLE_TABLE_COMMAND,
    Network,
)
from ._logger import logger
from ._split_line_list import split_line_list


VALID_CHAIN_LIST = ["PREROUTING", "INPUT", "OUTPUT"]


class IptablesMangleMark(object):

    @property
    def line_number(self):
        return self.__line_number

    @property
    def protocol(self):
        return self.__protocol

    @property
    def source(self):
        return self.__source

    @property
    def destination(self):
        return self.__destination

    @property
    def mark_id(self):
        return self.__mark_id

    @property
    def chain(self):
        return self.__chain

    def __init__(
            self, ip_version, mark_id, source, destination, chain,
            protocol="all", line_number=None):
        self.__line_number = line_number
        self.__mark_id = mark_id
        self.__source = sanitize_network(source, ip_version)
        self.__destination = sanitize_network(destination, ip_version)
        self.__protocol = protocol

        if chain not in VALID_CHAIN_LIST:
            raise ValueError("invalid chain: {}".format(chain))

        self.__chain = chain

    def __eq__(self, other):
        return all([
            self.chain == other.chain,
            self.mark_id == other.mark_id,
            self.protocol == other.protocol,
            self.source == other.source,
            self.destination == other.destination,
        ])

    def __repr__(self, *args, **kwargs):
        str_list = []

        if Integer(self.line_number).is_type():
            str_list.append("line-num={}".format(self.line_number))

        str_list.extend([
            "protocol={:s}".format(self.protocol),
            "source={:s}".format(self.source),
            "destination={:s}".format(self.destination),
            "mark_id={:d}".format(self.mark_id),
            "chain={:s}".format(self.chain),
        ])

        return ", ".join(str_list)

    def to_append_command(self):
        Integer(self.mark_id).validate()

        command_item_list = [
            "iptables -A {:s} -t mangle -j MARK".format(self.chain),
            "--set-mark {}".format(self.mark_id),
        ]

        if any([
            typepy.is_not_null_string(self.protocol),
            Integer(self.protocol).is_type(),
        ]):
            command_item_list.append("-p {}".format(self.protocol))
        if self.__is_valid_srcdst(self.source):
            command_item_list.append(
                "-s {:s}".format(self.source))
        if self.__is_valid_srcdst(self.destination):
            command_item_list.append(
                "-d {:s}".format(self.destination))

        return " ".join(command_item_list)

    def to_delete_command(self):
        Integer(self.line_number).validate()

        return "iptables -t mangle -D {:s} {}".format(
            self.chain, self.line_number)

    @staticmethod
    def __is_valid_srcdst(srcdst):
        return (
            typepy.is_not_null_string(srcdst) and
            srcdst not in (Network.Ipv4.ANYWHERE, Network.Ipv6.ANYWHERE)
        )


class IptablesMangleController(object):

    __RE_CHAIN = re.compile(
        "Chain {:s} |Chain {:s} |Chain {:s} ".format(*VALID_CHAIN_LIST))
    __RE_CHAIN_NAME = re.compile(
        "{:s}|{:s}|{:s}".format(*VALID_CHAIN_LIST))
    __MAX_MARK_ID = 0xffffffff
    __MARK_ID_OFFSET = 100

    @property
    def enable(self):
        return self.__enable

    def __init__(self, enable, ip_version):
        self.__enable = enable
        self.__ip_version = ip_version

    def clear(self):
        if not self.enable:
            return

        for mangle in self.parse():
            proc = SubprocessRunner(mangle.to_delete_command())
            if proc.run() != 0:
                raise RuntimeError(proc.stderr)

    def get_iptables(self):
        proc = SubprocessRunner(LIST_MANGLE_TABLE_COMMAND)
        if proc.run() != 0:
            raise RuntimeError(proc.stderr)

        return proc.stdout

    def get_unique_mark_id(self):
        mark_id_list = [
            mangle.mark_id for mangle in self.parse()]
        logger.debug("mangle mark list: {}".format(mark_id_list))

        unique_mark_id = 1 + self.__MARK_ID_OFFSET
        while unique_mark_id < self.__MAX_MARK_ID:
            if unique_mark_id not in mark_id_list:
                return unique_mark_id

            unique_mark_id += 1

        raise RuntimeError("usable mark id not found")

    def parse(self):
        for block in split_line_list(self.get_iptables().splitlines()):
            if len(block) <= 1:
                # skip if no entry exists
                continue

            match = self.__RE_CHAIN.search(block[0])
            if match is None:
                continue

            chain = self.__RE_CHAIN_NAME.search(match.group()).group()

            for line in reversed(block[2:]):
                item_list = line.split()
                if len(item_list) < 6:
                    continue

                line_number = int(item_list[0])
                target = item_list[1]
                protocol = item_list[2]
                source = item_list[4]
                destination = item_list[5]

                try:
                    mark = int(item_list[-1], 16)
                except ValueError:
                    continue

                if target != "MARK":
                    continue

                yield IptablesMangleMark(
                    ip_version=self.__ip_version,
                    mark_id=mark, source=source, destination=destination,
                    chain=chain, protocol=protocol, line_number=line_number)

    @classmethod
    def add(cls, mangling_mark):
        if not cls.enable:
            return 0

        return SubprocessRunner(mangling_mark.to_append_command()).run()
