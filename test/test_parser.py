"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import pytest
from simplesqlite import connect_memdb

import tcconfig.parser._filter
import tcconfig.parser._qdisc
import tcconfig.parser.shaping_rule
from tcconfig._const import Tc
from tcconfig.parser._class import TcClassParser
from tcconfig.parser._model import Filter, Qdisc

from .common import print_test_result


DEVICE = "eth0"


@pytest.fixture
def filter_parser_ipv4():
    return tcconfig.parser._filter.TcFilterParser(connect_memdb(), ip_version=4)


@pytest.fixture
def filter_parser_ipv6():
    return tcconfig.parser._filter.TcFilterParser(connect_memdb(), ip_version=6)


@pytest.fixture
def qdisc_parser():
    return tcconfig.parser._qdisc.TcQdiscParser(connect_memdb())


@pytest.fixture
def class_parser():
    return TcClassParser(connect_memdb())


def six_b(s):
    return s.encode("latin-1")


class Test_TcFilterParser_parse_filter_ipv4:
    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            [None, []],
            ["", []],
            [
                six_b(
                    """filter parent 1: protocol ip pref 1 u32
filter parent 1: protocol ip pref 1 u32 fh 801: ht divisor 1
filter parent 1: protocol ip pref 1 u32 fh 801::800 order 2048 key ht 801 bkt 0 flowid 1:1
  match c0a8000a/ffffffff at 16
filter parent 1: protocol ip pref 2 u32
filter parent 1: protocol ip pref 2 u32 fh 800: ht divisor 1
filter parent 1: protocol ip pref 2 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1:2
  match 00000000/00000000 at 16"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "801::800",
                            Tc.Param.FLOW_ID: "1:1",
                            Tc.Param.SRC_NETWORK: "0.0.0.0/0",
                            Tc.Param.DST_NETWORK: "192.168.0.10/32",
                            Tc.Param.PROTOCOL: "ip",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    ),
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::800",
                            Tc.Param.FLOW_ID: "1:2",
                            Tc.Param.SRC_NETWORK: "0.0.0.0/0",
                            Tc.Param.DST_NETWORK: "0.0.0.0/0",
                            Tc.Param.PROTOCOL: "ip",
                            Tc.Param.PRIORITY: 2,
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    ),
                ],
            ],
            [
                six_b(
                    """filter parent 1: protocol ip pref 1 u32
filter parent 1: protocol ip pref 1 u32 fh 801: ht divisor 1
filter parent 1: protocol ip pref 1 u32 fh 801::800 order 2048 key ht 801 bkt 0 flowid 1:1
  match c0a80000/ffffff00 at 16
  match 00000050/0000ffff at 20
filter parent 1: protocol ip pref 2 u32
filter parent 1: protocol ip pref 2 u32 fh 800: ht divisor 1
filter parent 1: protocol ip pref 2 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1:2
  match 00000000/00000000 at 16
  match 04d20000/ffff0000 at 20"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "801::800",
                            Tc.Param.FLOW_ID: "1:1",
                            Tc.Param.SRC_NETWORK: "0.0.0.0/0",
                            Tc.Param.DST_NETWORK: "192.168.0.0/24",
                            Tc.Param.PROTOCOL: "ip",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: 80,
                        }
                    ),
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::800",
                            Tc.Param.FLOW_ID: "1:2",
                            Tc.Param.SRC_NETWORK: "0.0.0.0/0",
                            Tc.Param.DST_NETWORK: "0.0.0.0/0",
                            Tc.Param.PROTOCOL: "ip",
                            Tc.Param.PRIORITY: 2,
                            Tc.Param.SRC_PORT: 1234,
                            Tc.Param.DST_PORT: None,
                        }
                    ),
                ],
            ],
            [
                six_b(
                    """filter parent 1: protocol ip pref 1 u32
filter parent 1: protocol ip pref 1 u32 fh 801: ht divisor 1
filter parent 1: protocol ip pref 1 u32 fh 801::800 order 2048 key ht 801 bkt 0 flowid 1:3
  match c0a8000a/ffffffff at 12
  match 00001f90/0000ffff at 20
filter parent 1: protocol ip pref 2 u32
filter parent 1: protocol ip pref 2 u32 fh 800: ht divisor 1
filter parent 1: protocol ip pref 2 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1:2
  match 00000000/00000000 at 12"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "801::800",
                            Tc.Param.FLOW_ID: "1:3",
                            Tc.Param.SRC_NETWORK: "192.168.0.10/32",
                            Tc.Param.DST_NETWORK: "0.0.0.0/0",
                            Tc.Param.PROTOCOL: "ip",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: 8080,
                        }
                    ),
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::800",
                            Tc.Param.FLOW_ID: "1:2",
                            Tc.Param.SRC_NETWORK: "0.0.0.0/0",
                            Tc.Param.DST_NETWORK: "0.0.0.0/0",
                            Tc.Param.PROTOCOL: "ip",
                            Tc.Param.PRIORITY: 2,
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    ),
                ],
            ],
            [
                six_b(
                    """filter parent 1a1a: protocol ip pref 1 u32
filter parent 1a1a: protocol ip pref 1 u32 fh 800: ht divisor 1
filter parent 1a1a: protocol ip pref 1 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1a1a:2
  match 00000000/00000000 at 16
  match 15b3115c/ffffffff at 20"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::800",
                            Tc.Param.FLOW_ID: "1a1a:2",
                            Tc.Param.SRC_NETWORK: "0.0.0.0/0",
                            Tc.Param.DST_NETWORK: "0.0.0.0/0",
                            Tc.Param.PROTOCOL: "ip",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_PORT: 5555,
                            Tc.Param.DST_PORT: 4444,
                        }
                    )
                ],
            ],
            [
                six_b(
                    """filter parent 1f1c: protocol ip pref 1 fw
filter parent 1f1c: protocol ip pref 1 fw handle 0x65 classid 1f1c:1"""
                ),
                [Filter(**{Tc.Param.DEVICE: DEVICE, "classid": "1f1c:1", "handle": 101})],
            ],
            [
                six_b(
                    """filter parent 120a: protocol ip pref 5 u32 chain 0
filter parent 120a: protocol ip pref 5 u32 chain 0 fh 800: ht divisor 1
filter parent 120a: protocol ip pref 5 u32 chain 0 fh 800::800 order 2048 key ht 800 bkt 0 flowid 120a:2 not_in_hw
  match 00000000/00000000 at 16
  match 00000000/00000000 at 12
filter parent 120a: protocol ipv6 pref 6 u32 chain 0
filter parent 120a: protocol ipv6 pref 6 u32 chain 0 fh 801: ht divisor 1
filter parent 120a: protocol ipv6 pref 6 u32 chain 0 fh 801::800 order 2048 key ht 801 bkt 0 flowid 120a:3 not_in_hw"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::800",
                            Tc.Param.FLOW_ID: "120a:2",
                            Tc.Param.SRC_NETWORK: "0.0.0.0/0",
                            Tc.Param.DST_NETWORK: "0.0.0.0/0",
                            Tc.Param.PROTOCOL: "ip",
                            Tc.Param.PRIORITY: 5,
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    ),
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "801::800",
                            Tc.Param.FLOW_ID: "120a:3",
                            Tc.Param.SRC_NETWORK: "0.0.0.0/0",
                            Tc.Param.DST_NETWORK: "0.0.0.0/0",
                            Tc.Param.PROTOCOL: "ipv6",
                            Tc.Param.PRIORITY: 6,
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    ),
                ],
            ],
        ],
    )
    def test_normal(self, filter_parser_ipv4, value, expected):
        Filter.attach(filter_parser_ipv4.con)
        Filter.create()
        filter_parser_ipv4.parse(DEVICE, value)
        actual = [f for f in Filter().select()]

        assert actual == expected


class Test_TcFilterParser_parse_filter_ipv6:
    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            [None, []],
            ["", []],
            [
                six_b(
                    """filter parent 1f87: protocol ipv6 pref 1 u32
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800: ht divisor 1
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1f87:2
  match 00000000/ffffffff at 24
  match 00000000/ffffffff at 28
  match 00000000/ffffffff at 32
  match 00000001/ffffffff at 36"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::800",
                            Tc.Param.FLOW_ID: "1f87:2",
                            Tc.Param.PROTOCOL: "ipv6",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_NETWORK: "::/0",
                            Tc.Param.DST_NETWORK: "::1/128",
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    )
                ],
            ],
            [
                six_b(
                    """filter parent 1f87: protocol ipv6 pref 1 u32
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800: ht divisor 1
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1f87:2
  match 2001db00/ffffffff at 8
  match 00000000/ffffffff at 12
  match 00000000/ffffffff at 16
  match 00000001/ffffffff at 20"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::800",
                            Tc.Param.FLOW_ID: "1f87:2",
                            Tc.Param.PROTOCOL: "ipv6",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_NETWORK: "2001:db00::1/128",
                            Tc.Param.DST_NETWORK: "::/0",
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    )
                ],
            ],
            [
                six_b(
                    """filter parent 1f87: protocol ipv6 pref 1 u32
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800: ht divisor 1
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1f87:2
  match 2001db00/ffffff00 at 24
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::801 order 2049 key ht 800 bkt 0 flowid 1f87:3
  match 2001db00/ffffffff at 24
  match 00000000/ffffffff at 28
  match 00000000/ffffffff at 32
  match 00000001/ffffffff at 36
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::802 order 2050 key ht 800 bkt 0 flowid 1f87:4
  match 00001f90/0000ffff at 40"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::800",
                            Tc.Param.FLOW_ID: "1f87:2",
                            Tc.Param.PROTOCOL: "ipv6",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_NETWORK: "::/0",
                            Tc.Param.DST_NETWORK: "2001:db00::/24",
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    ),
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::801",
                            Tc.Param.FLOW_ID: "1f87:3",
                            Tc.Param.PROTOCOL: "ipv6",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_NETWORK: "::/0",
                            Tc.Param.DST_NETWORK: "2001:db00::1/128",
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: None,
                        }
                    ),
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::802",
                            Tc.Param.FLOW_ID: "1f87:4",
                            Tc.Param.PROTOCOL: "ipv6",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_NETWORK: "::/0",
                            Tc.Param.DST_NETWORK: "::/0",
                            Tc.Param.SRC_PORT: None,
                            Tc.Param.DST_PORT: 8080,
                        }
                    ),
                ],
            ],
            [
                six_b(
                    """filter parent 1f87: protocol ipv6 pref 1 u32
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800: ht divisor 1
filter parent 1f87: protocol ipv6 pref 1 u32 fh 800::802 order 2050 key ht 800 bkt 0 flowid 1f87:4
  match 00501f90/ffffffff at 40"""
                ),
                [
                    Filter(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.FILTER_ID: "800::802",
                            Tc.Param.FLOW_ID: "1f87:4",
                            Tc.Param.PROTOCOL: "ipv6",
                            Tc.Param.PRIORITY: 1,
                            Tc.Param.SRC_NETWORK: "::/0",
                            Tc.Param.DST_NETWORK: "::/0",
                            Tc.Param.SRC_PORT: 80,
                            Tc.Param.DST_PORT: 8080,
                        }
                    )
                ],
            ],
        ],
    )
    def test_normal(self, filter_parser_ipv6, value, expected):
        Filter.attach(filter_parser_ipv6.con)
        Filter.create()
        filter_parser_ipv6.parse(DEVICE, value)
        actual = [f for f in Filter().select()]

        assert actual == expected


class Test_TcFilterParser_parse_incoming_device:
    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ["", None],
            [None, None],
            [
                six_b(
                    """filter parent ffff: protocol ip pref 49152 u32
filter parent ffff: protocol ip pref 49152 u32 fh 800: ht divisor 1
filter parent ffff: protocol ip pref 49152 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1f87:
  match 00000000/00000000 at 0
        action order 1: mirred (Egress Redirect to device ifb8071) stolen
        index 98 ref 1 bind 1"""
                ),
                "ifb8071",
            ],
            [
                six_b(
                    """filter parent ffff: protocol ip pref 49152 u32
filter parent ffff: protocol ip pref 49152 u32 fh 800: ht divisor 1
filter parent ffff: protocol ip pref 49152 u32 fh 800::800 order 2048 key ht 800 bkt 0 flowid 1:
  match 00000000/00000000 at 0
        action order 1: mirred (Egress Redirect to device ifb0) stolen
        index 3795 ref 1 bind 1"""
                ),
                "ifb0",
            ],
        ],
    )
    def test_normal(self, filter_parser_ipv4, value, expected):
        assert filter_parser_ipv4.parse_incoming_device(value) == expected


class Test_TcQdiscParser_parse:
    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            [
                six_b(
                    """qdisc htb 1f87: root refcnt 2 r2q 10 default 1 direct_packets_stat 1 direct_qlen 1000
qdisc netem 2007: parent 1f87:2 limit 1000 delay 1.0ms loss 0.01%
"""
                ),
                [
                    Qdisc(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            "delay": "1.0ms",
                            "loss": "0.01%",
                            Tc.Param.HANDLE: "2007:",
                            Tc.Param.PARENT: "1f87:2",
                            "direct_qlen": 1000,
                        }
                    )
                ],
            ],
            [
                six_b(
                    """qdisc htb 1a1a: root refcnt 2 r2q 10 default 1 direct_packets_stat 4 direct_qlen 1000
qdisc netem 1a9a: parent 1a1a:2 limit 1000
"""
                ),
                [
                    Qdisc(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            Tc.Param.HANDLE: "1a9a:",
                            Tc.Param.PARENT: "1a1a:2",
                            "direct_qlen": 1000,
                        }
                    )
                ],
            ],
            [
                six_b(
                    """
qdisc htb 1f87: root refcnt 2 r2q 10 default 1 direct_packets_stat 0 direct_qlen 1000
qdisc netem 2007: parent 1f87:2 limit 1000 delay 5.0ms
qdisc netem 2008: parent 1f87:3 limit 1000 delay 50.0ms  1.0ms loss 5%
"""
                ),
                [
                    Qdisc(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            "delay": "5.0ms",
                            Tc.Param.HANDLE: "2007:",
                            Tc.Param.PARENT: "1f87:2",
                            "direct_qlen": 1000,
                        }
                    ),
                    Qdisc(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            "delay": "50.0ms",
                            "loss": "5%",
                            "delay-distro": "1.0ms",
                            Tc.Param.HANDLE: "2008:",
                            Tc.Param.PARENT: "1f87:3",
                        }
                    ),
                ],
            ],
            [
                six_b(
                    """
qdisc htb 1f87: root refcnt 2 r2q 10 default 1 direct_packets_stat 0 direct_qlen 1000
qdisc netem 2007: parent 1f87:2 limit 1000 delay 2.5s
qdisc netem 2008: parent 1f87:3 limit 1000 delay 0.5s  1.0ms loss 5%
"""
                ),
                [
                    Qdisc(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            "delay": "2.5s",
                            Tc.Param.HANDLE: "2007:",
                            Tc.Param.PARENT: "1f87:2",
                            "direct_qlen": 1000,
                        }
                    ),
                    Qdisc(
                        **{
                            Tc.Param.DEVICE: DEVICE,
                            "delay": "0.5s",
                            "loss": "5%",
                            "delay-distro": "1.0ms",
                            Tc.Param.HANDLE: "2008:",
                            Tc.Param.PARENT: "1f87:3",
                        }
                    ),
                ],
            ],
        ],
    )
    def test_normal(self, qdisc_parser, value, expected):
        Qdisc.attach(qdisc_parser.con)
        Qdisc.create()
        qdisc_parser.parse(DEVICE, value)
        actual = [qdisc for qdisc in Qdisc.select()]

        assert actual == expected


class Test_TcClassParser_parse:
    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            [
                six_b(
                    """
class htb 120a:1 root prio rate 32Gbit ceil 32Gbit burst 0b cburst 0b
class htb 120a:2 root leaf 2946: prio rate 1Gbit ceil 1Gbit burst 125000Kb cburst 125000Kb
"""
                ),
                [
                    {
                        TcClassParser.Key.RATE: "32Gbps",
                        TcClassParser.Key.CLASS_ID: "120a:1",
                        TcClassParser.Key.DEVICE: "eth0",
                    },
                    {
                        TcClassParser.Key.RATE: "1Gbps",
                        TcClassParser.Key.CLASS_ID: "120a:2",
                        TcClassParser.Key.DEVICE: "eth0",
                    },
                ],
            ],
            [
                six_b(
                    """
class htb 120a:1 root prio rate 32Gbit ceil 32Gbit burst 0b cburst 0b
class htb 120a:2 root leaf 2518: prio rate 200Kbit ceil 200Kbit burst 25Kb cburst 25Kb
                    """
                ),
                [
                    {
                        TcClassParser.Key.RATE: "32Gbps",
                        TcClassParser.Key.DEVICE: "eth0",
                        TcClassParser.Key.CLASS_ID: "120a:1",
                    },
                    {
                        TcClassParser.Key.RATE: "200Kbps",
                        TcClassParser.Key.DEVICE: "eth0",
                        TcClassParser.Key.CLASS_ID: "120a:2",
                    },
                ],
            ],
        ],
    )
    def test_normal(self, class_parser, value, expected):
        actual = class_parser.parse(DEVICE, value)

        import json

        print_test_result(
            expected=json.dumps(expected, indent=4), actual=json.dumps(actual, indent=4)
        )

        assert actual == expected
