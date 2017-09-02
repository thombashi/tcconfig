# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import division

import pytest

from tcconfig._converter import (
    Humanreadable,
    HumanReadableTime,
)
from tcconfig._error import (
    InvalidParameterError,
    UnitNotFoundError,
)


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
        ["a", 1000, InvalidParameterError],
        ["1k0 ", 1000, InvalidParameterError],
        ["10kb", 1000, InvalidParameterError],
        ["-2m", 1000, InvalidParameterError],
        ["2m", None, InvalidParameterError],
        ["2m", 1001, InvalidParameterError],
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


class Test_HumanReadableTime_get_value(object):

    @pytest.mark.parametrize(["value", "expected"], [
        ["10", "10.000000ms"],
        ["1s", "1.000000sec"],
        ["1S", "1.000000sec"],
        ["1sec", "1.000000sec"],
        ["0.1secs", "0.100000sec"],
        ["1.5second", "1.500000sec"],
        ["1Seconds", "1.000000sec"],
        ["11ms", "11.000000ms"],
        ["11.5MS", "11.500000ms"],
        ["11msec", "11.000000ms"],
        ["11Msecs", "11.000000ms"],
        ["11millisecond", "11.000000ms"],
        ["11milliseconds", "11.000000ms"],
        ["123us", "123.000000us"],
        ["123US", "123.000000us"],
        ["123usec", "123.000000us"],
        ["123Usecs", "123.000000us"],
        ["123microsecond", "123.000000us"],
        ["123microseconds", "123.000000us"],
        ["0.1m", "6.000000sec"],
        ["0.2M", "12.000000sec"],
        ["1.1min", "66.000000sec"],
        ["0.1Mins", "6.000000sec"],
        ["0.1minute", "6.000000sec"],
        ["0.1Minutes", "6.000000sec"],
    ])
    def test_normal(self, value, expected):
        assert HumanReadableTime(value).get_value() == expected
        assert str(HumanReadableTime(value)) == expected

    @pytest.mark.parametrize(["value", "exception"], [
        ["", InvalidParameterError],
        [None, TypeError],
        [True, TypeError],
        [float("nan"), TypeError],
        ["a", InvalidParameterError],
        ["1k0 ", InvalidParameterError],
        ["10kb", InvalidParameterError],
    ])
    def test_exception(self, value, exception):
        with pytest.raises(exception):
            HumanReadableTime(value).get_value()


class Test_HumanReadableTime_get_msec(object):

    @pytest.mark.parametrize(["value", "expected"], [
        ["10", 10],
        ["1s", 1000],
        ["1ms", 1],
        ["1000us", 1],
        ["1m", 60000],
    ])
    def test_normal(self, value, expected):
        assert HumanReadableTime(value).get_msec() == expected


class Test_HumanReadableTime_validate(object):

    @pytest.mark.parametrize(["value", "min_value", "max_value"], [
        ["1", "0", "60m"],
        ["1s", "0s", "60m"],
        ["1s", HumanReadableTime("0s"), HumanReadableTime("60m")],
        ["1s", "1s", "60m"],
        ["10ms", "0s", "60m"],
        ["100us", "0s", "60m"],
    ])
    def test_normal(self, value, min_value, max_value):
        HumanReadableTime(value).validate(
            min_value=min_value, max_value=max_value)

    @pytest.mark.parametrize(["value", "min_value", "max_value", "expected"], [
        ["1s", "0s", "1ms", InvalidParameterError],
        ["-1s", "0s", "60m", InvalidParameterError],
        ["10ms", "0s", "1ms", InvalidParameterError],
        ["-10ms", "0s", "60m", InvalidParameterError],
        ["100us", "0s", "60us", InvalidParameterError],
        ["-100us", "0s", "60m", InvalidParameterError],
    ])
    def test_exception(self, value, min_value, max_value, expected):
        with pytest.raises(expected):
            HumanReadableTime(value).validate(
                min_value=min_value, max_value=max_value)
