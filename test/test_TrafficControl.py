# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

from __future__ import absolute_import
import itertools

import pytest
import thutils
import tcconfig
import tcconfig.traffic_control


MIN_PACKET_LOSS = 0.0000000232  # [%]


@pytest.fixture
def tc_obj():
    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()
    return tcconfig.traffic_control.TrafficControl(subproc_wrapper, "eth0")


@pytest.mark.parametrize(["value"], [
    ["".join(opt_list)]
    for opt_list in itertools.product(
        ["0.1", "1", "2147483647"],
        [
            "k", " k", "K", " K",
            "m", " m", "M", " M",
            "g", " g", "G", " G",
        ]
    )
])
def test_TrafficControl_validate_bandwidth_rate_normal(tc_obj, value):
    tc_obj.bandwidth_rate = value
    tc_obj._TrafficControl__validate_bandwidth_rate()


@pytest.mark.parametrize(["value", "expected"], [
    ["".join(opt_list), ValueError]
    for opt_list in itertools.product(
        ["0.1", "1", "2147483647"],
        [
            "kb", "kbps", "KB",
            "mb", "mbps", "MB",
            "gb", "gbps", "GB",
        ]
    )
])
def test_TrafficControl_validate_bandwidth_rate_exception_1(
        tc_obj, value, expected):
    tc_obj.bandwidth_rate = value
    with pytest.raises(expected):
        tc_obj._TrafficControl__validate_bandwidth_rate()


@pytest.mark.parametrize(["value", "expected"], [
    ["".join(opt_list), ValueError]
    for opt_list in itertools.product(
        ["-1", "0", "0.0"],
        ["k", "K", "m", "M", "g", "G"]
    )
])
def test_TrafficControl_validate_bandwidth_rate_exception_2(
        tc_obj, value, expected):
    tc_obj.bandwidth_rate = value
    with pytest.raises(expected):
        tc_obj._TrafficControl__validate_bandwidth_rate()


class Test_TrafficControl_validate:

    @pytest.mark.parametrize(
        [
            "rate", "delay", "delay_distro", "loss",
            "corrupt", "network", "port",
        ],
        [
            opt_list
            for opt_list in itertools.product(
                [None, "", "100K", "0.5M", "0.1G"],  # rate
                [None, 0, 10000],  # delay
                [None, 0, 10000],  # delay_distro
                [None, 0, MIN_PACKET_LOSS, 99],  # loss
                [None, 0, 99],  # corrupt
                [
                    None,
                    "",
                    "192.168.0.1", "192.168.0.254",
                    "192.168.0.1/32", "192.168.0.0/24"
                ],  # network
                [None, 0, 65535],  # port
            )
        ])
    def test_normal(
            self, tc_obj, rate, delay, delay_distro, loss, corrupt, network, port):
        tc_obj.bandwidth_rate = rate
        tc_obj.latency_ms = delay
        tc_obj.latency_distro_ms = delay_distro
        tc_obj.packet_loss_rate = loss
        tc_obj.corruption_rate = corrupt
        tc_obj.network = network
        tc_obj.port = port

        tc_obj.validate()

    @pytest.mark.parametrize(["value", "expected"], [
        [{"latency_ms": -1}, ValueError],
        [{"latency_ms": 10001}, ValueError],

        [{"latency_distro_ms": -1}, ValueError],
        [{"latency_distro_ms": 10001}, ValueError],

        [{"packet_loss_rate": -0.1}, ValueError],
        [{"packet_loss_rate": 99.1}, ValueError],

        [{"curruption_rate": -0.1}, ValueError],
        [{"curruption_rate": 99.1}, ValueError],

        [{"network": "192.168.0."}, ValueError],
        [{"network": "192.168.0.256"}, ValueError],
        [{"network": "192.168.0.0/0"}, ValueError],
        [{"network": "192.168.0.0/33"}, ValueError],
        [{"network": "192.168.0.2/24"}, ValueError],
        [{"network": "192.168.0.0000/24"}, ValueError],

        [{"port": -1}, ValueError],
        [{"port": 65536}, ValueError],
    ])
    def test_exception(self, tc_obj, value, expected):
        tc_obj.bandwidth_rate = value.get("bandwidth_rate")
        tc_obj.latency_ms = value.get("latency_ms")
        tc_obj.latency_distro_ms = value.get("latency_distro_ms")
        tc_obj.packet_loss_rate = value.get("packet_loss_rate")
        tc_obj.curruption_rate = value.get("curruption_rate")
        tc_obj.network = value.get("network")
        tc_obj.port = value.get("port")

        with pytest.raises(expected):
            tc_obj.validate()
