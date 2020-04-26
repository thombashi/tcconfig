"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import json

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc

from .common import print_test_result, runner_helper


@pytest.fixture
def device_value(request):
    return request.config.getoption("--device")


def execute_tcdel(device):
    return SubprocessRunner([Tc.Command.TCDEL, device, "--all"], dry_run=False).run()


class Test_tcdel:
    """
    Tests in this class are not executable on CI services.
    Execute the following command at the local environment to running tests:

        pytest --runxfail --device=<test device>
    """

    def test_normal_ipv4(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        for device_option in [[device_value], ["--device", device_value]]:
            execute_tcdel(device_value)

            tcshow_cmd = [Tc.Command.TCSHOW] + device_option

            runner_helper(
                [Tc.Command.TCSET]
                + device_option
                + [
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
            runner_helper(
                [Tc.Command.TCSET]
                + device_option
                + [
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
            runner_helper(
                [Tc.Command.TCSET]
                + device_option
                + [
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
            runner_helper(
                [Tc.Command.TCSET]
                + device_option
                + [
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

            runner = SubprocessRunner(tcshow_cmd)
            runner.run()
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

            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)

            assert json.loads(runner.stdout) == json.loads(expected)

            runner_helper([Tc.Command.TCDEL] + device_option + ["--network", "192.168.1.0/24"])
            runner_helper(
                [Tc.Command.TCDEL]
                + device_option
                + ["--network", "192.168.11.0/24", "--port", "80", "--direction", "incoming"]
            )

            runner = SubprocessRunner(tcshow_cmd)
            runner.run()
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                            "dst-network=192.168.0.10/32, dst-port=8080, protocol=ip": {
                                "delay": "10.0ms",
                                "loss": "0.01%",
                                "duplicate": "0.5%",
                                "filter_id": "800::800",
                                "delay-distro": "2.0ms",
                                "rate": "248bps",
                                "reorder": "0.2%"
                            }
                        },
                        "incoming": {
                            "protocol=ip": {
                                "delay": "10.0ms",
                                "rate": "500Kbps",
                                "delay-distro": "2.0ms",
                                "filter_id": "800::800"
                            }
                        }
                    }
                }"""
            )

            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            runner_helper([Tc.Command.TCDEL] + device_option + ["--id", "800::800"])
            runner_helper(
                [Tc.Command.TCDEL] + device_option + ["--id", "800::800", "--direction", "incoming"]
            )

            runner = SubprocessRunner(tcshow_cmd)
            runner.run()
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
            "outgoing": {},
            "incoming": {}
        }
    }"""
            )

            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            # finalize ---
            execute_tcdel(device_value)

    def test_normal_ipv6(self, device_value):
        if device_value is None:
            pytest.skip("device option is null")

        for device_option in [[device_value], ["--device", device_value]]:
            execute_tcdel(device_value)

            tcshow_cmd = [Tc.Command.TCSHOW] + device_option

            runner_helper(
                [Tc.Command.TCSET]
                + device_option
                + [
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
            runner_helper(
                [Tc.Command.TCSET]
                + device_option
                + [
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
            runner_helper(
                [Tc.Command.TCSET]
                + device_option
                + [
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
            runner_helper(
                [Tc.Command.TCSET]
                + device_option
                + [
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

            runner = SubprocessRunner(tcshow_cmd + ["--ipv6"])
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

            runner_helper(
                [Tc.Command.TCDEL] + device_option + ["--network", "2001:db00::0/24", "--ipv6"]
            )
            runner_helper(
                [Tc.Command.TCDEL]
                + device_option
                + [
                    "--network",
                    "2001:db00::0/25",
                    "--port",
                    "80",
                    "--direction",
                    "incoming",
                    "--ipv6",
                ]
            )

            runner = SubprocessRunner(tcshow_cmd)
            runner.run()
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {
                            "protocol=ipv6": {
                                "delay": "10.0ms",
                                "loss": "0.01%",
                                "duplicate": "5%",
                                "filter_id": "800::800",
                                "delay-distro": "2.0ms",
                                "rate": "248bps",
                                "reorder": "2%"
                            }
                        },
                        "incoming": {
                            "protocol=ipv6": {
                                "delay": "10.0ms",
                                "rate": "500Kbps",
                                "delay-distro": "2.0ms",
                                "filter_id": "800::800"
                            }
                        }
                    }
                }"""
            )

            print_test_result(expected=expected, actual=runner.stdout, error=runner.stderr)
            assert json.loads(runner.stdout) == json.loads(expected)

            runner_helper([Tc.Command.TCDEL] + device_option + ["--id", "800::800", "--ipv6"])
            runner_helper(
                [Tc.Command.TCDEL]
                + device_option
                + ["--id", "800::800", "--direction", "incoming", "--ipv6"]
            )

            runner = SubprocessRunner(tcshow_cmd)
            runner.run()
            expected = (
                "{"
                + '"{:s}"'.format(device_value)
                + ": {"
                + """
                        "outgoing": {},
                        "incoming": {}
                    }
                }"""
            )

            # finalize ---
            execute_tcdel(device_value)

    def test_abnormal(self):
        assert execute_tcdel("not_exist_device") != 0
