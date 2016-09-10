# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import unicode_literals
from collections import namedtuple

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._iptables import IptablesMangleMark
from tcconfig._iptables import IptablesMangleController


_DEF_SRC = "192.168.0.0/24"
_DEF_DST = "192.168.100.0/24"


mangle_mark_list = [
    IptablesMangleMark(
        line_number=1,
        mark_id=1,
        source=_DEF_SRC,
        destination=_DEF_DST,
        protocol="all"
    ),
    IptablesMangleMark(
        line_number=1,
        mark_id=12,
        source=_DEF_SRC,
        destination=_DEF_DST,
        protocol="tcp"
    ),
    IptablesMangleMark(
        line_number=100,
        mark_id=123,
        source=_DEF_SRC,
        destination="anywhere",
        protocol="all"
    ),
    IptablesMangleMark(
        line_number=100,
        mark_id=1234,
        source="anywhere",
        destination=_DEF_DST,
        protocol="all"
    ),
    IptablesMangleMark(
        line_number=100,
        mark_id=12345,
        source="anywhere",
        destination="anywhere",
        protocol="all"
    ),
]


def clear_mangle_table():
    SubprocessRunner("iptables -t mangle -F").run()


class Test_IptablesMangleMark_repr(object):

    def test_smoke(self):
        for mangle_mark in mangle_mark_list:
            assert len(str(mangle_mark)) > 0


class Test_IptablesMangleMark_to_append_command(object):
    _CMD_PREFIX = "iptables -A PREROUTING -t mangle -j MARK"

    @pytest.mark.parametrize(
        [
            "mark_id", "source", "destination", "protocol", "line_number",
            "expected"
        ],
        [
            [
                2, _DEF_SRC, _DEF_DST, "all", None,
                "{} --set-mark 2 -p all -s {} -d {}".format(
                    _CMD_PREFIX, _DEF_SRC, _DEF_DST),
            ],
            [
                2, _DEF_SRC, _DEF_DST, "all", 1,
                "{} --set-mark 2 -p all -s {} -d {}".format(
                    _CMD_PREFIX, _DEF_SRC, _DEF_DST),
            ],
            [
                2, _DEF_SRC, _DEF_DST, "tcp", 1,
                "{} --set-mark 2 -p tcp -s {} -d {}".format(
                    _CMD_PREFIX, _DEF_SRC, _DEF_DST),
            ],
            [
                100, _DEF_SRC, "anywhere", "all", 100,
                "{} --set-mark 100 -p all -s {}".format(
                    _CMD_PREFIX, _DEF_SRC),
            ],
            [
                1, "anywhere", _DEF_DST, "all", 100,
                "{} --set-mark 1 -p all -d {}".format(
                    _CMD_PREFIX, _DEF_DST),
            ],
            [
                1, "anywhere", "anywhere", "all", 100,
                "{} --set-mark 1 -p all".format(
                    _CMD_PREFIX),
            ],
        ]
    )
    def test_normal(
            self, mark_id, source, destination, protocol, line_number,
            expected):
        mark = IptablesMangleMark(
            mark_id, source, destination, protocol, line_number)
        assert mark.to_append_command() == expected


class Test_IptablesMangleMark_to_delete_command(object):

    @pytest.mark.parametrize(
        [
            "mark_id", "source", "destination", "protocol", "line_number",
            "expected"
        ],
        [
            [
                2, _DEF_SRC, _DEF_DST, "all", 1,
                "iptables -t mangle -D PREROUTING 1",
            ],
        ]
    )
    def test_normal(
            self, mark_id, source, destination, protocol, line_number,
            expected):
        mark = IptablesMangleMark(
            mark_id, source, destination, protocol, line_number)
        assert mark.to_delete_command() == expected

    @pytest.mark.parametrize(
        [
            "mark_id", "source", "destination", "protocol", "line_number",
            "expected"
        ],
        [
            [
                2, _DEF_SRC, _DEF_DST, "all", None,
                TypeError,
            ],
        ]
    )
    def test_exception(
            self, mark_id, source, destination, protocol, line_number,
            expected):
        mark = IptablesMangleMark(
            mark_id, source, destination, protocol, line_number)
        with pytest.raises(expected):
            mark.to_delete_command()


class Test_IptablesMangleController_get_unique_mark_id(object):

    @pytest.mark.xfail
    def test_normal(self):
        clear_mangle_table()

        for i in range(10):
            mark_id = IptablesMangleController.get_unique_mark_id()

            assert mark_id == (i + 1)
            assert IptablesMangleController.add(
                IptablesMangleMark(mark_id, _DEF_SRC, _DEF_DST)) == 0


class Test_IptablesMangleController_add(object):

    @pytest.mark.xfail
    def test_normal(self):
        clear_mangle_table()
        initial_len = len(IptablesMangleController.get_iptables())

        for mangle_mark in mangle_mark_list:
            assert IptablesMangleController.add(mangle_mark) == 0

        assert len(IptablesMangleController.get_iptables()) > initial_len


class Test_IptablesMangleController_clear(object):

    @pytest.mark.xfail
    def test_normal(self):
        clear_mangle_table()
        initial_len = len(IptablesMangleController.get_iptables())

        for mangle_mark in mangle_mark_list:
            assert IptablesMangleController.add(mangle_mark) == 0

        assert len(IptablesMangleController.get_iptables()) > initial_len

        IptablesMangleController.clear()

        assert len(IptablesMangleController.get_iptables()) == initial_len


class Test_IptablesMangleController_parse(object):

    @pytest.mark.xfail
    def test_normal(self):
        clear_mangle_table()

        for mangle_mark in mangle_mark_list:
            assert IptablesMangleController.add(mangle_mark) == 0

        for lhs_mangle, rhs_mangle in zip(
                IptablesMangleController.parse(), reversed(mangle_mark_list)):
            assert lhs_mangle.protocol == rhs_mangle.protocol
            assert lhs_mangle.source == rhs_mangle.source
            assert lhs_mangle.destination == rhs_mangle.destination
            assert lhs_mangle.mark_id == rhs_mangle.mark_id
