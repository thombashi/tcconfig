# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import pytest

from tcconfig._common import sanitize_network


class Test_sanitize_network:

    @pytest.mark.parametrize(["value", "expected"], [
        ["192.168.0.1", "192.168.0.1/32"],
        ["192.168.0.1/32", "192.168.0.1/32"],
        ["192.168.0.0/24", "192.168.0.0/24"],
        ["192.168.0.0/23", "192.168.0.0/23"],
        ["anywhere", "0.0.0.0/0"],
        ["ANYWHERE", "0.0.0.0/0"],
        ["", ""],
        [None, ""],
    ])
    def test_normal(self, value, expected):
        assert sanitize_network(value) == expected

    @pytest.mark.parametrize(["value", "expected"], [
        ["192.168.0.1111", ValueError],
        ["192.168.0.", ValueError],
        [".168.0.1", ValueError],
        ["192.168.1.0/23", ValueError],
        ["192.168.0.0/33", ValueError],
        ["test", ValueError],
    ])
    def test_exception(self, value, expected):
        with pytest.raises(expected):
            sanitize_network(value)
