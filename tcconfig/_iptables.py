"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import errno
import re

import typepy
from subprocrunner import SubprocessRunner
from typepy import Integer

from ._common import find_bin_path
from ._const import LIST_MANGLE_TABLE_OPTION, Network
from ._logger import logger
from ._network import sanitize_network
from ._split_line_list import split_line_list


VALID_CHAIN_LIST = ["PREROUTING", "INPUT", "OUTPUT"]


def get_iptables_base_command():
    iptables_path = find_bin_path("iptables")

    if iptables_path:
        if re.search("iptables$", iptables_path):
            return iptables_path

        # debian/ubuntu may return /sbin/xtables-multi
        return f"{iptables_path:s} iptables"

    return None


class IptablesMangleMarkEntry:
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
        self,
        ip_version,
        mark_id,
        source,
        destination,
        chain,
        protocol="all",
        line_number=None,
    ):
        self.__line_number = line_number
        self.__mark_id = mark_id
        self.__source = sanitize_network(source, ip_version)
        self.__destination = sanitize_network(destination, ip_version)
        self.__protocol = protocol

        if chain not in VALID_CHAIN_LIST:
            raise ValueError(f"invalid chain: {chain}")

        self.__chain = chain

    def __eq__(self, other):
        return all(
            [
                self.chain == other.chain,
                self.mark_id == other.mark_id,
                self.protocol == other.protocol,
                self.source == other.source,
                self.destination == other.destination,
            ]
        )

    def __repr__(self, *args, **kwargs):
        str_list = []

        if Integer(self.line_number).is_type():
            str_list.append(f"line-num={self.line_number}")

        str_list.extend(
            [
                f"protocol={self.protocol:s}",
                f"source={self.source:s}",
                f"destination={self.destination:s}",
                f"mark_id={self.mark_id:d}",
                f"chain={self.chain:s}",
            ]
        )

        return ", ".join(str_list)

    def to_append_command(self):
        Integer(self.mark_id).validate()

        command_item_list = [
            f"{get_iptables_base_command():s} -A {self.chain:s} -t mangle -j MARK",
            f"--set-mark {self.mark_id}",
        ]

        if typepy.is_not_null_string(self.protocol) or Integer(self.protocol).is_type():
            command_item_list.append(f"-p {self.protocol}")
        if self.__is_valid_srcdst(self.source):
            command_item_list.append(f"-s {self.source:s}")
        if self.__is_valid_srcdst(self.destination):
            command_item_list.append(f"-d {self.destination:s}")

        return " ".join(command_item_list)

    def to_delete_command(self):
        Integer(self.line_number).validate()

        return "{:s} -t mangle -D {:s} {}".format(
            get_iptables_base_command(), self.chain, self.line_number
        )

    @staticmethod
    def __is_valid_srcdst(srcdst):
        return typepy.is_not_null_string(srcdst) and srcdst not in (
            Network.Ipv4.ANYWHERE,
            Network.Ipv6.ANYWHERE,
        )


class IptablesMangleController:
    __RE_CHAIN = re.compile("Chain {:s} |Chain {:s} |Chain {:s} ".format(*VALID_CHAIN_LIST))
    __RE_CHAIN_NAME = re.compile("{:s}|{:s}|{:s}".format(*VALID_CHAIN_LIST))
    __MAX_MARK_ID = 0xFFFFFFFF
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

        self.__check_execution_authority()

        for mangle in self.parse():
            proc = SubprocessRunner(mangle.to_delete_command())
            if proc.run() != 0:
                raise OSError(proc.returncode, proc.stderr)

    def get_iptables(self):
        self.__check_execution_authority()

        proc = SubprocessRunner(f"{get_iptables_base_command():s} {LIST_MANGLE_TABLE_OPTION:s}")
        if proc.run() != 0:
            raise OSError(proc.returncode, proc.stderr)

        return proc.stdout

    def get_unique_mark_id(self):
        self.__check_execution_authority()

        mark_id_list = [mangle.mark_id for mangle in self.parse()]
        logger.debug(f"mangle mark list: {mark_id_list}")

        unique_mark_id = 1 + self.__MARK_ID_OFFSET
        while unique_mark_id < self.__MAX_MARK_ID:
            if unique_mark_id not in mark_id_list:
                return unique_mark_id

            unique_mark_id += 1

        raise RuntimeError("usable mark id not found")

    def parse(self):
        self.__check_execution_authority()

        MANGLE_ITEM_COUNT = 6

        for block in split_line_list(self.get_iptables().splitlines()):
            if len(block) <= 1:
                # skip if there is no mangle table entry exists
                continue

            match = self.__RE_CHAIN.search(block[0])
            if match is None:
                continue

            chain = self.__RE_CHAIN_NAME.search(match.group()).group()

            for line in reversed(block[2:]):
                item_list = line.split()
                if len(item_list) < MANGLE_ITEM_COUNT:
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

                yield IptablesMangleMarkEntry(
                    ip_version=self.__ip_version,
                    mark_id=mark,
                    source=source,
                    destination=destination,
                    chain=chain,
                    protocol=protocol,
                    line_number=line_number,
                )

    @classmethod
    def add(cls, mangling_mark):
        if not cls.enable:
            return 0

        cls.__check_execution_authority()

        return SubprocessRunner(mangling_mark.to_append_command()).run()

    @staticmethod
    def __check_execution_authority():
        from ._capabilities import get_permission_error_message, has_execution_authority

        if not has_execution_authority("iptables"):
            raise OSError(errno.EPERM, get_permission_error_message("iptables"))
