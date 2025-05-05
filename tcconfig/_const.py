"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import enum
from typing import Final


LIST_MANGLE_TABLE_OPTION: Final = "-t mangle --line-numbers -L"
IPV6_OPTION_ERROR_MSG_FORMAT: Final = "{}. --ipv6 option required to use IPv6 address."
DELAY_DISTRIBUTIONS = ("normal", "pareto", "paretonormal")


@enum.unique
class TcSubCommand(enum.Enum):
    CLASS = "class"
    FILTER = "filter"
    QDISC = "qdisc"


class Network:
    class Ipv4:
        ANYWHERE: Final = "0.0.0.0/0"

    class Ipv6:
        ANYWHERE: Final = "::/0"


@enum.unique
class ShapingAlgorithm(enum.Enum):
    HTB = "htb"
    TBF = "tbf"


class Tc:
    class Command:
        TCSET: Final = "tcset"
        TCDEL: Final = "tcdel"
        TCSHOW: Final = "tcshow"

    class Param:
        DEVICE: Final = "device"
        DIRECTION: Final = "direction"
        FILTER_ID: Final = "filter_id"
        CLASS_ID: Final = "classid"
        DST_NETWORK: Final = "dst_network"
        DST_PORT: Final = "dst_port"
        FLOW_ID: Final = "flowid"
        HANDLE: Final = "handle"
        PARENT: Final = "parent"
        PRIORITY: Final = "priority"
        PROTOCOL: Final = "protocol"
        SRC_NETWORK: Final = "src_network"
        SRC_PORT: Final = "src_port"

    class ValueRange:
        class LatencyTime:
            MIN: Final = "0ms"
            MAX: Final = "60min"

    class Min:
        LATENCY_TIME: Final = "0ms"

    class Max:
        LATENCY_TIME: Final = "60min"


class TcCommandOutput:
    NOT_SET: Final = None
    STDOUT: Final = "STDOUT"
    SCRIPT: Final = "SCRIPT"


class TrafficDirection:
    OUTGOING: Final = "outgoing"
    INCOMING: Final = "incoming"
    LIST: Final = [OUTGOING, INCOMING]
