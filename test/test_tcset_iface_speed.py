# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import Tc

from .common import execute_tcdel


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


class Test_tcset_iface_speed(object):
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
            execute_tcdel(tc_target)

    @pytest.mark.parametrize(["rate"], [["990Gbps"]])
    def test_normal_exceed_max_rate(self, monkeypatch, device_option, rate):
        if device_option is None:
            pytest.skip("device option is null")

        for tc_target in [device_option]:
            monkeypatch.setattr("tcconfig._network._read_iface_speed", lambda x: "1")

            runner = SubprocessRunner([Tc.Command.TCSET, tc_target, "--rate", rate, "--overwrite"])
            assert runner.run() == 0, (runner.command_str, runner.returncode, runner.stderr)

            # finalize ---
            execute_tcdel(tc_target)

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
            execute_tcdel(tc_target)
