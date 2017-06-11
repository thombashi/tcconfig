# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals


VERSION = "0.12.0"

KILO_SIZE = 1000
LIST_MANGLE_TABLE_COMMAND = "iptables -t mangle --line-numbers -L"


class Network(object):
    class Ipv4(object):
        ANYWHERE = "0.0.0.0/0"

    class Ipv6(object):
        ANYWHERE = "::0/0"


class Tc(object):

    class Subcommand(object):
        CLASS = "class"
        FILTER = "filter"
        QDISC = "qdisc"
        SHOW = "show"

    class Param(object):
        CLASS_ID = "classid"
        DST_NETWORK = "dst-network"
        DST_PORT = "dst-port"
        FLOW_ID = "flowid"
        HANDLE = "handle"
        PARENT = "parent"
        PROTOCOL = "protocol"
        SRC_NETWORK = "src-network"
        SRC_PORT = "src-port"


class TcCommand(object):
    TCSET = "tcset"
    TCDEL = "tcdel"
    TCSHOW = "tcshow"


class TcCommandOutput(object):
    NOT_SET = None
    STDOUT = "STDOUT"
    SCRIPT = "SCRIPT"


class TrafficDirection(object):
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    LIST = [OUTGOING, INCOMING]
