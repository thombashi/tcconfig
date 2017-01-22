# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import print_function
from __future__ import unicode_literals

import pytest
import six

import tcconfig.parser


@pytest.fixture
def filter_parser():
    return tcconfig.parser.TcFilterParser()


@pytest.fixture
def qdisc_parser():
    return tcconfig.parser.TcQdiscParser()


class Test_TcFilterParser_parse_filter(object):

    @pytest.mark.parametrize(["value", "expected"], [
        [None, []],
        ["", []],
        [
            six.b("""filter parent 1: protocol ip pref 1 u32
filter parent 1: protocol ip pref 1 u32 fh 801: ht divisor 1
filter parent 1: protocol ip pref 1 u32 fh 801::800 order 2048 key ht 801 bkt 0 flowid 1:1
  match c0a8000a/ffffffff at 16
filter parent 1: protocol ip pref 2 u32
filter parent 1: protocol ip pref 2 u32 fh 800: ht divisor 1
filter parent 1: protocol ip pref 2 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1:2
  match 00000000/00000000 at 16"""),
            [
                {'flowid': '1:1', 'network': '192.168.0.10/32', 'port': None},
                {'flowid': '1:2', 'network': '0.0.0.0/0', 'port': None},
            ],
        ],
        [
            six.b("""filter parent 1: protocol ip pref 1 u32
filter parent 1: protocol ip pref 1 u32 fh 801: ht divisor 1
filter parent 1: protocol ip pref 1 u32 fh 801::800 order 2048 key ht 801 bkt 0 flowid 1:1
  match c0a80000/ffffff00 at 16
  match 00000050/0000ffff at 20
filter parent 1: protocol ip pref 2 u32
filter parent 1: protocol ip pref 2 u32 fh 800: ht divisor 1
filter parent 1: protocol ip pref 2 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1:2
  match 00000000/00000000 at 16"""),
            [
                {'flowid': '1:1', 'network': '192.168.0.0/24', 'port': 80},
                {'flowid': '1:2', 'network': '0.0.0.0/0', 'port': None},
            ],
        ],
        [
            six.b("""filter parent 1: protocol ip pref 1 u32
filter parent 1: protocol ip pref 1 u32 fh 801: ht divisor 1
filter parent 1: protocol ip pref 1 u32 fh 801::800 order 2048 key ht 801 bkt 0 flowid 1:3
  match c0a8000a/ffffffff at 12
  match 00001f90/0000ffff at 20
filter parent 1: protocol ip pref 2 u32
filter parent 1: protocol ip pref 2 u32 fh 800: ht divisor 1
filter parent 1: protocol ip pref 2 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1:2
  match 00000000/00000000 at 12"""),
            [
                {'flowid': '1:3', 'network': '192.168.0.10/32', 'port': 8080},
                {'flowid': '1:2', 'network': '0.0.0.0/0', 'port': None},
            ],
        ],
        [
            six.b("""filter parent 1f1c: protocol ip pref 1 fw
filter parent 1f1c: protocol ip pref 1 fw handle 0x65 classid 1f1c:1"""),
            [
                {'classid': '1f1c:1', 'handle': 101},
            ],
        ],
    ])
    def test_normal(self, filter_parser, value, expected):
        actual = filter_parser.parse_filter(value)

        print("[expected]\n{}".format(expected))
        print("\n[actual]\n{}".format(actual))

        assert actual == expected


class Test_TcFilterParser_parse_incoming_device(object):

    @pytest.mark.parametrize(["value", "expected"], [
        ["", None],
        [None, None],
        [
            six.b("""filter parent ffff: protocol ip pref 49152 u32
filter parent ffff: protocol ip pref 49152 u32 fh 800: ht divisor 1
filter parent ffff: protocol ip pref 49152 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1f87:
  match 00000000/00000000 at 0
        action order 1: mirred (Egress Redirect to device ifb8071) stolen
        index 98 ref 1 bind 1"""),
            "ifb8071",
        ],
        [
            six.b("""filter parent ffff: protocol ip pref 49152 u32
filter parent ffff: protocol ip pref 49152 u32 fh 800: ht divisor 1
filter parent ffff: protocol ip pref 49152 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1:
  match 00000000/00000000 at 0
        action order 1: mirred (Egress Redirect to device ifb0) stolen
        index 3795 ref 1 bind 1"""),
            "ifb0",
        ],
    ])
    def test_normal(self, filter_parser, value, expected):
        assert filter_parser.parse_incoming_device(value) == expected


class Test_TcQdiscParser_parse(object):

    @pytest.mark.parametrize(["value", "expected"], [
        [
            six.b("""qdisc htb 1f87: root refcnt 2 r2q 10 default 1 direct_packets_stat 1 direct_qlen 1000
qdisc netem 2007: parent 1f87:2 limit 1000 delay 1.0ms loss 0.01%
"""),
            [{'delay': '1.0', 'loss': '0.01', 'parent': '1f87:2'}],
        ],
        [
            six.b("""
qdisc htb 1f87: root refcnt 2 r2q 10 default 1 direct_packets_stat 0 direct_qlen 1000
qdisc netem 2007: parent 1f87:2 limit 1000 delay 5.0ms
qdisc netem 2008: parent 1f87:3 limit 1000 delay 50.0ms  1.0ms loss 5%
"""),
            [
                {'delay': '5.0', 'parent': '1f87:2'},
                {
                    'delay': '50.0', 'loss': '5',
                    'delay-distro': '1.0', 'parent': '1f87:3',
                },
            ],
        ],
    ])
    def test_normal(self, qdisc_parser, value, expected):
        actual = list(qdisc_parser.parse(value))

        print("[expected]\n{}".format(expected))
        print("\n[actual]\n{}".format(actual))

        assert actual == expected
