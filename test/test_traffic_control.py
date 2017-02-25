# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import itertools

import pytest

from allpairspy import AllPairs
from tcconfig._traffic_direction import TrafficDirection
from tcconfig.traffic_control import TrafficControl

from .common import is_invalid_param


MIN_PACKET_LOSS = 0.0000000232  # [%]


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


@pytest.mark.parametrize(["value"], [
    ["".join(opt_list)]
    for opt_list in AllPairs([
        ["0.1", "1", "2147483647"],
        [
            "k", " k", "K", " K",
            "m", " m", "M", " M",
            "g", " g", "G", " G",
        ]
    ])
])
def test_TrafficControl_validate_bandwidth_rate_normal(value):
    tc_obj = TrafficControl("dummy", bandwidth_rate=value)
    tc_obj.validate_bandwidth_rate()


@pytest.mark.parametrize(["value", "expected"], [
    ["".join(opt_list), ValueError]
    for opt_list in AllPairs([
        ["0.1", "1", "2147483647"],
        [
            "kb", "kbps", "KB",
            "mb", "mbps", "MB",
            "gb", "gbps", "GB",
        ]
    ])
])
def test_TrafficControl_validate_bandwidth_rate_exception_1(value, expected):
    tc_obj = TrafficControl("dummy", bandwidth_rate=value)
    with pytest.raises(expected):
        tc_obj.validate_bandwidth_rate()


@pytest.mark.parametrize(["value", "expected"], [
    ["".join(opt_list), ValueError]
    for opt_list in itertools.product(
        ["-1", "0", "0.0"],
        ["k", "K", "m", "M", "g", "G"]
    )
])
def test_TrafficControl_validate_bandwidth_rate_exception_2(value, expected):
    tc_obj = TrafficControl("dummy", bandwidth_rate=value)
    with pytest.raises(expected):
        tc_obj.validate_bandwidth_rate()


class Test_TrafficControl_validate(object):

    @pytest.mark.parametrize(
        [
            "rate", "direction", "delay", "delay_distro", "loss",
            "corrupt", "network", "port",
        ],
        [
            opt_list
            for opt_list in AllPairs([
                [None, "", "100K", "0.5M", "0.1G"],  # rate
                [TrafficDirection.OUTGOING],
                [None, 0, 10000],  # delay
                [None, 0, 10000],  # delay_distro
                [None, 0, MIN_PACKET_LOSS, 100],  # loss
                [None, 0, 100],  # corrupt
                [
                    None,
                    "",
                    "192.168.0.1", "192.168.0.254",
                    "192.168.0.1/32", "192.168.0.0/24"
                ],  # network
                [None, 0, 65535],  # port
            ], n=3)
        ])
    def test_normal(
            self, device_option, rate, direction, delay, delay_distro, loss,
            corrupt, network, port):
        if device_option is None:
            pytest.skip("device option is null")

        tc_obj = TrafficControl(
            device=device_option,
            direction=direction,
            bandwidth_rate=rate,
            latency_ms=delay,
            latency_distro_ms=delay_distro,
            packet_loss_rate=loss,
            corruption_rate=corrupt,
            network=network,
            port=port,
            src_network=None,
            is_enable_iptables=True,
        )

        if is_invalid_param(rate, delay, loss, corrupt):
            with pytest.raises(ValueError):
                tc_obj.validate()
        else:
            tc_obj.validate()

    @pytest.mark.parametrize(["value", "expected"], [
        [{"latency_ms": -1}, ValueError],
        [{"latency_ms": 3600001}, ValueError],

        [{"latency_distro_ms": -1}, ValueError],
        [{"latency_distro_ms": 10001}, ValueError],

        [{"packet_loss_rate": -0.1}, ValueError],
        [{"packet_loss_rate": 100.1}, ValueError],

        [{"corruption_rate": -0.1}, ValueError],
        [{"corruption_rate": 100.1}, ValueError],

        [{"network": "192.168.0."}, ValueError],
        [{"network": "192.168.0.256"}, ValueError],
        [{"network": "192.168.0.0/0"}, ValueError],
        [{"network": "192.168.0.0/33"}, ValueError],
        [{"network": "192.168.0.2/24"}, ValueError],
        [{"network": "192.168.0.0000/24"}, ValueError],

        [{"port": -1}, ValueError],
        [{"port": 65536}, ValueError],
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
            corruption_rate=value.get("corruption_rate"),
            network=value.get("network"),
            port=value.get("port"),
        )

        with pytest.raises(expected):
            tc_obj.validate()
