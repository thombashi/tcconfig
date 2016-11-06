# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import division
import itertools

import dataproperty
import pytest
from subprocrunner import SubprocessRunner


SKIP_TEST = False


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


def is_invalid_param(rate, delay, loss, corrupt):
    params = [
        rate,
        delay,
        loss,
        corrupt,
    ]

    return all([
        dataproperty.is_empty_string(param) for param in params
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
        "--overwrite",
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
            "direction", "network", "port", "overwrite",
        ],
        [
            opt_list
            for opt_list in itertools.product(
                NormalTestValue.RATE_LIST,
                NormalTestValue.DELAY_LIST,
                NormalTestValue.DELAY_DISTRO_LIST,
                NormalTestValue.PACKET_LOSS_RATE_LIST,
                NormalTestValue.CORRUPTION_RATE_LIST,
                NormalTestValue.DIRECTION_LIST,
                NormalTestValue.NETWORK_LIST,
                NormalTestValue.PORT_LIST,
                NormalTestValue.OVERWRITE_LIST)
        ])
    def test_smoke(
            self, device_option, rate, delay, delay_distro, loss, corrupt,
            direction, network, port, overwrite):

        if device_option is None:
            pytest.skip("device option is null")

        if is_invalid_param(rate, delay, loss, corrupt):
            pytest.skip("skip null parameters")

        command = " ".join([
            "tcset",
            "--device " + device_option,
            rate, delay, delay_distro, loss, corrupt,
            direction, network, port, overwrite,
        ])
        assert SubprocessRunner(command).run() == 0

        SubprocessRunner("tcdel --device " + device_option).run()
