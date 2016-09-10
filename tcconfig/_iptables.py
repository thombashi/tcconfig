# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import re

import dataproperty
from dataproperty.type import IntegerTypeChecker
from subprocrunner import SubprocessRunner

from ._common import sanitize_network
from ._split_line_list import split_line_list


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

    def __init__(
            self, line_number, mark_id, source, destination, protocol="all"):
        self.__chain = "PREROUTING"
        self.__line_number = line_number
        self.__mark_id = mark_id
        self.__source = source
        self.__destination = destination
        self.__protocol = protocol

    def __repr__(self, *args, **kwargs):
        return "line-num={:d}, protocol={:s}, src={:s}, dst={:s}, mark-id={:d}".format(
            self.line_number, self.protocol, self.source, self.destination,
            self.mark_id)

    def to_append_command(self):
        if not IntegerTypeChecker(self.mark_id).is_type():
            raise ValueError(
                "mark attribute must be an integer: actual={}".format(
                    self.mark_id))

        command_item_list = [
            "iptables -A PREROUTING -t mangle -j MARK",
            "--set-mark {:d}".format(self.mark_id),
        ]

        if any([
            dataproperty.is_not_empty_string(self.protocol),
            IntegerTypeChecker(self.protocol).is_type(),
        ]):
            command_item_list.append("-p {}".format(self.protocol))
        if self.__is_valid_srcdst(self.source):
            command_item_list.append(
                "-s {:s}".format(sanitize_network(self.source)))
        if self.__is_valid_srcdst(self.destination):
            command_item_list.append(
                "-d {:s}".format(sanitize_network(self.destination)))

        return " ".join(command_item_list)

    @staticmethod
    def __is_valid_srcdst(srcdst):
        return all([
            dataproperty.is_not_empty_string(srcdst),
            srcdst.lower() != "anywhere",
        ])


class IptablesMangleController(object):

    __RE_CHAIN_NAME_PREROUTING = re.compile("Chain PREROUTING")

    @classmethod
    def clear(cls):
        for mangle in cls.parse():
            proc = SubprocessRunner(
                "iptables -t mangle -D PREROUTING {:d}".format(
                    mangle.line_number))
            if proc.run() != 0:
                raise RuntimeError(str(proc.stderr))

    @classmethod
    def get_iptables(cls):
        proc = SubprocessRunner("iptables -t mangle --line-numbers -L")
        if proc.run() != 0:
            raise RuntimeError(str(proc.stderr))

        return proc.stdout

    @classmethod
    def parse(cls):
        for block in split_line_list(cls.get_iptables().splitlines()):
            if len(block) <= 1:
                # skip if no entry exists
                continue

            if cls.__RE_CHAIN_NAME_PREROUTING.search(block[0]) is None:
                continue

            for line in reversed(block[2:]):
                item_list = line.split()
                if len(item_list) < 6:
                    continue

                number = int(item_list[0])
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
                    number, mark, source, destination, protocol)

    @classmethod
    def add(cls, mangling_mark):
        return SubprocessRunner(mangling_mark.to_append_command()).run()


if __name__ == '__main__':
    # temporal tests

    iptables = IptablesMangleController()
    for mangling_mark in iptables.parse():
        print(mangling_mark.to_append_command())
        print(mangling_mark)

    iptables.clear()
    for _i in range(3):
        iptables.add(mangling_mark)
