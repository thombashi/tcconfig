# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import json

import pytest
from subprocrunner import SubprocessRunner


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


class Test_tcshow(object):
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:
      python setup.py test --addopts "--runxfail --device=<test device>"
    """

    @pytest.mark.xfail
    def test_normal(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        device_option = "--device {:s}".format(device_value)
        tcdel_command = "tcdel {:s}".format(device_option)

        assert SubprocessRunner(" ".join([
            "tcset",
            device_option,
            "--delay", "10",
            "--delay-distro", "2",
            "--loss", "0.01",
            "--rate", "0.25K",
            "--network", "192.168.0.10",
            "--port", "8080",
            "--overwrite",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            "tcset",
            device_option,
            "--delay", "1",
            "--loss", "1",
            "--rate", "100M",
            "--network", "192.168.1.0/24",
            "--add",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            "tcset",
            device_option,
            "--delay", "10",
            "--delay-distro", "2",
            "--rate", "500K",
            "--direction", "incoming",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            "tcset",
            device_option,
            "--delay", "1",
            "--loss", "0.02",
            "--rate", "0.1M",
            "--network", "192.168.11.0/24",
            "--port", "80",
            "--direction", "incoming",
            "--add",
        ])).run() == 0

        runner = SubprocessRunner("tcshow {:s}".format(device_option))
        runner.run()

        expected = "{" + '"{:s}"'.format(device_value) + ": {" + """
        "outgoing": {
            "network=192.168.1.0/24": {
                "delay": "1.0",
                "loss": "1",
                "rate": "100M"
            },
           "network=192.168.0.10/32, port=8080": {
                "delay": "10.0",
                "loss": "0.01",
                "rate": "248",
                "delay-distro": "2.0"
            }
        },
        "incoming": {
            "network=192.168.11.0/24, port=80": {
                "delay": "1.0",
                "loss": "0.02",
                "rate": "100K"
            },
            "network=0.0.0.0/0": {
                "delay": "10.0",
                "delay-distro": "2.0",
                "rate": "500K"
            }
        }
    }
}"""

        print("[expected]\n{}".format(expected))
        print("[actual]\n{}".format(runner.stdout))

        assert json.loads(runner.stdout) == json.loads(expected)

        SubprocessRunner(tcdel_command).run()
