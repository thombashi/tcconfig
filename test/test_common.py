# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

import pytest

from tcconfig._common import (
    is_anywhere_network,
    get_anywhere_network,
    sanitize_network,
)


class Test_is_anywhere_network(object):

    @pytest.mark.parametrize(["network", "ip_version", "expected"], [
        ["0.0.0.0/0", 4, True],
        ["192.168.0.0/0", 4, False],
        ["::0/0", 6, True],
        ["2001:db00::0/24", 6, False],
    ])
    def test_normal(self, network, ip_version, expected):
        assert is_anywhere_network(network, ip_version) == expected

    @pytest.mark.parametrize(["network", "ip_version",  "expected"], [
        [None, 4, ValueError],
        ["0.0.0.0/0", None, ValueError],
    ])
    def test_exception(self, network, ip_version, expected):
        with pytest.raises(expected):
            is_anywhere_network(network, ip_version)


class Test_get_anywhere_network(object):

    @pytest.mark.parametrize(["value", "expected"], [
        [4, "0.0.0.0/0"],
        ["4", "0.0.0.0/0"],
        [6, "::0/0"],
        ["6", "::0/0"],
    ])
    def test_normal(self, value, expected):
        assert get_anywhere_network(value) == expected

    @pytest.mark.parametrize(["value", "expected"], [
        [None, ValueError],
        ["test", ValueError],
    ])
    def test_exception(self, value, expected):
        with pytest.raises(expected):
            get_anywhere_network(value)


class Test_sanitize_network(object):

    @pytest.mark.parametrize(["value", "ip_version", "expected"], [
        ["192.168.0.1", 4, "192.168.0.1/32"],
        ["192.168.0.1/32", 4, "192.168.0.1/32"],
        ["192.168.0.0/24", 4, "192.168.0.0/24"],
        ["192.168.0.0/23", 4, "192.168.0.0/23"],
        ["2001:db00::0/24", 6, "2001:db00::/24"],
        ["anywhere", 4, "0.0.0.0/0"],
        ["ANYWHERE", 4, "0.0.0.0/0"],
        ["anywhere", 6, "::0/0"],
        ["ANYWHERE", 6, "::0/0"],
        ["", 4, "0.0.0.0/0"],
        [None, 4, "0.0.0.0/0"],
        ["", 6, "::0/0"],
        [None, 6, "::0/0"],
    ])
    def test_normal(self, value, ip_version, expected):
        assert sanitize_network(value, ip_version) == expected

    @pytest.mark.parametrize(["value", "ip_version", "expected"], [
        ["192.168.0.1111", 4, ValueError],
        ["192.168.0.", 4, ValueError],
        [".168.0.1", 4, ValueError],
        ["192.168.1.0/23", 4, ValueError],
        ["192.168.0.0/33", 4, ValueError],
        ["192.168.1.0/24", 6, ValueError],
        ["2001:db00::0/24", 4, ValueError],
    ])
    def test_exception(self, value, ip_version, expected):
        with pytest.raises(expected):
            sanitize_network(value, ip_version)
