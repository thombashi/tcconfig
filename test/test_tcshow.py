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


class Test_tcshow:
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        pytest --runxfail --device=<test device>
    """

    def test_normal_empty(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        for tc_target in [device_value, "--device {}".format(device_value)]:
            delete_all_rules(tc_target)

            runner = SubprocessRunner(" ".join([Tc.Command.TCSHOW, tc_target]))
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                        },
                        "incoming": {
                        }
                    }
                }"""
            )

            print(runner.command_str)
            runner.run()

            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert runner.returncode == 0
            assert json.loads(runner.stdout) == json.loads(expected)

            # smoe test for --color option
            runner = SubprocessRunner(" ".join([Tc.Command.TCSHOW, tc_target, "--color"]))
            assert runner.run() == 0, runner.stderr

    def test_normal_ipv4(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        for tc_target in [device_value, "--device {}".format(device_value)]:
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        tc_target,
                        "--delay",
                        "10",
                        "--delay-distro",
                        "2",
                        "--loss",
                        "0.01",
                        "--duplicate",
                        "0.5",
                        "--reorder",
                        "0.2",
                        "--rate",
                        "0.25Kbps",
                        "--network",
                        "192.168.0.10",
                        "--port",
                        "8080",
                        "--overwrite",
                    ]
                )
            )

            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        tc_target,
                        "--delay",
                        "1",
                        "--loss",
                        "1",
                        "--rate",
                        "100Mbit/s",
                        "--network",
                        "192.168.1.0/24",
                        "--add",
                    ]
                )
            )
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        tc_target,
                        "--delay",
                        "10",
                        "--delay-distro",
                        "2",
                        "--rate",
                        "500Kbit/s",
                        "--direction",
                        "incoming",
                    ]
                )
            )
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        tc_target,
                        "--delay",
                        "1",
                        "--loss",
                        "0.02",
                        "--duplicate",
                        "0.5",
                        "--reorder",
                        "0.2",
                        "--rate",
                        "0.1Mbit/s",
                        "--network",
                        "192.168.11.0/24",
                        "--port",
                        "80",
                        "--direction",
                        "incoming",
                        "--add",
                    ]
                )
            )

            runner = SubprocessRunner(" ".join([Tc.Command.TCSHOW, tc_target]))
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                        "dst-network=192.168.0.10/32, dst-port=8080, protocol=ip": {
                                "filter_id": "800::800",
                                "delay": "10.0ms",
                                "loss": "0.01%",
                                "duplicate": "0.5%",
                                "reorder": "0.2%",
                                "rate": "248bps",
                                "delay-distro": "2.0ms"
                            },
                            "dst-network=192.168.1.0/24, protocol=ip": {
                                "filter_id": "800::801",
                                "delay": "1.0ms",
                                "loss": "1%",
                                "rate": "100Mbps"
                            }
                        },
                        "incoming": {
                            "dst-network=192.168.11.0/24, dst-port=80, protocol=ip": {
                                "filter_id": "800::801",
                                "delay": "1.0ms",
                                "loss": "0.02%",
                                "duplicate": "0.5%",
                                "reorder": "0.2%",
                                "rate": "100Kbps"
                            },
                            "protocol=ip": {
                                "filter_id": "800::800",
                                "delay": "10.0ms",
                                "delay-distro": "2.0ms",
                                "rate": "500Kbps"
                            }
                        }
                    }
                }"""
            )

            runner.run()
            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            # smoe test for --color option
            runner = SubprocessRunner(" ".join([Tc.Command.TCSHOW, tc_target, "--color"]))
            assert runner.run() == 0, runner.stderr

            delete_all_rules(tc_target)

    def test_normal_ipv6(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        for tc_target in [device_value, "--device {}".format(device_value)]:
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        tc_target,
                        "--delay",
                        "10",
                        "--delay-distro",
                        "2",
                        "--loss",
                        "0.01",
                        "--duplicate",
                        "5",
                        "--reorder",
                        "2",
                        "--rate",
                        "0.25Kbps",
                        "--network",
                        "::1",
                        "--port",
                        "8080",
                        "--overwrite",
                        "--ipv6",
                    ]
                )
            )
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        tc_target,
                        "--delay",
                        "1",
                        "--loss",
                        "1",
                        "--rate",
                        "100Mbit/s",
                        "--network",
                        "2001:db00::0/24",
                        "--add",
                        "--ipv6",
                    ]
                )
            )
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        tc_target,
                        "--delay",
                        "10",
                        "--delay-distro",
                        "2",
                        "--rate",
                        "500Kbit/s",
                        "--direction",
                        "incoming",
                        "--ipv6",
                    ]
                )
            )
            runner_helper(
                " ".join(
                    [
                        Tc.Command.TCSET,
                        tc_target,
                        "--delay",
                        "1",
                        "--loss",
                        "0.02",
                        "--duplicate",
                        "5",
                        "--reorder",
                        "2",
                        "--rate",
                        "0.1Mbit/s",
                        "--network",
                        "2001:db00::0/25",
                        "--port",
                        "80",
                        "--direction",
                        "incoming",
                        "--add",
                        "--ipv6",
                    ]
                )
            )

            runner = SubprocessRunner(" ".join([Tc.Command.TCSHOW, tc_target, "--ipv6"]))
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                            "dst-network=::1/128, dst-port=8080, protocol=ipv6": {
                                "filter_id": "800::800",
                                "delay": "10.0ms",
                                "loss": "0.01%",
                                "duplicate": "5%",
                                "reorder": "2%",
                                "rate": "248bps",
                                "delay-distro": "2.0ms"
                            },
                            "dst-network=2001:db00::/24, protocol=ipv6": {
                                "filter_id": "800::801",
                                "delay": "1.0ms",
                                "loss": "1%",
                                "rate": "100Mbps"
                            }
                        },
                        "incoming": {
                            "dst-network=2001:db00::/25, dst-port=80, protocol=ipv6": {
                                "filter_id": "800::801",
                                "delay": "1.0ms",
                                "loss": "0.02%",
                                "duplicate": "5%",
                                "reorder": "2%",
                                "rate": "100Kbps"
                            },
                            "protocol=ipv6": {
                                "filter_id": "800::800",
                                "delay": "10.0ms",
                                "rate": "500Kbps",
                                "delay-distro": "2.0ms"
                            }
                        }
                    }
                }"""
            )

            runner.run()
            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            # smoe test for --color option
            runner = SubprocessRunner(" ".join([Tc.Command.TCSHOW, tc_target, "--color"]))
            assert runner.run() == 0, runner.stderr

            delete_all_rules(tc_target)
