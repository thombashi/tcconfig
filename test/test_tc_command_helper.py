# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import pytest

import tcconfig._common
from tcconfig._const import TcSubCommand
from tcconfig._tc_command_helper import get_tc_base_command


class Test_get_tc_base_command(object):
    @pytest.mark.parametrize(
        ["subcommand", "expected"],
        [
            [TcSubCommand.CLASS, "/sbin/tc class"],
            [TcSubCommand.FILTER, "/sbin/tc filter"],
            [TcSubCommand.QDISC, "/sbin/tc qdisc"],
        ],
    )
    def test_normal(self, monkeypatch, subcommand, expected):
        monkeypatch.setattr(tcconfig._common, "find_bin_path", lambda _: "/sbin/tc")

        assert get_tc_base_command(subcommand) == expected

    @pytest.mark.parametrize(
        ["subcommand", "expected"], [["qdisc", ValueError], [None, ValueError]]
    )
    def test_exception(self, subcommand, expected):
        with pytest.raises(expected):
            get_tc_base_command(subcommand)
