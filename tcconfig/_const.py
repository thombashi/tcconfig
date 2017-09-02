# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals


VERSION = "0.15.0"

KILO_SIZE = 1000
LIST_MANGLE_TABLE_COMMAND = "iptables -t mangle --line-numbers -L"
IPV6_OPTION_ERROR_MSG_FORMAT = "{}. --ipv6 option required to use IPv6 address."


class Network(object):
    class Ipv4(object):
        ANYWHERE = "0.0.0.0/0"

    class Ipv6(object):
        ANYWHERE = "::/0"


class ShapingAlgorithm(object):
    HTB = "htb"
    TBF = "tbf"
    LIST = [HTB, TBF]


class Tc(object):

    class Command(object):
        TCSET = "tcset"
        TCDEL = "tcdel"
        TCSHOW = "tcshow"

    class Subcommand(object):
        CLASS = "class"
        FILTER = "filter"
        QDISC = "qdisc"
        SHOW = "show"

        LIST = (CLASS, FILTER, QDISC, SHOW)

    class Param(object):
        DEVICE = "device"
        FILTER_ID = "filter_id"
        CLASS_ID = "classid"
        DST_NETWORK = "dst-network"
        DST_PORT = "dst-port"
        FLOW_ID = "flowid"
        HANDLE = "handle"
        PARENT = "parent"
        PRIORITY = "priority"
        PROTOCOL = "protocol"
        SRC_NETWORK = "src-network"
        SRC_PORT = "src-port"

    class ValueRange(object):
        class LatencyTime(object):
            MIN = "0ms"
            MAX = "60min"

    class Min(object):
        LATENCY_TIME = "0ms"

    class Max(object):
        LATENCY_TIME = "60min"


class TcCommandOutput(object):
    NOT_SET = None
    STDOUT = "STDOUT"
    SCRIPT = "SCRIPT"


class TrafficDirection(object):
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    LIST = [OUTGOING, INCOMING]
