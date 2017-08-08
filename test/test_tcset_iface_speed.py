# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import absolute_import

import pytest
from subprocrunner import SubprocessRunner

from tcconfig._const import TcCommand

from .common import execute_tcdel


@pytest.fixture
def device_option(request):
    return request.config.getoption("--device")


class Test_tcset_iface_speed(object):

    @pytest.mark.parametrize(["speed"], [
        [1],
        [-1],  # para-virtualized network driver
    ])
    def test_smoke_speed(self, monkeypatch, device_option, speed):
        if device_option is None:
            pytest.skip("device option is null")

        execute_tcdel(device_option)
        monkeypatch.setattr(
            "tcconfig._common.read_iface_speed", lambda x: speed)

        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "--rate {:s}".format("1kbps"),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() == 0

        # finalize ---
        execute_tcdel(device_option)

    @pytest.mark.parametrize(["rate"], [
        ["0kbps"],
        ["99Gbps"],
    ])
    def test_abnormal(self, monkeypatch, device_option, rate):
        if device_option is None:
            pytest.skip("device option is null")

        execute_tcdel(device_option)
        monkeypatch.setattr(
            "tcconfig._common.read_iface_speed", lambda x: "1")

        command_list = [
            TcCommand.TCSET,
            "--device {:s}".format(device_option),
            "--rate {:s}".format(rate),
        ]
        assert SubprocessRunner(" ".join(command_list)).run() != 0

        # finalize ---
        execute_tcdel(device_option)
