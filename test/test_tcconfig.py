# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import division
from __future__ import unicode_literals

import pytest
from subprocrunner import SubprocessRunner
import typepy

from allpairspy import AllPairs
from tcconfig._const import TcCommand


SKIP_TEST = False


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


def is_valid_combination(row):
    if all([typepy.is_null_string(param) for param in row]):
        return False

    return True


def is_invalid_param(rate, delay, loss, corrupt):
    params = [
        rate,
        delay,
        loss,
        corrupt,
    ]

    return all([
        typepy.is_null_string(param) for param in params
    ])


class NormalTestValue(object):
    RATE_LIST = [
        "",
        "--rate 100K",
        "--rate 0.5M",
    ]
    DELAY_LIST = [
        "",
        "--delay 100",
    ]
    DELAY_DISTRO_LIST = [
        "",
        "--delay-distro 20",
    ]
    PACKET_LOSS_RATE_LIST = [
        "",
        "--loss 0.1",
    ]
    CORRUPTION_RATE_LIST = [
        "",
        "--corrupt 0.1",
    ]
    DIRECTION_LIST = [
        "",
        "--direction outgoing",
        "--direction incoming",
    ]
    NETWORK_LIST = [
        "",
        "--network 192.168.0.10",
        "--network 192.168.0.0/24",
    ]
    PORT_LIST = [
        "",
        "--port 80",
    ]
    OVERWRITE_LIST = [
        "",
        "--add",
        "--overwrite",
    ]
    IPTABLES_LIST = [
        "",
        "--iptables",
    ]


class Test_tcconfig(object):
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:
      python setup.py test --addopts "--runxfail --device=<test device>"

    These tests are expected to execute on following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    @pytest.mark.skipif("SKIP_TEST is True")
    @pytest.mark.parametrize(
        [
            "rate", "delay", "delay_distro", "loss", "corrupt",
            "direction", "network", "port", "overwrite", "is_enable_iptables",
        ],
        [
            opt_list
            for opt_list in AllPairs([
                NormalTestValue.RATE_LIST,
                NormalTestValue.DELAY_LIST,
                NormalTestValue.DELAY_DISTRO_LIST,
                NormalTestValue.PACKET_LOSS_RATE_LIST,
                NormalTestValue.CORRUPTION_RATE_LIST,
                NormalTestValue.DIRECTION_LIST,
                NormalTestValue.NETWORK_LIST,
                NormalTestValue.PORT_LIST,
                NormalTestValue.OVERWRITE_LIST,
                NormalTestValue.IPTABLES_LIST,
            ], n=3, filter_func=is_valid_combination)
        ])
    def test_smoke(
            self, device_value, rate, delay, delay_distro, loss, corrupt,
            direction, network, port, overwrite, is_enable_iptables):

        if device_value is None:
            pytest.skip("device is empty")

        if is_invalid_param(rate, delay, loss, corrupt):
            pytest.skip("skip null parameters")

        device_option = "--device {}".format(device_value)

        SubprocessRunner("{:s} {:s}".format(
            TcCommand.TCDEL, device_option)).run()

        tcset_proc = SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            rate, delay, delay_distro, loss, corrupt,
            direction, network, port, overwrite, is_enable_iptables,
        ]))
        assert tcset_proc.run() == 0, tcset_proc.stderr

        SubprocessRunner("tcdel {:s}".format(device_option)).run()
