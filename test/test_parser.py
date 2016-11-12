# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

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
                {'classid': u'1f1c:1', 'handle': 101},
            ],
        ],
    ])
    def test_normal(self, filter_parser, value, expected):
        assert filter_parser.parse_filter(value) == expected


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
        ["", {}],
        [
            six.b("""qdisc prio 1: root refcnt 2 bands 3 priomap  1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1
qdisc netem 11: parent 1:1 limit 1000 delay 10.0ms loss 0.1% corrupt 0.1%
qdisc tbf 20: parent 11:1 rate 100Mbit burst 100000b limit 10000b"""),
            {
                'parent': '1:1',
                'corrupt': "0.1",
                'delay': '10.0',
                'loss': '0.1',
                'rate': '100M',
            },
        ],
        [
            six.b("""qdisc prio 1: dev eth0 root refcnt 2 bands 3 priomap  1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1
qdisc netem 11: dev eth0 parent 1:1 limit 1000 delay 10.0ms  2.0ms loss 0.1% corrupt 0.1%
qdisc tbf 20: dev eth0 parent 11:1 rate 100Mbit burst 100000b limit 10000b
qdisc pfifo_fast 0: dev ifb0 root refcnt 2 bands 3 priomap  1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1"""),
            {
                'parent': '1:1',
                'corrupt': "0.1",
                'delay': '10.0',
                'delay-distro': '2.0',
                'loss': '0.1',
                'rate': '100M',
            },
        ],
        [
            six.b("""qdisc prio 1: root refcnt 2 bands 3 priomap  1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1
qdisc netem 11: parent 1:1 limit 1000 delay 1.0ms loss 0.01%
qdisc tbf 20: parent 11:1 rate 250Kbit burst 1600b lat 268.8ms"""),
            {
                'parent': '1:1',
                'delay': '1.0',
                'loss': '0.01',
                'rate': '250K',
            },
        ]
    ])
    def test_normal(self, qdisc_parser, value, expected):
        assert qdisc_parser.parse(value) == expected

    @pytest.mark.parametrize(["value", "expected"], [
        [None, AttributeError],
    ])
    def test_exception(self, qdisc_parser, value, expected):
        with pytest.raises(expected):
            qdisc_parser.parse(value)
