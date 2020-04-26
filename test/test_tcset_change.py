"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import json

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc
from tcconfig.traffic_control import delete_all_rules

from .common import print_test_result, runner_helper


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


class Test_tcset_change:
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        pytest --device=<test device>

    These tests expected to execute in the following environment:
       - Linux w/ iputils-ping package
       - English locale (for parsing ping output)
    """

    def test_smoke_multiple(self, device_value):
        if device_value is None:
            pytest.skip("device is null")

        for device_option in [device_value, "--device {}".format(device_value)]:
            delete_all_rules(device_option)

            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        device_option,
                        "--delay 100ms --rate 50Kbps --network 192.168.1.2 --change",
                    ]
                )
            )
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        device_option,
                        "--delay 100ms --rate 50Kbps --network 192.168.1.3 --change",
                    ]
                )
            )

            delete_all_rules(device_option)

    def test_normal(self, device_value):
        if device_value is None:
            pytest.skip("device is null")

        for device_option in [device_value, "--device {}".format(device_value)]:
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        device_option,
                        "--delay 100ms --rate 50Kbps --network 192.168.1.2 --overwrite",
                    ]
                )
            )
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        device_option,
                        "--delay 200.0ms",
                        "--delay-distro 20",
                        "--rate 100Kbps",
                        "--loss 0.01%",
                        "--duplicate 5%",
                        "--reorder 2%",
                        "--network 192.168.1.3",
                        "--add",
                    ]
                )
            )

            runner = SubprocessRunner("{:s} {:s}".format(Tc.Command.TCSHOW, device_option))
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                            "dst-network=192.168.1.2/32, protocol=ip": {
                                "filter_id": "800::800",
                                "delay": "100.0ms",
                                "rate": "50Kbps"
                            },
                            "dst-network=192.168.1.3/32, protocol=ip": {
                                "filter_id": "800::801",
                                "delay": "200.0ms",
                                "loss": "0.01%",
                                "duplicate": "5%",
                                "delay-distro": "20.0ms",
                                "rate": "100Kbps",
                                "reorder": "2%"
                            }
                        },
                        "incoming": {}
                    }
                }"""
            )
            runner.run()
            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        device_option,
                        "--delay 300ms",
                        "--delay-distro 30",
                        "--rate 200Kbps",
                        "--loss 0.02%",
                        "--duplicate 5.5%",
                        "--reorder 0.2%",
                        "--network 192.168.1.3",
                        "--change",
                    ]
                )
            )

            runner = SubprocessRunner("{:s} {:s}".format(Tc.Command.TCSHOW, device_option))
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                            "dst-network=192.168.1.2/32, protocol=ip": {
                                "filter_id": "800::800",
                                "delay": "100.0ms",
                                "rate": "50Kbps"
                            },
                            "dst-network=192.168.1.3/32, protocol=ip": {
                                "filter_id": "800::801",
                                "delay": "300.0ms",
                                "loss": "0.02%",
                                "duplicate": "5.5%",
                                "delay-distro": "30.0ms",
                                "rate": "200Kbps",
                                "reorder": "0.2%"
                            }
                        },
                        "incoming": {}
                    }
                }"""
            )
            runner.run()
            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            # finalize ---
            delete_all_rules(device_option)
