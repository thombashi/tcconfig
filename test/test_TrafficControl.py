# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

import itertools

import pytest
import thutils
import tcconfig


MIN_PACKET_LOSS = 0.0000000232  # [%]


@pytest.fixture
def tc_obj():
    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()
    return tcconfig.TrafficControl(subproc_wrapper, "eth0")


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
def test_TrafficControl_validate_rate_normal(tc_obj, value):
    tc_obj.rate = value
    tc_obj._TrafficControl__validate_rate()


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
def test_TrafficControl_validate_rate_exception_1(tc_obj, value, expected):
    tc_obj.rate = value
    with pytest.raises(expected):
        tc_obj._TrafficControl__validate_rate()


@pytest.mark.parametrize(["value", "expected"], [
    ["".join(opt_list), ValueError]
    for opt_list in itertools.product(
        ["-1", "0", "0.0"],
        ["k", "K", "m", "M", "g", "G"]
    )
])
def test_TrafficControl_validate_rate_exception_2(tc_obj, value, expected):
    tc_obj.rate = value
    with pytest.raises(expected):
        tc_obj._TrafficControl__validate_rate()


class Test_TrafficControl_validate:

    @pytest.mark.parametrize(["rate", "delay", "loss", "network", "port"], [
        opt_list
        for opt_list in itertools.product(
            [None, "", "100K", "0.5M", "0.1G"],  # rate
            [None, 0, 10000],  # delay
            [None, 0, MIN_PACKET_LOSS, 99],  # loss
            [
                None,
                "",
                "192.168.0.1", "192.168.0.254",
                "192.168.0.1/32", "192.168.0.0/24"
            ],  # network
            [None, 0, 65535],  # port
        )
    ])
    def test_normal(self, tc_obj, rate, delay, loss, network, port):
        tc_obj.rate = rate
        tc_obj.delay_ms = delay
        tc_obj.loss_percent = loss
        tc_obj.network = network
        tc_obj.port = port

        tc_obj.validate()

    @pytest.mark.parametrize(["value", "expected"], [
        [{"delay_ms": -1}, ValueError],
        [{"delay_ms": 10001}, ValueError],

        [{"loss_percent": -0.1}, ValueError],
        [{"loss_percent": 99.1}, ValueError],

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
        tc_obj.rate = value.get("rate")
        tc_obj.delay_ms = value.get("delay_ms")
        tc_obj.loss_percent = value.get("loss_percent")
        tc_obj.network = value.get("network")
        tc_obj.port = value.get("port")

        with pytest.raises(expected):
            tc_obj.validate()
