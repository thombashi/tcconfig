# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import division

import pytest

from tcconfig._converter import Humanreadable
from tcconfig._error import UnitNotFoundError


class Test_to_bit(object):

    @pytest.mark.parametrize(["value", "kilo_size", "expected"], [
        ["2b", 1024, 2],
        ["2 b", 1024, 2],
        ["2 B", 1024, 2],
        ["2k", 1024, 2 * 1024 ** 1],
        ["2 k", 1024, 2 * 1024 ** 1],
        ["2 K", 1024, 2 * 1024 ** 1],
        ["2m", 1024, 2 * 1024 ** 2],
        ["2 m", 1024, 2 * 1024 ** 2],
        ["2 M", 1024, 2 * 1024 ** 2],
        ["2g", 1024, 2 * 1024 ** 3],
        ["2 g", 1024, 2 * 1024 ** 3],
        ["2 G", 1024, 2 * 1024 ** 3],
        ["2t", 1024, 2 * 1024 ** 4],
        ["2 t", 1024, 2 * 1024 ** 4],
        ["2 T", 1024, 2 * 1024 ** 4],
        ["2p", 1024, 2 * 1024 ** 5],
        ["2 p", 1024, 2 * 1024 ** 5],
        ["2 P", 1024, 2 * 1024 ** 5],
        ["2.5 M", 1024, int(2.5 * 1024 ** 2)],
        ["2.5 m", 1024, int(2.5 * 1024 ** 2)],
        ["2b", 1000, 2],
        ["2 b", 1000, 2],
        ["2 B", 1000, 2],
        ["2k", 1000, 2 * 1000 ** 1],
        ["2 k", 1000, 2 * 1000 ** 1],
        ["2 K", 1000, 2 * 1000 ** 1],
        ["2m", 1000, 2 * 1000 ** 2],
        ["2 m", 1000, 2 * 1000 ** 2],
        ["2 M", 1000, 2 * 1000 ** 2],
        ["2g", 1000, 2 * 1000 ** 3],
        ["2 g", 1000, 2 * 1000 ** 3],
        ["2 G", 1000, 2 * 1000 ** 3],
        ["2t", 1000, 2 * 1000 ** 4],
        ["2 t", 1000, 2 * 1000 ** 4],
        ["2 T", 1000, 2 * 1000 ** 4],
        ["2p", 1000, 2 * 1000 ** 5],
        ["2 p", 1000, 2 * 1000 ** 5],
        ["2 P", 1000, 2 * 1000 ** 5],
        ["2.5 M", 1000, int(2.5 * 1000 ** 2)],
        ["2.5 m", 1000, int(2.5 * 1000 ** 2)],
    ])
    def test_normal(self, value, kilo_size, expected):
        assert Humanreadable(value, kilo_size).to_bit() == expected

    @pytest.mark.parametrize(["value", "kilo_size", "exception"], [
        ["10", 1000, UnitNotFoundError],
        ["", 1000, TypeError],
        [None, 1000, TypeError],
        [True, 1000, TypeError],
        [float("nan"), 1000, TypeError],
        ["a", 1000, ValueError],
        ["1k0 ", 1000, ValueError],
        ["10kb", 1000, ValueError],
        ["-2m", 1000, ValueError],
        ["2m", None, ValueError],
        ["2m", 1001, ValueError],
    ])
    def test_exception(self, value, kilo_size, exception):
        with pytest.raises(exception):
            Humanreadable(value, kilo_size).to_bit()


class Test_to_kilo_bit(object):

    @pytest.mark.parametrize(["value", "kilo_size", "expected"], [
        ["2b", 1024, 2 / 1024],
        ["2k", 1024, 2 * 1024 ** 0],
        ["2m", 1024, 2 * 1024 ** 1],
        ["2g", 1024, 2 * 1024 ** 2],
        ["2t", 1024, 2 * 1024 ** 3],
        ["2p", 1024, 2 * 1024 ** 4],
        ["2b", 1000, 2 / 1000],
        ["2k", 1000, 2 * 1000 ** 0],
        ["2m", 1000, 2 * 1000 ** 1],
        ["2g", 1000, 2 * 1000 ** 2],
        ["2t", 1000, 2 * 1000 ** 3],
        ["2p", 1000, 2 * 1000 ** 4],
    ])
    def test_normal(self, value, kilo_size, expected):
        assert Humanreadable(value, kilo_size).to_kilo_bit() == expected
