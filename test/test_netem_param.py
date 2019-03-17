# encoding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import pytest
from humanreadable import ParameterError

from tcconfig._netem_param import NetemParameter, convert_rate_to_f


class Test_convert_rate_to_f(object):
    @pytest.mark.parametrize(
        ["value", "expected"],
        [[0, 0], [100.0, 100.0], ["1", 1.0], ["100", 100.0], ["0.1%", 0.1], [" 10 % ", 10.0]],
    )
    def test_normal(self, value, expected):
        assert convert_rate_to_f(value) == expected

    @pytest.mark.parametrize(
        ["value", "expected"], [["hoge", ValueError], ["1&", ValueError], ["%1", ValueError]]
    )
    def test_exception(self, value, expected):
        with pytest.raises(expected):
            convert_rate_to_f(value)


class Test_NetemParameter_validate_bandwidth_rate(object):
    @pytest.mark.parametrize(
        ["value", "expected"],
        [["1bps", ParameterError], ["7bps", ParameterError], ["8bps", None], ["1Gbps", None]],
    )
    def test_normal(self, value, expected):
        param = NetemParameter(device="eth0", bandwidth_rate=value)

        if expected is None:
            param.validate_bandwidth_rate()
        else:
            with pytest.raises(expected):
                param.validate_bandwidth_rate()
