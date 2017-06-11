# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import json

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import TcCommand


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
    def test_normal_ipv4(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        device_option = "--device {:s}".format(device_value)
        tcdel_command = "{:s} {:s}".format(TcCommand.TCDEL, device_option)

        assert SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            "--delay", "10",
            "--delay-distro", "2",
            "--loss", "0.01",
            "--duplicate", "0.5",
            "--reorder", "0.2",
            "--rate", "0.25K",
            "--network", "192.168.0.10",
            "--port", "8080",
            "--overwrite",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            "--delay", "1",
            "--loss", "1",
            "--rate", "100M",
            "--network", "192.168.1.0/24",
            "--add",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            "--delay", "10",
            "--delay-distro", "2",
            "--rate", "500K",
            "--direction", "incoming",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            "--delay", "1",
            "--loss", "0.02",
            "--duplicate", "0.5",
            "--reorder", "0.2",
            "--rate", "0.1M",
            "--network", "192.168.11.0/24",
            "--port", "80",
            "--direction", "incoming",
            "--add",
        ])).run() == 0

        runner = SubprocessRunner("{:s} {:s}".format(
            TcCommand.TCSHOW, device_option))
        runner.run()

        expected = "{" + '"{:s}"'.format(device_value) + ": {" + """
        "outgoing": {
           "dst-network=192.168.0.10/32, dst-port=8080, protocol=ip": {
                "delay": "10.0",
                "loss": "0.01",
                "duplicate": "0.5",
                "reorder": "0.2",
                "rate": "248",
                "delay-distro": "2.0"
            },
            "dst-network=192.168.1.0/24, protocol=ip": {
                "delay": "1.0",
                "loss": "1",
                "rate": "100M"
            }
        },
        "incoming": {
            "dst-network=192.168.11.0/24, dst-port=80, protocol=ip": {
                "delay": "1.0",
                "loss": "0.02",
                "duplicate": "0.5",
                "reorder": "0.2",
                "rate": "100K"
            },
            "dst-network=0.0.0.0/0, protocol=ip": {
                "delay": "10.0",
                "delay-distro": "2.0",
                "rate": "500K"
            }
        }
    }
}"""

        print("[expected]\n{}\n".format(expected))
        print("[actual]\n{}\n".format(runner.stdout))

        assert json.loads(runner.stdout) == json.loads(expected)

        SubprocessRunner(tcdel_command).run()

    @pytest.mark.xfail
    def test_normal_ipv6(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        device_option = "--device {:s}".format(device_value)
        tcdel_command = "{:s} {:s}".format(TcCommand.TCDEL, device_option)

        assert SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            "--delay", "10",
            "--delay-distro", "2",
            "--loss", "0.01",
            "--duplicate", "5",
            "--reorder", "2",
            "--rate", "0.25K",
            "--network", "::1",
            "--port", "8080",
            "--overwrite",
            "--ipv6",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            "--delay", "1",
            "--loss", "1",
            "--rate", "100M",
            "--network", "2001:db00::0/24",
            "--add",
            "--ipv6",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            "--delay", "10",
            "--delay-distro", "2",
            "--rate", "500K",
            "--direction", "incoming",
            "--ipv6",
        ])).run() == 0

        assert SubprocessRunner(" ".join([
            TcCommand.TCSET,
            device_option,
            "--delay", "1",
            "--loss", "0.02",
            "--duplicate", "5",
            "--reorder", "2",
            "--rate", "0.1M",
            "--network", "2001:db00::0/25",
            "--port", "80",
            "--direction", "incoming",
            "--add",
            "--ipv6",
        ])).run() == 0

        runner = SubprocessRunner("tcshow {:s} --ipv6".format(device_option))
        runner.run()

        expected = "{" + '"{:s}"'.format(device_value) + ": {" + """
        "outgoing": {
            "dst-network=::1/128, dst-port=8080, protocol=ipv6": {
                "delay": "10.0",
                "loss": "0.01",
                "duplicate": "5",
                "reorder": "2",
                "rate": "248",
                "delay-distro": "2.0"
            },
            "dst-network=2001:db00::/24, protocol=ipv6": {
                "delay": "1.0",
                "loss": "1",
                "rate": "100M"
            }
        },
        "incoming": {
            "dst-network=2001:db00::/25, dst-port=80, protocol=ipv6": {
                "delay": "1.0",
                "loss": "0.02",
                "duplicate": "5",
                "reorder": "2",
                "rate": "100K"
            },
            "protocol=ipv6": {
                "delay": "10.0",
                "rate": "500K",
                "delay-distro": "2.0"
            }
        }
    }
}"""

        print("[expected]\n{}\n".format(expected))
        print("[actual]\n{}\n".format(runner.stdout))

        assert json.loads(runner.stdout) == json.loads(expected)

        SubprocessRunner(tcdel_command).run()
