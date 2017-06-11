# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import itertools

import pytest

from allpairspy import AllPairs
from tcconfig._const import (
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
        "dummy", bandwidth_rate=value, direction=TrafficDirection.OUTGOING)
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
            "dummy", bandwidth_rate=value, direction=TrafficDirection.OUTGOING)
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
        tc_obj = TrafficControl("dummy", bandwidth_rate=value)
        tc_obj.validate_bandwidth_rate()


class Test_TrafficControl_validate(object):

    @pytest.mark.parametrize(
        [
            "rate", "direction", "delay", "delay_distro", "loss", "duplicate",
            "corrupt", "network", "src_port", "dst_port",
        ],
        [
            opt_list
            for opt_list in AllPairs([
                [None, "", "100K", "0.5M", "0.1G"],  # rate
                [TrafficDirection.OUTGOING],
                [
                    None, TrafficControl.MIN_LATENCY_MS,
                    TrafficControl.MAX_LATENCY_MS,
                ],  # delay
                [
                    None, TrafficControl.MIN_LATENCY_MS,
                    TrafficControl.MAX_LATENCY_MS,
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
                [
                    None,
                    "",
                    "192.168.0.1", "192.168.0.254",
                    "192.168.0.1/32", "192.168.0.0/24"
                ],  # network
                [None, 65535],  # src_port
                [None, 65535],  # dst_port
            ], n=3)
        ])
    def test_normal(
            self, device_option, rate, direction, delay, delay_distro,
            loss, duplicate, corrupt, network, src_port, dst_port):
        if device_option is None:
            pytest.skip("device option is null")

        tc_obj = TrafficControl(
            device=device_option,
            direction=direction,
            bandwidth_rate=rate,
            latency_ms=delay,
            latency_distro_ms=delay_distro,
            packet_loss_rate=loss,
            packet_duplicate_rate=duplicate,
            corruption_rate=corrupt,
            dst_network=network,
            src_port=src_port,
            dst_port=dst_port,
            src_network=None,
            is_enable_iptables=True,
        )

        if is_invalid_param(
                rate, delay, loss, duplicate, corrupt, reordering=None):
            with pytest.raises(ValueError):
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
                    TrafficControl.MIN_LATENCY_MS + 0.1,
                    TrafficControl.MAX_LATENCY_MS,
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
            latency_ms=delay,
            reordering_rate=reordering,
        )

        tc_obj.validate()

    @pytest.mark.parametrize(["value", "expected"], [
        [{"latency_ms": TrafficControl.MIN_LATENCY_MS - 1}, ValueError],
        [{"latency_ms": TrafficControl.MAX_LATENCY_MS + 1}, ValueError],

        [
            {
                "latency_ms": 100,
                "latency_distro_ms": TrafficControl.MIN_LATENCY_MS - 1,
            },
            ValueError
        ],
        [
            {
                "latency_ms": 100,
                "latency_distro_ms": TrafficControl.MAX_LATENCY_MS + 1,
            },
            ValueError
        ],

        [
            {"packet_loss_rate": TrafficControl.MIN_PACKET_LOSS_RATE - 0.1},
            ValueError
        ],
        [
            {"packet_loss_rate": TrafficControl.MAX_PACKET_LOSS_RATE + 0.1},
            ValueError
        ],

        [
            {
                "latency_ms": 100,
                "packet_duplicate_rate": TrafficControl.MIN_PACKET_DUPLICATE_RATE - 0.1,
            },
            ValueError
        ],
        [
            {
                "latency_ms": 100,
                "packet_duplicate_rate": TrafficControl.MAX_PACKET_DUPLICATE_RATE + 0.1,
            },
            ValueError
        ],

        [
            {"corruption_rate": TrafficControl.MIN_CORRUPTION_RATE - 0.1},
            ValueError
        ],
        [
            {"corruption_rate": TrafficControl.MAX_CORRUPTION_RATE + 0.1},
            ValueError
        ],

        [
            {"reordering_rate": TrafficControl.MIN_REORDERING_RATE - 0.1},
            ValueError
        ],
        [
            {"reordering_rate": TrafficControl.MAX_REORDERING_RATE + 0.1},
            ValueError
        ],


        [{Tc.Param.DST_NETWORK: "192.168.0."}, ValueError],
        [{Tc.Param.DST_NETWORK: "192.168.0.256"}, ValueError],
        [{Tc.Param.DST_NETWORK: "192.168.0.0/0"}, ValueError],
        [{Tc.Param.DST_NETWORK: "192.168.0.0/33"}, ValueError],
        [{Tc.Param.DST_NETWORK: "192.168.0.2/24"}, ValueError],
        [{Tc.Param.DST_NETWORK: "192.168.0.0000/24"}, ValueError],

        [{"src_port": -1}, ValueError],
        [{"src_port": 65536}, ValueError],

        [{"dst_port": -1}, ValueError],
        [{"dst_port": 65536}, ValueError],
    ])
    def test_exception(self, device_option, value, expected):
        if device_option is None:
            pytest.skip("device option is null")

        tc_obj = TrafficControl(
            device=device_option,
            bandwidth_rate=value.get("bandwidth_rate"),
            latency_ms=value.get("latency_ms"),
            latency_distro_ms=value.get("latency_distro_ms"),
            packet_loss_rate=value.get("packet_loss_rate"),
            packet_duplicate_rate=value.get("packet_duplicate_rate"),
            corruption_rate=value.get("corruption_rate"),
            dst_network=value.get(Tc.Param.DST_NETWORK),
            src_port=value.get("src_port"),
            dst_port=value.get("dst_port"),
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
            device=device_option, dst_network=network, is_ipv6=is_ipv6)

        assert tc_obj.ip_version == expected_ip_ver
        assert tc_obj.protocol == expected_protocol
        assert tc_obj.protocol_match == expected_protocol_match
