# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
import re

import dataproperty
from dataproperty import IntegerType
from subprocrunner import SubprocessRunner

from ._common import ANYWHERE_NETWORK
from ._common import sanitize_network
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
            self, mark_id, source, destination, chain, protocol="all",
            line_number=None):
        self.__line_number = line_number
        self.__mark_id = mark_id
        self.__source = sanitize_network(source)
        self.__destination = sanitize_network(destination)
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

        if IntegerType(self.line_number).is_type():
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
        IntegerType(self.mark_id).validate()

        command_item_list = [
            "iptables -A {:s} -t mangle -j MARK".format(self.chain),
            "--set-mark {}".format(self.mark_id),
        ]

        if any([
            dataproperty.is_not_empty_string(self.protocol),
            IntegerType(self.protocol).is_type(),
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
        IntegerType(self.line_number).validate()

        return "iptables -t mangle -D {:s} {}".format(
            self.chain, self.line_number)

    @staticmethod
    def __is_valid_srcdst(srcdst):
        return (
            dataproperty.is_not_empty_string(srcdst) and
            srcdst != ANYWHERE_NETWORK
        )


class IptablesMangleController(object):

    __RE_CHAIN = re.compile(
        "Chain {:s} |Chain {:s} |Chain {:s} ".format(*VALID_CHAIN_LIST))
    __RE_CHAIN_NAME = re.compile(
        "{:s}|{:s}|{:s}".format(*VALID_CHAIN_LIST))
    __MAX_MARK_ID = 0xffffffff

    enable = True

    @classmethod
    def clear(cls):
        if not cls.enable:
            return

        for mangle in cls.parse():
            proc = SubprocessRunner(mangle.to_delete_command())
            if proc.run() != 0:
                raise RuntimeError(str(proc.stderr))

    @classmethod
    def get_iptables(cls):
        proc = SubprocessRunner("iptables -t mangle --line-numbers -L")
        if proc.run() != 0:
            raise RuntimeError(str(proc.stderr))

        return proc.stdout

    @classmethod
    def get_unique_mark_id(cls):
        mark_id_list = [mangle.mark_id for mangle in cls.parse()]
        unique_mark_id = 1
        while unique_mark_id < cls.__MAX_MARK_ID:
            if unique_mark_id not in mark_id_list:
                return unique_mark_id

            unique_mark_id += 1

        raise RuntimeError("usable mark id not found")

    @classmethod
    def parse(cls):
        for block in split_line_list(cls.get_iptables().splitlines()):
            if len(block) <= 1:
                # skip if no entry exists
                continue

            match = cls.__RE_CHAIN.search(block[0])
            if match is None:
                continue

            chain = cls.__RE_CHAIN_NAME.search(match.group()).group()

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
                    mark_id=mark, source=source, destination=destination,
                    chain=chain, protocol=protocol, line_number=line_number)

    @classmethod
    def add(cls, mangling_mark):
        if not cls.enable:
            return 0

        return SubprocessRunner(mangling_mark.to_append_command()).run()
