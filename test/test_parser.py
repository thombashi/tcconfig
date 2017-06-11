# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import print_function
from __future__ import unicode_literals

import pytest
import six

from tcconfig._const import Tc
import tcconfig.parser._filter
import tcconfig.parser._qdisc
import tcconfig.parser.shaping_rule


@pytest.fixture
def filter_parser_ipv4():
    return tcconfig.parser._filter.TcFilterParser(ip_version=4)


@pytest.fixture
def filter_parser_ipv6():
    return tcconfig.parser._filter.TcFilterParser(ip_version=6)


@pytest.fixture
def qdisc_parser():
    return tcconfig.parser._qdisc.TcQdiscParser()


class Test_TcFilterParser_parse_filter_ipv4(object):

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
                {
                    Tc.Param.FLOW_ID: '1:1',
                    Tc.Param.DST_NETWORK: '192.168.0.10/32',
                    Tc.Param.PROTOCOL: 'ip',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: None,
                },
                {
                    Tc.Param.FLOW_ID: '1:2',
                    Tc.Param.DST_NETWORK: '0.0.0.0/0',
                    Tc.Param.PROTOCOL: 'ip',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: None,
                },
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
  match 00000000/00000000 at 16
  match 04d20000/ffff0000 at 20"""),
            [
                {
                    Tc.Param.FLOW_ID: '1:1',
                    Tc.Param.DST_NETWORK: '192.168.0.0/24',
                    Tc.Param.PROTOCOL: 'ip',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: 80,
                },
                {
                    Tc.Param.FLOW_ID: '1:2',
                    Tc.Param.DST_NETWORK: '0.0.0.0/0',
                    Tc.Param.PROTOCOL: 'ip',
                    Tc.Param.SRC_PORT: 1234,
                    Tc.Param.DST_PORT: None,
                },
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
                {
                    Tc.Param.FLOW_ID: '1:3',
                    Tc.Param.DST_NETWORK: '192.168.0.10/32',
                    Tc.Param.PROTOCOL: 'ip',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: 8080,
                },
                {
                    Tc.Param.FLOW_ID: '1:2',
                    Tc.Param.DST_NETWORK: '0.0.0.0/0',
                    Tc.Param.PROTOCOL: 'ip',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: None,
                },
            ],
        ],
        [
            six.b("""filter parent 1a1a: protocol ip pref 1 u32
filter parent 1a1a: protocol ip pref 1 u32 fh 800: ht divisor 1
filter parent 1a1a: protocol ip pref 1 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1a1a:2
  match 00000000/00000000 at 16
  match 15b3115c/ffffffff at 20"""),
            [
                {
                    Tc.Param.FLOW_ID: '1a1a:2',
                    Tc.Param.DST_NETWORK: '0.0.0.0/0',
                    Tc.Param.PROTOCOL: 'ip',
                    Tc.Param.SRC_PORT: 5555,
                    Tc.Param.DST_PORT: 4444,
                },
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
    def test_normal(self, filter_parser_ipv4, value, expected):
        actual = filter_parser_ipv4.parse_filter(value)

        print("[expected]\n{}".format(expected))
        print("\n[actual]\n{}".format(actual))

        assert actual == expected


class Test_TcFilterParser_parse_filter_ipv6(object):

    @pytest.mark.parametrize(["value", "expected"], [
        [None, []],
        ["", []],
        [
            six.b("""filter parent 1f87: protocol ipv6 pref 1 u32
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800: ht divisor 1
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1f87:2
  match 00000000/ffffffff at 24
  match 00000000/ffffffff at 28
  match 00000000/ffffffff at 32
  match 00000001/ffffffff at 36"""),
            [
                {
                    Tc.Param.FLOW_ID: '1f87:2',
                    Tc.Param.DST_NETWORK: '::1/128',
                    Tc.Param.PROTOCOL: 'ipv6',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: None,
                },
            ]
        ],
        [
            six.b("""filter parent 1f87: protocol ipv6 pref 1 u32
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800: ht divisor 1
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1f87:2
  match 2001db00/ffffffff at 8
  match 00000000/ffffffff at 12
  match 00000000/ffffffff at 16
  match 00000001/ffffffff at 20"""),
            [
                {
                    Tc.Param.FLOW_ID: '1f87:2',
                    Tc.Param.PROTOCOL: 'ipv6',
                    Tc.Param.DST_NETWORK: '2001:db00::1/128',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: None
                }
            ]
        ],
        [
            six.b("""filter parent 1f87: protocol ipv6 pref 1 u32
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800: ht divisor 1
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1f87:2
  match 2001db00/ffffff00 at 24
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::801 order 2049 key ht 800 bkt 0 flowid 1f87:3
  match 2001db00/ffffffff at 24
  match 00000000/ffffffff at 28
  match 00000000/ffffffff at 32
  match 00000001/ffffffff at 36
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::802 order 2050 key ht 800 bkt 0 flowid 1f87:4
  match 00001f90/0000ffff at 40"""),
            [
                {
                    Tc.Param.FLOW_ID: '1f87:2',
                    Tc.Param.PROTOCOL: 'ipv6',
                    Tc.Param.DST_NETWORK: '2001:db00::/24',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: None
                },
                {
                    Tc.Param.FLOW_ID: '1f87:3',
                    Tc.Param.PROTOCOL: 'ipv6',
                    Tc.Param.DST_NETWORK: '2001:db00::1/128',
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: None
                },
                {
                    Tc.Param.FLOW_ID: '1f87:4',
                    Tc.Param.PROTOCOL: 'ipv6',
                    Tc.Param.DST_NETWORK: None,
                    Tc.Param.SRC_PORT: None,
                    Tc.Param.DST_PORT: 8080
                },
            ]
        ],
        [
            six.b("""filter parent 1f87: protocol ipv6 pref 1 u32
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800: ht divisor 1
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::802 order 2050 key ht 800 bkt 0 flowid 1f87:4
  match 00501f90/ffffffff at 40"""),
            [
                {
                    Tc.Param.FLOW_ID: '1f87:4',
                    Tc.Param.PROTOCOL: 'ipv6',
                    Tc.Param.DST_NETWORK: None,
                    Tc.Param.SRC_PORT: 80,
                    Tc.Param.DST_PORT: 8080
                },
            ]
        ],
    ])
    def test_normal(self, filter_parser_ipv6, value, expected):
        actual = filter_parser_ipv6.parse_filter(value)

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
    def test_normal(self, filter_parser_ipv4, value, expected):
        assert filter_parser_ipv4.parse_incoming_device(value) == expected


class Test_TcQdiscParser_parse(object):

    @pytest.mark.parametrize(["value", "expected"], [
        [
            six.b("""qdisc htb 1f87: root refcnt 2 r2q 10 default 1 direct_packets_stat 1 direct_qlen 1000
qdisc netem 2007: parent 1f87:2 limit 1000 delay 1.0ms loss 0.01%
"""),
            [{'delay': '1.0', 'loss': '0.01', Tc.Param.PARENT: '1f87:2'}],
        ],
        [
            six.b("""
qdisc htb 1f87: root refcnt 2 r2q 10 default 1 direct_packets_stat 0 direct_qlen 1000
qdisc netem 2007: parent 1f87:2 limit 1000 delay 5.0ms
qdisc netem 2008: parent 1f87:3 limit 1000 delay 50.0ms  1.0ms loss 5%
"""),
            [
                {'delay': '5.0', Tc.Param.PARENT: '1f87:2'},
                {
                    'delay': '50.0', 'loss': '5',
                    'delay-distro': '1.0', Tc.Param.PARENT: '1f87:3',
                },
            ],
        ],
    ])
    def test_normal(self, qdisc_parser, value, expected):
        actual = list(qdisc_parser.parse(value))

        print("[expected]\n{}".format(expected))
        print("\n[actual]\n{}".format(actual))

        assert actual == expected
