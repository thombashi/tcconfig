# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import unicode_literals

import random

import pytest

from tcconfig._iptables import (
    IptablesMangleController,
    IptablesMangleMark,
    VALID_CHAIN_LIST,
)


_DEF_SRC = "192.168.0.0/24"
_DEF_DST = "192.168.100.0/24"


prerouting_mangle_mark_list = [
    IptablesMangleMark(
        ip_version=4,
        line_number=1,
        mark_id=1,
        source=_DEF_SRC,
        destination=_DEF_DST,
        chain="PREROUTING",
        protocol="all"
    ),
]

input_mangle_mark_list = [
    IptablesMangleMark(
        ip_version=4,
        line_number=1,
        mark_id=1234,
        source="anywhere",
        destination=_DEF_DST,
        chain="INPUT",
        protocol="all"
    ),
]

output_mangle_mark_list = [
    IptablesMangleMark(
        ip_version=4,
        line_number=1,
        mark_id=12,
        source=_DEF_SRC,
        destination=_DEF_DST,
        chain="OUTPUT",
        protocol="tcp"
    ),
    IptablesMangleMark(
        ip_version=4,
        line_number=2,
        mark_id=123,
        source=_DEF_SRC,
        destination="anywhere",
        chain="OUTPUT",
        protocol="all"
    ),
    IptablesMangleMark(
        ip_version=4,
        line_number=3,
        mark_id=12345,
        source="anywhere",
        destination="anywhere",
        chain="OUTPUT",
        protocol="all"
    ),
]

mangle_mark_list = (
    prerouting_mangle_mark_list +
    input_mangle_mark_list +
    output_mangle_mark_list
)

reverse_mangle_mark_list = (
    list(reversed(prerouting_mangle_mark_list)) +
    list(reversed(input_mangle_mark_list)) +
    list(reversed(output_mangle_mark_list))
)


@pytest.fixture
def iptables_ctrl_ipv4():
    return IptablesMangleController(True, ip_version=4)


class Test_IptablesMangleMark_repr(object):

    def test_smoke(self):
        for mangle_mark in mangle_mark_list:
            assert len(str(mangle_mark)) > 0


class Test_IptablesMangleMark_to_append_command(object):
    _CMD_PREFIX = "iptables -A {:s} -t mangle -j MARK"

    @pytest.mark.parametrize(
        [
            "mark_id", "source", "destination", "chain", "protocol",
            "line_number", "expected"
        ],
        [
            [
                2, _DEF_SRC, _DEF_DST, "PREROUTING", "all", None,
                "{} --set-mark 2 -p all -s {} -d {}".format(
                    _CMD_PREFIX.format("PREROUTING"), _DEF_SRC, _DEF_DST),
            ],
            [
                2, _DEF_SRC, _DEF_DST, "OUTPUT", "all", 1,
                "{} --set-mark 2 -p all -s {} -d {}".format(
                    _CMD_PREFIX.format("OUTPUT"), _DEF_SRC, _DEF_DST),
            ],
            [
                2, _DEF_SRC, _DEF_DST, "OUTPUT", "tcp", 1,
                "{} --set-mark 2 -p tcp -s {} -d {}".format(
                    _CMD_PREFIX.format("OUTPUT"), _DEF_SRC, _DEF_DST),
            ],
            [
                100, _DEF_SRC, "anywhere", "INPUT", "all", 100,
                "{} --set-mark 100 -p all -s {}".format(
                    _CMD_PREFIX.format("INPUT"), _DEF_SRC),
            ],
            [
                1, "anywhere", _DEF_DST, "OUTPUT", "all", 100,
                "{} --set-mark 1 -p all -d {}".format(
                    _CMD_PREFIX.format("OUTPUT"), _DEF_DST),
            ],
            [
                1, "anywhere", "anywhere", "OUTPUT", "all", 100,
                "{} --set-mark 1 -p all".format(
                    _CMD_PREFIX.format("OUTPUT")),
            ],
        ]
    )
    def test_normal(
            self, mark_id, source, destination, chain, protocol, line_number,
            expected):
        mark = IptablesMangleMark(
            ip_version=4,
            mark_id=mark_id, source=source, destination=destination,
            chain=chain, protocol=protocol, line_number=line_number)
        assert mark.to_append_command() == expected


class Test_IptablesMangleMark_to_delete_command(object):

    @pytest.mark.parametrize(
        [
            "mark_id", "source", "destination",  "chain", "protocol",
            "line_number", "expected"
        ],
        [
            [
                2, _DEF_SRC, _DEF_DST, "PREROUTING", "all", 1,
                "iptables -t mangle -D PREROUTING 1",
            ],
            [
                20, None, None, "OUTPUT", "all", 2,
                "iptables -t mangle -D OUTPUT 2",
            ],
        ]
    )
    def test_normal(
            self, mark_id, source, destination, chain, protocol, line_number,
            expected):
        mark = IptablesMangleMark(
            ip_version=4,
            mark_id=mark_id, source=_DEF_SRC, destination=_DEF_DST,
            chain=chain, protocol=protocol, line_number=line_number)
        assert mark.to_delete_command() == expected

    @pytest.mark.parametrize(
        [
            "mark_id", "source", "destination", "chain", "protocol",
            "line_number", "expected"
        ],
        [
            [
                2, _DEF_SRC, _DEF_DST, "OUTPUT", "all", None,
                TypeError,
            ],
        ]
    )
    def test_exception(
            self, mark_id, source, destination, chain, protocol, line_number,
            expected):
        mark = IptablesMangleMark(
            ip_version=4,
            mark_id=mark_id, source=source, destination=destination,
            chain=chain, protocol=protocol, line_number=line_number)
        with pytest.raises(expected):
            mark.to_delete_command()


class Test_IptablesMangleController_get_unique_mark_id(object):

    @pytest.mark.xfail
    def test_normal(self, iptables_ctrl_ipv4):
        iptables_ctrl_ipv4.clear()

        for i in range(5):
            mark_id = iptables_ctrl_ipv4.get_unique_mark_id()

            assert mark_id == (i + 101)

            mangle_mark = IptablesMangleMark(
                ip_version=4,
                mark_id=mark_id, source=_DEF_SRC, destination=_DEF_DST,
                chain=random.choice(VALID_CHAIN_LIST))

            assert iptables_ctrl_ipv4.add(mangle_mark) == 0


class Test_IptablesMangleController_add(object):

    @pytest.mark.xfail
    def test_normal(self, iptables_ctrl_ipv4):
        iptables_ctrl_ipv4.clear()
        initial_len = len(iptables_ctrl_ipv4.get_iptables())

        for mangle_mark in mangle_mark_list:
            assert iptables_ctrl_ipv4.add(mangle_mark) == 0

        assert len(iptables_ctrl_ipv4.get_iptables()) > initial_len


class Test_IptablesMangleController_clear(object):

    @pytest.mark.xfail
    def test_normal(self, iptables_ctrl_ipv4):
        iptables_ctrl_ipv4.clear()

        initial_len = len(iptables_ctrl_ipv4.get_iptables())

        for mangle_mark in mangle_mark_list:
            assert iptables_ctrl_ipv4.add(mangle_mark) == 0

        assert len(iptables_ctrl_ipv4.get_iptables()) > initial_len

        iptables_ctrl_ipv4.clear()

        assert len(iptables_ctrl_ipv4.get_iptables()) == initial_len


class Test_IptablesMangleController_parse(object):
    @pytest.mark.xfail
    def test_normal(self, iptables_ctrl_ipv4):
        iptables_ctrl_ipv4.clear()

        for mangle_mark in mangle_mark_list:
            assert iptables_ctrl_ipv4.add(mangle_mark) == 0

        for lhs_mangle, rhs_mangle in zip(
                iptables_ctrl_ipv4.parse(), reverse_mangle_mark_list):

            print("lhs: {}".format(lhs_mangle))
            print("rhs: {}".format(rhs_mangle))

            assert lhs_mangle == rhs_mangle
