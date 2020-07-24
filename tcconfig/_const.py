"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import enum


LIST_MANGLE_TABLE_OPTION = "-t mangle --line-numbers -L"
IPV6_OPTION_ERROR_MSG_FORMAT = "{}. --ipv6 option required to use IPv6 address."
DELAY_DISTRIBUTIONS = ("normal", "pareto", "paretonormal")


@enum.unique
class TcSubCommand(enum.Enum):
    CLASS = "class"
    FILTER = "filter"
    QDISC = "qdisc"


class Network:
    class Ipv4:
        ANYWHERE = "0.0.0.0/0"

    class Ipv6:
        ANYWHERE = "::/0"


class ShapingAlgorithm:
    HTB = "htb"
    TBF = "tbf"
    LIST = [HTB, TBF]


class Tc:
    class Command:
        TCSET = "tcset"
        TCDEL = "tcdel"
        TCSHOW = "tcshow"

    class Param:
        DEVICE = "device"
        DIRECTION = "direction"
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

    class ValueRange:
        class LatencyTime:
            MIN = "0ms"
            MAX = "60min"

    class Min:
        LATENCY_TIME = "0ms"

    class Max:
        LATENCY_TIME = "60min"


class TcCommandOutput:
    NOT_SET = None
    STDOUT = "STDOUT"
    SCRIPT = "SCRIPT"


class TrafficDirection:
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    LIST = [OUTGOING, INCOMING]
