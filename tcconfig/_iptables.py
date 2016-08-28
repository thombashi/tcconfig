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

from ._split_line_list import split_line_list


class IptablesMangleMark(object):

    @property
    def number(self):
        return self.__number

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
    def mark(self):
        return self.__mark

    def __init__(self, number, mark, source, destination, protocol="all"):
        self.__chain = "PREROUTING"
        self.__number = number
        self.__mark = mark
        self.__source = source
        self.__destination = destination
        self.__protocol = protocol

    def __repr__(self, *args, **kwargs):
        return "num={:d}, protocol={:s}, src={:s}, dst={:s}, mark={:d}".format(
            self.number, self.protocol, self.source, self.destination,
            self.mark)

    def to_append_command(self):
        if not IntegerTypeChecker(self.mark).is_type():
            raise ValueError(
                "mark attribute must be an integer: actual={}".format(
                    self.mark))

        command_item_list = [
            "iptables -A PREROUTING -t mangle -j MARK",
            "--set-mark {:d}".format(self.mark),
        ]

        if any([
            dataproperty.is_not_empty_string(self.protocol),
            IntegerTypeChecker(self.protocol).is_type(),
        ]):
            command_item_list.append("-p {}".format(self.protocol))
        if self.__is_valid_srcdst(self.source):
            command_item_list.append("-s {:s}".format(self.source))
        if self.__is_valid_srcdst(self.destination):
            command_item_list.append("-d {:s}".format(self.destination))

        return " ".join(command_item_list)

    @staticmethod
    def __is_valid_srcdst(srcdst):
        return all([
            dataproperty.is_not_empty_string(srcdst),
            srcdst.lower() != "anywhere",
        ])


class IptablesMangleController(object):

    __RE_CHAIN_NAME_PREROUTING = re.compile("Chain PREROUTING")

    def clear(self):
        for mangle in self.parse():
            proc = SubprocessRunner(
                "iptables -t mangle -D PREROUTING {:d}".format(mangle.number))
            if proc.run():
                raise RuntimeError(str(proc.stderr))

    def parse(self):
        proc = SubprocessRunner("iptables -t mangle --line-numbers -L")
        if proc.run() != 0:
            raise RuntimeError(str(proc.stderr))

        for block in split_line_list(proc.stdout.splitlines()):
            if len(block) <= 1:
                # skip if no entry exists
                continue

            if self.__RE_CHAIN_NAME_PREROUTING.search(block[0]) is None:
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

    def add(self, mangling_mark):
        SubprocessRunner(mangling_mark.to_append_command()).run()


if __name__ == '__main__':
    # temporal tests

    iptables = IptablesMangleController()
    for mangling_mark in iptables.parse():
        print(mangling_mark.to_append_command())
        print(mangling_mark)

    iptables.clear()
    for _i in range(3):
        iptables.add(mangling_mark)
