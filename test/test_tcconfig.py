# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import division, print_function, unicode_literals

import pytest
import typepy
from allpairspy import AllPairs
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc

from .common import execute_tcdel


SKIP_TEST = False


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


def is_valid_combination(row):
    if all([typepy.is_null_string(param) for param in row]):
        return False

    return True


def is_invalid_param(rate, delay, loss, corrupt):
    params = [rate, delay, loss, corrupt]

    return all([typepy.is_null_string(param) for param in params])


class NormalTestValue(object):
    RATE_LIST = ["", "--rate 100Kbps", "--rate 0.5Mbps"]
    DELAY_LIST = ["", "--delay 100ms"]
    DELAY_DISTRO_LIST = ["", "--delay-distro 20ms"]
    PACKET_LOSS_RATE_LIST = ["", "--loss 0.1", "--loss 10%"]
    CORRUPTION_RATE_LIST = ["", "--corrupt 0.1", "--loss 10%"]
    DIRECTION_LIST = ["", "--direction outgoing", "--direction incoming"]
    NETWORK_LIST = ["", "--network 192.168.0.10", "--network 192.168.0.0/24"]
    PORT_LIST = ["", "--port 80"]
    OVERWRITE_LIST = ["", "--add", "--overwrite"]
    IPTABLES_LIST = ["", "--iptables"]


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
            "rate",
            "delay",
            "delay_distro",
            "loss",
            "corrupt",
            "direction",
            "network",
            "port",
            "overwrite",
            # "is_enable_iptables",
        ],
        [
            opt_list
            for opt_list in AllPairs(
                [
                    NormalTestValue.RATE_LIST,
                    NormalTestValue.DELAY_LIST,
                    NormalTestValue.DELAY_DISTRO_LIST,
                    NormalTestValue.PACKET_LOSS_RATE_LIST,
                    NormalTestValue.CORRUPTION_RATE_LIST,
                    NormalTestValue.DIRECTION_LIST,
                    NormalTestValue.NETWORK_LIST,
                    NormalTestValue.PORT_LIST,
                    NormalTestValue.OVERWRITE_LIST,
                    # NormalTestValue.IPTABLES_LIST,
                ],
                n=3,
                filter_func=is_valid_combination,
            )
        ],
    )
    def test_smoke(
        self,
        device_value,
        rate,
        delay,
        delay_distro,
        loss,
        corrupt,
        direction,
        network,
        port,
        overwrite,  # is_enable_iptables
    ):

        if device_value is None:
            pytest.skip("device is empty")

        if is_invalid_param(rate, delay, loss, corrupt):
            pytest.skip("skip null parameters")

        for device_option in [device_value, "--device {}".format(device_value)]:
            execute_tcdel(device_value)

            command = " ".join(
                [
                    Tc.Command.TCSET,
                    device_option,
                    rate,
                    delay,
                    delay_distro,
                    loss,
                    corrupt,
                    direction,
                    network,
                    port,
                    overwrite,
                    # is_enable_iptables,
                ]
            )
            print("command: {}".format(command))
            tcset_proc = SubprocessRunner(command)
            assert tcset_proc.run() == 0, tcset_proc.stderr

            execute_tcdel(device_value)
