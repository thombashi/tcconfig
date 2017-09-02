# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import itertools

from allpairspy import AllPairs
import pytest

from tcconfig._const import (
    ShapingAlgorithm,
    Tc,
    TrafficDirection,
)
from tcconfig._error import (
    InvalidParameterError,
    UnitNotFoundError,
)
from tcconfig.traffic_control import TrafficControl

from .common import is_invalid_param


MIN_VALID_PACKET_LOSS = 0.0000000232  # [%]


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


@pytest.mark.parametrize(["value"], [
    ["".join(opt_list)]
    for opt_list in AllPairs([
        ["0.1", "+1.25", "30"],
        [
            "k", " k ", "K", " K ", "kbps", "Kbps",
            "m", " m ", "M", " M ", "mbps", "Mbps",
            "g", " g ", "G", " G ", "gbps", "Gbps",
        ]
    ])
])
def test_TrafficControl_validate_bandwidth_rate_normal(value):
    tc_obj = TrafficControl(
        "dummy", bandwidth_rate=value, direction=TrafficDirection.OUTGOING,
        shaping_algorithm=ShapingAlgorithm.HTB)
    tc_obj.validate_bandwidth_rate()


@pytest.mark.parametrize(["value", "expected"], [
    ["".join(opt_list), UnitNotFoundError]
    for opt_list in AllPairs([
        ["0.1", "1"],
        ["", "kb", "KB", "mb", "MB", "gb", "GB"]
    ])
] + [
    ["".join(value), InvalidParameterError]
    for value in ("B", "K", "M", "G")
] + [
    ["0bps", InvalidParameterError],
    ["34359738361bps", InvalidParameterError],
])
def test_TrafficControl_validate_bandwidth_rate_exception_1(value, expected):
    with pytest.raises(expected):
        tc_obj = TrafficControl(
            "dummy", bandwidth_rate=value, direction=TrafficDirection.OUTGOING,
            latency_time=Tc.ValueRange.LatencyTime.MIN,
            latency_distro_time=Tc.ValueRange.LatencyTime.MIN,
            shaping_algorithm=ShapingAlgorithm.HTB)
        tc_obj.validate_bandwidth_rate()


@pytest.mark.parametrize(["value", "expected"], [
    ["".join(opt_list), InvalidParameterError]
    for opt_list in itertools.product(
        ["-1", "0", "0.0"],
        ["k", "K", "m", "M", "g", "G"]
    )
])
def test_TrafficControl_validate_bandwidth_rate_exception_2(value, expected):
    with pytest.raises(expected):
        tc_obj = TrafficControl(
            "dummy", bandwidth_rate=value,
            latency_time=Tc.ValueRange.LatencyTime.MIN,
            latency_distro_time=Tc.ValueRange.LatencyTime.MIN,
            shaping_algorithm=ShapingAlgorithm.HTB)
        tc_obj.validate_bandwidth_rate()


class Test_TrafficControl_validate(object):

    @pytest.mark.parametrize(
        [
            "rate", "direction", "delay", "delay_distro", "loss", "duplicate",
            "corrupt",
            "src_network", "exclude_src_network",
            "dst_network", "exclude_dst_network",
            "src_port", "exclude_src_port",
            "dst_port", "exclude_dst_port",
            "shaping_algorithm",
        ],
        [
            opt_list
            for opt_list in AllPairs([
                [None, "", "100K", "0.5M", "0.1G"],  # rate
                [TrafficDirection.OUTGOING],
                [
                    Tc.ValueRange.LatencyTime.MIN,
                    Tc.ValueRange.LatencyTime.MAX,
                ],  # delay
                [
                    Tc.ValueRange.LatencyTime.MIN,
                    Tc.ValueRange.LatencyTime.MAX,
                ],  # delay_distro
                [
                    None,
                    TrafficControl.MIN_PACKET_LOSS_RATE, MIN_VALID_PACKET_LOSS,
                    TrafficControl.MAX_PACKET_LOSS_RATE,
                ],  # loss
                [
                    None, TrafficControl.MIN_PACKET_DUPLICATE_RATE,
                    TrafficControl.MAX_PACKET_DUPLICATE_RATE,
                ],  # duplicate
                [
                    None, TrafficControl.MIN_CORRUPTION_RATE,
                    TrafficControl.MAX_CORRUPTION_RATE,
                ],  # corrupt
                [None, "192.168.0.1", "192.168.0.0/24"],  # src_network
                [None, "192.168.0.1", "192.168.0.0/25"],  # exclude_src_network
                [
                    None,
                    "",
                    "192.168.0.1", "192.168.0.254",
                    "192.168.0.1/32", "192.168.0.0/24"
                ],  # dst_network
                [None, "192.168.0.1", "192.168.0.0/25"],  # exclude_dst_network
                [None, 65535],  # src_port
                [None, 22],  # exclude_src_port
                [None, 65535],  # dst_port
                [None, 22],  # exclude_dst_port
                [
                    ShapingAlgorithm.HTB, ShapingAlgorithm.TBF,
                ],  # shaping_algorithm
            ], n=3)
        ])
    def test_normal(
            self, device_option, rate, direction, delay, delay_distro,
            loss, duplicate, corrupt,
            src_network, exclude_src_network,
            dst_network, exclude_dst_network,
            src_port, exclude_src_port,
            dst_port, exclude_dst_port,
            shaping_algorithm):
        if device_option is None:
            pytest.skip("device option is null")

        tc_obj = TrafficControl(
            device=device_option,
            direction=direction,
            bandwidth_rate=rate,
            latency_time=delay,
            latency_distro_time=delay_distro,
            packet_loss_rate=loss,
            packet_duplicate_rate=duplicate,
            corruption_rate=corrupt,
            src_network=src_network,
            exclude_src_network=exclude_src_network,
            dst_network=dst_network,
            exclude_dst_network=exclude_dst_network,
            src_port=src_port,
            exclude_src_port=exclude_src_port,
            dst_port=dst_port,
            exclude_dst_port=exclude_dst_port,
            is_enable_iptables=True,
            shaping_algorithm=shaping_algorithm,
        )

        if is_invalid_param(
                rate, delay, loss, duplicate, corrupt, reordering=None):
            with pytest.raises(InvalidParameterError):
                tc_obj.validate()
        else:
            tc_obj.validate()

    @pytest.mark.parametrize(
        ["direction", "delay", "reordering"],
        [
            opt_list
            for opt_list in AllPairs([
                [TrafficDirection.OUTGOING],
                [
                    "0.1ms",
                    Tc.ValueRange.LatencyTime.MAX,
                ],  # delay
                [
                    TrafficControl.MIN_REORDERING_RATE,
                    TrafficControl.MAX_REORDERING_RATE,
                ],  # reordering
            ], n=2)
        ])
    def test_normal_reordering(
            self, device_option, direction, delay, reordering):
        if device_option is None:
            pytest.skip("device option is null")

        tc_obj = TrafficControl(
            device=device_option,
            direction=direction,
            latency_time=delay,
            latency_distro_time=Tc.ValueRange.LatencyTime.MIN,
            reordering_rate=reordering,
            shaping_algorithm=ShapingAlgorithm.HTB,
        )

        tc_obj.validate()

    @pytest.mark.parametrize(["value", "expected"], [
        [
            {"latency_time": "-1ms"},
            InvalidParameterError,
        ],
        [
            {"latency_time": "61min"},
            InvalidParameterError,
        ],

        [
            {
                "latency_time": "100ms",
                "latency_distro_time": "-1ms",
            },
            InvalidParameterError,
        ],
        [
            {
                "latency_time": "100ms",
                "latency_distro_time": "61min",
            },
            InvalidParameterError,
        ],

        [
            {"packet_loss_rate": TrafficControl.MIN_PACKET_LOSS_RATE - 0.1},
            InvalidParameterError,
        ],
        [
            {"packet_loss_rate": TrafficControl.MAX_PACKET_LOSS_RATE + 0.1},
            InvalidParameterError,
        ],

        [
            {
                "latency_time": "100ms",
                "packet_duplicate_rate": TrafficControl.MIN_PACKET_DUPLICATE_RATE - 0.1,
            },
            InvalidParameterError,
        ],
        [
            {
                "latency_time": "100ms",
                "packet_duplicate_rate": TrafficControl.MAX_PACKET_DUPLICATE_RATE + 0.1,
            },
            InvalidParameterError,
        ],

        [
            {"corruption_rate": TrafficControl.MIN_CORRUPTION_RATE - 0.1},
            InvalidParameterError,
        ],
        [
            {"corruption_rate": TrafficControl.MAX_CORRUPTION_RATE + 0.1},
            InvalidParameterError,
        ],

        [
            {"reordering_rate": TrafficControl.MIN_REORDERING_RATE - 0.1},
            InvalidParameterError,
        ],
        [
            {"reordering_rate": TrafficControl.MAX_REORDERING_RATE + 0.1},
            InvalidParameterError,
        ],

        [{Tc.Param.DST_NETWORK: "192.168.0."}, InvalidParameterError],
        [{Tc.Param.DST_NETWORK: "192.168.0.256"}, InvalidParameterError],
        [{Tc.Param.DST_NETWORK: "192.168.0.0/0"}, InvalidParameterError],
        [{Tc.Param.DST_NETWORK: "192.168.0.0/33"}, InvalidParameterError],
        [{Tc.Param.DST_NETWORK: "192.168.0.2/24"}, InvalidParameterError],
        [{Tc.Param.DST_NETWORK: "192.168.0.0000/24"}, InvalidParameterError],

        [{"src_port": -1}, InvalidParameterError],
        [{"src_port": 65536}, InvalidParameterError],

        [{"dst_port": -1}, InvalidParameterError],
        [{"dst_port": 65536}, InvalidParameterError],
    ])
    def test_exception(self, device_option, value, expected):
        if device_option is None:
            pytest.skip("device option is null")

        tc_obj = TrafficControl(
            device=device_option,
            bandwidth_rate=value.get("bandwidth_rate"),
            latency_time=value.get("latency_time", Tc.ValueRange.LatencyTime.MIN),
            latency_distro_time=value.get(
                "latency_distro_time", Tc.ValueRange.LatencyTime.MIN),
            packet_loss_rate=value.get("packet_loss_rate"),
            packet_duplicate_rate=value.get("packet_duplicate_rate"),
            corruption_rate=value.get("corruption_rate"),
            dst_network=value.get(Tc.Param.DST_NETWORK),
            src_port=value.get("src_port"),
            dst_port=value.get("dst_port"),
            shaping_algorithm=ShapingAlgorithm.HTB,
        )

        with pytest.raises(expected):
            tc_obj.validate()


class Test_TrafficControl_ipv4(object):

    @pytest.mark.parametrize(
        [
            "network", "is_ipv6",
            "expected_ip_ver", "expected_protocol", "expected_protocol_match"
        ],
        [
            ["192.168.0.1", False, 4, "ip", "ip"],
            ["192.168.0.0/24", False, 4, "ip", "ip"],
            ["::1", True, 6, "ipv6", "ip6"],
            ["2001:db00::0/24", True, 6, "ipv6", "ip6"],
        ])
    def test_normal(
            self, device_option, network, is_ipv6,
            expected_ip_ver, expected_protocol, expected_protocol_match):
        if device_option is None:
            pytest.skip("device option is null")

        tc_obj = TrafficControl(
            device=device_option, dst_network=network, is_ipv6=is_ipv6,
            latency_time=Tc.ValueRange.LatencyTime.MIN,
            latency_distro_time=Tc.ValueRange.LatencyTime.MIN,
            shaping_algorithm=ShapingAlgorithm.HTB,
        )

        assert tc_obj.ip_version == expected_ip_ver
        assert tc_obj.protocol == expected_protocol
        assert tc_obj.protocol_match == expected_protocol_match
