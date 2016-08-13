# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import json

import pytest
from subprocrunner import SubprocessRunner


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


class Test_tcshow(object):
    """
    Tests of in this class are inappropriate for Travis CI.
    Execute following command at the local environment  when running tests:
      python setup.py test --addopts "--runxfail --device <test device>"
    """

    @pytest.mark.xfail
    def test_normal(self, device_option):
        SubprocessRunner("tcdel --device " + device_option).run()

        command = " ".join([
            "tcset",
            "--device", device_option,
            "--delay", "10",
            "--delay-distro", "2",
            "--loss", "0.01",
            "--rate", "0.25M",
            "--network", "192.168.0.10",
            "--port", "8080",
        ])
        assert SubprocessRunner(command).run() == 0

        command = " ".join([
            "tcset",
            "--device", device_option,
            "--delay", "1",
            "--loss", "0.02",
            "--rate", "500K",
            "--direction", "incoming",
        ])
        assert SubprocessRunner(command).run() == 0

        command = " ".join([
            "tcshow",
            "--device", device_option,
        ])
        runner = SubprocessRunner(command)
        runner.run()

        expected = "{" + '"{:s}"'.format(device_option) + ": {" + """
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
            "network=0.0.0.0/0": {
                "delay": "1.0",
                "loss": "0.02",
                "rate": "500K"
            }
        }
    }
}"""

        assert json.loads(runner.stdout) == json.loads(expected)

        assert SubprocessRunner("tcdel --device " + device_option).run() == 0
