# encoding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import pytest

from tcconfig._netem_param import convert_rate_to_f


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
