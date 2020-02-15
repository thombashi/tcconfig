"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""


import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc
from tcconfig.traffic_control import delete_all_rules


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


class Test_tcset_iface_speed:
    @pytest.mark.parametrize(["speed"], [[1], [-1]])  # para-virtualized network driver
    def test_smoke_speed(self, monkeypatch, device_option, speed):
        if device_option is None:
            pytest.skip("device option is null")

        for tc_target in [device_option]:
            monkeypatch.setattr("tcconfig._network._read_iface_speed", lambda x: speed)

            runner = SubprocessRunner(
                [Tc.Command.TCSET, tc_target, "--rate", "1kbps", "--overwrite"]
            )
            assert runner.run() == 0, (runner.command_str, runner.returncode, runner.stderr)

            # finalize ---
            delete_all_rules(tc_target)

    @pytest.mark.parametrize(["rate"], [["990Gbps"]])
    def test_normal_exceed_max_rate(self, monkeypatch, device_option, rate):
        if device_option is None:
            pytest.skip("device option is null")

        for tc_target in [device_option]:
            monkeypatch.setattr("tcconfig._network._read_iface_speed", lambda x: "1")

            runner = SubprocessRunner([Tc.Command.TCSET, tc_target, "--rate", rate, "--overwrite"])
            assert runner.run() == 0, (runner.command_str, runner.returncode, runner.stderr)

            # finalize ---
            delete_all_rules(tc_target)

    @pytest.mark.parametrize(["rate"], [["0kbps"]])
    def test_abnormal(self, monkeypatch, device_option, rate):
        if device_option is None:
            pytest.skip("device option is null")

        for tc_target in [device_option]:
            monkeypatch.setattr("tcconfig._network._read_iface_speed", lambda x: "1")

            runner = SubprocessRunner(
                " ".join([Tc.Command.TCSET, tc_target, "--rate", rate, "--overwrite"])
            )
            assert runner.run() != 0, (runner.command_str, runner.returncode, runner.stderr)

            # finalize ---
            delete_all_rules(tc_target)
