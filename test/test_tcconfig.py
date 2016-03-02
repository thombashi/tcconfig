# encoding: utf-8

'''
@author: Tsuyoshi Hombashi
'''

import itertools

import pytest
import thutils
import tcconfig


@pytest.fixture
def subproc_wrapper():
    return thutils.subprocwrapper.SubprocessWrapper()


DEVICE = "eth0"


class NormalTestValue:
    RATE_LIST = [
        "",
        "--rate 100K",
        "--rate 0.5M",
        "--rate 0.1G",
    ]
    DELAY_LIST = [
        "",
        "--delay 0",
        "--delay 10",
        "--delay 100",
    ]
    LOSS_LIST = [
        "",
        "--loss 0",
        "--loss 0.1",
        "--loss 99",
    ]
    NETWORK_LIST = [
        "",
        "--network 192.168.0.10",
        "--network 192.168.0.10/24",
    ]
    PORT_LIST = [
        "",
        "--port 80",
    ]
    OVERWRITE_LIST = [
        "",
        "--overwrite",
    ]


class Test_tcconfig:

    @pytest.mark.parametrize(["rate", "delay", "loss", "overwrite"], [
        opt_list
        for opt_list in itertools.product(
            NormalTestValue.RATE_LIST,
            NormalTestValue.DELAY_LIST,
            NormalTestValue.LOSS_LIST,
            NormalTestValue.OVERWRITE_LIST)
    ])
    def test_smoke(self, subproc_wrapper, rate, delay, loss, overwrite):
        option_list = [rate, delay, loss, overwrite]
        command = "tcset --device %s " % (DEVICE) + " ".join(option_list)
        assert subproc_wrapper.run(command) == 0

        command = "tcdel --device %s" % (DEVICE)
        assert subproc_wrapper.run(command) == 0


@pytest.fixture
def tc_obj():
    subproc_wrapper = thutils.subprocwrapper.SubprocessWrapper()
    return tcconfig.TrafficControl(subproc_wrapper, "eth0")


@pytest.mark.parametrize(["value"], [
    [None],
    [0],
    [10000],
])
def test_TrafficControl_validate_network_delay_normal(tc_obj, value):
    tc_obj.delay_ms = value
    tc_obj._TrafficControl__validate_network_delay()


@pytest.mark.parametrize(["value", "expected"], [
    [-1, ValueError],
    [10001, ValueError],
])
def test_TrafficControl_validate_network_delay_exception(tc_obj, value, expected):
    tc_obj.delay_ms = value
    with pytest.raises(expected):
        tc_obj._TrafficControl__validate_network_delay()


@pytest.mark.parametrize(["value"], [
    [None],
    [0],
    [99],
])
def test_TrafficControl_validate_packet_loss_rate_normal(tc_obj, value):
    tc_obj.loss_percent = value
    tc_obj._TrafficControl__validate_packet_loss_rate()


@pytest.mark.parametrize(["value", "expected"], [
    [-0.1, ValueError],
    [99.1, ValueError],
])
def test_TrafficControl_validate_packet_loss_rate_exception(tc_obj, value, expected):
    tc_obj.loss_percent = value
    with pytest.raises(expected):
        tc_obj._TrafficControl__validate_packet_loss_rate()


@pytest.mark.parametrize(["value"], [
    [None],
    [""],

    ["192.168.0.1"],
    ["192.168.0.254"],

    ["192.168.0.1/32"],
    ["192.168.0.0/24"],
])
def test_TrafficControl_validate_network_normal(tc_obj, value):
    tc_obj.network = value
    tc_obj._TrafficControl__validate_network()


@pytest.mark.parametrize(["value", "expected"], [
    ["192.168.0.", ValueError],
    ["192.168.0.256", ValueError],

    ["192.168.0.0/0", ValueError],
    ["192.168.0.0/33", ValueError],
    ["192.168.0.2/24", ValueError],
    ["192.168.0.0000/24", ValueError],
])
def test_TrafficControl_validate_network_exception(tc_obj, value, expected):
    tc_obj.network = value
    with pytest.raises(expected):
        tc_obj._TrafficControl__validate_network()


@pytest.mark.parametrize(["value"], [
    [None],
    [0],
    [65535],
])
def test_TrafficControl_validate_port_normal(tc_obj, value):
    tc_obj.port = value
    tc_obj._TrafficControl__validate_port()


@pytest.mark.parametrize(["value", "expected"], [
    [-1, ValueError],
    [65536, ValueError],
])
def test_TrafficControl_validate_port_exception(tc_obj, value, expected):
    tc_obj.port = value
    with pytest.raises(expected):
        tc_obj._TrafficControl__validate_port()
