# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import

import json

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc

from .common import execute_tcdel


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


class Test_tcset_change(object):
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        python setup.py test --addopts "--device=<test device>"

    These tests expected to execute in the following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    def test_normal(self, device_value):
        if device_value is None:
            pytest.skip("device is null")

        device_option = "--device {:s}".format(device_value)

        command_list = [
            Tc.Command.TCSET, device_option,
            "--delay 100ms --rate 50k --network 192.168.1.2 --overwrite",
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        command_list = [
            Tc.Command.TCSET, device_option,
            "--delay 200.0ms",
            "--delay-distro 20",
            "--rate 100k",
            "--loss 0.01",
            "--duplicate 5",
            "--reorder 2",
            "--network 192.168.1.3",
            "--add",
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        runner = SubprocessRunner("{:s} {:s}".format(
            Tc.Command.TCSHOW, device_option))
        runner.run()

        expected = "{" + '"{:s}"'.format(device_value) + ": {" + """
        "outgoing": {
            "dst-network=192.168.1.2/32, protocol=ip": {
                "filter_id": "800::800",
                "delay": "100.0ms",
                "rate": "50K"
            },
            "dst-network=192.168.1.3/32, protocol=ip": {
                "filter_id": "800::801",
                "delay": "200.0ms",
                "loss": 0.01,
                "duplicate": 5,
                "delay-distro": "20.0ms",
                "rate": "100K",
                "reorder": 2
            }
        },
        "incoming": {}
    }
}"""

        print("[expected]\n{}\n".format(expected))
        print("[actual]\n{}\n".format(runner.stdout))
        assert json.loads(runner.stdout) == json.loads(expected)

        command_list = [
            Tc.Command.TCSET, device_option,
            "--delay 300ms",
            "--delay-distro 30",
            "--rate 200k",
            "--loss 0.02",
            "--duplicate 5.5",
            "--reorder 0.2",
            "--network 192.168.1.3",
            "--change",
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        runner = SubprocessRunner("{:s} {:s}".format(
            Tc.Command.TCSHOW, device_option))
        runner.run()

        expected = "{" + '"{:s}"'.format(device_value) + ": {" + """
        "outgoing": {
            "dst-network=192.168.1.2/32, protocol=ip": {
                "filter_id": "800::800",
                "delay": "100.0ms",
                "rate": "50K"
            },
            "dst-network=192.168.1.3/32, protocol=ip": {
                "filter_id": "800::801",
                "delay": "300.0ms",
                "loss": 0.02,
                "duplicate": 5.5,
                "delay-distro": "30.0ms",
                "rate": "200K",
                "reorder": 0.2
            }
        },
        "incoming": {}
    }
}"""

        print("[expected]\n{}\n".format(expected))
        print("[actual]\n{}\n".format(runner.stdout))
        assert json.loads(runner.stdout) == json.loads(expected)

        # finalize ---
        execute_tcdel(device_option)
