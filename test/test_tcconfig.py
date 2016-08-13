# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import division
import itertools
import json
import platform

import dataproperty
import pingparsing
import pytest
from subprocrunner import SubprocessRunner


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


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
    Tests of in this class are inappropriate for Travis CI.
    Execute following command at the local environment  when running tests:
      python setup.py test --addopts "--runxfail --device <test device>"

    These tests are expected to execute on following environment:
       - Linux w/ iputils-ping package
       - English environment (for parsing ping output)
    """

    @pytest.mark.xfail
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
        command = " ".join([
            "tcset",
            "--device " + device_option,
            rate, delay, delay_distro, loss,
            direction, network, port, overwrite,
        ])
        assert SubprocessRunner(command).run() == 0

        assert SubprocessRunner("tcdel --device " + device_option).run() == 0

    @pytest.mark.xfail
    @pytest.mark.parametrize(["overwrite", "expected"], [
        ["", 0],
        ["--overwrite", 255],
    ])
    def test_config_file(self, tmpdir, device_option, overwrite, expected):
        p = tmpdir.join("tcconfig.json")
        config = "{" + '"{:s}"'.format(device_option) + ": {" + """
        "outgoing": {
            "network=192.168.0.10/32, port=8080": {
                "delay": "10.0", 
                "loss": "0.01", 
                "rate": "250K", 
                "delay-distro": "2.0"
            }, 
            "network=0.0.0.0/0": {}
        }, 
        "incoming": {
            "network=192.168.10.0/24": {
                "corrupt": "0.02", 
                "rate": "1500K"
            }, 
            "network=0.0.0.0/0": {}
        }
    }
}
"""
        p.write(config)

        SubprocessRunner("tcdel --device " + device_option).run()
        command = " ".join(["tcset -f ", str(p), overwrite])
        assert SubprocessRunner(command).run() == expected

        runner = SubprocessRunner("tcshow --device " + device_option)
        runner.run()
        assert json.loads(runner.stdout) == json.loads(config)

        assert SubprocessRunner("tcdel --device " + device_option).run() == 0
